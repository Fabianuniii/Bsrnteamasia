import socket
import threading
import toml
import sys
import time
import os

class Client:
    def __init__(self, idx, config):
        self.has_joined = False
        self.config = config
        self.idx = idx
        user = config["users"][idx-1]
        self.name = user["name"]
        self.handle = user.get("handle", self.name)
        self.host_ip = user["host_ip"]
        self.udp_port = user["port"]
        self.ipc_port = user["ipc_port"]
        self.image_ipc_port = user.get("image_ipc_port", user["ipc_port"] + 1)
        self.broadcast_ip = config["network"]["broadcast_ip"]
        self.whois_port = config["network"]["whoisport"]

        self.known_users = {}
        self.away_message = None
        self.autoreply = False
        self.bilder_ordner = config["storage"].get("imagepath", "bilder/")
        os.makedirs(self.bilder_ordner, exist_ok=True)

        self.cli_sockets = []

        # *** Nur der IPC-Server läuft von Anfang an ***
        self.start_ipc_server()

        # *** Die Netzwerk-Sockets werden erst bei JOIN gestartet ***
        self.sock = None

    def periodic_who_sync(self):
        while True:
            time.sleep(3)
            if self.has_joined:
                self.get_online_users()

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
        if msg.startswith("KNOWUSERS"):
            users_str = msg[len("KNOWUSERS"):].strip()
            self._parse_knowusers(users_str)
            return
        parts = msg.split(" ", 2)
        if parts[0] == "JOIN" and len(parts) == 3:
            handle, port = parts[1], int(parts[2])
            if handle != self.handle:
                self.known_users[handle] = (addr[0], port)
                self.send_to_cli(f"{handle} ist beigetreten von: {addr[0]}:{port}")
                self.get_online_users()
        elif parts[0] == "AWAY" and len(parts) >= 2:
            handle = parts[1]
            self.send_to_cli(f"{handle} ist weg.")
        elif parts[0] == "BACK" and len(parts) >= 2:
            handle = parts[1]
            self.send_to_cli(f"{handle} ist zurück.")
        elif parts[0] == "LEAVE" and len(parts) >= 2:
            self.get_online_users()
        elif parts[0] == "MSG" and len(parts) == 3:
            sender, text = parts[1], parts[2]
            self.send_to_cli(f"[{sender}]: {text}")
            if self.away_message and self.autoreply:
                self.send_message(sender, f"(Autoreply): {self.away_message}")
        elif parts[0] == "WHO":
            if self.has_joined:
                self.join_network()

    def _parse_knowusers(self, users_str):
        users = users_str.split(",")
        self.known_users = {}
        for user in users:
            fields = user.strip().split(" ")
            if len(fields) >= 3:
                handle, ip, port = fields[0], fields[1], int(fields[2])
                if handle != self.handle:
                    self.known_users[handle] = (ip, port)

    def get_online_users(self):
        if self.sock:  # Nur senden, wenn Socket existiert
            self.sock.sendto(b"WHO\n", (self.broadcast_ip, self.whois_port))

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
        cmd = parts[0].upper()
        if cmd == "JOIN":
            self.has_joined = True

            # *** Netzwerk erst ab hier ***
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            self.sock.bind(("0.0.0.0", self.udp_port))

            self.start_udp_listener()
            self.start_tcp_server()
            threading.Thread(target=self.periodic_who_sync, daemon=True).start()
            self.join_network()
            time.sleep(0.2)
            self.get_online_users()
        elif cmd == "MSG" and len(parts) == 3:
            self.get_online_users()
            self.send_message(parts[1], parts[2])
        elif cmd == "AWAY":
            self.away_message = parts[1] if len(parts) == 2 else "Ich bin gerade nicht da."
            self.autoreply = True
            self.broadcast(f"AWAY {self.handle}")
        elif cmd == "BACK":
            self.away_message = None
            self.autoreply = False
            self.broadcast(f"BACK {self.handle}")
        elif cmd == "IMG" and len(parts) == 3:
            self.get_online_users()
            self.send_image(parts[1], parts[2])
        elif cmd == "WHO":
            self.get_online_users()
            time.sleep(0.2)
            if self.known_users:
                userlist = ", ".join([f"{h} {ip} {port}" for h, (ip, port) in self.known_users.items()])
                self.send_to_cli("KNOWUSERS " + userlist)
            else:
                self.send_to_cli("KNOWUSERS")
        elif cmd == "LEAVE":
            self.broadcast(f"LEAVE {self.handle}")
            time.sleep(0.2)
            self.get_online_users()
        elif cmd == "HANDLE":
            text = msg[len("HANDLE"):].strip()
            if text:
                old_handle = self.handle
                self.handle = text
                self.send_to_cli(f"Handle geändert: {old_handle} ➔ {self.handle}")
                self.broadcast(f"JOIN {self.handle} {self.udp_port}")
                time.sleep(0.2)
                self.get_online_users()
            else:
                self.send_to_cli("❌ Bitte gib einen gültigen Handle ein.")
        elif cmd == "AUTOREPLY":
            text = msg[len("AUTOREPLY"):].strip()
            if text:
                self.away_message = text
                self.send_to_cli(f"Autoreply-Text geändert: {self.away_message}")
            else:
                self.away_message = "Ich bin gerade nicht da."
                self.send_to_cli("Autoreply-Text zurückgesetzt.")

    def join_network(self):
        self.broadcast(f"JOIN {self.handle} {self.udp_port}")

    def send_message(self, target, text):
        if target == self.handle:
            self.send_to_cli("❌ Du kannst dir selbst keine Nachricht senden.")
            return
        if target in self.known_users:
            ip, port = self.known_users[target]
            self.send_to_cli(f"➡️  Versende Nachricht an {target} ({ip}:{port})")
            msg = f"MSG {self.handle} {text}"
            self.sock.sendto(msg.encode(), (ip, port))
        else:
            self.send_to_cli(f"❌ Unbekannter Nutzer: {target}")

    def broadcast(self, message):
        if self.sock:
            self.sock.sendto(message.encode(), (self.broadcast_ip, self.whois_port))

    def _get_image_port_for(self, handle):
        for user in self.config["users"]:
            if user.get("handle", user["name"]) == handle:
                return user.get("image_ipc_port", user["ipc_port"] + 1)
        return None

    def send_image(self, target, path):
        if target == self.handle:
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
            header = f"IMG {self.handle} {os.path.basename(path)} {len(data)} ".encode()
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
                rest = parts[4]
                image_data = rest
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

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 client.py <Index>")
        sys.exit(1)
    try:
        idx = int(sys.argv[1])
    except ValueError:
        print("Bitte eine gültige Usernummer als Argument übergeben!")
        sys.exit(1)

    config = load_config()
    if not (1 <= idx <= len(config["users"])):
        print("Ungültiger Index. Siehe config.toml.")
        sys.exit(1)

    Client(idx, config)
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()