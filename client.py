import socket
import threading
import toml
import sys
import time
import os

class Client:
    def __init__(self, name, host_ip, udp_port, ipc_port, image_ipc_port, broadcast_ip, whois_port):
        self.name = name
        self.host_ip = host_ip
        self.udp_port = udp_port
        self.ipc_port = ipc_port
        self.image_ipc_port = image_ipc_port
        self.broadcast_ip = broadcast_ip
        self.whois_port = whois_port

        self.known_users = {}  # handle -> (ip, port)
        self.away_message = None
        self.autoreply = False
        self.bilder_ordner = "bilder/"
        os.makedirs(self.bilder_ordner, exist_ok=True)

        self.cli_sockets = []

        # UDP-Socket für Netzwerkkommunikation (SLCP)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("0.0.0.0", self.udp_port))

        self.start_udp_listener()
        self.start_ipc_server()
        self.start_tcp_server()

        # Direkt nach Start: JOIN und WHO senden (optional Delay für Robustheit)
        time.sleep(0.5)
        self.join_network()
        time.sleep(0.5)
        self.get_online_users()  # <-- baut die Peer-Liste sofort beim Start auf

    def start_udp_listener(self):
        threading.Thread(target=self._udp_listener_thread, daemon=True).start()

    def _udp_listener_thread(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(4096)
                msg = data.decode().strip()
                self.handle_udp_message(msg, addr)
            except Exception as e:
                print(f"UDP Listener error: {e}")

    def handle_udp_message(self, msg, addr):
        parts = msg.split(" ", 2)
        if parts[0] == "JOIN" and len(parts) == 3:
            handle, port = parts[1], int(parts[2])
            if handle != self.name:
                self.known_users[handle] = (addr[0], port)
                self.send_to_cli(f"{handle} joined from {addr[0]}:{port}")
        elif parts[0] == "AWAY" and len(parts) >= 2:
            handle = parts[1]
            self.send_to_cli(f"{handle} is away.")
        elif parts[0] == "BACK" and len(parts) >= 2:
            handle = parts[1]
            self.send_to_cli(f"{handle} is back.")
        elif parts[0] == "MSG" and len(parts) == 3:
            sender, text = parts[1], parts[2]
            self.send_to_cli(f"[{sender}]: {text}")
            if self.away_message and self.autoreply:
                self.send_message(sender, f"(Autoreply): {self.away_message}")
        elif parts[0] == "WHO":
            self.join_network()
        elif parts[0] == "KNOWUSERS" and len(parts) == 2:
            self._parse_knowusers(parts[1])

    def _parse_knowusers(self, users_str):
        users = users_str.split(",")
        self.known_users = {}
        new_users = []
        for user in users:
            fields = user.strip().split(" ")
            if len(fields) >= 3:
                handle, ip, port = fields[0], fields[1], int(fields[2])
                if handle != self.name:
                    self.known_users[handle] = (ip, port)
                    new_users.append(f"{handle}@{ip}:{port}")
        if new_users:
            self.send_to_cli("Known users updated: " + ", ".join(new_users))

    def get_online_users(self):
        # Holt die aktuelle Userliste synchron wie im alten Code!
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.settimeout(2)
        try:
            s.sendto(b"WHO\n", (self.broadcast_ip, self.whois_port))
            data, _ = s.recvfrom(2048)
            reply = data.decode().strip()
            if reply.startswith("KNOWUSERS"):
                users_str = reply[len("KNOWUSERS"):].strip()
                self._parse_knowusers(users_str)
        except Exception as e:
            self.send_to_cli(f"[Discovery-Fehler]: {e}")
        finally:
            s.close()

    def send_to_cli(self, text):
        for conn in self.cli_sockets[:]:
            try:
                conn.sendall((text + "\n").encode())
            except Exception:
                self.cli_sockets.remove(conn)

    def start_ipc_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host_ip, self.ipc_port))
        server.listen()
        threading.Thread(target=self._ipc_accept_loop, args=(server,), daemon=True).start()

    def _ipc_accept_loop(self, server):
        while True:
            conn, _ = server.accept()
            self.cli_sockets.append(conn)
            threading.Thread(target=self._ipc_handler, args=(conn,), daemon=True).start()

    def _ipc_handler(self, conn):
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                msg = data.decode().strip()
                self.handle_cli_command(msg)
            except Exception:
                break
        if conn in self.cli_sockets:
            self.cli_sockets.remove(conn)
        conn.close()

    def handle_cli_command(self, msg):
        parts = msg.split(" ", 2)
        if parts[0] == "JOIN":
            self.join_network()
            time.sleep(0.2)
            self.get_online_users()
        elif parts[0] == "MSG" and len(parts) == 3:
            self.get_online_users()   # <-- hier Peer-Liste immer vor MSG frisch holen!
            self.send_message(parts[1], parts[2])
        elif parts[0] == "AWAY":
            self.away_message = parts[1] if len(parts) == 2 else "I'm away."
            self.autoreply = True
            self.broadcast(f"AWAY {self.name}")
        elif parts[0] == "BACK":
            self.away_message = None
            self.autoreply = False
            self.broadcast(f"BACK {self.name}")
        elif parts[0] == "IMG" and len(parts) == 3:
            self.get_online_users()   # <-- vor Senden von Bildern auch Peer-Liste holen!
            self.send_image(parts[1], parts[2])
        elif parts[0] == "WHO":
            self.get_online_users()
        elif parts[0] == "LEAVE":
            self.broadcast(f"LEAVE {self.name}")

    def join_network(self):
        self.broadcast(f"JOIN {self.name} {self.udp_port}")

    def send_message(self, target, text):
        if target == self.name:
            self.send_to_cli("❌ Du kannst dir selbst keine Nachricht senden.")
            return
        if target in self.known_users:
            ip, port = self.known_users[target]
            self.send_to_cli(f"➡️  Versende Nachricht an {target} ({ip}:{port})")
            msg = f"MSG {self.name} {text}"
            self.sock.sendto(msg.encode(), (ip, port))
        else:
            self.send_to_cli(f"❌ Unbekannter Nutzer: {target}")

    def broadcast(self, message):
        self.sock.sendto(message.encode(), (self.broadcast_ip, self.whois_port))

    def _get_image_port_for(self, handle):
        # Lies die config nochmal aus, alternativ speicher die Ports beim Start
        config = load_config()
        for user in config["users"]:
            if user["name"] == handle or user["handle"] == handle:
                return user.get("image_ipc_port", user["ipc_port"] + 1)
        return None  # Fehlerfall

    def send_image(self, target, path):
        if target == self.name:
            self.send_to_cli("❌ Du kannst dir selbst kein Bild senden.")
            return
        if target not in self.known_users:
            self.send_to_cli(f"❌ Unbekannter Benutzer: {target}")
            return
        try:
            with open(path, "rb") as f:
                data = f.read()
            ip, _ = self.known_users[target]
            image_ipc_port = self._get_image_port_for(target)
            if image_ipc_port is None:
                self.send_to_cli(f"❌ Konnte Port von {target} nicht ermitteln.")
                return
            self.send_to_cli(f"➡️  Versende Bild an {target} ({ip}:{image_ipc_port})")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((ip, image_ipc_port))
            header = f"IMG {self.name} {os.path.basename(path)} {len(data)} ".encode()
            sock.sendall(header + data)
            sock.close()
        except Exception as e:
            self.send_to_cli(f"❌ Bild konnte nicht gesendet werden: {e}")

    def start_tcp_server(self):
        def handler():
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host_ip, self.image_ipc_port))
            server.listen()
            while True:
                conn, _ = server.accept()
                threading.Thread(target=self._handle_incoming_image, args=(conn,), daemon=True).start()
        threading.Thread(target=handler, daemon=True).start()

    def _handle_incoming_image(self, conn):
        try:
            # Header einlesen (bis 4 Spaces = nach Dateigröße)
            header = b""
            space_count = 0
            while space_count < 4:
                byte = conn.recv(1)
                if not byte:
                    break
                header += byte
                if byte == b' ':
                    space_count += 1
            parts = header.split(b" ", 4)
            if len(parts) >= 5 and parts[0] == b"IMG":
                sender = parts[1].decode()
                filename = parts[2].decode()
                filesize = int(parts[3].decode())
                rest = parts[4]  # Anfang der Bilddaten (kann schon was drin sein!)
                image_data = rest
                # Jetzt die restlichen Bytes einlesen
                while len(image_data) < filesize:
                    chunk = conn.recv(min(4096, filesize - len(image_data)))
                    if not chunk:
                        break
                    image_data += chunk
                full_path = os.path.join(self.bilder_ordner, "empfangen_" + filename)
                with open(full_path, "wb") as f:
                    f.write(image_data)
                self.send_to_cli(f"[Bild] von {sender} gespeichert als {full_path}")
            else:
                self.send_to_cli(f"Fehler: Header konnte nicht gelesen werden!")
        except Exception as e:
            self.send_to_cli(f"Fehler beim Empfangen eines Bildes: {e}")
        finally:
            conn.close()

def load_config():
    return toml.load("config.toml")

def find_client_config(config, name):
    for client in config["users"]:
        if client["name"] == name:
            return client
    raise Exception(f"Keine Konfiguration für {name} gefunden")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <Name>")
        sys.exit(1)

    name = sys.argv[1]
    config = load_config()
    conf = find_client_config(config, name)

    Client(
        name=name,
        host_ip=conf["host_ip"],
        udp_port=conf["port"],
        ipc_port=conf["ipc_port"],
        image_ipc_port=conf.get("image_ipc_port", conf["ipc_port"] + 1),
        broadcast_ip=config["network"]["broadcast_ip"],
        whois_port=config["network"]["whoisport"]
    )

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
