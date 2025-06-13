import socket
import threading
import os
import random

class ClientNetwork:
    def __init__(self, username, udp_port, tcp_port, srv_port=4000, bilder_ordner="./bilder/"):
        self.username = username
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.srv_port = srv_port
        self.bilder_ordner = bilder_ordner
        self._udp_listener_thread = None
        self._tcp_server_thread = None
        self._listening = False
        # Starte Listener direkt beim Erzeugen!
        self._start_udp_listener()
        self._start_tcp_server()

    def _start_udp_listener(self):
        def udp_listener():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('localhost', self.udp_port))
            print(f"[Listener] Hört auf UDP-Port {self.udp_port}")
            while True:
                try:
                    data, addr = sock.recvfrom(2048)
                    print(f"\n[Nachricht empfangen]: {data.decode(errors='ignore')}")
                    print("> ", end="", flush=True)
                except Exception as e:
                    print(f"Listener-Fehler: {e}")
                    break
        if not self._udp_listener_thread:
            self._udp_listener_thread = threading.Thread(target=udp_listener, daemon=True)
            self._udp_listener_thread.start()

    def _start_tcp_server(self):
        def tcp_img_server():
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('localhost', self.tcp_port))
            server_sock.listen(5)
            print(f"[IMG-Server] Hört auf TCP-Port {self.tcp_port}")
            while True:
                try:
                    conn, addr = server_sock.accept()
                    header = conn.recv(512).decode()
                    if header.startswith("IMG|"):
                        try:
                            _, sender_name, filename, size, _ = header.split("|")
                            size = int(size)
                        except Exception:
                            print("[FEHLER] Bild-Header fehlerhaft!")
                            conn.close()
                            continue
                        received = b""
                        while len(received) < size:
                            chunk = conn.recv(min(4096, size - len(received)))
                            if not chunk:
                                break
                            received += chunk
                        os.makedirs(self.bilder_ordner, exist_ok=True)
                        rand_id = random.randint(1000, 9999)
                        ext = os.path.splitext(filename)[1] or ".jpg"
                        out_path = os.path.join(self.bilder_ordner, f"empfangen_{sender_name}_{rand_id}{ext}")
                        with open(out_path, "wb") as imgf:
                            imgf.write(received)
                        print(f"\n[IMG empfangen von {sender_name}] Gespeichert als {out_path}")
                        print("> ", end="", flush=True)
                    conn.close()
                except Exception as e:
                    print(f"IMG-Server Fehler: {e}")
        if not self._tcp_server_thread:
            self._tcp_server_thread = threading.Thread(target=tcp_img_server, daemon=True)
            self._tcp_server_thread.start()

    def join_network(self):
        """
        Melde dich beim Broadcast-Server an und erhalte aktuelle Online-User-Liste.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        msg = f"JOIN|{self.username}|{self.udp_port}".encode()
        sock.sendto(msg, ('localhost', self.srv_port))
        try:
            data, _ = sock.recvfrom(2048)
            reply = data.decode()
            online = []
            if reply:
                for entry in reply.split(";"):
                    if not entry.strip():
                        continue
                    uname, uport = entry.split(":")
                    online.append((uname, int(uport)))
            return online
        except Exception as e:
            print(f"[Discovery-Fehler]: {e}")
            return []
        finally:
            sock.close()

    def get_online_users(self):
        """
        Hole aktuelle Liste aller Online-User vom Broadcast-Server.
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        try:
            sock.sendto(b"GET", ('localhost', self.srv_port))
            data, _ = sock.recvfrom(2048)
            reply = data.decode()
            online = []
            if reply:
                for entry in reply.split(";"):
                    if not entry.strip():
                        continue
                    uname, uport = entry.split(":")
                    online.append((uname, int(uport)))
            return online
        except Exception as e:
            print(f"[Discovery-Fehler]: {e}")
            return []
        finally:
            sock.close()

    def send_message(self, msg):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        online_list = self.get_online_users()
        for uname, uport in online_list:
            if uport != self.udp_port:
                sock.sendto(f"{self.username}: {msg}".encode(), ('localhost', uport))
        sock.close()

    def send_image(self, img_path):
        if not os.path.isfile(img_path):
            print("Datei nicht gefunden!")
            return
        filesize = os.path.getsize(img_path)
        filename = os.path.basename(img_path)
        with open(img_path, "rb") as f:
            img_data = f.read()
        header = f"IMG|{self.username}|{filename}|{filesize}|".encode().ljust(512, b" ")
        online_list = self.get_online_users()
        for uname, uport in online_list:
            if uport != self.udp_port:
                peer_tcp_port = uport + 10000
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.connect(('localhost', peer_tcp_port))
                    sock.sendall(header)
                    sock.sendall(img_data)
                    sock.close()
                except Exception as e:
                    print(f"[Fehler beim Senden an {uname}]: {e}")
        print("Bild gesendet.")
