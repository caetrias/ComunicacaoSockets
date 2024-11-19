import socket
import time
import asyncio

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

seq_num = 0  # Sequência de pacotes enviada
congestion_window = 1  # Janela de congestionamento inicial (1 pacote)
max_cwnd = 10  # Tamanho máximo da janela de congestionamento
receiver_window = 5  # Tamanho da janela de recepção do servidor (simulado)
ack_received = set()  # Conjunto para armazenar ACKs recebidos


# Função para calcular o checksum de uma string
def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256


# Função assíncrona para enviar pacotes
async def send_packet(data, protocol, error_type=None):
    global seq_num
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    packet_checksum = checksum(data)

    # Introduz erro de acordo com a escolha do usuário
    if error_type == "integrity":
        packet_checksum += 1  # Introduz erro de integridade no checksum
    elif error_type == "timeout":
        time.sleep(5)  # Simula um atraso, causando um erro de timeout

    # Adiciona o protocolo ao pacote
    packet = f"{protocol}|{seq_num}|{data}|{packet_checksum}"
    message = packet.encode(FORMAT)

    client.send(message)
    print(f"[CLIENT] Pacote {seq_num} enviado usando {protocol}: {data}")

    try:
        response = client.recv(2048).decode(FORMAT)
        if response.startswith("ACK"):
            print(f"[SERVER] ACK recebido para pacote {seq_num}")
            ack_received.add(seq_num)  # Adiciona o ACK ao conjunto
            seq_num += 1  # Incrementa o número de sequência

            # Aumenta a janela de congestionamento (caminho de controle de congestionamento)
            global congestion_window
            if congestion_window < max_cwnd:
                congestion_window += 1

        elif response.startswith("NAK"):
            print(f"[SERVER] NAK recebido para pacote {seq_num}. Reenviando...")
            await send_packet(data, protocol, error_type)  # Reenvia o pacote
    except socket.timeout:
        print(f"[CLIENT] Tempo de espera excedido para pacote {seq_num}. Reenviando...")
        await send_packet(data, protocol, error_type)  # Reenvia em caso de timeout

    client.close()


# Função assíncrona para enviar pacotes em lote, respeitando a janela de congestionamento
async def send_batch(data_list, protocol, error_type=None):
    tasks = []
    global congestion_window

    for i, data in enumerate(data_list):
        if i < congestion_window:  # Respeita a janela de congestionamento
            tasks.append(send_packet(data, protocol, error_type=error_type))
        else:
            break  # Não envia mais pacotes do que a janela permite

    # Executa todas as tarefas de envio em paralelo
    await asyncio.gather(*tasks)


# Função principal do cliente
def menu():
    global congestion_window, ack_received
    while True:
        print("\nMenu:")
        print("1. Enviar uma única mensagem")
        print("2. Enviar várias mensagens em lote")
        print("3. Sair")

        choice = input("Escolha uma opção: ")

        if choice == '1':
            protocol = input("Escolha o protocolo (GBN/SR): ").upper()
            if protocol not in ["GBN", "SR"]:
                print("[CLIENT] Protocolo inválido. Tente novamente.")
                continue

            message = input("Digite a mensagem para enviar: ")
            error_choice = input("Escolha o tipo de erro (integrity/timeout/não): ").lower()
            asyncio.run(send_packet(message, protocol, error_type=error_choice))
        elif choice == '2':
            protocol = input("Escolha o protocolo (GBN/SR): ").upper()
            if protocol not in ["GBN", "SR"]:
                print("[CLIENT] Protocolo inválido. Tente novamente.")
                continue

            num_messages = int(input("Quantas mensagens deseja enviar? "))
            messages = [f"Mensagem {i+1}" for i in range(num_messages)]
            error_choice = input("Escolha o tipo de erro (integrity/timeout/não): ").lower()
            asyncio.run(send_batch(messages, protocol, error_type=error_choice))
        elif choice == '3':
            asyncio.run(send_packet(DISCONNECT_MESSAGE, "GBN"))  # Desconecta usando GBN como padrão
            print("[CLIENT] Desconectando...")
            break
        else:
            print("Opção inválida. Tente novamente.")


menu()
