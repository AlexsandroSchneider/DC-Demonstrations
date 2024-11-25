import socket
import threading
from time import sleep

running, starting, application = True, True, True
server_address, dht_node_id, response = None, None, None
messages_history, clients, dht, routing_table = [], [], [], []
timeStamp = 1
dht_node_size = 10
resources = {}


#########
class Person:
    def __init__(self, id, name, age):
        self.__id = id
        self.__name = name
        self.__age = age
    def get_id(self):
        return self.__id
    def get_all(self):
        return self.__id, self.__name, self.__age
    def set_name(self, name):
        self.__name = name
    def set_age(self, age):
        self.__age = age
#########

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

def handle_application(client_socket):
    client_name = client_socket.getpeername()
    print(f"Novo cliente: {client_name}")
    while True:
        try:
            message = client_socket.recv(1024).decode('utf-8')
            if message.lower() == '!sair':
                break
            elif message.startswith('RES_'):
                resource_requests(client_socket, message[4:])
            elif message == 'get_all_records()':
                print("SELF get_all_records()")
                get_all_records(client_socket)
            else:
                redirect_to_node(client_socket, message)
        except:
            break
    print(f"Cliente desconectado: {client_name}")

def handle_client(client_socket):
    global running, messages_history, timeStamp, response, dht_node_size, resources
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
            elif message.startswith('node_'):
                print(f"RQST {message} from {client_socket.getpeername()}")
                process_response = process_message(message[5:])
                print(f"RESP {process_response} to {client_socket.getpeername()}\n")
                client_socket.send(process_response.encode('utf-8'))
                continue
            elif message.startswith('resp_'):
                print(f"RESP {message} from {client_socket.getpeername()}\n")
                response = message[5:]
                continue
            elif message.startswith('get_node_records()'):
                print(f"RQST {message} from {client_socket.getpeername()}")
                process_response = f"resp_{get_node_records()}"
                print(f"RESP {process_response} to {client_socket.getpeername()}\n")
                client_socket.send(process_response.encode('utf-8'))
                continue
            elif message.startswith('REQ_'):
                if message[4:] in ['OK', 'DENIED'] or message[4:].startswith('REG'):
                    response = message
                    continue
                if resources.get(message[4:]):
                    client_socket.send("REQ_DENIED".encode('utf-8'))
                    print("REQ_" + message[4:] + "_DENIED")
                else:
                    reg = get_record_if_node(message[4:])
                    if reg:
                        client_socket.send(f"REQ_REG_{reg}".encode('utf-8'))
                        print(f"REQ_REG_{reg}")
                        continue
                    client_socket.send("REQ_OK".encode('utf-8'))
                    print("REQ_" + message[4:] + "_OK")
            elif message.startswith('SET_'):
                resources[message[4:]] = 1
            elif message.startswith('REL_'):
                resources.pop(message[4:])
            elif message.startswith('start_dht('):
                dht_node_size = int(message[10:-1])
                start_dht()
                continue
            else:
                print(message)
                continue
        except Exception as e:
            break

def auto_connect(new_client):
    if all(int(client[1]) != int(new_client[1]) for client in clients) and int(new_client[1]) != int(server_address[1]):
        try:
            ip, port = new_client
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((ip, int(port)))
            threading.Thread(target=handle_client, args=(client_socket,)).start()
        except Exception as e:
            print(f"[!] ERRO! {e}\n")

def broadcast(message):
    for client in clients:
        try:
            client[0].send(message.encode('utf-8'))
        except:
            pass

def resource_requests(client_socket, msg):
    global resources, response
    print(msg)
    res = msg[:-1].split('(')[1]
    if msg.startswith('RELEASE'):
        broadcast(f"REL_{res}")
        resources.pop(res)
    else:
        if resources.get(res):
            client_socket.send(f"DENIED({res})".encode('utf-8'))
            print(f"DENIED({res})")
            return
        reg = get_record_if_node(res)
        count = len(clients)
        for client in clients:
            client[0].send(f"REQ_{res}".encode('utf-8'))
            while response == None:
                sleep(0.1)
            if response == 'REQ_OK':
                count -= 1
            elif response.startswith('REQ_REG_'):
                reg = response[8:]
                count -= 1
            response = None
        if count == 0:
            resources[res] = 1
            broadcast(f"SET_{res}")
            if reg:
                client_socket.send(f"APPROVED({reg})".encode('utf-8'))
            else:
                client_socket.send(f"APPROVED({res})".encode('utf-8'))
            print(f"APPROVED({res})")
        else:
            client_socket.send(f"DENIED({res})".encode('utf-8'))
            print(f"DENIED({res})")

def get_record_if_node(id):
    h_idx = hash_idx_node(int(id))
    if routing_table[dht_node_id][1] <= h_idx <= routing_table[dht_node_id][2]:
        h_dht = h_idx - (dht_node_id * dht_node_size)
        reg = get_record(id, h_dht)
        if reg:
            return reg.get_all()
        return None

def get_record(id, h_idx):
    for reg in dht[h_idx]:
        if reg.get_id() == id:
            return reg
    return None

def get_node_records():
    records = []
    for rec_list in dht:
        for rec in rec_list:
            records.append(rec.get_all())
    msg = ""
    for rec in records:
        msg += str(rec)
        if rec != records[-1]:
            msg += ";"
    return msg

def get_all_records(client_socket):
    global response
    node_records = []
    recs = get_node_records()
    if recs != "":
        node_records.append(recs)
    for cli in clients:
        cli[0].send('get_node_records()'.encode('utf-8'))
        print(f"SENT get_node_records() to {cli[0].getpeername()}")
        while response == None:
            sleep(0.1)
        if response != "":
            node_records.append(response)
        response = None
    msg = "list_"
    if node_records:
        for recs in node_records:
            msg += recs
            if recs != node_records[-1]:
                msg += ";"
    else:
        msg += "EMPTY"
    print(f"RESP {msg}\n")
    client_socket.send(msg.encode('utf-8'))

def msg_get_parts(msg):
    if msg.startswith('insert('):
        parts = msg[7:-1].replace("'",'').split(';')
        parts.append(0)
    elif msg.startswith('update('):
        parts = msg[7:-1].replace("'",'').split(';')
        parts.append(1)
    elif msg.startswith('get('):
        parts = [msg[4:-1]]
        parts.append(2)
    elif msg.startswith('delete('):
        parts = [msg[7:-1]]
        parts.append(3)
    return parts

def hash_idx_node(val):
    return val % (dht_node_size * len(routing_table))

def process_message(msg):
    parts = msg_get_parts(msg)
    h_dht = hash_idx_node(int(parts[0])) - (dht_node_id * dht_node_size) ## hash idx on dht list
    reg = get_record(parts[0], h_dht)
    if parts[-1] == 0:
        if not reg:
            dht[h_dht].append(Person(parts[0], parts[1], int(parts[2])))
            return f"resp_Inclusão do cadastro concluído! Nó: {dht_node_id}, Hash DHT: {hash_idx_node(int(parts[0]))}, Hash NODE: {h_dht}"
        return f"resp_Já existe cadastro com ID {parts[0]}"
    elif parts[-1] == 1:
        if reg:
            reg.set_name(parts[1])
            reg.set_age(int(parts[2]))
            return f"resp_Atualização do cadastro concluída! Nó: {dht_node_id}, Hash DHT: {hash_idx_node(int(parts[0]))}, Hash NODE: {h_dht}"
        return f"resp_Não existe cadastro com ID {parts[0]}"
    elif parts[-1] == 2:
        if reg:
            id, name, age = reg.get_all()
            message = f"ID: {id}, Nome: {name}, Idade: {age}. Nó: {dht_node_id}, Hash DHT: {hash_idx_node(int(parts[0]))}, Hash NODE: {h_dht}"
            return f"resp_{message}"
        return f"resp_Não existe cadastro com ID {parts[0]}"
    elif parts[-1] == 3:
        if reg:
            dht[h_dht].remove(reg)
            message = f"Cadastro removido! Nó: {dht_node_id}, Hash DHT: {hash_idx_node(int(parts[0]))}, Hash NODE: {h_dht}"
            return f"resp_{message}"
        return f"resp_Não existe cadastro com ID {parts[0]}"
    return "Algo de errado não está certo..."

def redirect_to_node(client_socket, msg):
    global response
    parts = msg_get_parts(msg)
    h_idx = hash_idx_node(int(parts[0]))
    msg = "node_" + msg
    for node in routing_table: ## check which node to send resquest
        if node[1] <= h_idx <= node[2]:
            if node[0] == server_address[1]: ## node is self
                print(f"SELF {msg}")
                response = process_message(msg[5:])[5:]
                print(f"RESP {response}\n")
                break
            for cli in clients:
                if cli[1] == node[0]:
                    print(f"SENT {msg} to {cli[0].getpeername()}")
                    cli[0].send(msg.encode('utf-8'))
                    break
            break
    while not response:
        sleep(0.1)
    client_socket.send(response.encode('utf-8'))
    response = None
    
def connect_to():
    while True:
        try:
            dest = str(input("Informe endereço do servidor (formato 'IP:PORTA'): "))
            ip, port = dest.split(":")
        except:
            print("[!] Endereço inválido!\n")
            break
        try:
            auto_connect([ip, port])
        except:
            print("\nERRO! Cliente não encontrado :-(\n")
        finally:
            break

def start_dht():
    global dht, routing_table, starting, dht_node_id
    starting = False

    try: ## stop listening to nodes
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_socket.connect((server_address[0],server_address[1]))
    except:
        pass

    for _ in range(dht_node_size):
        dht.append([]) # adjacency
    routing_table.append(server_address[1])
    for c in clients:
        routing_table.append(c[1])
    routing_table.sort()
    dht_node_id = routing_table.index(server_address[1]) # node id on routing table
    for i in range(len(routing_table)):
        routing_table[i] = (routing_table[i], dht_node_size*i, (dht_node_size*(i+1))-1) # node, hash_id_start, hash_id_end
    print("\nServidor DHT inicializado!")
    print(f"Nós ({len(routing_table)}) * Tamanho da lista ({dht_node_size}) = Hash Keys (0 - {(dht_node_size*len(routing_table))-1})\n")

def messaging():
    global running, timeStamp, dht_node_size
    print("Digite sua mensagem, ou '!ajuda': ")
    while running:
        try:
            message = input()
            timeStamp += 1
            if message.lower().removeprefix('!') in ['ajuda','help','h']:
                print("\nComandos:\n'!S' -> Iniciar serviço DHT\n'!C' -> Conectar a um Nó")
                print("'!L' -> Listar cadastros\n'!RT' -> Ver tabela Routing\n'!RC' Ver recursos em uso\n\n")
            elif message.lower() == '!c':
                connect_to()
                continue
            elif message.lower() in ['!exit','!sair','!quit']:
               break
            elif message.lower() == '!s':
                while True:
                    try:
                        dht_node_size = int(input("Digite o número de chaves em cada nó: "))
                        break
                    except:
                        print("Inválido! Informe um número inteiro.")
                        continue
                broadcast(f"start_dht({dht_node_size})")
                start_dht()
                continue
            elif message.lower() == '!rt':
                if not starting:
                    print("\nTABELA ROUTING:")
                    for i, node in enumerate(routing_table):
                        print(f"Nó: {i} ({node[0]}) -> índices:({node[1]} - {node[2]})")
                else:
                    print("\nDHT não iniciado, digite '!s' para iniciar com os nós atuais.\n")
                continue
            elif message.lower() == '!rc':
                print(resources)
                continue
            elif message.lower() == '!l':
                print("\nLista de cadastros:")
                for i in dht:
                    for j in i:
                        print(j.get_all())
                print()
            else:
                try:
                    broadcast(message)
                except Exception as e:
                    print(f"[ERRO] Falha no envio da mensagem: {e}")
                    break
        except:
            break

def service():
    global server_address
    
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((get_my_ip(), 0))
    server_address = server_socket.getsockname()
    server_socket.listen(5)
    print(f"[!] Ouvindo no endereço -> {server_address[0]}:{server_address[1]}\n[!] Aguardando nós DHT\n")
    threading.Thread(target=messaging).start()

    while starting:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket,)).start()
    
    print("[!] Aguardando clientes\n")
    while application:
        client_socket, client_address = server_socket.accept()
        threading.Thread(target=handle_application, args=(client_socket,)).start()

if __name__ == "__main__":
    service()