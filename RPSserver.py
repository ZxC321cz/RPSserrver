import socket
import threading
import time


# Server IP and PORT
SERVER_IP = "0.0.0.0"  # Listen all players
PORT = 8080


# List of connected clients
class ServerGameCoordinator:
    def __init__(self):
        self.players: dict[socket.socket, str]
        self.ready_players: set[str]
        self.countdown_started: bool
        self.game_started: bool
        self.lock = threading.Lock() 
        self.beats = {
            "rock": "scissors",
            "paper": "rock",
            "scissors": "paper"
        }


    def register_nickname(self, client_socket: socket.socket) -> bool:
        while True:
            client_socket.sendall("Enter nickname!\n ".encode())
            raw_nick = client_socket.recv(1024)

            if not raw_nick:
                return None
            
            nick = raw_nick.decode()

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


    def game_coordinator(self, state, lock):
        pass
        while True:
            # is_over = round_step(round_num, state["clients"], lock)
            # if is_over:
            #     break
            round



    def ask_player_move(self, client_socket):
        while True:
            try:
                client_socket.sendall("Choose rock, paper or scissors:\n".encode())
                move = client_socket.recv(1024)
            except OSError:
                return None
            
            if not move:
                return None
            
            if move.decode().strip().lower() not in {"rock", "paper", "scissors"}:
                try:
                    client_socket.sendall("Wrong input, choose rock, paper or scissors:\n".encode())
                except OSError:
                    return None
                continue
            return move


    def game(self, choices: dict[str, str]) -> list[str]:
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


    def round(self, round_num: int) -> list[str]:
        with self.lock:
            players_snapshot = list(self.players.items())
        
        if len(players_snapshot) < 2:
            return [nick for sock, nick in players_snapshot]
    
        self.notify_players(f"Round {round_num} started!")
        choices: dict[str, str] = {}

        for sock, nick in players_snapshot:
            move = self.ask_player_move(sock)
            if move is None:
                with self.lock:
                    self.players.pop(sock, None)
                try:
                    sock.close()
                except OSError:
                    pass
                continue
            choices[nick] = move

        if len(choices) < 2:
            return list(choices.keys())
        
        return self.game(choices)


    def play_match(self) -> str:
        round_num = 1

        while True:
            with self.lock:
                players_snapshot = list(self.players.items())
            
            if len(players_snapshot) == 0:
                return None
            
            if len(players_snapshot) == 1:
                winner_nick = players_snapshot[0]
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

    def menu(self, client_socket, nick) -> bool:
            data = client_socket.recv(1024)
            if data.decode() == "/start":
                with self.lock:
                    self.ready_players.add(nick)


            elif not data or data.decode() == "/exit":
                return True
            
            else:
                print(f"{self.players[client_socket]}: {data}")

                
    def handle_client(self, client_socket, address):
        self.address = address
        print(f"[NEW CONNECTION] {address} connected.")
        nick = self.register_nickname(client_socket)
        if not nick:
            return
        move = self.menu(client_socket, nick)
        if move: pass




    def start_server(self):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((SERVER_IP, PORT))
        server_socket.listen(50)

        print(f"[SERVER STARTED] Listening on {SERVER_IP}:{PORT}")

        while True:
            client_socket, address = server_socket.accept()

            thread = threading.Thread(target=self.handle_client, args=(client_socket, address))
            thread.start()

            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

            if self.counter1 >= 3:
                break
        self.game()