# peer_corrigido.py
import socket
import os
import threading
import time
import json
import random
import math

CHUNK_SIZE = 1024 
P2P_PORT = 50550 # A porta que este peer usará para escutar

class Peer:
    def __init__(self, tracker_ip, tracker_port, my_ip):
        self.tracker_addr = (tracker_ip, tracker_port)
        self.my_ip = my_ip
        self.my_pieces = {} 

        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.scan_local_files()

        threading.Thread(target=self.start_tcp_server, daemon=True).start()
        threading.Thread(target=self.update_tracker_periodically, daemon=True).start()

    def scan_local_files(self):
        """Verifica os arquivos .txt locais e calcula os pedaços que possui."""
        print("Verificando arquivos locais...")
        for filename in os.listdir('.'):
            if filename.endswith(".txt"):
                file_size = os.path.getsize(filename)
                total_pieces = math.ceil(file_size / CHUNK_SIZE)
                self.my_pieces[filename] = {
                    'total_pieces': total_pieces,
                    'have_pieces': set(range(total_pieces))
                }
        print(f"Peços que possuo inicialmente: {json.dumps(self.my_pieces, default=list, indent=2)}")

    def update_tracker_periodically(self):
        """Envia a lista de pedaços e a porta P2P para o Tracker a cada 3 segundos via UDP."""
        while True:
            try:              
                pieces_info_serializable = {
                    file: {
                        'total_pieces': data['total_pieces'],
                        'have_pieces': list(data['have_pieces'])
                    } for file, data in self.my_pieces.items()
                }
                message = json.dumps({
                    "command": "!update_pieces",
                    "port": P2P_PORT, # <--- MUDANÇA: Envia a porta P2P deste peer para o tracker
                    "pieces_info": pieces_info_serializable
                }).encode('utf-8')
                self.tracker_socket.sendto(message, self.tracker_addr)
            except Exception as e:
                print(f"Erro ao contatar o tracker: {e}")
            time.sleep(3)

    def start_tcp_server(self):
        """Inicia um servidor TCP para atender pedidos de pedaços de outros peers."""
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.my_ip, P2P_PORT))
        server.listen(5)
        print(f"Servidor P2P escutando em {self.my_ip}:{P2P_PORT} (TCP)")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_piece_request, args=(conn, addr), daemon=True).start()

    def handle_piece_request(self, conn, addr):
        """Lida com um pedido de pedaço de outro peer."""
        try:
            request_data = conn.recv(1024).decode('utf-8')
            request = json.loads(request_data)
            filename = request['file']
            piece_index = request['piece']

            if filename in self.my_pieces and piece_index in self.my_pieces[filename]['have_pieces']:
                with open(filename, 'rb') as f:
                    f.seek(piece_index * CHUNK_SIZE)
                    chunk = f.read(CHUNK_SIZE)
                    conn.sendall(chunk)
            else:
                conn.sendall(b"ERROR: Piece not found")
        except Exception as e:
            print(f"Erro ao enviar pedaço para {addr}: {e}")
        finally:
            conn.close()

    def download_file(self):
        """Orquestra o processo de download de um arquivo seguindo as regras do enunciado."""
        print("Solicitando lista de peers do tracker...")
        message = json.dumps({"command": "!get_peers"}).encode('utf-8')
        self.tracker_socket.sendto(message, self.tracker_addr)
        try:
            self.tracker_socket.settimeout(5.0)
            response_data, _ = self.tracker_socket.recvfrom(4096)
            network_pieces = json.loads(response_data.decode('utf-8'))
            self.tracker_socket.settimeout(None)
        except socket.timeout:
            print("Erro: Tracker não respondeu.")
            return
        
        # <--- MUDANÇA: Verifica se a rede tem no mínimo 3 outros peers.
        if len(network_pieces) < 3:
            print(f"\n[ERRO] O download requer no mínimo 3 outros peers na rede.")
            print(f"       Peers encontrados no momento: {len(network_pieces)}.")
            return

        rarest_piece = self._calculate_rarest_missing_piece(network_pieces)

        if not rarest_piece:
            print("Nenhum pedaço novo para baixar. Você já tem tudo ou os arquivos não existem na rede.")
            return
        
        filename, piece_to_download, rarity = rarest_piece
        print(f"Pedaço mais raro a ser baixado: '{filename}' - Peça #{piece_to_download} (Disponível em {rarity} peer(s))")

        # <--- MUDANÇA: Lógica de escolha de peer conforme o enunciado.
        # Escolhe aleatoriamente um peer da LISTA GERAL, não da lista de quem tem a peça.
        all_peer_ips = list(network_pieces.keys())
        if not all_peer_ips:
            print("Erro crítico: A lista de peers está vazia após a verificação inicial.")
            return
            
        target_peer_ip = random.choice(all_peer_ips)
        target_peer_info = network_pieces[target_peer_ip]
        target_peer_port = target_peer_info.get('port')

        if not target_peer_port:
            print(f"Erro: Peer {target_peer_ip} não informou uma porta P2P. Abortando.")
            return

        print(f"Escolhido peer aleatoriamente da lista geral: {target_peer_ip}:{target_peer_port}.")
        print(f"Tentando baixar a peça rara #{piece_to_download} deste peer...")
        
        self._download_piece(target_peer_ip, target_peer_port, filename, piece_to_download)
        
    def _calculate_rarest_missing_piece(self, network_pieces):
        """Analisa a rede e encontra o pedaço mais raro que eu não tenho."""
        piece_availability = {}
        all_network_files = {}

        for peer_ip, data in network_pieces.items():
            for filename, file_data in data.get('files', {}).items():
                if filename not in all_network_files:
                    all_network_files[filename] = file_data['total_pieces']
                for piece_index in file_data['have_pieces']:
                    key = f"{filename}_{piece_index}"
                    piece_availability[key] = piece_availability.get(key, 0) + 1

        missing_pieces = []
        for filename, total in all_network_files.items():
            if filename not in self.my_pieces:
                self.my_pieces[filename] = {'total_pieces': total, 'have_pieces': set()}
            
            my_haves = self.my_pieces[filename]['have_pieces']
            for i in range(total):
                if i not in my_haves:
                    rarity = piece_availability.get(f"{filename}_{i}", 0)
                    if rarity > 0: 
                        missing_pieces.append({'file': filename, 'piece': i, 'rarity': rarity})
        
        if not missing_pieces:
            return None
        
        rarest = min(missing_pieces, key=lambda x: x['rarity'])
        return (rarest['file'], rarest['piece'], rarest['rarity'])

    # <--- MUDANÇA: A função agora aceita 'peer_port' como argumento.
    def _download_piece(self, peer_ip, peer_port, filename, piece_index):
        """Conecta a um peer via TCP e baixa um único pedaço."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # <--- MUDANÇA: Usa a porta recebida do tracker, não um valor fixo.
                s.connect((peer_ip, peer_port))
                request = json.dumps({"file": filename, "piece": piece_index}).encode('utf-8')
                s.sendall(request)
                
                # Aumentado o buffer para garantir que recebe todo o chunk
                piece_data = s.recv(CHUNK_SIZE + 128) # Buffer extra
                
                if piece_data and b"ERROR" not in piece_data:               
                    self._save_piece(filename, piece_index, piece_data)
                    print(f"Sucesso! Pedaço {piece_index} de '{filename}' baixado de {peer_ip}.")
                else:
                    print(f"Falha ao baixar pedaço {piece_index} de {peer_ip}. O peer pode não ter a peça ou retornou um erro.")

        except Exception as e:
            print(f"Erro de conexão com o peer {peer_ip}:{peer_port} -> {e}")

    def _save_piece(self, filename, piece_index, data):
        """Salva um pedaço de dados na posição correta do arquivo."""
        # Garante que o arquivo exista com o tamanho correto antes de escrever
        if not os.path.exists(filename):
            total_size = self.my_pieces[filename]['total_pieces'] * CHUNK_SIZE
            with open(filename, 'wb') as f:
                f.write(b'\0' * total_size)

        with open(filename, 'r+b') as f:
            f.seek(piece_index * CHUNK_SIZE)
            f.write(data)
        
        self.my_pieces[filename]['have_pieces'].add(piece_index)
        print(f"Meus pedaços de '{filename}': {sorted(list(self.my_pieces[filename]['have_pieces']))}")
        
    def disconnect(self):
        """Informa ao tracker que está saindo."""
        message = json.dumps({"command": "!sair"}).encode('utf-8')
        self.tracker_socket.sendto(message, self.tracker_addr)
        self.tracker_socket.close()
        print("\nSinal de desconexão enviado ao tracker.")

def main():
    try:
        TRACKER_IP = input("Digite o IP do Servidor (Tracker): ")
        TRACKER_PORT = int(input("Digite a Porta do Tracker: "))
        MY_IP = input("Digite o SEU PRÓPRIO IP para outros peers se conectarem: ")
        global P2P_PORT
        P2P_PORT = int(input(f"Digite a porta para escutar conexões P2P (padrão {P2P_PORT}): ") or P2P_PORT)

        peer = Peer(TRACKER_IP, TRACKER_PORT, MY_IP)
        
        print("\nCliente Peer iniciado. Comandos disponíveis:")
        print("!baixar - Tenta baixar o pedaço mais raro de um arquivo na rede.")
        print("!meus_pedacos - Mostra os pedaços que você possui.")
        print("!sair - Desconecta da rede.")

        while True:
            cmd = input("> ")
            if cmd == "!baixar":
                peer.download_file()
            elif cmd == "!meus_pedacos":
                my_pieces_serializable = {f: {
                    'total_pieces': d['total_pieces'],
                    'have_pieces': sorted(list(d['have_pieces']))
                } for f, d in peer.my_pieces.items()}
                print(json.dumps(my_pieces_serializable, indent=2))
            elif cmd == "!sair":
                peer.disconnect()
                break
            else:
                print("Comando inválido.")
    except KeyboardInterrupt:
        print("\nSaindo por interrupção do teclado...")
        peer.disconnect()
    except ValueError:
        print("Entrada inválida. Por favor, insira números para as portas.")
    finally:
        print("Encerrando o peer.")


if __name__ == "__main__":
    main()