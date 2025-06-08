import socket
import threading
import json
import toml

config = toml.load("config.toml")
PORT = config["network"]["port"]
BROADCAST_IP = config["network"]["broadcast_ip"]
BUFFER_SIZE = config["network"]["buffer_size"]

class Network:
    def __init__(self, username):
        self.username = username
        self.running = True

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(("", PORT))

        self.thread = threading.Thread(target=self.receive_loop, daemon=True)
        self.thread.start()

    def receive_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
                msg = json.loads(data.decode())
                sender = msg.get("username", "Unbekannt")
                text = msg.get("text", "")
                print(f"[{sender}] {text}")
            except Exception as e:
                print(f"[Fehler] Empfang: {e}")

    def send(self, text):
        message = {
            "type": "chat",
            "username": self.username,
            "text": text
        }
        try:
            self.sock.sendto(json.dumps(message).encode(), (BROADCAST_IP, PORT))
        except Exception as e:
            print(f"[Fehler] Senden: {e}")

    def stop(self):
        self.running = False
        self.sock.close()
