import socket
import threading

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

receiver_window = 5  # Janela de recepção inicial
lost_packets = []  # Lista de pacotes simulados como "perdidos"
protocol = "SR"  # Padrão: Repetição Seletiva


# Função para calcular checksum
def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256


# Função para manipular pacotes recebidos
def handle_client(conn, addr):
    global protocol, receiver_window
    print(f"[NEW CONNECTION] {addr} conectado.")

    connected = True
    while connected:
        msg = conn.recv(2048).decode(FORMAT)
        if not msg:
            continue

        if msg.startswith("PROTOCOL"):
            _, chosen_protocol = msg.split("|")
            protocol = chosen_protocol
            conn.send(protocol.encode(FORMAT))
            continue

        seq_num, data, received_checksum = msg.split("|")
        seq_num = int(seq_num)
        received_checksum = int(received_checksum)

        # Simulação de pacotes perdidos
        if seq_num in lost_packets:
            print(f"[SERVER] Pacote {seq_num} perdido (simulado).")
            continue

        # Verificação de integridade
        if checksum(data) != received_checksum:
            print(f"[SERVER] Erro de integridade no pacote {seq_num}. Enviando NAK.")
            conn.send(f"NAK|{seq_num}".encode(FORMAT))
            continue

        print(f"[SERVER] Pacote {seq_num} recebido com sucesso.")
        conn.send(f"ACK|{seq_num}".encode(FORMAT))

        if data == DISCONNECT_MESSAGE:
            connected = False

    conn.close()


# Início do servidor
def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print("[SERVER] Servidor iniciado.")
    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()
        print(f"[ACTIVE CONNECTIONS] {threading.activeCount() - 1}")


print("[SERVER] Iniciando...")
start()
