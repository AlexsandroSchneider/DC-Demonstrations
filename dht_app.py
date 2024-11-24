import socket
import threading
import os
from time import sleep

def receive_messages(client_socket):
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message.startswith('list_'):
                list_records(message[5:])
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
        records = msg.replace(' ','').replace("'","").split(';')
        for rec in records:
            print(rec)

def insert_data(client_socket):
    print("Carregando dados de exemplo:")
    sample_data = [(64543821092,'João',18),(58298719042,'Maria',19),(97349002009,'Tiago',20),(14472648008,'Carla',21),
              (44610061074,'José',22),('05186612022','Jonas',23),('06052667001','Taís',24),(39087038089,'Paula',25)]
    for reg in sample_data:
        msg = f"insert({reg[0]};{reg[1]};{reg[2]})"
        client_socket.send(msg.encode('utf-8'))
        sleep(0.1)

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

def insert_record():
    print("Novo cadastro:")
    id = verify_id()
    name = input("(text) Digite o nome: ").replace(';',',').strip()
    age = verify_age()
    return f"insert({id};{name};{age})"

def update_record():
    print("Atualizar cadastro:")
    id = verify_id()
    name = input("(text) Digite o nome: ").replace(';',',').strip()
    age = verify_age()
    return f"update({id};{name};{age})"

def get_record():
    print("Buscar cadastro:")
    id = verify_id()
    return f"get({id})"

def delete_record():
    print("Remover cadastro:")
    id = verify_id()
    return f"delete({id})"

def messaging(client_socket):
    print("Digite sua mensagem, ou 'ajuda': ")
    while True:
        try:
            message = input()
            os.system('cls' if os.name == 'nt' else 'clear')
            if message.lower() in ['help','ajuda','h']:
                print("Comandos:\n'1' -> Inserir cadastro\n'2' -> Atualizar cadastro\n'3' -> Buscar cadastro")
                print("'4' -> Remover cadastro\n'5' -> Listar todos cadastros\n'LOAD' -> Carregar dados de exemplo\n'SAIR' -> Sair do programa\n")
            elif message == '1':
                client_socket.send(insert_record().encode('utf-8'))
                continue
            elif message == '2':
                client_socket.send(update_record().encode('utf-8'))
                continue
            elif message == '3':
                client_socket.send(get_record().encode('utf-8'))
                continue
            elif message == '4':
                client_socket.send(delete_record().encode('utf-8'))
                continue
            elif message == '5':
                client_socket.send('get_all_records()'.encode('utf-8'))
                continue
            elif message.lower() == 'load':
                insert_data(client_socket)
                continue
            elif message.lower() in ['sair','exit','quit']:
                client_socket.send('!sair'.encode('utf-8'))
                break
            else:
                print("Comando inválido!\nDigite 'ajuda' para ver comandos disponíveis.\n")
                continue
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