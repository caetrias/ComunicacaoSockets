import socket
import random
import time

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "192.168.56.1"  
ADDR = (SERVER, PORT)

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(ADDR)

seq_num = 0  


def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256

def send_packet(data, introduce_error=False):
    global seq_num
    packet_checksum = checksum(data)

    if introduce_error:
        packet_checksum += 1  

    packet = f"{seq_num}|{data}|{packet_checksum}"
    message = packet.encode(FORMAT)
    msg_length = len(message)
    send_length = str(msg_length).encode(FORMAT)
    send_length += b' ' * (HEADER - len(send_length))

    client.send(send_length)
    client.send(message)
    print(f"[CLIENT] Pacote {seq_num} enviado: {data}")

    try:
        response = client.recv(2048).decode(FORMAT)
        if response.startswith("ACK"):
            print(f"[SERVER] ACK recebido para pacote {seq_num}")
            seq_num += 1  
        elif response.startswith("NAK"):
            print(f"[SERVER] NAK recebido para pacote {seq_num}. Reenviando...")
            send_packet(data)  
    except socket.timeout:
        print(f"[CLIENT] Tempo de espera excedido para pacote {seq_num}. Reenviando...")
        send_packet(data)  

def send_batch(data_list):
    for data in data_list:
        introduce_error = random.choice([True, False])  
        send_packet(data, introduce_error=introduce_error)
        time.sleep(0.5)  


send_batch(["Mensagem1", "Mensagem2", "Mensagem3", "Mensagem4", "Mensagem5"])

send_packet(DISCONNECT_MESSAGE)
client.close()
