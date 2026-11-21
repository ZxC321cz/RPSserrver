import socket

HOST = "127.0.0.1"
PORT = 8080

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((HOST, PORT))
    print(f"Connected to {HOST} | {PORT}")

    for i in range(5):
        q = client.recv(1024).decode()
        print(f"Question: {q}")
        answer = input("Your answer: ")
        if answer == "idk" or answer == "i don't know":
            print("U failed the test!")
        client.sendall(answer.encode())
        reply = client.recv(1024).decode()
        print(f"[SERVER]: {reply}")
        client.sendall("ok".encode())


    overall = client.recv(1024).decode()
    print(overall)
    print("Quiz done. Server disconnected")
    client.close()
    

main()