import socket
import threading
import time
from typing import TypedDict


# Server IP and PORT
SERVER_IP = "0.0.0.0"  # Listen all players
PORT = 8080

class GameState(TypedDict):
    players: dict[socket.socket, str]
    ready_ids: set[int]
    countdown_started: bool
    game_started: bool

# List of connected clients
class ServerGameCoordinator:
    def __init__(self):
        self.players = {}
        self.state: GameState = {
            "players": {},
            "ready_ids": set(),
            "countdown_started": False,
            "game_started": False,
        }
        self.lock = threading.Lock()
        self.counter1 = 0 
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
                return True

    def menu(self, client_socket, nickname: str) -> bool:
            data = client_socket.recv(1024).decode()
            if data == "/start":
                self.counter1 += 1
                print(self.counter1)

                if self.counter1 >= 3:

                    
                    ...
            elif not data or data == "/exit":
                return True
            
            else:
                print(f"{self.players[client_socket]}: {data}")

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

    def round(self, round_num: int, players: dict):
        pass
            # else:
            #     choices: dict[str, str] = {}
            #     with self.lock:
            #         choices[players.values()] = data
            #         winners = self.game(choices)
            #         return winners
            #     disconnect_losers()

    def disconnect_losers(self, winner_set: set[str]) -> None:
        with self.lock:
            losers = list(self.players.items())

        for sock, nick in losers:
            if nick not in winner_set:
                with self.lock:
                    self.players.pop(sock, None)
                try:
                    sock.sendall("You were eliminated!\n".encode())
                except OSError:
                    pass
                try:
                    sock.close()
                except OSError:
                    pass


    def handle_client(self, client_socket, address):
        print(f"[NEW CONNECTION] {address} connected.")
        

        try:
            if not self.register_nickname(client_socket):
                return
            while True:
                move = self.menu(client_socket, self.players[client_socket])
                if move:
                    break
                

        finally:
            print(f"[DISCONNECTED] {address}")
            self.players.pop(client_socket)
            client_socket.close()

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
