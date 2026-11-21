import socket

HOST = "127.0.0.1"
PORT = 5000

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print(f"Connected to {HOST}, {PORT}")

    while True:
        day = input("Enter a day: ").strip()
        if day == "exit":
            break
        
        client.sendall(day.encode())
        reply = client.recv(1024).decode()
        print("[SERVER]", reply)

    client.close()
    print("Disconnected")

main()

