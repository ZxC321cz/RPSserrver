import socket

HOST = "127.0.0.1"
PORT = 5000

menu = {
    "Monday": "Plov",
    "Tuesday": "Lagman",
    "Wednesday": "Mastava",
    "Thursday": "Manti",
    "Friday": "Fish"
}

closed = ["Saturday", "Sunday"]

def meal(day):
    day  = day.strip().capitalize()
    short = day[:3]
    for d in closed:
        if d[:3] == short:
            return "Canteen is closed on weekends, try another day"
    for d in menu:
        if d[:3] == short:
            return menu[d]
    return "Invalid day"
    
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST, PORT))

    server.listen()
    print(f"Listening on: {HOST}, {PORT}")

    conn, addr = server.accept()
    print("Client connected: ", addr)

    while True:
        data = conn.recv(1024) # receive the data from the client
        if not data: # if client sent nothing then break out of the loop
            break

        day = data.decode() # convert client input  in bytes to string 
        reply = meal(day)
        print(f"[CLIENT]: {day}, [REPLY]: {reply}")
        conn.sendall(reply.encode()) # send the result back to client and convert to bytes

    conn.close()
    server.close()
main()

