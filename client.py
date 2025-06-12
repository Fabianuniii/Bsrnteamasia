import socket
import threading
import os
import random
import time

def join_broadcast_server(name, port, srv_port=15000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    msg = f"JOIN|{name}|{port}".encode()
    sock.sendto(msg, ('localhost', srv_port))
    try:
        data, _ = sock.recvfrom(2048)
        reply = data.decode()
        online = []
        if reply:
            for entry in reply.split(";"):
                uname, uport = entry.split(":")
                online.append((uname, int(uport)))
        return online
    except Exception as e:
        print(f"[Discovery error]: {e}")
        return []
    finally:
        sock.close()

def get_online_users(srv_port=15000):
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
        print(f"[Discovery error]: {e}")
        return []
    finally:
        sock.close()

def udp_listener(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', port))
    print(f"[Listener] Listening on port {port} (UDP for chat messages)")
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            print(f"\n[Message received]: {data.decode(errors='ignore')}")
            print("> ", end="", flush=True)
        except Exception as e:
            print(f"Listener error: {e}")
            break

def tcp_img_server(port, image_folder):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('localhost', port))
    server_sock.listen(5)
    print(f"[IMG-Server] Listening on port {port} (TCP for image transfer)")
    while True:
        try:
            conn, addr = server_sock.accept()
            header = conn.recv(512).decode()
            if header.startswith("IMG|"):
                try:
                    _, sender_name, filename, size, _ = header.split("|")
                    size = int(size)
                except Exception:
                    print("[ERROR] Invalid image header!")
                    conn.close()
                    continue
                
                received = b""
                start_time = time.time()
                while len(received) < size:
                    chunk = conn.recv(min(4096, size - len(received)))
                    if not chunk:
                        break
                    received += chunk
                    
                    # Progress bar
                    progress = len(received) / size * 100
                    elapsed = time.time() - start_time
                    speed = len(received) / (1024 * elapsed) if elapsed > 0 else 0
                    print(f"\rReceiving: {progress:.1f}% ({len(received)/1024:.1f} KB / {size/1024:.1f} KB) {speed:.1f} KB/s", end="")
                
                print()  # New line after progress
                
                os.makedirs(image_folder, exist_ok=True)
                rand_id = random.randint(1000, 9999)
                ext = os.path.splitext(filename)[1] or ".jpg"
                out_path = os.path.join(image_folder, f"received_{sender_name}_{rand_id}{ext}")
                with open(out_path, "wb") as imgf:
                    imgf.write(received)
                print(f"\n[Image received from {sender_name}] Saved as {out_path}")
                print("> ", end="", flush=True)
            conn.close()
        except Exception as e:
            print(f"IMG-Server error: {e}")

def send_msg_to_online(sender_name, msg, my_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    online_list = get_online_users()
    for uname, uport in online_list:
        if uport != my_port:
            sock.sendto(f"{sender_name}: {msg}".encode(), ('localhost', uport))
    sock.close()

def send_img_to_online_tcp(sender_name, img_path, my_port):
    if not os.path.isfile(img_path):
        print("File not found!")
        return
    
    filesize = os.path.getsize(img_path)
    filename = os.path.basename(img_path)
    
    with open(img_path, "rb") as f:
        img_data = f.read()
    
    header = f"IMG|{sender_name}|{filename}|{filesize}|".encode().ljust(512, b" ")

    online_list = get_online_users()
    for uname, uport in online_list:
        if uport != my_port:
            peer_tcp_port = uport + 10000
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect(('localhost', peer_tcp_port))
                
                # Send header
                sock.sendall(header)
                
                # Send image data with progress
                sent = 0
                start_time = time.time()
                with open(img_path, "rb") as f:
                    while sent < filesize:
                        chunk = f.read(4096)
                        sock.sendall(chunk)
                        sent += len(chunk)
                        
                        # Progress bar
                        progress = sent / filesize * 100
                        elapsed = time.time() - start_time
                        speed = sent / (1024 * elapsed) if elapsed > 0 else 0
                        print(f"\rSending to {uname}: {progress:.1f}% ({sent/1024:.1f} KB / {filesize/1024:.1f} KB) {speed:.1f} KB/s", end="")
                
                print()  # New line after progress
                sock.close()
            except Exception as e:
                print(f"[Error sending to {uname}]: {e}")
    print("Image sent to all online users.")