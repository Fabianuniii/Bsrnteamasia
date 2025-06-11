import socket

online_users = {}  # name -> port

def run_broadcast_server(port=15000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', port))
    print(f"[Broadcast-Server] Läuft auf Port {port}")
    while True:
        data, addr = sock.recvfrom(1024)
        msg = data.decode()
        if msg.startswith("JOIN|"):
            # JOIN|Name|Port
            _, name, user_port = msg.split("|")
            online_users[name] = int(user_port)
            print(f"[INFO] {name} (Port {user_port}) ist online.")
            # Sende Liste aller Online-User zurück
            reply = ";".join([f"{n}:{p}" for n, p in online_users.items()])
            sock.sendto(reply.encode(), addr)
        elif msg == "GET":
            reply = ";".join([f"{n}:{p}" for n, p in online_users.items()])
            sock.sendto(reply.encode(), addr)

if __name__ == "__main__":
    run_broadcast_server()
