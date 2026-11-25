import socket
import threading
import os 

SERVER_IP = "0.0.0.0"   # CHANGE IT TO SERVER's IP
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

    t_recv = threading.Thread(target=recieving, args=(client_socket, stop_event), daemon=True)
    t_send = threading.Thread(target=sending, args=(client_socket, stop_event), daemon=True)
    t_recv.start()
    t_send.start()

    try:
        while not stop_event.is_set():
            stop_event.wait(timeout=0.2)
    except KeyboardInterrupt:
        stop_event.set()
    finally:
        stop_event.set()
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client_socket.close()
        except OSError:
            pass
main()
