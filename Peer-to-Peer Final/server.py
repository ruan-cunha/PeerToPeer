# tracker_corrigido.py
import socket
import threading
import time
import json

peer_list = {}
LOCK = threading.Lock()
PEER_TIMEOUT = 15

class Tracker:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind((self.ip, self.port))
        print(f"Servidor Tracker iniciado em {self.ip}:{self.port} (UDP)")

    def check_inactive_peers(self):
        """Thread que remove peers inativos periodicamente."""
        while True:
            time.sleep(PEER_TIMEOUT)
            with LOCK:
                now = time.time()
                inactive_peers = [
                    addr for addr, data in peer_list.items()
                    if now - data.get('last_seen', 0) > PEER_TIMEOUT
                ]
                for addr in inactive_peers:
                    print(f"Removendo peer inativo: {addr}")
                    del peer_list[addr]
                if inactive_peers:
                    print("Lista de Peers Atualizada:", json.dumps(peer_list, indent=2))

    def start(self):
        """Inicia o loop principal do servidor para escutar mensagens UDP."""
        threading.Thread(target=self.check_inactive_peers, daemon=True).start()

        while True:
            try:
                data, addr = self.server.recvfrom(4096)
                message = json.loads(data.decode('utf-8'))
                client_ip = addr[0]
                command = message.get("command")

                with LOCK:
                    if command == "!update_pieces":
                        # <--- MUDANÇA: Armazenar a porta P2P do peer, enviada na mensagem
                        peer_list[client_ip] = {
                            'port': message.get('port'), 
                            'files': message.get('pieces_info', {}),
                            'last_seen': time.time()
                        }
                        # Descomente as linhas abaixo para depuração
                        # print(f"Peer {client_ip} atualizou suas informações.")
                        # print("Lista de Peers:", json.dumps(peer_list, indent=2))

                    elif command == "!get_peers":
                        peers_to_send = {
                            ip: data for ip, data in peer_list.items() if ip != client_ip
                        }
                        response = json.dumps(peers_to_send).encode('utf-8')
                        self.server.sendto(response, addr)
                        print(f"Lista de peers enviada para {client_ip}")

                    elif command == "!sair":
                        if client_ip in peer_list:
                            del peer_list[client_ip]
                            print(f"Peer {client_ip} desconectado.")
                            print("Lista de Peers Atualizada:", json.dumps(peer_list, indent=2))

            except (json.JSONDecodeError, KeyError) as e:
                print(f"Recebida mensagem mal formatada de {addr}: {e}")
            except Exception as e:
                print(f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    IP = input("Digite o IP do Servidor (Tracker): ")
    try:
        PORT = int(input("Digite a Porta do Servidor (ex: 9090): "))
        tracker = Tracker(IP, PORT)
        tracker.start()
    except ValueError:
        print("Porta inválida. Por favor, insira um número.")
    except Exception as e:
        print(f"Não foi possível iniciar o tracker: {e}")