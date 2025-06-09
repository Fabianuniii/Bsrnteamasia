import sys
import os
def cli_help():
    print("Verfügbare Kommandos:")
    print(" JOIN           Dem Netzwerk beitreten (automatisch beim Start)")
    print(" MSG [Text]     Sendet Nachricht")
    print(" IMG [Pfad]     Sendet Bild über TCP")
    print(" LEAVE          Netzwerk verlassen und Programm beenden")
    print(" WHO            Nutzerliste anzeigen")
    print(" HELP           Diese Hilfe anzeigen")
def is_valid_image(path):
    valid_extensions = (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp")
    if not os.path.isfile(path):
        print("[Fehler] Datei existiert nicht")
        return False
    if not path.lower().endswith(valid_extensions):
        print("[Fehler] Nur folgende Bildformate erlaubt: .jpg, .jpeg, .png, .gif, .bmp, .webp")
        return False
    if os.path.getsize(path) > 10 * 1024 * 1024:  # 10MB
        print("[Fehler] Bild ist zu groß (maximal 10MB erlaubt)")
        return False
    return True
def process_command(command, network):
    if command.startswith("JOIN"):
        print("[System] Sie sind bereits dem Netzwerk beigetreten")
    elif command.startswith("MSG"):
        parts = command.split(" ", 1)
        if len(parts) > 1:
            network.send(parts[1])
        else:
            print("[Fehler] Bitte Nachricht eingeben: MSG [Ihr Text]")
    elif command.startswith("IMG"):
        parts = command.split(" ", 1)
        if len(parts) > 1:
            path = parts[1].strip('"\'')  # Entfernt Anführungszeichen falls vorhanden
            if is_valid_image(path):
                network.send_image_tcp(path)
            else:
                print("[Fehler] Ungültige Bilddatei")
        else:
            print("[Fehler] Bitte Pfad angeben: IMG [Pfad/zum/Bild.jpg]")
    elif command.startswith("WHO"):
        if network.known_users:
            print("\n[System] Bekannte Nutzer:")
            for user, (ip, port) in network.known_users.items():
                print(f" - {user} (IP: {ip}, TCP-Port: {port})")
        else:
            print("[System] Keine anderen Nutzer online")
    elif command.startswith("LEAVE"):
        print("Auf Wiedersehen!")
        network.stop()
        sys.exit(0)
    elif command.startswith("HELP"):
        cli_help()
    else:
        print("Unbekanntes Kommando. Tippen Sie HELP für verfügbare Befehle")
def start_cli(network):
    print("\n\U0001F44B Willkommen beim SLCP Chat Client")
    print("Tippen Sie HELP für eine Liste aller Befehle\n")
    
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
            process_command(user_input, network)
        except (EOFError, KeyboardInterrupt):
            print("\n[System] Client wird beendet...")
            network.stop()
            break