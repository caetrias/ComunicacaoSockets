import socket
import threading
import time

HEADER = 64
PORT = 5050
SERVER = '0.0.0.0'  # socket.gethostbyname(socket.gethostname())
ADDR = (SERVER, PORT)
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
WINDOW_SIZE = 5  # Tamanho da janela de recepção
TIMEOUT = 2  

def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256

# Servidor
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(ADDR)

# Função para lidar com cada cliente
def handle_client(conn, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    window_start = 0  # Primeiro pacote na janela
    ack_received = set()

    while connected:
        try:
            packet = conn.recv(1024).decode(FORMAT)
            if packet == DISCONNECT_MESSAGE:
                print(f"[DISCONNECT] {addr} disconnected.")
                connected = False
                break

            # Protocolo e pacote recebidos
            protocol, seq_num, data, checksum_received = packet.split("|")
            seq_num, checksum_received = int(seq_num), int(checksum_received)

            if checksum(data) == checksum_received:
                if protocol == "GBN":
                    # GBN: Apenas aceita pacotes em ordem
                    if seq_num == window_start:
                        print(f"[{addr}] GBN: Pacote {seq_num} recebido corretamente.")
                        conn.send(f"ACK|{seq_num}".encode(FORMAT))
                        ack_received.add(seq_num)
                        window_start += 1  # Atualiza o início da janela
                    else:
                        print(f"[{addr}] GBN: Pacote fora de ordem {seq_num}.")
                        conn.send(f"NAK|{window_start}".encode(FORMAT))

                elif protocol == "SR":
                    # SR: Aceita pacotes fora de ordem
                    if seq_num >= window_start:
                        print(f"[{addr}] SR: Pacote {seq_num} recebido corretamente.")
                        conn.send(f"ACK|{seq_num}".encode(FORMAT))
                        ack_received.add(seq_num)

                        # Atualiza a janela removendo pacotes já confirmados
                        while window_start in ack_received:
                            window_start += 1
            else:
                print(f"[{addr}] Erro de integridade no pacote {seq_num}.")
                conn.send(f"NAK|{seq_num}".encode(FORMAT))

        except ConnectionResetError:
            print(f"[ERROR] Conexão perdida com {addr}.")
            connected = False

    conn.close()

# Função de início do servidor
def start():
    server.listen()
    print(f"[LISTENING] Server is listening on {SERVER}")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")

print("[STARTING] Server is starting...")
start()
