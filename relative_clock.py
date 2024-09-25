import socket
import threading
from time import sleep

running = True
balance = 1000.00
acks, messages = [], []
pid, tr = 0, 1

def receive_messages(client_socket):
    global running, messages, acks, tr, pid
    while running:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message.startswith("msg"):
                messages.append(message[4:-1].split(','))
                print(f"Received MSG {message}, TR.id = {tr}.{pid}")
                continue
            if message.startswith("ack"):
                print(f"Received ACK {message}, TR.id = {tr}.{pid}")
                acks.append(message[8:-2].split(','))
                continue
            if message == "DESCONECTANDO":
                running = False
                client_socket.send("DESCONECTANDO".encode('utf-8'))
                break
        except Exception as e:
            print(f"[ERRO] Erro ao receber mensagem: {e}")
            break
    print("Desconectado!")

def treat_messages(client_socket):
    global running, messages, acks, tr, pid, balance
    while running:
        tr_id = float(str(tr)+'.'+str(pid))
        for msg in messages:
            if float(msg[1]) <= tr_id:
                msg = messages.pop(messages.index(msg))
                message = f"ack(msg({msg[0]},{msg[1]}))"
                client_socket.send(message.encode('utf-8'))
                print(f"Sent ACK {message}, TR.id = {tr_id}")
        for msg in acks:
            if float(msg[1]) <= tr_id:
                msg = acks.pop(acks.index(msg))
                if msg[0][0] == 'D':
                    balance += int(msg[0][1:])
                else:
                    balance += (balance * int(msg[0][1:])/100)
                tr = max(int(msg[1].split('.')[0]), tr) + 1
                print(f"Executed {msg}: balance = {balance}, TR.id = {tr_id + 1}")
                break
        sleep(0.1)

def port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return False
        except OSError:
            return True
        
def messaging(client_socket):
    global running, messages, tr, pid
    
    client_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    client_thread.start()
    treat_msg = threading.Thread(target=treat_messages, args=(client_socket,))
    treat_msg.start()

    while running:
        try:
            message = input() ## Operações : Dnum, para deposito; Jnum, para juros
            tr += 1
            message = f"msg({message},{str(tr)+'.'+str(pid)})"
            if not running or message in ['!exit','!sair','!quit']:
                break
            try:
                messages.append(message[4:-1].split(','))
                client_socket.send(message.encode('utf-8'))
                print(f"Sent MSG {message}, TR.id = {tr}.{pid}")
            except Exception as e:
                print(f"[ERRO] Falha no envio da mensagem: {e}")
                break
        except:
            running = False
            pass
    client_socket.send("DESCONECTANDO".encode('utf-8'))
    client_thread.join()
    client_socket.close()


def service():
    global pid

    host = 'localhost'
    port = 12345
    
    if not port_in_use(host, port): # listens
        pid = 1
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"[*] Ouvindo na porta: {port}; PID = {pid}")
        client_socket, client_address = server_socket.accept() # awaits connection
        print(f"Conectado ao cliente: {client_address}\n")
        messaging(client_socket)
        server_socket.close()

    else: # connects
        pid = 2
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print(f"[*] Conexão com servidor: {host}:{port}; PID = {pid}\n")
        messaging(client_socket)

if __name__ == "__main__":
    service()