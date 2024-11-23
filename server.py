import socket
import threading

from concurrent.futures import ThreadPoolExecutor

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

receiver_window = 5  
lost_packets = []
protocol = "SR" 


# Função para calcular checksum
def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256


# Função para manipular pacotes recebidos
def handle_client(conn, addr):
    print("\n")
    global protocol, receiver_window
    print(f"[NEW CONNECTION] {addr} conectado.")

    connected = True
    try:
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

            if seq_num in lost_packets:
                print(f"[SERVER] Pacote {seq_num} perdido (simulado).")
                continue

            if checksum(data) != received_checksum:
                print(f"[SERVER] Erro de integridade no pacote {seq_num}. Enviando NAK.")
                conn.send(f"NAK|{seq_num}".encode(FORMAT))
                continue

            print(f"[SERVER] Pacote {seq_num} recebido com sucesso.")
            conn.send(f"ACK|{seq_num}".encode(FORMAT))

            if data == DISCONNECT_MESSAGE:
                connected = False
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
