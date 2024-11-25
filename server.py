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

            if msg.startswith("PROTOCOL"):
                _, chosen_protocol = msg.split("|")
                protocol = chosen_protocol
                conn.send(protocol.encode(FORMAT))
                continue

            parts = msg.split("|")
            if len(parts) == 4:
                seq_num, data, received_checksum, error_type = parts
            elif len(parts) == 3:
                seq_num, data, received_checksum = parts
                error_type = None
            else:
                print("[SERVER] Formato de pacote inválido.")
                continue

            print(f"[SERVER] Mensagem recebida: {data}")

            seq_num = int(seq_num)
            received_checksum = int(received_checksum)

            if error_type == "timeout":
                print(f"[SERVER] Simulando timeout para pacote {seq_num}. Não enviando ACK ou NAK.")
                continue  # Não envia nada para simular timeout

            if seq_num in lost_packets:
                print(f"[SERVER] Pacote {seq_num} perdido (simulado).")
                continue

            if checksum(data) != received_checksum:
                print(f"[SERVER] Erro de integridade no pacote {seq_num}. Enviando NAK com erro de integridade.")
                fake_checksum = simulate_integrity_error(f"NAK|{seq_num}")
                conn.send(f"NAK|{seq_num}|{fake_checksum}".encode(FORMAT))
                continue

            print(f"[SERVER] Pacote {seq_num} recebido com sucesso.")
            fake_checksum = simulate_integrity_error(f"ACK|{seq_num}")
            conn.send(f"ACK|{seq_num}|{fake_checksum}".encode(FORMAT))

            if data == DISCONNECT_MESSAGE:
                connected = False

            # Enviar a janela de recepção ao cliente
            conn.send(f"RECEIVER_WINDOW|{receiver_window}".encode(FORMAT))

    except Exception as e:
        print(f"[SERVER] Erro ao processar cliente {addr}: {e}")
    finally:
        conn.close()
        print(f"[SERVER] Conexão com {addr} encerrada.")

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
