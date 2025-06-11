import socket

def join_broadcast_server(name, port, srv_port=15000):
    """
    Melde dich beim Broadcast-Server an und erhalte aktuelle Online-User-Liste.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    msg = f"JOIN|{name}|{port}".encode()
    sock.sendto(msg, ('localhost', srv_port))
    try:
        data, _ = sock.recvfrom(2048)
        reply = data.decode()
        # Liste: "Fabian:12345;Can:12347;Jin:12348"
        online = []
        if reply:
            for entry in reply.split(";"):
                uname, uport = entry.split(":")
                online.append((uname, int(uport)))
        return online
    except Exception as e:
        print(f"[Discovery-Fehler]: {e}")
        return []
    finally:
        sock.close()

def get_online_users(srv_port=15000):
    """
    Hole aktuelle Liste aller Online-User vom Broadcast-Server.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        sock.sendto(b"GET", ('localhost', srv_port))
        data, _ = sock.recvfrom(2048)
        reply = data.decode()
        online = []
        if reply:
            for entry in reply.split(";"):
                uname, uport = entry.split(":")
                online.append((uname, int(uport)))
        return online
    except Exception as e:
        print(f"[Discovery-Fehler]: {e}")
        return []
    finally:
        sock.close()
