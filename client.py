import socket
import threading
import json
import toml
import os
import base64

config = toml.load("config.toml")
PORT = config["network"]["port"]
BROADCAST_IP = config["network"]["broadcast_ip"]
BUFFER_SIZE = config["network"]["buffer_size"]
IMAGE_PATH = config["network"]["imagepath"]

class Network:
    def __init__(self, username, tcp_port):
        self.username = username
        self.running = True
        self.tcp_port = tcp_port
        
        # UDP Socket für Chatnachrichten
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", PORT))
        
        # TCP Socket für Bildempfang
        self.tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.tcp_sock.bind(('', self.tcp_port))
            self.tcp_sock.listen()
        except OSError as e:
            print(f"[Fehler] TCP-Port {self.tcp_port} kann nicht benutzt werden: {e}")
            raise
        
        self.known_users = {}  # {username: (ip, tcp_port)}
        
        # Threads starten
        threading.Thread(target=self.tcp_server, daemon=True).start()
        threading.Thread(target=self.receive_loop, daemon=True).start()
        
        # JOIN senden
        self.send_join()
    def send_join(self):
        msg = {
            "type": "join",
            "username": self.username,
            "tcp_port": self.tcp_port
        }
        self._send_udp(msg)
    def send_leave(self):
        msg = {
            "type": "leave",
            "username": self.username
        }
        self._send_udp(msg)
    def _send_udp(self, msg_dict):
        try:
            self.sock.sendto(json.dumps(msg_dict).encode(), (BROADCAST_IP, PORT))
        except Exception as e:
            print(f"[Fehler] UDP senden: {e}")
    def send(self, text):
        msg = {
            "type": "chat",
            "username": self.username,
            "text": text
        }
        self._send_udp(msg)
    def receive_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
                msg = json.loads(data.decode())
                mtype = msg.get("type")
                
                if mtype == "join":
                    user = msg.get("username")
                    tcp_p = msg.get("tcp_port")
                    ip = addr[0]
                    if user and tcp_p:
                        self.known_users[user] = (ip, tcp_p)
                        print(f"[System] {user} ist dem Chat beigetreten (TCP-Port: {tcp_p})")
                
                elif mtype == "leave":
                    user = msg.get("username")
                    if user and user in self.known_users:
                        del self.known_users[user]
                        print(f"[System] {user} hat den Chat verlassen.")
                
                elif mtype == "chat":
                    user = msg.get("username")
                    text = msg.get("text")
                    if user != self.username:
                        print(f"[{user}] {text}")
                        
            except Exception as e:
                print(f"[Fehler] UDP Empfang: {e}")
    def tcp_server(self):
        while self.running:
            try:
                conn, addr = self.tcp_sock.accept()
                threading.Thread(target=self.handle_tcp_connection, args=(conn, addr), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"[Fehler] TCP Server: {e}")
    def handle_tcp_connection(self, conn, addr):
        try:
            # Header empfangen (enthält Dateiname und Größe)
            header_data = b''
            while True:
                chunk = conn.recv(1)
                if chunk == b'\n':
                    break
                header_data += chunk
            
            header = json.loads(header_data.decode())
            filename = header.get('filename', f'image_from_{addr[0]}.jpg')
            total_size = header.get('size', 0)
            
            # Bilddaten empfangen
            received = 0
            img_data = b''
            while received < total_size:
                chunk = conn.recv(min(4096, total_size - received))
                if not chunk:
                    break
                img_data += chunk
                received += len(chunk)
                print(f"\rEmpfange Bild: {received}/{total_size} bytes", end='')
            
            print()  # Neue Zeile nach Fortschrittsbalken
            
            # Bild speichern
            os.makedirs(IMAGE_PATH, exist_ok=True)
            full_path = os.path.join(IMAGE_PATH, filename)
            with open(full_path, 'wb') as f:
                f.write(img_data)
            print(f"[TCP] Bild erfolgreich gespeichert: {full_path}")
            
        except Exception as e:
            print(f"\n[Fehler] Bildempfang: {e}")
        finally:
            conn.close()
    def send_image_tcp(self, filepath):
        if not os.path.isfile(filepath):
            print(f"[Fehler] Datei nicht gefunden: {filepath}")
            return
        
        try:
            with open(filepath, 'rb') as f:
                img_data = f.read()
            
            if len(img_data) > 10 * 1024 * 1024:  # 10MB Limit
                print("[Fehler] Bild ist zu groß (max 10MB)")
                return
                
            filename = os.path.basename(filepath)
            
            for user, (ip, tcp_port) in self.known_users.items():
                if user == self.username:
                    continue
                    
                try:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                        s.settimeout(10)
                        s.connect((ip, tcp_port))
                        
                        # Header senden
                        header = {
                            'filename': filename,
                            'size': len(img_data)
                        }
                        s.send(json.dumps(header).encode() + b'\n')
                        
                        # Bilddaten senden
                        s.sendall(img_data)
                        print(f"[System] Bild '{filename}' an {user} gesendet.")
                        
                except Exception as e:
                    print(f"[Fehler] Verbindung zu {user} ({ip}:{tcp_port}): {e}")
                    
        except Exception as e:
            print(f"[Fehler] Bild senden: {e}")
    def stop(self):
        self.send_leave()
        self.running = False
        self.sock.close()
        self.tcp_sock.close()
        print("[System] Client beendet.")
    
    
