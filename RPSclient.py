import socket
import threading
import os 

SERVER_IP = "192.168.0.153"   # CHANGE IT TO SERVER's IP
PORT = 8080


def recieving(client_socket: socket.socket, stop_event: threading.Event):
    while not stop_event.is_set():
        try:
            recieve = client_socket.recv(1024)
            
        except OSError:
            break

        if not recieve:
            print("\n [Disconnected from server]")
            break
        print(f"{recieve.decode()}", end="")

def sending(client_socket, stop_event):
    while True:
        message = input()

        if stop_event.is_set():
            break
        try:
            client_socket.sendall(message.encode())
        except OSError:
            stop_event.is_set()
            break

def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((SERVER_IP, PORT))
    print("Connected to server!")

    stop_event = threading.Event()

    t_recv = threading.Thread(target=recieving, args=(client_socket, stop_event))
    t_send = threading.Thread(target=sending, args=(client_socket, stop_event))
    t_recv.start()
    t_send.start()

    try:
        while not stop_event.is_set():
            stop_event.wait(timeout=0.2)
    finally:
        stop_event.set()
        client_socket.close()
        os.exit(0)
main()
