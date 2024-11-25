import socket  # Importa a biblioteca socket para comunicação de rede
import threading  # Importa a biblioteca threading para execução em múltiplas threads
from concurrent.futures import ThreadPoolExecutor  # Importa ThreadPoolExecutor para gerenciar o pool de threads
import time 

# Constantes de configuração
HEADER = 64  # Tamanho do cabeçalho
PORT = 5050  # Porta de comunicação
FORMAT = 'utf-8'  # Formato de codificação de mensagens
DISCONNECT_MESSAGE = "!DISCONNECT"  # Mensagem de desconexão
SERVER = "127.0.0.1"  # Endereço do servidor
ADDR = (SERVER, PORT)  # Endereço completo do servidor

# Variáveis globais
receiver_window = 5  # Tamanho da janela de recepção (para controle do Go-Back-N)
lost_packets = []    # Lista para pacotes simulados como perdidos
protocol = "SR"      # Protocolo padrão (Selective Repeat)

# Função para calcular o checksum de uma mensagem
def checksum(data):
    return sum(bytearray(data, 'utf-8')) % 256  # Soma os bytes e retorna o módulo 256

# Função para incluir erro de integridade nas confirmações
def simulate_integrity_error(data):
    return sum(bytearray(data, 'utf-8')) % 256 + 1  # Simula erro no checksum (erro de integridade)

# Função para manipular pacotes recebidos
def handle_client(conn, addr):
    global protocol, receiver_window  # Usa as variáveis globais do protocolo e janela de recepção
    print(f"[NEW CONNECTION] {addr} conectado.")  # Exibe mensagem ao conectar

    connected = True  # Variável para controlar a conexão
    try:
        while connected:
            msg = conn.recv(2048).decode(FORMAT)  # Recebe a mensagem do cliente
            if not msg:  # Caso não haja mensagem
                print(f"[SERVER] Cliente {addr} fechou a conexão.")  # Exibe mensagem de desconexão
                connected = False  # Encerra a conexão
                continue  # Continua a execução

            # Negociação de protocolo
            if msg.startswith("PROTOCOL"):  # Verifica se a mensagem é de negociação de protocolo
                _, chosen_protocol = msg.split("|")  # Extrai o protocolo escolhido
                protocol = chosen_protocol  # Atualiza o protocolo global
                print(f"[SERVER] Protocolo definido: {protocol}")  # Exibe protocolo recebido
                conn.send(protocol.encode(FORMAT))  # Envia o protocolo de volta ao cliente
                continue  # Continua a execução

            # Processamento do pacote recebido
            parts = msg.split("|")  # Divide a mensagem em partes
            if len(parts) < 3:  # Verifica se o formato do pacote está correto
                print("[SERVER] Formato de pacote inválido.")  # Exibe mensagem de erro
                continue  # Continua a execução

            # Extração dos dados do pacote
            seq_num, data, received_checksum = int(parts[0]), parts[1], int(parts[2])  # Separa o número de sequência, dados e checksum
            error_type = parts[3] if len(parts) == 4 else None  # Verifica se há erro no pacote

            print(f"[SERVER] Pacote {seq_num} recebido.")  # Exibe o número do pacote recebido

            # Simulação de timeout
            if error_type == "timeout":  # Verifica se foi configurado para erro de timeout
                print(f"[SERVER] Timeout simulado para pacote {seq_num}.")  # Exibe a mensagem de erro de timeout
                continue  # Ignora o pacote e continua

            # Verifica integridade do pacote
            if checksum(data) != received_checksum:  # Verifica se o checksum está correto
                print(f"[SERVER] Checksum inválido para pacote {seq_num}.")  # Exibe erro de checksum
                conn.send(f"NAK|{seq_num}".encode(FORMAT))  # Envia NAK indicando erro no pacote
                if protocol == "GBN":  # Se o protocolo for GBN (Go-Back-N)
                    print(f"[SERVER] GBN: Ignorando pacotes subsequentes após {seq_num}.")  # Exibe que pacotes subsequentes são ignorados
                    continue  # Ignora pacotes subsequentes
                else:  # Se for SR (Selective Repeat)
                    continue  # Continua processando o próximo pacote

            print(f"[SERVER] Pacote {seq_num} aceito.")  # Exibe confirmação de aceitação do pacote

            # Envia ACK (acknowledgement) para o cliente
            conn.send(f"ACK|{seq_num}".encode(FORMAT))  # Envia ACK indicando que o pacote foi aceito

            # Controle de recepção no protocolo Go-Back-N (GBN)
            if protocol == "GBN":
                receiver_window -= 1  # Decrementa o tamanho da janela de recepção
                if receiver_window == 0:  # Caso a janela de recepção esteja cheia
                    print("[SERVER] Janela cheia no GBN. Pausando envio.")  # Exibe mensagem de pausa
                    time.sleep(1)  # Simula uma pausa no envio
                    receiver_window = 5  # Reseta o tamanho da janela de recepção

            # Verifica se a mensagem é de desconexão
            if data == DISCONNECT_MESSAGE:  # Caso o cliente envie a mensagem de desconexão
                connected = False  # Encerra a conexão
    except Exception as e:  # Caso ocorra algum erro
        print(f"[SERVER] Erro: {e}")  # Exibe a mensagem de erro
    finally:
        conn.close()  # Fecha a conexão com o cliente
        print(f"[SERVER] Conexão encerrada com {addr}.")  # Exibe que a conexão foi encerrada

# Função para iniciar o servidor
def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria o socket para o servidor
    server.bind(ADDR)  # Associa o socket ao endereço e porta
    server.listen()  # Coloca o servidor em modo de escuta
    print("[SERVER] Servidor iniciado.")  # Exibe mensagem de início do servidor

    # Usa um pool de threads para lidar com múltiplos clientes simultaneamente
    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            conn, addr = server.accept()  # Aceita uma conexão do cliente
            executor.submit(handle_client, conn, addr)  # Submete a conexão para ser tratada em uma thread

print("[SERVER] Iniciando...")  # Exibe mensagem de início do servidor
start()  # Inicia o servidor
