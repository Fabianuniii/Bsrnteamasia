import socket
import threading

class BroadcastServer:
    def __init__(self, port=4000):
        self.port = port
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
            print(f"[Broadcast-Server] Running on port {self.port}")
            
            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    msg = data.decode().strip()
                    
                    if msg.startswith("JOIN "):
                        # Format: JOIN <Handle> <Port>
                        parts = msg.split(" ")
                        if len(parts) >= 3:
                            handle = parts[1]
                            user_port = int(parts[2])
                            self.online_users[handle] = (addr[0], user_port)
                            # User ist wieder online, nicht mehr AFK
                            if handle in self.away_users:
                                self.away_users.remove(handle)
                            print(f"[INFO] {handle} (IP: {addr[0]}, Port {user_port}) is now online.")
                        
                    elif msg.startswith("LEAVE "):
                        # Format: LEAVE <Handle>
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            if handle in self.online_users:
                                del self.online_users[handle]
                            if handle in self.away_users:
                                self.away_users.remove(handle)
                            print(f"[INFO] {handle} has left the chat.")
                    
                    elif msg.startswith("AWAY "):
                        # Format: AWAY <Handle>
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            if handle in self.online_users:
                                self.away_users.add(handle)
                                print(f"[INFO] {handle} is now away (AFK).")
                    
                    elif msg.startswith("BACK "):
                        # Format: BACK <Handle>
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            if handle in self.away_users:
                                self.away_users.remove(handle)
                                print(f"[INFO] {handle} is back from being away.")
                        
                    elif msg == "WHO":
                        # Format: KNOWUSERS <Handle1> <IP1> <Port1>, <Handle2> <IP2> <Port2>
                        if self.online_users:
                            user_list = []
                            for handle, (ip, port) in self.online_users.items():
                                status = " [AFK]" if handle in self.away_users else ""
                                user_list.append(f"{handle} {ip} {port}{status}")
                            reply = "KNOWUSERS " + ", ".join(user_list) + "\n"
                        else:
                            reply = "KNOWUSERS\n"
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