import sys
import threading
import socket
import toml
import os
import random

from client import join_broadcast_server, get_online_users

with open("config.toml", "r") as f:
    config = toml.load(f)

current_user = None
listener_thread = None
tcp_server_thread = None

def udp_listener(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('localhost', port))
    print(f"[Listener] Hört auf Port {port} (UDP für Chatnachrichten)")
    while True:
        try:
            data, addr = sock.recvfrom(2048)
            print(f"\n[Nachricht empfangen]: {data.decode(errors='ignore')}")
            print("> ", end="", flush=True)
        except Exception as e:
            print(f"Listener-Fehler: {e}")
            break

def tcp_img_server(port, bilder_ordner):
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('localhost', port))
    server_sock.listen(5)
    print(f"[IMG-Server] Hört auf Port {port} (TCP für Bildübertragung)")
    while True:
        try:
            conn, addr = server_sock.accept()
            header = conn.recv(512).decode()
            if header.startswith("IMG|"):
                try:
                    _, sender_name, filename, size, _ = header.split("|")
                    size = int(size)
                except Exception:
                    print("[FEHLER] Bild-Header fehlerhaft!")
                    conn.close()
                    continue
                received = b""
                while len(received) < size:
                    chunk = conn.recv(min(4096, size - len(received)))
                    if not chunk:
                        break
                    received += chunk
                os.makedirs(bilder_ordner, exist_ok=True)
                rand_id = random.randint(1000, 9999)
                ext = os.path.splitext(filename)[1] or ".jpg"
                out_path = os.path.join(bilder_ordner, f"empfangen_{sender_name}_{rand_id}{ext}")
                with open(out_path, "wb") as imgf:
                    imgf.write(received)
                print(f"\n[IMG empfangen von {sender_name}] Gespeichert als {out_path}")
                print("> ", end="", flush=True)
            conn.close()
        except Exception as e:
            print(f"IMG-Server Fehler: {e}")

def send_msg_to_online(sender_name, msg, my_port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    online_list = get_online_users()
    for uname, uport in online_list:
        if uport != my_port:
            sock.sendto(f"{sender_name}: {msg}".encode(), ('localhost', uport))
    sock.close()

def send_img_to_online_tcp(sender_name, img_path, my_port):
    if not os.path.isfile(img_path):
        print("Datei nicht gefunden!")
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
                sock.sendall(header)
                sock.sendall(img_data)
                sock.close()
            except Exception as e:
                print(f"[Fehler beim Senden an {uname}]: {e}")
    print("Bild gesendet.")

def cli_help():
    print("Verfügbare Kommandos:")
    print(" JOIN           Dem Netzwerk beitreten")
    print(" MSG [Text]     Sendet Nachricht")
    print(" IMG [Pfad]     Sendet Bild an alle (per TCP)")
    print(" LEAVE          Das Netzwerk verlassen")
    print(" WHO            Nutzerliste ausgeben (nur aktuell Online)")

def process_command(command):
    global current_user, listener_thread, tcp_server_thread
    if command.startswith("JOIN"):
        check = 0
        while check == 0:
            print("Tippe ACCOUNTS ein um eine Liste aller verfügbaren Nutzernamen zu bekommen.")
            username_input = input("Welchen User Account willst du benutzen: ")
            found = False
            if username_input == "ACCOUNTS":
                for user in config["users"]:
                    print(user["name"])
            for user in config["users"]:
                if user["name"].lower() == username_input.lower():
                    current_user = user
                    bilder_ordner = config.get("bild_pfad", "./bilder/")
                    if listener_thread is None:
                        listener_thread = threading.Thread(target=udp_listener, args=(user["port"],), daemon=True)
                        listener_thread.start()
                    if tcp_server_thread is None:
                        tcp_port = user["port"] + 10000
                        tcp_server_thread = threading.Thread(target=tcp_img_server, args=(tcp_port, bilder_ordner), daemon=True)
                        tcp_server_thread.start()
                    # Discovery: beim Broadcast-Server anmelden
                    online_list = join_broadcast_server(current_user["name"], current_user["port"])
                    print("Aktuelle Online-User:", [n for n, p in online_list])
                    print(f"Erfolgreich eingeloggt als {user['name']} (UDP-Port: {user['port']}, IMG-TCP-Port: {user['port']+10000})")
                    found = True
                    check = 1
                    break
            if not found:
                print("User nicht gefunden. Versuche es erneut mit einem gültigen Namen!")
    elif command.startswith("MSG"):
        if current_user is None:
            print("Bitte erst JOIN benutzen!")
            return
        message = command[4:].strip()
        if not message:
            print("Bitte gib eine Nachricht nach MSG ein, z.B. MSG Hallo Welt!")
            return
        send_msg_to_online(current_user["name"], message, current_user["port"])
    elif command.startswith("IMG"):
        if current_user is None:
            print("Bitte erst JOIN benutzen!")
            return
        img_path = command[4:].strip()
        if not img_path:
            img_path = input("Pfad zur Bilddatei: ").strip()
        send_img_to_online_tcp(current_user["name"], img_path, current_user["port"])
    elif command.startswith("WHO"):
        online_list = get_online_users()
        print("Online-USER:")
        for uname, uport in online_list:
            print(f"- {uname} (Port {uport})")
    elif command.startswith("LEAVE"):
        print("Bye!")
        sys.exit(0)
    elif command.startswith("HELP"):
        cli_help()
    else:
        print("Unbekanntes Kommando. Mit HELP bekommst du Hilfe.")

def main():
    print("Hallo!!! Tippen Sie HELP ein um alle Kommandos zu bekommen")
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
            process_command(user_input)
        except (EOFError, KeyboardInterrupt):
            print("\nBeende CLI.")
            break

if __name__ == "__main__":
    main()
