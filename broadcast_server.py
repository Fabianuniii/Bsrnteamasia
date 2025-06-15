import socket

class BroadcastServer:
    def __init__(self, port=4000):
        self.port = port
        self.online_users = {}  # {handle: (ip, port)}
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
                    msg = data.decode(errors='ignore').strip()
                    # JOIN <handle> <port>
                    if msg.startswith("JOIN"):
                        parts = msg.split(" ")
                        if len(parts) >= 3:
                            handle = parts[1]
                            user_port = int(parts[2])
                            self.online_users[handle] = (addr[0], user_port)
                            print(f"[INFO] {handle} (IP: {addr[0]}, Port: {user_port}) is now online.")
                            # Send updated list
                            reply = ";".join([f"{h}:{p[1]}" for h, p in self.online_users.items()])
                            self.sock.sendto(reply.encode(), addr)
                    # GET (Userlist abfragen)
                    elif msg == "GET":
                        reply = ";".join([f"{h}:{p[1]}" for h, p in self.online_users.items()])
                        self.sock.sendto(reply.encode(), addr)
                    # LEAVE <handle>
                    elif msg.startswith("LEAVE"):
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            if handle in self.online_users:
                                del self.online_users[handle]
                                print(f"[INFO] {handle} is now offline.")
                except Exception as e:
                    print(f"[Broadcast-Server Error]: {e}")
        except Exception as e:
            print(f"[Broadcast-Server Startup Error]: {e}")

if __name__ == "__main__":
    server = BroadcastServer(port=4000)
    server.start()
