import toml
import socket
import threading

# Lese die Broadcast-IP (und Port) aus config.toml
try:
    config = toml.load("config.toml")
    BROADCAST_IP = config["network"]["broadcast_ip"]
    WHOIS_PORT = config["network"]["whoisport"]
except Exception:
    BROADCAST_IP = "192.168.2.255"  # Fallback für LAN
    WHOIS_PORT = 4000

class BroadcastServer:
    def __init__(self, port=WHOIS_PORT, broadcast_ip=BROADCAST_IP):
        self.port = port
        self.broadcast_ip = broadcast_ip
        self.online_users = {}  # {handle: (ip, port)}
        self.away_users = set()  # Set der AFK User
        self.running = False
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            self.sock.bind(('0.0.0.0', self.port))
            self.running = True
            print(f"[Broadcast-Server] läuft auf dem Port: {self.port}")

            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    msg = data.decode().strip()
                    

                    if msg.startswith("JOIN "):
                        parts = msg.split(" ")
                        if len(parts) >= 3:
                            handle = parts[1]
                            user_port = int(parts[2])
                            self.online_users[handle] = (addr[0], user_port)
                            if handle in self.away_users:
                                self.away_users.remove(handle)
                            print(f"[INFO] {handle} (IP: {addr[0]}, Port {user_port}) ist jetzt online.")

                    elif msg.startswith("LEAVE "):
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            self.online_users.pop(handle, None)
                            self.away_users.discard(handle)
                            print(f"[INFO] {handle} hat den Chat verlassen.")

                    elif msg.startswith("AWAY "):
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            if handle in self.online_users:
                                self.away_users.add(handle)
                                print(f"[INFO] {handle} ist nun weg (AFK).")

                    elif msg.startswith("BACK "):
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            self.away_users.discard(handle)
                            print(f"[INFO] {handle} ist wieder zurück.")

                    elif msg.startswith("WHO"):
                        if self.online_users:
                            user_list = []
                            for handle, (ip, port) in self.online_users.items():
                                status = " [AFK]" if handle in self.away_users else ""
                                user_list.append(f"{handle} {ip} {port}{status}")
                            reply = "KNOWUSERS " + ", ".join(user_list) + "\n"
                        else:
                            reply = "KNOWUSERS\n"

                        # **NEU: Antworte IMMER direkt an den Absender-Port**
                        self.sock.sendto(reply.encode(), addr)

                except Exception as e:
                    if self.running:
                        print(f"[Broadcast-Server Error]: {e}")
        except OSError as e:
            print(f"[Error] Server kann nicht gestartet werden: {e}")

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()

def run_broadcast_server():
    server = BroadcastServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    run_broadcast_server()