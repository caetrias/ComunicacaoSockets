import socket
import threading
import random
import time

HEADER = 64
PORT = 5050
SERVER = socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
WINDOW_SIZE = 5  
TIMEOUT = 2  

def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256

# Servidor
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    window = []
    connected = True

    while connected:
        try:
            msg_length = conn.recv(HEADER).decode(FORMAT)
            if msg_length:
                msg_length = int(msg_length)
                packet = conn.recv(msg_length).decode(FORMAT)
                seq_num, data, received_checksum = packet.split('|')
                seq_num = int(seq_num)
                received_checksum = int(received_checksum)

                
                if checksum(data) == received_checksum:
                    print(f"[{addr}] Pacote {seq_num} recebido com sucesso.")
                    conn.send(f"ACK|{seq_num}".encode(FORMAT))
                else:
                    print(f"[{addr}] Erro de integridade no pacote {seq_num}.")
                    conn.send(f"NAK|{seq_num}".encode(FORMAT))

                if len(window) < WINDOW_SIZE:
                    window.append(seq_num)
                else:
                    print("Janela cheia, aguardando espaço.")

                time.sleep(0.1)
        except socket.timeout:
            print(f"[{addr}] Tempo de espera excedido para o pacote {seq_num}.")
            conn.send(f"NAK|{seq_num}".encode(FORMAT))

    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        conn.settimeout(TIMEOUT)
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

print("[STARTING] Server is starting...")
start()
