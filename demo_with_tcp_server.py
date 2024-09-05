import socket
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
            message = client_socket.recv(1024)
            if not message:
                break

            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"{message.decode('utf-8')}\nRecebida às {current_time}\n")

        except socket.error as e:
            print(f"Erro de socket: {e}\nUtilize '!change' para trocar destinatário\n")
            break

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
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        my_socket.bind((get_my_ip(), 0))
        my_address = my_socket.getsockname()
        my_socket.listen(5)

        print(f"Conexão TCP ouvindo na porta {my_address[0]}:{my_address[1]}\n")

        client_socket, addr = my_socket.accept()

        print(f"Conexão TCP estabelecida com {my_address[0]}:{my_address[1]}\n")

        while running:
            try:
                message = client_socket.recv(1024)
                if not message:
                    break

                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"{message.decode('utf-8')}\nRecebida às {current_time}\n")

            except socket.error as e:
                print(f"Erro de socket: {e}\nUtilize '!change' para trocar destinatário\n")
                break

            except Exception as e:
                print(f"[ERRO] Erro ao receber mensagem: {e}")
                break

            print("Digite '!help' para ajuda\n")
            message = input()
            match message:
                case '!exit':
                    break
                case '!me':
                    print(f"Conectado ao servidor TCP {my_address[0]}:{my_address[1]}\n")
                    continue
                case '!clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                case '!help':
                    print(f"\nComandos:\n{'!change':10} = trocar endereço e porta de destino\n{'!clear':10} = limpar a tela")
                    print(f"{'!exit':10} = sair do programa\n{'!me':10} = mostrar IP e PORTA do servidor\n")
                    continue
                case '':
                    continue
                case _:
                    try:
                        client_socket.send(message.encode('utf-8'))
                        current_time = datetime.now().strftime('%H:%M:%S')
                        print(f"Enviada às {current_time}\n")
                    except Exception as e:
                        print(f"[ERRO] Falha no envio da mensagem: {e}")
                        break

    except Exception as e:
        print(f"[ERRO] Erro na conexão: {e}")

    finally:
        print("\n[INFO] Saindo.")
        running = False
        my_socket.close()


if __name__ == "__main__":
    my_client()
