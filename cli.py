import socket
import sys
import threading
import toml

def load_config():
    return toml.load("config.toml")

def find_client_config(config, name):
    for client in config["users"]:
        if client["name"] == name:
            return client
    raise Exception(f"Keine Konfiguration für {name} gefunden")

def listen_to_client(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            print(data.decode().strip())
        except:
            break

def main():
    # Änderung: Name kann als Argument oder per Eingabe gesetzt werden
    if len(sys.argv) < 2:
        client_name = input("Welchen Usernamen möchtest du verwenden? ")
    else:
        client_name = sys.argv[1]

    config = load_config()
    try:
        conf = find_client_config(config, client_name)
    except Exception as e:
        print(e)
        sys.exit(1)

    host = conf["host_ip"]
    port = conf["ipc_port"]

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"✅ Verbunden mit {client_name} auf {host}:{port}")
    except Exception as e:
        print(f"Verbindung fehlgeschlagen zu {client_name}: {e}")
        sys.exit(1)

    # Thread für eingehende Nachrichten starten
    threading.Thread(target=listen_to_client, args=(sock,), daemon=True).start()

    print("📨 Befehle:")
    print("  JOIN                  - Tritt dem Chat bei")
    print("  MSG <Handle> <Nachricht> - Sende Nachricht an bestimmten Nutzer")
    print("  AWAY                  - Aktiviere Abwesenheitsmodus")
    print("  BACK                  - Beende Abwesenheitsmodus")
    print("  IMG <Handle> <Pfad>   - Sende ein Bild an einen Nutzer")
    print("  WHO                   - Frage nach allen Nutzern im Netz")
    print("  LEAVE                 - Chat verlassen")
    print("STRG+C zum Beenden.\n")

    while True:
        try:
            cmd = input("» ").strip()
            if cmd:
                sock.sendall((cmd + "\n").encode())
        except (EOFError, KeyboardInterrupt):
            print("\nVerbindung beendet.")
            break

if __name__ == "__main__":
    main()
