import socket
import time
import asyncio

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

seq_num = 0  # Número de sequência para pacotes enviados
congestion_window = 1  # Janela de congestionamento inicial
max_cwnd = 10  # Janela máxima de congestionamento
ack_received = set()  # Conjunto de ACKs recebidos
protocol = "SR"  # Padrão: Repetição Seletiva (SR)


# Função para calcular checksum
def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256


# Função assíncrona para enviar pacotes
async def send_packet(data, error_type=None, max_retries=5):
    global seq_num, congestion_window
    retries = 0  # Contador de retransmissões

    while retries < max_retries:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(ADDR)

        packet_checksum = checksum(data)
        if error_type == "integrity":
            packet_checksum += 1  # Simula erro de integridade

        packet = f"{seq_num}|{data}|{packet_checksum}"
        client.send(packet.encode(FORMAT))
        print(f"[CLIENT] Pacote {seq_num} enviado. Tentativa {retries + 1}/{max_retries}.")

        try:
            response = client.recv(2048).decode(FORMAT)
            if response.startswith("ACK"):
                print(f"[SERVER] ACK recebido para {seq_num}")
                ack_received.add(seq_num)
                seq_num += 1
                if congestion_window < max_cwnd:
                    congestion_window += 1
                break  # Sai do loop ao receber ACK
            elif response.startswith("NAK"):
                print(f"[SERVER] NAK recebido para {seq_num}. Reenviando...")
                retries += 1
                congestion_window = max(1, congestion_window // 2)  # Reduz janela
        except socket.timeout:
            print(f"[CLIENT] Timeout para {seq_num}. Reenviando...")
            retries += 1
            congestion_window = max(1, congestion_window // 2)

        client.close()

    if retries == max_retries:
        print(f"[CLIENT] Falha ao enviar pacote {seq_num} após {max_retries} tentativas.")



# Função para negociar protocolo
def negotiate_protocol():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    client.send(f"PROTOCOL|{protocol}".encode(FORMAT))
    response = client.recv(HEADER).decode(FORMAT)
    print(f"[SERVER] Protocolo negociado: {response}")
    client.close()


# Menu principal
def menu():
    global protocol, congestion_window, seq_num
    negotiate_protocol()
    while True:
        print("\nMenu:")
        print("1. Enviar uma única mensagem")
        print("2. Enviar várias mensagens em lote")
        print("3. Sair")

        choice = input("Escolha uma opção: ")

        if choice == '1':
            message = input("Digite a mensagem para enviar: ")
            error_choice = input("Escolha o tipo de erro (integrity/timeout/não): ").lower()
            asyncio.run(send_packet(message, error_type=error_choice))
        elif choice == '2':
            num_messages = int(input("Quantas mensagens deseja enviar? "))
            messages = [f"Mensagem {i+1}" for i in range(num_messages)]
            error_choice = input("Escolha o tipo de erro (integrity/timeout/nao): ").lower()
        
            tasks = [send_packet(msg, error_choice) for msg in messages]
            asyncio.run(asyncio.gather(*tasks))

        elif choice == '3':
            asyncio.run(send_packet(DISCONNECT_MESSAGE))
            print("[CLIENT] Desconectando...")
            break
        else:
            print("Opção inválida. Tente novamente.")


menu()