import socket
import threading

class BroadcastServer:
    def __init__(self, port=4000):
        self.port = port
        self.online_users = {}
        self.running = False
        self.sock = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            self.sock.bind(('0.0.0.0', self.port))
            self.running = True
            print(f"[Broadcast-Server] Running on port {self.port}")
            
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    msg = data.decode()
                    
                    if msg.startswith("JOIN|"):
                        _, name, user_port = msg.split("|")
                        self.online_users[name] = int(user_port)
                        print(f"[INFO] {name} (Port {user_port}) is now online.")
                        reply = ";".join([f"{n}:{p}" for n, p in self.online_users.items()])
                        self.sock.sendto(reply.encode(), addr)
                        
                    elif msg == "GET":
                        reply = ";".join([f"{n}:{p}" for n, p in self.online_users.items()])
                        self.sock.sendto(reply.encode(), addr)
                        
                except Exception as e:
                    if self.running:
                        print(f"[Broadcast-Server Error]: {e}")
        except OSError as e:
            print(f"[Error] Could not start server: {e}")

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