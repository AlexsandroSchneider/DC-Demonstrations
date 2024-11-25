import socket
import threading
import os
from time import sleep

response, insert = None, None

def receive_messages(client_socket):
    global response, insert
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message.startswith('list_'):
                list_records(message[5:])
            elif message.startswith('DENIED') or message.startswith('APPROVED'):
                response = message
            elif message.startswith('Inclusão') or message.startswith('Já existe'):
                insert = message
                print(message + '\n')
            else:
                print(message + '\n')
        except:
            break
    print("Desconectado!")

def list_records(msg):
    print("Lista de cadastros (ID, Nome, Idade):\n")
    if msg == "EMPTY":
        print("Nenhum cadastro localizado")
    else:
        records = msg.replace("'","").split(';')
        for rec in records:
            print(rec)

def verify_age():
    while True:
        try:
            age = int(input("(int) Digite a idade: "))
            break
        except:
            print("Idade inválida. Informe um número inteiro.")
            continue
    return age

def verify_id():
    while True:
        id = input("(int) Digite o código identificador: ")
        if id.isdigit():
            break
        else:
            print("Identificador inválido. Informe um número inteiro.")
            continue
    return id

def request_id(client_socket, id):
    global response
    client_socket.send(f"RES_REQUEST({id})".encode('utf-8'))
    while response == None:
        sleep(0.01)
    if response == f"DENIED({id})":
        var = None
    else:
        var = response[9:-1].replace('(','').replace(')','').replace("'","").split(',')
    response = None
    return var

def insert_record(client_socket):
    print("Novo cadastro:")
    id = verify_id()
    resp = request_id(client_socket, id)
    if not resp:
        print(f"ID ({id}) em uso (já existe, ou está sendo cadastrado).\nTente novamente mais tarde.\n")
        return
    if len(resp) > 1:
        print(f"Já existe cadastro de ID ({id}).\n")
        client_socket.send(f"RES_RELEASE({id})".encode('utf-8'))
        return
    name = input("(text) Digite o nome: ").replace(';',',').strip()
    age = verify_age()
    client_socket.send(f"insert({id};{name};{age})".encode('utf-8'))
    sleep(0.1)
    client_socket.send(f"RES_RELEASE({id})".encode('utf-8'))

def update_record(client_socket):
    print("Atualizar cadastro:")
    id = verify_id()
    resp = request_id(client_socket, id)
    if not resp:
        print(f"ID ({id}) em uso.\nTente novamente mais tarde.\n")
        return
    if len(resp) == 1:
        print(f"Não existe cadastro de ID ({id}).\n")
        client_socket.send(f"RES_RELEASE({id})".encode('utf-8'))
        return
    print(f"ATUAL -> Nome: {resp[1]}, Idade:{resp[2]}\nDigite as novas informações:\n")
    name = input("(text) Digite o nome: ").replace(';',',').strip()
    age = verify_age()
    client_socket.send(f"update({id};{name};{age})".encode('utf-8'))
    sleep(0.1)
    client_socket.send(f"RES_RELEASE({id})".encode('utf-8'))

def delete_record(client_socket):
    print("Remover cadastro:")
    id = verify_id()
    resp = request_id(client_socket, id)
    if not resp:
        print(f"ID ({id}) em uso.\nTente novamente mais tarde.\n")
        return
    if len(resp) == 1:
        print(f"Não existe cadastro de ID ({id}).\n")
        client_socket.send(f"RES_RELEASE({id})".encode('utf-8'))
        return
    client_socket.send(f"delete({id})".encode('utf-8'))
    sleep(0.1)
    client_socket.send(f"RES_RELEASE({id})".encode('utf-8'))

def get_record():
    print("Buscar cadastro:")
    id = verify_id()
    return f"get({id})"

def messaging(client_socket):
    global response
    print("Digite sua mensagem, ou 'ajuda': ")
    while True:
        try:
            message = input()
            os.system('cls' if os.name == 'nt' else 'clear')
            if message.lower() in ['help','ajuda','h']:
                print("Comandos:\n'1' -> Inserir cadastro\n'2' -> Atualizar cadastro\n'3' -> Buscar cadastro")
                print("'4' -> Remover cadastro\n'5' -> Listar todos cadastros\n'SAIR' -> Sair do programa\n")
            elif message == '1':
                insert_record(client_socket)
            elif message == '2':
                update_record(client_socket)
            elif message == '3':
                client_socket.send(get_record().encode('utf-8'))
                continue
            elif message == '4':
                delete_record(client_socket)
            elif message == '5':
                client_socket.send('get_all_records()'.encode('utf-8'))
                continue
            elif message.lower() in ['sair','exit','quit']:
                client_socket.send('!sair'.encode('utf-8'))
                break
            else:
                print("Comando inválido!\nDigite 'ajuda' para ver comandos disponíveis.\n")
                continue
            response = None
        except:
            print("Erro!\n")
            break

def application():
    while True:
        try:
            dest = str(input("Informe endereço do servidor (formato 'IP:PORTA'): "))
            ip, port = dest.split(":")
        except:
            print("[!] Endereço inválido!\n")
            continue
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, int(port)))
            threading.Thread(target=receive_messages, args=(client_socket,)).start()
            os.system('cls' if os.name == 'nt' else 'clear')
            messaging(client_socket)
            client_socket.close()
        except Exception as e:
            print(f"\n[!] ERRO! {e} :-(\n\nSAINDO!")
        finally:
            break

if __name__ == "__main__":
    application()