import sys
import toml
from client import Client

with open("config.toml", "r") as f:
    config = toml.load(f)

current_user = None
network = None

def cli_help():
    print("Verfügbare Kommandos:")
    print(" JOIN        Dem Netzwerk beitreten")
    print(" MSG [Text]  Sendet Nachricht!")
    print(" IMG [Pfad]  Sendet Bild an alle (optional)")
    print(" AWAY        Status auf abwesend setzen (Auto-Reply aktiv!)")
    print(" BACK        Status auf aktiv zurücksetzen")
    print(" LEAVE       Das Netzwerk verlassen")
    print(" WHO         Nutzerliste ausgeben (nur aktuell Online)")
    print(" HELP        Zeigt diese Hilfe")

def get_all_users():
    return [(u["name"], u["port"]) for u in config["users"]]

def process_command(command):
    global current_user, network

    if command.startswith("JOIN"):
        print("Tippe ACCOUNTS ein um eine Liste aller verfügbaren Nutzernamen zu bekommen.")
        username_input = input("Welchen User Account willst du benutzen: ").strip()
        if username_input.upper() == "ACCOUNTS":
            print("Alle User:", [u["name"] for u in config["users"]])
            username_input = input("Welchen User Account willst du benutzen: ").strip()

        for user in config["users"]:
            if user["name"].lower() == username_input.lower():
                current_user = user
                udp_port = user["port"]
                # Erstelle Client-Objekt
                network = Client(user["name"], udp_port)
                # Userliste (alle aus der config, aber NUR die Ports!)
                userlist = get_all_users()
                network.set_userlist(userlist)
                network._start_udp_listener()
                print(f"Erfolgreich eingeloggt als {user['name']} (UDP: {udp_port})")
                break
        else:
            print("User nicht gefunden.")

    elif command.startswith("MSG"):
        if not current_user or not network:
            print("Bitte erst JOIN ausführen.")
            return
        try:
            target_and_msg = command[4:].strip().split(" ", 1)
            if len(target_and_msg) != 2:
                print("MSG [Name] [Text]")
                return
            target, msg = target_and_msg
            network.send_msg(target, msg)
        except Exception as e:
            print("MSG-Fehler:", e)

    elif command.strip() == "AWAY":
        if network:
            network.set_afk()

    elif command.strip() == "BACK":
        if network:
            network.set_back()

    elif command.strip() == "LEAVE":
        print("Bye!")
        sys.exit(0)

    elif command.strip() == "WHO":
        print("Online-USER:")
        if network:
            for name, port in network.get_online_users():
                print(f"- {name} (Port {port})")
        else:
            print("Noch nicht verbunden.")

    elif command.strip() == "HELP":
        cli_help()

    else:
        print("Unbekanntes Kommando. Mit HELP bekommst du Hilfe.")

def main():
    print("Hallo! Tippe HELP ein um alle Kommandos zu bekommen")
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
