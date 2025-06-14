import socket
import threading
import os
import random
import sys
from time import sleep
import time

class ClientNetwork:
    def __init__(self, username, udp_port, tcp_port, srv_port=4000, bilder_ordner="./bilder/"):
        self.username = username
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.srv_port = srv_port
        self.bilder_ordner = bilder_ordner
        self.known_users = {}  # {handle: (ip, port)}
        self._udp_listener_thread = None
        self._tcp_server_thread = None
        self._listening = False
        self._start_udp_listener()
        self._start_tcp_server()

    def _start_udp_listener(self):
        def udp_listener():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('0.0.0.0', self.udp_port))
            print(f"[Listener] Hört auf UDP-Port {self.udp_port}")
            
            while True:
                try:
                    data, addr = sock.recvfrom(2048)
                    msg = data.decode(errors='ignore').strip()
                    
                    if msg.startswith("MSG "):
                        parts = msg.split(" ", 2)
                        if len(parts) >= 3:
                            sender = parts[1]
                            text = parts[2]
                            if text.startswith('"') and text.endswith('"'):
                                text = text[1:-1]
                            print(f"\n[Nachricht von {sender}]: {text}")
                            print("> ", end="", flush=True)
                    
                    elif msg.startswith("IMG "):
                        parts = msg.split(" ")
                        if len(parts) >= 3:
                            sender = parts[1]
                            size = int(parts[2])
                            print(f"\n[Bild wird empfangen von {sender}] Größe: {size} Bytes")
                            print("> ", end="", flush=True)
                    
                    elif msg.startswith("JOIN "):
                        parts = msg.split(" ")
                        if len(parts) >= 3:
                            handle = parts[1]
                            port = int(parts[2])
                            print(f"\n[INFO] {handle} ist dem Chat beigetreten")
                            print("> ", end="", flush=True)
                    
                    elif msg.startswith("LEAVE "):
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            print(f"\n[INFO] {handle} hat den Chat verlassen")
                            print("> ", end="", flush=True)
                    
                    else:
                        print(f"\n[Unbekannte Nachricht]: {msg}")
                        print("> ", end="", flush=True)

                except Exception as e:
                    print(f"\n[Listener-Fehler]: {e}")
                    sleep(1)  # Bei Fehlern kurz warten

        if not self._udp_listener_thread:
            self._udp_listener_thread = threading.Thread(target=udp_listener, daemon=True)
            self._udp_listener_thread.start()

    def _start_tcp_server(self):
        def tcp_img_server():
            server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind(('0.0.0.0', self.tcp_port))
            server_sock.listen(5)
            print(f"[IMG-Server] Hört auf TCP-Port {self.tcp_port}")
            
            while True:
                conn, addr = None, None
                try:
                    conn, addr = server_sock.accept()
                    conn.settimeout(30)  # 30 Sekunden Timeout
                    
                    # Empfange alle Daten
                    img_data = b''
                    while True:
                        chunk = conn.recv(4096)
                        if not chunk:
                            break
                        img_data += chunk
                    
                    if img_data:
                        os.makedirs(self.bilder_ordner, exist_ok=True)
                        filename = f"empfangen_{self.username}_{int(time.time())}.jpg"
                        out_path = os.path.join(self.bilder_ordner, filename)
                        
                        with open(out_path, "wb") as imgf:
                            imgf.write(img_data)
                        
                        print(f"\n[Bild empfangen] Gespeichert als {out_path}")
                        print("> ", end="", flush=True)

                except socket.timeout:
                    print(f"\n[Timeout] Bildübertragung zu langsam")
                except Exception as e:
                    print(f"\n[IMG-Server Fehler]: {e}")
                finally:
                    if conn:
                        try:
                            conn.close()
                        except:
                            pass

        if not self._tcp_server_thread:
            self._tcp_server_thread = threading.Thread(target=tcp_img_server, daemon=True)
            self._tcp_server_thread.start()

    def join_network(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        # JOIN Nachricht senden
        join_msg = f"JOIN {self.username} {self.udp_port}\n"
        sock.sendto(join_msg.encode(), ('255.255.255.255', self.srv_port))
        
        # WHO Nachricht senden
        sock.sendto(b"WHO\n", ('255.255.255.255', self.srv_port))
        sock.settimeout(2)
        
        try:
            data, _ = sock.recvfrom(2048)
            reply = data.decode().strip()
            if reply.startswith("KNOWUSERS"):
                self._parse_knowusers(reply)
        except socket.timeout:
            print("[Info] Keine Antwort vom Server erhalten")
        except Exception as e:
            print(f"[Discovery-Fehler]: {e}")
        finally:
            sock.close()
        
        return list(self.known_users.items())

    def _parse_knowusers(self, reply):
        self.known_users.clear()
        if reply == "KNOWUSERS":
            return
            
        user_data = reply[10:].strip()
        if not user_data:
            return
            
        for entry in user_data.split(", "):
            entry = entry.strip()
            if entry:
                parts = entry.split(" ")
                if len(parts) >= 3:
                    handle = parts[0]
                    ip = parts[1]
                    port = int(parts[2])
                    self.known_users[handle] = (ip, port)

    def get_online_users(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.settimeout(2)
        
        try:
            sock.sendto(b"WHO\n", ('255.255.255.255', self.srv_port))
            data, _ = sock.recvfrom(2048)
            reply = data.decode().strip()
            if reply.startswith("KNOWUSERS"):
                self._parse_knowusers(reply)
        except socket.timeout:
            print("[Info] Keine Antwort vom Server erhalten")
        except Exception as e:
            print(f"[Discovery-Fehler]: {e}")
        finally:
            sock.close()
        
        return list(self.known_users.items())

    def send_message(self, target_handle, msg):
        if target_handle not in self.known_users:
            print(f"User {target_handle} nicht bekannt. Verwende WHO um User-Liste zu aktualisieren.")
            return
        
        ip, port = self.known_users[target_handle]
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            if " " in msg:
                slcp_msg = f'MSG {self.username} "{msg}"\n'
            else:
                slcp_msg = f'MSG {self.username} {msg}\n'
            
            sock.sendto(slcp_msg.encode(), (ip, port))
            print(f"Nachricht an {target_handle} gesendet.")
        except Exception as e:
            print(f"[Fehler beim Senden]: {e}")
        finally:
            sock.close()

    def send_image(self, target_handle, img_path):
        if not os.path.isfile(img_path):
            print("Datei nicht gefunden!")
            return
            
        if target_handle not in self.known_users:
            print(f"User {target_handle} nicht bekannt. Verwende WHO um User-Liste zu aktualisieren.")
            return
        
        filesize = os.path.getsize(img_path)
        ip, port = self.known_users[target_handle]
        
        # 1. IMG-Nachricht senden
        sock_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        img_msg = f"IMG {self.username} {filesize}\n"
        sock_udp.sendto(img_msg.encode(), (ip, port))
        sock_udp.close()
        
        # 2. Bild senden
        sock_tcp = None
        try:
            with open(img_path, "rb") as f:
                img_data = f.read()
            
            tcp_port = port + 10000
            sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock_tcp.settimeout(15)
            sock_tcp.connect((ip, tcp_port))
            sock_tcp.sendall(img_data)
            print(f"Bild an {target_handle} gesendet.")
        except socket.timeout:
            print("[Timeout] Verbindung zu langsam")
        except ConnectionResetError:
            print("[Warnung] Verbindung abgebrochen - Bild möglicherweise trotzdem angekommen")
        except Exception as e:
            print(f"[Fehler beim Bildversand]: {e}")
        finally:
            if sock_tcp:
                try:
                    sock_tcp.close()
                except:
                    pass

    def leave_network(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        leave_msg = f"LEAVE {self.username}\n"
        
        try:
            # An Server senden
            sock.sendto(leave_msg.encode(), ('255.255.255.255', self.srv_port))
            
            # An alle bekannten Clients senden
            for handle, (ip, port) in self.known_users.items():
                try:
                    sock.sendto(leave_msg.encode(), (ip, port))
                except:
                    continue
                    
        except Exception as e:
            print(f"[Fehler beim Verlassen]: {e}")
        finally:
            sock.close()