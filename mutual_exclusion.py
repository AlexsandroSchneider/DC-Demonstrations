import socket
import threading

running = True
server_address, res_request = None, None
messages, messages_history, clients = [], [], []
oks, timeStamp = 0, 1
resource = [0,0,0]

def get_my_ip():
    try:
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(('8.8.8.8', 80))
        ip = temp_socket.getsockname()[0]
        temp_socket.close()
        return ip
    except Exception as e:
        print(f"Erro ao localizar IP: {e}")
        return None

def send_clients_list(client_socket):
    message = f"conn({timeStamp};"
    for i in range(len(clients)):
        message += f"{clients[i][0].getpeername()[0]},{clients[i][1]}"
        message += ";" if (i+1 < len(clients)) else ")"
    client_socket.send(message.encode('utf-8'))

def handle_client(client_socket):
    global running, messages_history, timeStamp
    client_socket.send(f"listening_port({server_address[1]})".encode('utf-8'))
    while running:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            messages_history.append(message)
            if message.startswith('conn('):
                msg = message[5:-1].split(';')
                timeStamp = max(int(msg[0]), timeStamp) + 1
                for conn in msg[1:]:
                    auto_connect(conn.split(','))
                continue
            elif message.startswith('listening_port('):
                port = int(message[15:-1])
                if all(int(c[1]) != port for c in clients):
                    print(f"[+] New connection from {client_socket.getpeername()[0]}:{port}")
                    clients.append((client_socket, port))
                    send_clients_list(client_socket)
                    continue
                return
            elif message.startswith('M('):
                manage_M(message, client_socket)
                continue
            elif message.startswith('OK('):
                manage_OK()
                continue
            elif message == "DESCONECTANDO":
                running = False
                client_socket.send("DESCONECTANDO".encode('utf-8'))
                break
            else:
                print(message)
                continue
        except Exception as e:
            print(f"[ERRO] Erro ao receber mensagem: {e}")
            break
    print("Desconectado!")

def auto_connect(new_client):
    if all(int(client[1]) != int(new_client[1]) for client in clients) and int(new_client[1]) != int(server_address[1]):
        try:
            ip, port = new_client
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, int(port)))
            threading.Thread(target=handle_client, args=(client_socket,)).start()
        except Exception as e:
            print(e)

def broadcast(message):
    for client in clients:
        try:
            client[0].send(message.encode('utf-8'))
        except:
            pass

def manage_M(message, client_socket):
    global messages, timeStamp
    id, rc, ts = map(int, message[3:-2].replace(' ','').split(','))
    if resource[rc]:
        messages.append(message)
        print(f"Retido, possui o recurso RC: {rc} -> ID {id}")
    else:
        if res_request and rc == res_request[0]:
            if ts < res_request[1]:
                client_socket.send(f"OK({message})".encode('utf-8'))
                timeStamp = max(ts, timeStamp) + 1
                print(f"({ts} < {res_request[1]})?, OK RC: {rc} -> ID {id}")
            else:
                messages.append(message)
                print(f"({ts} < {res_request[1]})?, Retido RC: {rc} -> ID {id}")
        else:
            client_socket.send(f"OK({message})".encode('utf-8'))
            timeStamp = max(ts, timeStamp) + 1
            print(f"OK RC: {rc} -> ID {id}")

def manage_OK():
    global oks, res_request, resource
    oks += 1
    if oks == res_request[2]:
        resource[res_request[0]] = 1
        print(f"Obteve RC: {res_request[0]}, Lista de RCs = ", list(x for x in resource))
        res_request = None
        oks = 0

def resource_acquire():
    global timeStamp, res_request
    if res_request:
        print(f"Aguardando RC: {res_request[0]}\n")
        return
    else:
        try:
            rc = int(input("ID do RC (0,1,2): "))
            if rc not in [0,1,2]:
                print(f"ID {rc} inválido! ", end = '')
                raise Exception
            elif resource[rc] == 1:
                print(f"Já possui o RC {rc}! ", end = '')
                raise Exception
            timeStamp += 1
            res_request = (rc, timeStamp, len(clients))
            print(f"Solicitou RC: {res_request[0]}")
            broadcast(f"M({server_address[1], rc, timeStamp})")
        except:
            print("Retornando ao MENU\n")

def resource_return():
    global timeStamp, resource, messages
    if any(x for x in resource):
        print("Possui RCs: ", end='')
        for id, x in enumerate(resource):
            if x:
                print(id, end=' ')
        try:
            rc = int(input("\nID do RC a devolver (0,1,2): "))
            if not resource[rc]:
                print("Não possui esse RC! ", end='')
                raise Exception
            resource[rc] = 0
            print(f"RC Devolvido: {rc}")
            mssgs = messages.copy()
            for msg in mssgs:
                if msg.startswith('M('):
                    idM, rcM, tsM = map(int, msg[3:-2].replace(' ','').split(','))
                    if rcM == rc:
                        for c in clients:
                            if c[1] == idM:
                                c[0].send(f"OK({msg})".encode('utf-8'))
                                messages.remove(msg)
                                print(f"Devolução, OK RC: {rc} -> ID {idM}")
                                timeStamp = max(tsM, timeStamp) + 1
        except:
            print(f"Retornando ao MENU\n")
    else:
        print("Não possui RCs...\n")

def connect_to():
    while True:
        try:
            dest = str(input("IP e Porta do destinatário, no formato 'IP:PORTA': "))
            ip, port = dest.split(":")
        except:
            print("\nERRO! Forneça um endereço no formato 'IP:PORTA'")
            continue
        finally:
            try:
                auto_connect([ip, port])
                break
            except:
                print("\nERRO! Cliente não encontrado :-(")
                break

def messaging():
    global running, timeStamp
    print("Digite sua mensagem, ou '!help': ")
    while running:
        try:
            message = input()
            timeStamp += 1
            if message.lower() in ['!h','!help']:
                print("\n\nComandos:\n'!S' -> sair\n'!C' -> conectar à um cliente\n'!L' -> listar conexões")
                print("'!M' -> Requisitar RECURSO\n'!R' -> Retornar RECURSO\n'!IP' -> ver seu endereço\n\n")
            elif message.lower() == '!c':
                connect_to()
                continue
            elif message.lower() == '!l':
                print(f"Lista de clientes ({len(clients)}):")
                for client in clients:
                    print(client[0].getpeername(), client[1])
                continue
            elif message.lower() == '!ip':
                print(f"\n\nSeu endereço é {server_address}\n\n")
            elif message.lower() in ['!exit','!sair','!quit','!s']:
                break
            elif message.lower() == '!m':
                resource_acquire()
                continue
            elif message.lower() == '!r':
                resource_return()
                continue
            else:
                try:
                    broadcast(message)
                except Exception as e:
                    print(f"[ERRO] Falha no envio da mensagem: {e}")
                    break
        except:
            break
    broadcast("DESCONECTANDO")
    running = False

def service():
    global running, server_address
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((get_my_ip(), 0))
    server_address = server_socket.getsockname()
    server_socket.listen(5)
    print(f"Ouvindo no endereço {server_address[0]}:{server_address[1]}\n")
    threading.Thread(target=messaging).start()

    while running:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()
    
    for client in clients:
        clients.remove(client)
        clients.close()


if __name__ == "__main__":
    service()