import asyncio

HEADER = 64
PORT = 5050
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!DISCONNECT"
SERVER = "127.0.0.1"
ADDR = (SERVER, PORT)

seq_num = 0 
congestion_window = 1
max_cwnd = 10 
ack_received = set()  
protocol = "SR"

# Função para calcular checksum
def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256

# Função para negociar protocolo
async def negotiate_protocol(writer, reader):
    message = f"PROTOCOL|{protocol}"
    writer.write(message.encode(FORMAT))
    await writer.drain()
    response = await reader.read(HEADER)
    print(f"[SERVER] Protocolo negociado: {response.decode(FORMAT)}")

# Função para enviar pacotes
async def send_packet(writer, reader, data, error_type=None, max_retries=5):
    global seq_num, congestion_window
    retries = 0 

    while retries < max_retries:
        try:
            packet_checksum = checksum(data)
            if error_type == "integrity":
                packet_checksum += 1

            if error_type:
                packet = f"{seq_num}|{data}|{packet_checksum}|{error_type}"
            else:
                packet = f"{seq_num}|{data}|{packet_checksum}"

            writer.write(packet.encode(FORMAT))
            await writer.drain()
            print(f"[CLIENT] Pacote {seq_num} enviado. Tentativa {retries + 1}/{max_retries}.")

            try:
                response = await asyncio.wait_for(reader.read(2048), timeout=5)
                response = response.decode(FORMAT)
                if response.startswith("ACK"):
                    print(f"[SERVER] ACK recebido para {seq_num}")
                    ack_received.add(seq_num)
                    seq_num += 1
                    if congestion_window < max_cwnd:
                        congestion_window += 1
                    break 
                elif response.startswith("NAK"):
                    print(f"[SERVER] NAK recebido para {seq_num}. Reenviando...")
                    retries += 1
                    congestion_window = max(1, congestion_window // 2)
            except asyncio.TimeoutError:
                print(f"[CLIENT] Timeout para {seq_num}. Reenviando...")
                retries += 1
                congestion_window = max(1, congestion_window // 2)

        except Exception as e:
            print(f"[CLIENT] Erro: {e}")
            retries += 1
            congestion_window = max(1, congestion_window // 2)

    if retries == max_retries:
        print(f"[CLIENT] Falha ao enviar pacote {seq_num} após {max_retries} tentativas.")

# Menu principal
async def menu(writer, reader):
    global protocol, congestion_window, seq_num
    await negotiate_protocol(writer, reader)
    while True:
        print("\nMenu:")
        print("1. Enviar uma única mensagem")
        print("2. Enviar várias mensagens em lote")
        print("3. Sair")

        choice = input("Escolha uma opção: ")

        if choice == '1':
            message = input("Digite a mensagem para enviar: ")
            error_choice = input("Escolha o tipo de erro (integrity/timeout/não): ").lower()
            error_type = error_choice if error_choice in ["integrity", "timeout"] else None
            await send_packet(writer, reader, message, error_type=error_type)
        elif choice == '2':
            num_messages = int(input("Quantas mensagens deseja enviar? "))
            messages = [f"Mensagem {i+1}" for i in range(num_messages)]
            error_choice = input("Escolha o tipo de erro (integrity/timeout/não): ").lower()
            error_type = error_choice if error_choice in ["integrity", "timeout"] else None

            for msg in messages:
                await send_packet(writer, reader, msg, error_type=error_type)
        elif choice == '3':
            await send_packet(writer, reader, DISCONNECT_MESSAGE)
            print("[CLIENT] Desconectando...")
            break
        else:
            print("Opção inválida. Tente novamente.")

async def main():
    try:
        reader, writer = await asyncio.open_connection(SERVER, PORT)
        await menu(writer, reader)
    except ConnectionRefusedError:
        print("[CLIENT] Não foi possível conectar ao servidor.")
    finally:
        writer.close()
        await writer.wait_closed()
        print("[CLIENT] Conexão encerrada.")

if __name__ == "__main__":
    asyncio.run(main())
