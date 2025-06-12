import socket
import threading
import os
import random
import time
import toml
from typing import List, Tuple

class ClientNetwork:
    def __init__(self, username: str, udp_port: int, tcp_port: int):
        self.username = username
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        
        # Load config
        self.config = self._load_config()
        self.image_folder = self.config["storage"].get("imagepath", "./bilder/")
        self.broadcast_ip = self.config["network"].get("broadcast_ip", "255.255.255.255")
        self.discovery_port = self.config["network"].get("whoisport", 4000)
        
        self.running = True
        self.known_users = {}
        self.away_mode = False
        
        # Initialize sockets
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.udp_socket.bind(('0.0.0.0', self.udp_port))
        
        self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.tcp_socket.bind(('0.0.0.0', self.tcp_port))
        self.tcp_socket.listen(5)
        
        # Start threads
        threading.Thread(target=self._udp_listener, daemon=True).start()
        threading.Thread(target=self._tcp_server, daemon=True).start()

    def _load_config(self):
        try:
            with open("config.toml", "r") as f:
                return toml.load(f)
        except FileNotFoundError:
            print("[Error] config.toml not found, using defaults")
            return {
                "network": {"port": 12345, "broadcast_ip": "255.255.255.255", "whoisport": 4000},
                "storage": {"imagepath": "./bilder/"},
                "features": {"autoreply_enabled": False}
            }

    def _udp_listener(self):
        while self.running:
            try:
                data, addr = self.udp_socket.recvfrom(2048)
                msg = data.decode(errors='ignore')
                print(f"\n[Message from {addr[0]}:{addr[1]}]: {msg}")
                print("> ", end="", flush=True)
                
                # Auto-reply if enabled
                if self.away_mode and self.config["features"].get("autoreply_enabled", False):
                    reply_msg = f"{self.username} (Auto): {self.config['features'].get('autoreply', '')}"
                    self.send_message(reply_msg)
                    
            except Exception as e:
                if self.running:
                    print(f"\n[UDP Listener Error]: {e}")

    def _tcp_server(self):
        while self.running:
            try:
                conn, addr = self.tcp_socket.accept()
                threading.Thread(target=self._handle_tcp_connection, args=(conn, addr), daemon=True).start()
            except Exception as e:
                if self.running:
                    print(f"\n[TCP Server Error]: {e}")

    def _handle_tcp_connection(self, conn, addr):
        try:
            header = conn.recv(512).decode()
            if header.startswith("IMG|"):
                _, sender_name, filename, size, _ = header.split("|")
                size = int(size)
                
                received = b""
                start_time = time.time()
                
                while len(received) < size:
                    chunk = conn.recv(min(4096, size - len(received)))
                    if not chunk:
                        break
                    received += chunk
                    
                    progress = len(received) / size * 100
                    elapsed = time.time() - start_time
                    speed = len(received) / (elapsed * 1024) if elapsed > 0 else 0
                    print(f"\rReceiving: {progress:.1f}% ({len(received)/1024:.1f}KB/{size/1024:.1f}KB) {speed:.1f}KB/s", end="")
                
                print()
                
                os.makedirs(self.image_folder, exist_ok=True)
                rand_id = random.randint(1000, 9999)
                ext = os.path.splitext(filename)[1] or ".jpg"
                out_path = os.path.join(self.image_folder, f"received_{sender_name}_{rand_id}{ext}")
                
                with open(out_path, "wb") as f:
                    f.write(received)
                
                print(f"\n[Image received from {sender_name}] Saved as {out_path}")
                print("> ", end="", flush=True)
                
        except Exception as e:
            print(f"\n[Image Receive Error]: {e}")
        finally:
            conn.close()

    def join_network(self) -> List[Tuple[str, int]]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2)
        
        msg = f"JOIN|{self.username}|{self.udp_port}".encode()
        
        try:
            sock.sendto(msg, (self.broadcast_ip, self.discovery_port))
            data, _ = sock.recvfrom(2048)
            reply = data.decode()
            online_users = []
            
            if reply:
                for entry in reply.split(";"):
                    name, port = entry.split(":")
                    online_users.append((name, int(port)))
                    self.known_users[name] = (self.broadcast_ip, int(port))
            
            return online_users
        except Exception as e:
            print(f"[Discovery Error]: {e}")
            return []
        finally:
            sock.close()

    def get_online_users(self) -> List[Tuple[str, int]]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2)
        
        try:
            sock.sendto(b"GET", (self.broadcast_ip, self.discovery_port))
            data, _ = sock.recvfrom(2048)
            reply = data.decode()
            online_users = []
            
            if reply:
                for entry in reply.split(";"):
                    name, port = entry.split(":")
                    online_users.append((name, int(port)))
            
            return online_users
        except Exception as e:
            print(f"[Discovery Error]: {e}")
            return []
        finally:
            sock.close()

    def send_message(self, message: str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        for _, (ip, port) in self.known_users.items():
            if port != self.udp_port:
                sock.sendto(f"{self.username}: {message}".encode(), (ip, port))
        
        sock.close()

    def send_image(self, image_path: str):
        if not os.path.isfile(image_path):
            print("[Error] File not found!")
            return
            
        filesize = os.path.getsize(image_path)
        filename = os.path.basename(image_path)
        
        with open(image_path, "rb") as f:
            img_data = f.read()
        
        header = f"IMG|{self.username}|{filename}|{filesize}|".encode().ljust(512, b" ")
        
        for name, (ip, port) in self.known_users.items():
            if name != self.username:
                tcp_port = port + 10000
                
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    sock.connect((ip, tcp_port))
                    
                    sock.sendall(header)
                    
                    sent = 0
                    start_time = time.time()
                    with open(image_path, "rb") as f:
                        while sent < filesize:
                            chunk = f.read(4096)
                            sock.sendall(chunk)
                            sent += len(chunk)
                            
                            progress = sent / filesize * 100
                            elapsed = time.time() - start_time
                            speed = sent / (elapsed * 1024) if elapsed > 0 else 0
                            print(f"\rSending to {name}: {progress:.1f}% ({sent/1024:.1f}KB/{filesize/1024:.1f}KB) {speed:.1f}KB/s", end="")
                    
                    print()
                    sock.close()
                    
                except Exception as e:
                    print(f"\n[Error sending to {name}]: {e}")
        
        print("[Image] Sent to all online users")

    def toggle_away_mode(self):
        self.away_mode = not self.away_mode
        status = "aktiviert" if self.away_mode else "deaktiviert"
        print(f"[System] Abwesenheitsmodus {status}")

    def stop(self):
        self.running = False
        self.udp_socket.close()
        self.tcp_socket.close()