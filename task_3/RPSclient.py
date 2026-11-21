import socket

SERVER_IP = "192.168.137.1"   # CHANGE IT TO SERVER's IP
PORT = 8080

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

print("Connected to server!")

recieve = client_socket.recv(1024).decode()
print(recieve)
message = input("Entering the nickname: ")
client_socket.send(message.encode())
print("You’ve entered a game of Rock, Paper, Scissors. Use /start to start the game or exit using /exit.")
while True:
    message = input("Send message: ")
    client_socket.send(message.encode())