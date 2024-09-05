import socket
import threading
import os
from datetime import datetime

running = True

def get_my_ip():
    try:
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(('8.8.8.8', 80))
        ip = temp_socket.getsockname()[0]
        temp_socket.close()
        return ip
    except Exception as e:
        print(f"Erro ao localizar IP local: {e}")
        return None

def receive_messages(client_socket):
    global running
    while running:
        try:
            message, adress = client_socket.recvfrom(1024)
            if not message:
                break
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"{message.decode('utf-8')}\nRecebida de {adress}, às {current_time}\n")
        except socket.error as e:
            print(f"{e}\nUtilize '!change' para trocar destinatário\n")
            continue
        except Exception as e:
            print(f"[ERRO] Erro ao receber mensagem: {e}")
            break


def destination():
    dest = str(input("IP e Porta do destinatário (IP:PORTA): "))
    print()
    ip, port = dest.split(":")
    return ip, int(port)

def my_client():
    global running

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.bind((get_my_ip(), 0))
    client_address = client_socket.getsockname()

    print(f"CHAT UDP!\nCliente vinculado à porta {client_address[0]}:{client_address[1]}\n")
    receiver_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    receiver_thread.start()

    try:
        dest_ip, dest_port = destination()
        print("Digite '!help' para ajuda\n")
        while True:
            message = input()
            match (message):
                case '!exit':
                    break
                case '!change':
                    dest_ip, dest_port = destination()
                    continue
                case '!me':
                    print(f"Cliente vinculado à UDP {client_address[0]}:{client_address[1]}\n")
                    continue
                case '!clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                case '!help':
                    print(f"\nComandos:\n{'!change':10} = trocar endereço e porta de destino\n{'!clear':10} = limpar a tela")
                    print(f"{'!exit':10} = sair do programa\n{'!me':10} = mostrar IP e PORTA vinculado ao usuário\n")
                    continue
                case '':
                    continue
                case _:
                    try:
                        client_socket.sendto(message.encode('utf-8'), (dest_ip, dest_port))
                        current_time = datetime.now().strftime('%H:%M:%S')
                        print(f"Enviada às {current_time}\n")
                    except Exception as e:
                        print(f"[ERRO] Falha no envio da mensagem: {e}")
                        break
    except:
        pass
    finally:
        print("\n[INFO] Saindo.")
        running = False
        client_socket.sendto("".encode('utf-8'), client_address) ## recvfrom é bloqueante, envia último pacote
        receiver_thread.join()
        client_socket.close()

if __name__ == "__main__":
    my_client()