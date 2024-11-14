import socket
import threading
import random
import time

HEADER = 64
PORT = 5050
SERVER = '0.0.0.0' #socket.gethostbyname(socket.gethostname())
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
        packet = conn.recv(1024).decode(FORMAT)
        if packet:
            # Processa o pacote recebido
                #tipo_mensagem vai ser a variavel para tratar o menu
            seq_num, data, tipo_mensagem, received_checksum = packet.split('|')
            seq_num = int(seq_num)
            received_checksum = int(received_checksum)

            # Verifica a integridade do pacote
            if checksum(data) == received_checksum:
                print(f"[{addr}] Pacote {seq_num} recebido com sucesso. Mensagem: {data}")
                conn.send(f"ACK|{seq_num}".encode(FORMAT))
            else:
                print(f"[{addr}] Erro de integridade no pacote {seq_num}.")
                conn.send(f"NAK|{seq_num}".encode(FORMAT))

            # Adiciona o pacote à janela
            if len(window) < WINDOW_SIZE:
                window.append(seq_num)
            else:
                print("Janela cheia, aguardando espaço.")

            time.sleep(0.1)

    conn.close()

def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")

print("[STARTING] Server is starting...")
start()