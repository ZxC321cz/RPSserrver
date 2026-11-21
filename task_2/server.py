import socket 
questions = [
    ("Q1) What is a thread?\n"
     "A) A program stored on disk\n"
     "B) The smallest unit of execution inside a process\n"
     "C) A type of main memory\n"
     "D) An input/output device", "B"),

    ("Q2) What is a kernel?\n"
     "A) The core part of the OS that manages hardware and resources\n"
     "B) A user application like a web browser\n"
     "C) A programming language\n"
     "D) A type of hard disk", "A"),

    ("Q3) Which of these is NOT a process state?\n"
     "A) Ready\n"
     "B) Running\n"
     "C) Waiting\n"
     "D) Compiling", "D"),

    ("Q4) What is a deadlock?\n"
     "A) When the CPU runs too fast\n"
     "B) When a process finishes successfully\n"
     "C) When processes wait for each other forever and none can continue\n"
     "D) When memory is full", "C"),

    ("Q5) Which scheduling algorithm always runs the shortest job first?\n"
     "A) FCFS (First Come First Served)\n"
     "B) Round Robin\n"
     "C) Priority Scheduling\n"
     "D) SJF (Shortest Job First)", "D"),
]

HOST = "127.0.0.1"
PORT = 8080

def check_answer(answer, correct):
    answer = answer.strip().upper()
    if answer == correct:
        return "Correct!"
    else:
        return "Wrong!"
    
def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server.bind((HOST, PORT))

    server.listen()
    print(f"Listening on: {HOST} | {PORT}")

    conn, addr = server.accept() 
    # addr = client's port and IP address
    # conn = new socket (socket ID) 
    # used to talk to this client: recv / sendall / close
    print(f"Client connected: {addr}")

    """
    server must send a message three times:
    1 to ask the question 
    2 to give feedback(Correct/Wrong) 
    3 to give overall result
    that is why there are two sendall() commands
    """
    # main logic 
    score = 0
    for q, correct in questions:
        conn.sendall(q.encode())
        answer = conn.recv(1024).decode()
        print(f"[CLIENT]: {answer}")
        result = check_answer(answer, correct)
        if result == "Correct!":
            score += 1
        conn.sendall(result.encode())
        conn.recv(1024)


    conn.sendall(f"Your overall score: {score}/{len(questions)}".encode()) # could write 5 but avoiding hardcoding
    conn.close()
    print("Quiz done. client disconnected")
    server.close()

main()