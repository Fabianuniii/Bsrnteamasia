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
    print(" MSG <Handle> <Text>  Sendet Nachricht an bestimmten User")
    print(" IMG <Handle> <Pfad>  Sendet Bild an bestimmten User")
    print(" AWAY [Text]    AFK setzen mit optionaler Autoreply-Nachricht")
    print(" BACK           Nicht mehr AFK (zurück zum Chat)")
    print(" LEAVE          Das Netzwerk verlassen")
    print(" WHO            Nutzerliste ausgeben (nur aktuell Online)")
    print(" HELP           Zeigt diese Hilfe")
    print(" ACCOUNTS       Zeigt alle Accounts an")

def process_command(command):
    global current_user, network
    if command.startswith("JOIN"):
        check = 0
        check2 = 0
        while check2 == 0:
            acc_check = input("Tippe ACCOUNTS ein um eine Liste aller verfügbaren Nutzernamen zu bekommen. Oder SKIP eingeben fürs Überspringen ")
            if acc_check == "ACCOUNTS":
                for user in config["users"]:
                    print(user["name"])
            elif acc_check =="SKIP":
                check2 = 1

        while check == 0:
            username_input = input("Welchen User Account willst du benutzen: ")
            found = False
            
            for user in config["users"]:
                if user["name"].lower() == username_input.lower():
                    current_user = user
                    udp_port = user["port"]
                    tcp_port = udp_port + 10000
                    bilder_ordner = config["storage"]["bild_pfad"]
                    srv_port = config["network"]["whoisport"]
                    autoreply_msg = config["features"]["autoreply"]
                    network = ClientNetwork(user["name"], udp_port, tcp_port, srv_port=srv_port, bilder_ordner=bilder_ordner, autoreply_msg=autoreply_msg)
                    # Netzwerk beitreten
                    online_users = network.join_network()
                    network.get_online_users()
                    print("Aktuelle Online-User:", online_users)
                    print(f"Erfolgreich eingeloggt als {user['name']} (UDP: {udp_port}, TCP: {tcp_port})")
                    network.get_online_users() # Automatischer Abruf nach dem JOIN. Zum aktualisieren der Liste.
                    found = True
                    check = 1
                    break
            if not found and username_input != "ACCOUNTS":
                print("User nicht gefunden. Versuche es erneut mit einem gültigen Namen!")
                
    elif command.startswith("MSG"):
        if current_user is None or network is None:
            print("Bitte erst JOIN benutzen!")
            return
        parts = command.split(" ", 2)
        if len(parts) < 3:
            print("Bitte gib Empfänger und Nachricht an: MSG <Handle> <Text>")
            return
        target_handle = parts[1]
        message = parts[2]
        network.get_online_users() #Hier zum aktualisieren der Online Liste
        network.send_message(target_handle, message)
        
    elif command.startswith("IMG"):
        if current_user is None or network is None:
            print("Bitte erst JOIN benutzen!")
            return
        parts = command.split(" ", 2)
        if len(parts) < 3:
            print("Bitte gib Empfänger und Bildpfad an: IMG <Handle> <Pfad>")
            return
        target_handle = parts[1]
        img_path = parts[2]
        network.send_image(target_handle, img_path)
        
    elif command.startswith("AWAY"):
        if current_user is None or network is None:
            print("Bitte erst JOIN benutzen!")
            return
        parts = command.split(" ", 1)
        if len(parts) > 1:
            # Benutzerdefinierte Autoreply-Nachricht
            custom_message = parts[1]
            network.set_away(custom_message)
        else:
            # Standard Autoreply-Nachricht aus config
            network.set_away()
            
    elif command.startswith("BACK"):
        if current_user is None or network is None:
            print("Bitte erst JOIN benutzen!")
            return
        network.set_back()
        
    elif command.startswith("WHO"):
        if network is None:
            print("Bitte erst JOIN benutzen!")
            return
        online_users = network.get_online_users()
        print("KNOWUSER:")
        for handle, (ip, port) in online_users:
            away_status = " [AFK]" if network.username == handle and network.is_away else ""
            print(f"- {handle} (IP: {ip}, Port: {port}){away_status}")
            
    elif command.startswith("LEAVE"):
        if network is not None:
            network.leave_network()
        print("Bye!")
        sys.exit(0)
        
    elif command.startswith("HELP"):
        cli_help()
        
    elif command.startswith("ACCOUNTS"):
        for user in config["users"]:
            print(user["name"])
    else:
        print("Unbekanntes Kommando. Mit HELP bekommst du Hilfe.")

def main():
    print("Hallo!!! Tippen Sie HELP ein um alle Kommandos zu bekommen")
    while True:
        try:
            # Zeige AFK Status in der Eingabeaufforderung
            if network and network.is_away:
                user_input = input("[AFK] > ").strip()
            else:
                user_input = input("> ").strip()
                
            if not user_input:
                continue
            process_command(user_input)
        except (EOFError, KeyboardInterrupt):
            if network is not None:
                network.leave_network()
            print("\nBeende CLI.")
            break

if __name__ == "__main__":
    main()