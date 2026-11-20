import socket
import threading

# Server IP and PORT
SERVER_IP = "0.0.0.0"  # Listen all players
PORT = 8080

# List of connected clients

players = {}

counter1 = 0 

beats = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper"
}
def game(choices: dict[str, str]) -> list[str]:

    unique_moves = set(choices.values())

    if len(unique_moves) != 2:
        return []
    
    move_a, move_b = list(unique_moves)

    if beats[move_a] == move_b:
        winning_move = move_a
    elif beats[move_b] == move_a:
        winning_move = move_b
    
    winners = []
    for player, move in choices.items():
        if move == winning_move:
            winners.append(player)
    return winners

def set_value(client_socket, nickname: str, data: str,) -> bool:
    if data.strip().lower() != ("rock" or "paper" or "scissors"):
        client_socket.send("Wrong input, enter right object: ".encode())
    else:
        temp_dict: dict[str, str] = {}
        temp_dict[nickname.values()] = data
        return True


def handle_client(client_socket, address):
    print(f"[NEW CONNECTION] {address} connected.")
    client_socket.send("Enter nickname! ".encode())
    players[client_socket] = client_socket.recv(1024).decode()

    while True:
        try:
            data = client_socket.recv(1024).decode()
            if not data or data == "/exit":
                break
            print(f"{players[client_socket]}: {data}")
            if data == "/start":
                global counter1
                counter1 += 1
                print(counter1)
                if counter1 >= 3:
                    while True:
                        client_socket.send("Choose rock, paper or scissors ".encode())
                        data = client_socket.recv(1024).decode()
                        set_value(client_socket, players[client_socket], data)
                        if set_value == True:
                            break
        except:
            break

    print(f"[DISCONNECTED] {address}")
    players.pop(client_socket)
    client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, PORT))
    server_socket.listen()

    print(f"[SERVER STARTED] Listening on {SERVER_IP}:{PORT}")

    while True:
        client_socket, address = server_socket.accept()

        thread = threading.Thread(target=handle_client, args=(client_socket, address))
        thread.start()

        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

        if counter1 >= 3:
            break
    game()



start_server()