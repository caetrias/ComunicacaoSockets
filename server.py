import socket
import threading
from concurrent.futures import ThreadPoolExecutor

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

receiver_window = 5  # Tamanho da janela de recepção
lost_packets = []    # Lista para pacotes simulados como perdidos
protocol = "SR"      # Protocolo padrão (SR)

# Função para calcular checksum
def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256

# Função para incluir erro de integridade nas confirmações
def simulate_integrity_error(data):
    return sum(bytearray(data, 'utf-8')) % 256 + 1  # Simula erro no checksum

# Função para manipular pacotes recebidos
def handle_client(conn, addr):
    global protocol, receiver_window
    print(f"[NEW CONNECTION] {addr} conectado.")

    connected = True
    try:
        while connected:
            msg = conn.recv(2048).decode(FORMAT)
            if not msg:
                print(f"[SERVER] Cliente {addr} fechou a conexão.")
                connected = False
                continue

            # Negociação de protocolo
            if msg.startswith("PROTOCOL"):
                _, chosen_protocol = msg.split("|")
                protocol = chosen_protocol
                print(f"[SERVER] Protocolo definido: {protocol}")
                conn.send(protocol.encode(FORMAT))
                continue

            parts = msg.split("|")
            if len(parts) < 3:
                print("[SERVER] Formato de pacote inválido.")
                continue

            seq_num, data, received_checksum = int(parts[0]), parts[1], int(parts[2])
            error_type = parts[3] if len(parts) == 4 else None

            print(f"[SERVER] Pacote {seq_num} recebido.")

            # Simulação de timeout
            if error_type == "timeout":
                print(f"[SERVER] Timeout simulado para pacote {seq_num}.")
                continue

            # Verifica integridade
            if checksum(data) != received_checksum:
                print(f"[SERVER] Checksum inválido para pacote {seq_num}.")
                conn.send(f"NAK|{seq_num}".encode(FORMAT))
                if protocol == "GBN":
                    print(f"[SERVER] GBN: Ignorando pacotes subsequentes após {seq_num}.")
                    continue
                else:
                    continue

            print(f"[SERVER] Pacote {seq_num} aceito.")

            # Envia ACK
            conn.send(f"ACK|{seq_num}".encode(FORMAT))

            # Controle de recepção no GBN (tamanho da janela)
            if protocol == "GBN":
                receiver_window -= 1
                if receiver_window == 0:
                    print("[SERVER] Janela cheia no GBN. Pausando envio.")
                    time.sleep(1)  # Simula pausa
                    receiver_window = 5  # Reseta a janela

            if data == DISCONNECT_MESSAGE:
                connected = False
    except Exception as e:
        print(f"[SERVER] Erro: {e}")
    finally:
        conn.close()
        print(f"[SERVER] Conexão encerrada com {addr}.")


# Início do servidor
def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print("[SERVER] Servidor iniciado.")

    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            conn, addr = server.accept()
            executor.submit(handle_client, conn, addr)

print("[SERVER] Iniciando...")
start()
