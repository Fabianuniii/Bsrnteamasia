import sys
import toml
from client import ClientNetwork

with open("config.toml", "r") as f:
    config = toml.load(f)

current_user = None
network = None

def cli_help():
    print("Verfügbare Kommandos:")
    print(" JOIN           Dem Netzwerk beitreten")
    print(" MSG [Text]     Sendet Nachricht")
    print(" IMG [Pfad]     Sendet Bild an alle")
    print(" LEAVE          Das Netzwerk verlassen")
    print(" WHO            Nutzerliste ausgeben (nur aktuell Online)")
    print(" HELP           Zeigt diese Hilfe")

def process_command(command):
    global current_user, network
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
                    udp_port = user["port"]
                    tcp_port = udp_port + 10000
                    bilder_ordner = config["storage"]["bild_pfad"]
                    srv_port = config["network"]["whoisport"]
                    network = ClientNetwork(user["name"], udp_port, tcp_port, srv_port=srv_port, bilder_ordner=bilder_ordner)
                    # Netzwerk beitreten
                    online_users = network.join_network()
                    print("Aktuelle Online-User:", online_users)
                    print(f"Erfolgreich eingeloggt als {user['name']} (UDP: {udp_port}, TCP: {tcp_port})")
                    found = True
                    check = 1
                    break
            if not found and username_input != "ACCOUNTS":
                print("User nicht gefunden. Versuche es erneut mit einem gültigen Namen!")
    elif command.startswith("MSG"):
        if current_user is None or network is None:
            print("Bitte erst JOIN benutzen!")
            return
        message = command[4:].strip()
        if not message:
            print("Bitte gib eine Nachricht nach MSG ein, z.B. MSG Hallo Welt!")
            return
        network.send_message(message)
    elif command.startswith("IMG"):
        if current_user is None or network is None:
            print("Bitte erst JOIN benutzen!")
            return
        img_path = command[4:].strip()
        if not img_path:
            img_path = input("Pfad zur Bilddatei: ").strip()
        network.send_image(img_path)
    elif command.startswith("WHO"):
        if network is None:
            print("Bitte erst JOIN benutzen!")
            return
        online_users = network.get_online_users()
        print("Online-USER:")
        for uname, uport in online_users:
            print(f"- {uname} (Port {uport})")
    elif command.startswith("LEAVE"):
        print("Bye!")
        sys.exit(0)
    elif command.startswith("HELP"):
        cli_help()
    elif command.startswith("ACCOUNTS"):
        pass
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
