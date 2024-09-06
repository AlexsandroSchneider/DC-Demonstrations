import socket
import threading
from datetime import datetime

running = True

def receive_messages(client_socket):
    global running
    while running:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message == "DESCONECTANDO":
                running = False
                client_socket.send("DESCONECTANDO".encode('utf-8'))
                break
            current_time = datetime.now().strftime('%H:%M:%S')
            print(f"{message}\nRecebida às {current_time}\n")
        except Exception as e:
            print(f"[ERRO] Erro ao receber mensagem: {e}")
            break
    print("Desconectado!")

def port_in_use(host, port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind((host, port))
            return False
        except OSError:
            return True
        
def messaging(client_socket):
    global running
    client_thread = threading.Thread(target=receive_messages, args=(client_socket,))
    client_thread.start()
    while running:
        try:
            message = input()
            if not running or message in ['!exit','!sair','!quit']:
                break
            try:
                client_socket.send(message.encode('utf-8'))
                current_time = datetime.now().strftime('%H:%M:%S')
                print(f"Enviada às {current_time}\n")
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
    global running
    host = 'localhost'
    port = 12345

    if not port_in_use(host, port): # listens
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"[*] Servidor iniciado na porta: {port}")
        client_socket, client_address = server_socket.accept() # awaits connection
        print(f"Conectado ao cliente: {client_address}\n")
        messaging(client_socket)
        server_socket.close()

    else: # connects
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((host, port))
        print(f"[*] Conexão com servidor: {host}:{port}\n")
        messaging(client_socket)

if __name__ == "__main__":
    service()