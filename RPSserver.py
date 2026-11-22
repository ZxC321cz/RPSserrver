import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

VALID_MOVES = {"rock", "paper", "scissors"}
MIN_PLAYERS = 2
START_TIMEOUT = 15.0


class ServerGameCoordinator:
    def __init__(self, SERVER_IP: str = "0.0.0.0", PORT: int = 8080):

        self.SERVER_IP = SERVER_IP
        self.PORT = PORT

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # Server configs
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # For port reuse
        
        self.players: dict[socket.socket, str] = {} # dict of connected players(to validate all operations with clients)

        self.ready_players: set[str] = set() # players, which ready to play

        self.lobby_deadline: float | None = None # timer
        self.last_reminder: dict[socket.socket, float] = {} # reminder to use commands for players
        
        self.beats = {                      #
            "rock": "scissors",             #
            "paper": "rock",                # dict of rules
            "scissors": "paper"             #
        }                                   #

        self.lock = threading.Lock()        # locker for threads, don't allow to access 1 data for several threads

        self.game_started = threading.Event()   # flag for start 
        self.game_finished = threading.Event()  # flag for finish

    def register_nickname(self, client_socket: socket.socket) -> bool:
        # Nick registration(recieving, validating and adding to dict)
        while True:
            client_socket.sendall("Enter nickname!\n ".encode())
            raw_nick = client_socket.recv(1024)

            if not raw_nick:
                return None
            
            nick = raw_nick.decode().strip()

            if not nick:
                client_socket.sendall("Nickname can't be empty!\n ".encode())
                continue

            with self.lock:
                if nick in self.players.values():
                    client_socket.sendall("Nickname has already exist, enter another!\n ".encode())
                    continue
                self.players[client_socket] = nick
                return nick


    def notify_players(self, message):
        # Text to all
        with self.lock:
            sockets = list(self.players.keys()) # To avoid idling

        for sock in sockets:
            try:
                sock.sendall(message.encode())
            except OSError: # avoiding dead clients
                with self.lock:
                    self.players.pop(sock, None)
                try:
                    sock.close()
                except OSError:
                    pass


    def ask_player_move(self, client_socket: socket.socket) -> str | None:
        # Function, that collect move from each player
        try:
            client_socket.settimeout(None)
        except OSError:
            return None

        while True:
            try:
                client_socket.sendall("Choose rock, paper or scissors:\n".encode())
                move = client_socket.recv(1024)
            except OSError:
                return None

            if not move:
                return None

            cleaned_move = move.decode(errors="ignore").strip().lower()

            if cleaned_move not in {"rock", "paper", "scissors"}:
                try:
                    client_socket.sendall(
                        "Wrong input, choose rock, paper or scissors:\n".encode()
                    )
                except OSError:
                    return None
                continue

            return cleaned_move


    def _collect_move_for_player(self, sock: socket.socket, nick: str) -> tuple[socket.socket, str, str | None]:
        # Helper function
        move = self.ask_player_move(sock)
        return sock, nick, move
    
    
    def round(self, round_num: int) -> list[str]:
        # Initializing the round
        with self.lock:
            players_snapshot = list(self.players.items())

        if len(players_snapshot) < 2:
            return [nick for _, nick in players_snapshot]

        self.notify_players(f"Round {round_num} started!\n")
        choices: dict[str, str] = {}

        with ThreadPoolExecutor(max_workers=len(players_snapshot)) as executor: # using concurrent.futures module to provide simultanious text to all users, because with.lock blocks other threads
            if self.game_finished.is_set():
                return []
            futures = [
                executor.submit(self._collect_move_for_player, sock, nick)
                for sock, nick in players_snapshot
            ]
            for future in as_completed(futures):
                sock, nick, move = future.result()
                if move is None:
                    with self.lock:
                        self.players.pop(sock, None)
                        self.ready_players.discard(sock)
                    try:
                        sock.close()
                    except OSError:
                        pass
                    continue
                choices[nick] = move

        if len(choices) < 2:
            return list(choices.keys())

        return self.game(choices)


    def game(self, choices: dict[str, str]) -> list[str]:
        # Winners determinant
        unique_moves = set(choices.values())

        if len(unique_moves) != 2:
            return []
        
        move_a, move_b = list(unique_moves)
        
        if self.beats[move_a] == move_b:
            winning_move = move_a

        elif self.beats[move_b] == move_a:
            winning_move = move_b
        
        winners = []

        for player, move in choices.items():
            if move == winning_move:
                winners.append(player)
        return winners


    def play_match(self) -> str:
        # Sequential playing of rounds
        round_num = 1
        try:
            while True:
                with self.lock:
                    players_snapshot = list(self.players.items())
                
                if len(players_snapshot) == 0:
                    return None
                
                if len(players_snapshot) == 1:
                    _, winner_nick = players_snapshot[0]
                    self.notify_players(f"Winner: {winner_nick}")
                    return winner_nick
                
                winners = self.round(round_num)

                if not winners:
                    self.notify_players("Draw! Replaying round...")
                    continue
                
                winner_set = set(winners)
                for sock, nick in players_snapshot:
                    if nick not in winner_set:
                        with self.lock:
                            self.players.pop(sock, None)
                        try:
                            sock.sendall("You were eliminated!\n".encode())
                        except OSError:
                            pass
                        try:
                            print(f"[DISCONNECTED] {nick}")
                            sock.close()
                        except OSError:
                            pass
                
                round_num += 1
        finally:
            self.game_finished.set()

    def _remind_unready_player(self, client_socket, now: float) -> bool:
        # Reminder for unready players. Text to each player
        data: str | None = None
        with self.lock:
            if (client_socket not in self.players or client_socket in self.ready_players):
                return True
            
            last = self.last_reminder.get(client_socket, 0.0)
            if now - last < 1.0:
                return True
            
            self.last_reminder[client_socket] = now
            if self.lobby_deadline is not None:
                left = max(0, int(self.lobby_deadline - now))
                data = f"still waiting for /start ({left}s left)\n"
            else:
                data = "Still waiting for /start\n"
                time.sleep(5)

        try:
            client_socket.sendall(data.encode())
            return True
        except OSError:
            return False


    def _stop_accepting(self) -> None:
        # Stops accepting the clients
        try:
            self.server_socket.close()
        except OSError:
            pass

    def menu(self, client_socket) -> bool:
        # Main logic for game menu, where players can use commands: /start, /exit
        prev_timeout = client_socket.gettimeout()
        client_socket.settimeout(1.0)
        try:
            try:
                client_socket.sendall("Type /start when ready:\n".encode())
            except OSError:
                return False
            
            while not self.game_started.is_set():
                now = time.monotonic()

                if self.lobby_deadline is not None and now >= self.lobby_deadline:
                    self._kick_unready_players()
                    with self.lock:
                        if client_socket not in self.players:
                            return False
                        total = len(self.players)
                        ready = len(self.ready_players)
                        should_start = (total >= MIN_PLAYERS and ready >= total and not self.game_started.is_set())

                        if should_start:
                            self.game_started.set()

                    if should_start:
                        self.notify_players(f"Ready: {ready}/{total}. Starting match!\n")
                        self._stop_accepting()
                        self.play_match()
                        return True
                if not self._remind_unready_player(client_socket, now):
                    return False
                
                try:
                    data = client_socket.recv(1024)
                except TimeoutError:
                    continue
                except OSError:
                    return False
            
                if not data or data.decode().strip() == "/exit":
                    return False
            
                elif data.decode().strip() != "/start":
                    try:
                        client_socket.sendall("Unknown command. \n".encode())
                    except OSError:
                        return False
                    continue

                should_start = False
                with self.lock:
                    if client_socket not in self.players:
                        return False
                    self.ready_players.add(client_socket)
                    self.last_reminder.pop(client_socket, None)

                    total = len(self.players)
                    ready = len(self.ready_players)

                    if (total >= MIN_PLAYERS and self.lobby_deadline is None):
                        self.lobby_deadline = time.monotonic() + START_TIMEOUT
                    
                    if (total >= MIN_PLAYERS and ready >= total and not self.game_started.is_set()):
                        self.game_started.set()
                        should_start = True

                self.notify_players(f"Ready: {ready}/{total}.\n")
                if should_start:
                    self._stop_accepting()
                    self.play_match()
                    
                    return True
                return True
        finally:
            with self.lock:
                self.last_reminder.pop(client_socket, None)
            try:
                client_socket.settimeout(prev_timeout)
            except OSError:
                pass
                
                
    def _kick_unready_players(self) -> None:
        with self.lock:
            players_snapshot = list(self.players.items())
            unready = [
                (sock, nick)
                for sock, nick in players_snapshot
                if sock not in self.ready_sockets
            ]
            for sock, nick in unready:
                self.players.pop(sock, None)
                self.ready_sockets.discard(sock)
                self.lobby_deadline = None

        for sock, nick in unready:
            try:
                sock.sendall("Kicked: too slow to type /start.\n".encode())
                sock.close()
            except OSError:
                pass

    def handle_client(self, client_socket, address):
        print(f"[NEW CONNECTION] {address} connected.")
        try:
            nick = self.register_nickname(client_socket)
            if not nick:
                return
            ready_ok = self.menu(client_socket)
            if not ready_ok: 
                return
            
            self.game_started.wait()

            while not self.game_finished.is_set():
                with self.lock:
                    if client_socket not in self.players:
                        break
                self.game_finished.wait(timeout=0.5)
        except OSError as error:
            print(f"[CONNECTION ERROR] {address}: {error}")
        finally:
            print(f"[DISCONNECTED] {address}")
            with self.lock:
                self.players.pop(client_socket, None)
                self.ready_players.discard(client_socket)
                self.last_reminder.pop(client_socket, None)
            try:
                client_socket.close()
            except OSError:
                pass


    def start_server(self):
        self.server_socket.bind((self.SERVER_IP, self.PORT))
        self.server_socket.listen(50)

        print(f"[SERVER STARTED] Listening on {self.SERVER_IP}:{self.PORT}")
        
        try:
            while not self.game_started.is_set():
                try:
                    client_socket, address = self.server_socket.accept()
                except OSError:
                    if self.game_started.is_set():
                        break
                    continue

                if self.game_started.is_set():
                    try:
                        client_socket.close()
                    except OSError:
                        pass
                    break

                thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
                thread.start()

                print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

            if self.game_started.is_set():
                self.game_finished.wait()
        finally:
            try:
                self.server_socket.close()
            except OSError:
                pass

game_server = ServerGameCoordinator()
game_server.start_server()