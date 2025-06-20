import socket
import sys
import threading
import toml

def load_config():
    return toml.load("config.toml")

def find_client_config(config, idx):
    try:
        return config["users"][idx-1]
    except IndexError:
        raise Exception(f"Kein User mit Index {idx} gefunden.")

def list_users(config):
    print("\nVerfügbare Benutzer:")
    for i, user in enumerate(config["users"], start=1):
        handle = user.get("handle", user.get("name", f"User{i}"))
        print(f"  {i}. {handle}  ({user['host_ip']}:{user['ipc_port']})")
    print()

def listen_to_client(sock):
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                break
            print(data.decode().strip())
        except:
            break

def print_help():
    print("📨 Befehle:")
    print("  JOIN                      - Tritt dem Chat bei")
    print("  MSG <Handle> <Nachricht>  - Sende Nachricht an bestimmten Nutzer")
    print("  AWAY                      - Aktiviere Abwesenheitsmodus")
    print("  BACK                      - Beende Abwesenheitsmodus")
    print("  IMG <Handle> <Pfad>       - Sende ein Bild an einen Nutzer")
    print("  WHO                       - Frage nach allen Nutzern im Netz")
    print("  LEAVE                     - Chat verlassen")
    print("  HANDLE <NeuerName>        - Setze neuen Anzeigenamen (Handle)")
    print("  AUTOREPLY <Text>          - Setze neuen Autoreply-Text")
    print("  HELP                      - Zeige diese Hilfe an")
    print("STRG+C zum Beenden.\n")

def main():
    config = load_config()

    # Benutzerindex abfragen oder als Argument erlauben
    if len(sys.argv) < 2:
        list_users(config)
        user_idx = input("Nummer des gewünschten Benutzers eingeben: ")
    else:
        user_idx = sys.argv[1]

    try:
        user_idx = int(user_idx)
    except ValueError:
        print("Ungültige Eingabe – bitte eine Zahl eingeben.")
        sys.exit(1)

    try:
        conf = find_client_config(config, user_idx)
    except Exception as e:
        print(e)
        sys.exit(1)

    host = conf["host_ip"]
    port = conf["ipc_port"]

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print(f"✅ Verbunden mit User {user_idx} auf {host}:{port}")
    except Exception as e:
        print(f"Verbindung fehlgeschlagen zu User {user_idx}: {e}")
        sys.exit(1)

    # Nach dem Handle fragen – **Eingabe MUSS erfolgen**
    while True:
        chosen_handle = input("Welchen Handle willst du im Chat verwenden?\n> ").strip()
        if chosen_handle:
            sock.sendall(f"HANDLE {chosen_handle}\n".encode())
            break
        else:
            print("Bitte gib einen Handle ein (Pflichtfeld)!")

    threading.Thread(target=listen_to_client, args=(sock,), daemon=True).start()

    print_help()

    while True:
        try:
            cmd = input("» ").strip()
            if cmd.upper() in ("HELP", "?"):
                print_help()
                continue
            if cmd:
                sock.sendall((cmd + "\n").encode())
        except (EOFError, KeyboardInterrupt):
            print("\nVerbindung beendet.")
            break

if __name__ == "__main__":
    main()