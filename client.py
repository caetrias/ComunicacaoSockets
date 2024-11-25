import asyncio  # Importa a biblioteca asyncio para operações assíncronas

# Constantes de configuração
HEADER = 64  # Tamanho do cabeçalho
PORT = 5050  # Porta de comunicação
FORMAT = 'utf-8'  # Formato de codificação de mensagens
DISCONNECT_MESSAGE = "!DISCONNECT"  # Mensagem de desconexão
SERVER = "127.0.0.1"  # Endereço do servidor
ADDR = (SERVER, PORT)  # Endereço completo do servidor

# Variáveis globais
seq_num = 0  # Número de sequência do cliente
congestion_window = 1  # Janela de congestionamento inicial
max_cwnd = 10  # Tamanho máximo da janela de congestionamento
ack_received = set()  # Conjunto de ACKs recebidos
protocol = "SR"  # Protocolo padrão (Selective Repeat)

# Função para calcular o checksum de uma mensagem
def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256  # Soma os bytes e retorna o módulo 256

# Função para negociar o protocolo com o servidor
async def negotiate_protocol(writer, reader):
    message = f"PROTOCOL|{protocol}"  # Mensagem de negociação de protocolo
    writer.write(message.encode(FORMAT))  # Envia a mensagem ao servidor
    await writer.drain()  # Garante que o buffer foi enviado
    response = await reader.read(HEADER)  # Lê a resposta do servidor
    print(f"[SERVER] Protocolo negociado: {response.decode(FORMAT)}")  # Exibe o protocolo negociado

# Função para enviar um pacote
async def send_packet(writer, reader, data, error_type=None, max_retries=5):
    global seq_num, congestion_window  # Usa as variáveis globais de sequência e janela
    retries = 0  # Número de tentativas

    # Loop para tentativas de envio
    while retries < max_retries:
        try:
            packet_checksum = checksum(data)  # Calcula o checksum do pacote
            if error_type == "integrity":  # Se for simular erro de integridade
                packet_checksum += 1  # Altera o checksum para simular o erro

            # Monta o pacote com ou sem erro
            if error_type:
                packet = f"{seq_num}|{data}|{packet_checksum}|{error_type}"
            else:
                packet = f"{seq_num}|{data}|{packet_checksum}"

            writer.write(packet.encode(FORMAT))  # Envia o pacote
            await writer.drain()  # Garante que o buffer foi enviado
            print(f"[CLIENT] Pacote {seq_num} enviado. Tentativa {retries + 1}/{max_retries}.")  # Exibe informações

            try:
                response = await asyncio.wait_for(reader.read(2048), timeout=5)  # Espera pela resposta com timeout
                response = response.decode(FORMAT)  # Decodifica a resposta
                if response.startswith("ACK"):  # Caso seja um ACK
                    print(f"[SERVER] ACK recebido para {seq_num}")  # Exibe mensagem de confirmação
                    ack_received.add(seq_num)  # Adiciona o número de sequência aos ACKs recebidos
                    seq_num += 1  # Incrementa o número de sequência
                    if congestion_window < max_cwnd:  # Se a janela puder aumentar
                        congestion_window += 1  # Incrementa a janela
                    break  # Sai do loop
                elif response.startswith("NAK"):  # Caso seja um NAK
                    print(f"[SERVER] NAK recebido para {seq_num}. Reenviando...")  # Mensagem de retransmissão
                    retries += 1  # Incrementa o número de tentativas
                    congestion_window = max(1, congestion_window // 2)  # Reduz a janela de congestionamento
            except asyncio.TimeoutError:  # Caso ocorra um timeout
                print(f"[CLIENT] Timeout para {seq_num}. Reenviando...")  # Mensagem de timeout
                retries += 1  # Incrementa o número de tentativas
                congestion_window = max(1, congestion_window // 2)  # Reduz a janela de congestionamento

        except Exception as e:  # Captura erros gerais
            print(f"[CLIENT] Erro: {e}")  # Exibe o erro
            retries += 1  # Incrementa o número de tentativas
            congestion_window = max(1, congestion_window // 2)  # Reduz a janela de congestionamento

    # Se as tentativas se esgotarem
    if retries == max_retries:
        print(f"[CLIENT] Falha ao enviar pacote {seq_num} após {max_retries} tentativas.")  # Mensagem de falha

# Menu principal do cliente
async def menu(writer, reader):
    global protocol  # Usa a variável global do protocolo

    # Escolha do protocolo
    print("\nEscolha o protocolo:")
    print("1. Selective Repeat (SR)")  # Opção para SR
    print("2. Go-Back-N (GBN)")  # Opção para GBN
    choice = input("Digite o número do protocolo: ")  # Lê a escolha do usuário

    if choice == '1':  # Caso SR seja escolhido
        protocol = "SR"  # Define o protocolo para SR
    elif choice == '2':  # Caso GBN seja escolhido
        protocol = "GBN"  # Define o protocolo para GBN
    else:  # Caso a escolha seja inválida
        print("Opção inválida. Padrão para SR.")  # Mensagem padrão
        protocol = "SR"  # Define o protocolo padrão para SR

    await negotiate_protocol(writer, reader)  # Realiza a negociação do protocolo

    # Loop principal do menu
    while True:
        print("\nMenu:")  # Exibe o menu
        print("1. Enviar uma única mensagem")  # Opção para enviar uma mensagem
        print("2. Enviar várias mensagens em lote")  # Opção para enviar mensagens em lote
        print("3. Sair")  # Opção para sair

        choice = input("Escolha uma opção: ")  # Lê a escolha do usuário

        if choice == '1':  # Caso escolha enviar uma única mensagem
            message = input("Digite a mensagem para enviar: ")  # Lê a mensagem
            error_choice = input("Escolha o tipo de erro (integrity/timeout/não): ").lower()  # Lê o tipo de erro
            error_type = error_choice if error_choice in ["integrity", "timeout"] else None  # Define o tipo de erro
            await send_packet(writer, reader, message, error_type=error_type)  # Envia o pacote
        elif choice == '2':  # Caso escolha enviar mensagens em lote
            num_messages = int(input("Quantas mensagens deseja enviar? "))  # Lê a quantidade de mensagens
            messages = [f"Mensagem {i+1}" for i in range(num_messages)]  # Cria as mensagens
            error_choice = input("Escolha o tipo de erro (integrity/timeout/não): ").lower()  # Lê o tipo de erro
            error_type = error_choice if error_choice in ["integrity", "timeout"] else None  # Define o tipo de erro

            for msg in messages:  # Loop pelas mensagens
                await send_packet(writer, reader, msg, error_type=error_type)  # Envia cada mensagem
        elif choice == '3':  # Caso escolha sair
            await send_packet(writer, reader, DISCONNECT_MESSAGE)  # Envia a mensagem de desconexão
            print("[CLIENT] Desconectando...")  # Mensagem de desconexão
            break  # Sai do loop
        else:  # Caso escolha inválida
            print("Opção inválida. Tente novamente.")  # Mensagem de erro

# Função principal do cliente
async def main():
    try:
        reader, writer = await asyncio.open_connection(SERVER, PORT)  # Abre a conexão com o servidor
        await menu(writer, reader)  # Inicia o menu
    except ConnectionRefusedError:  # Caso o servidor não esteja disponível
        print("[CLIENT] Não foi possível conectar ao servidor.")  # Mensagem de erro
    finally:
        writer.close()  # Fecha a conexão
        await writer.wait_closed()  # Aguarda o fechamento
        print("[CLIENT] Conexão encerrada.")  # Mensagem de encerramento

# Execução principal do programa
if __name__ == "__main__":
    asyncio.run(main())  # Executa a função principal
