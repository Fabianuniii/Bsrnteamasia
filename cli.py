import sys
import toml
import os
from typing import Optional
from client import ClientNetwork

class ChatCLI:
    def __init__(self):
        self.config = self._load_config()
        self.network: Optional[ClientNetwork] = None
        self.current_user: Optional[dict] = None

    def _load_config(self):
        try:
            with open("config.toml", "r") as f:
                return toml.load(f)
        except FileNotFoundError:
            print("[Error] config.toml not found!")
            sys.exit(1)

    def _select_user(self):
        users = self.config.get("users", [])
        if not users:
            print("No users configured in config.toml")
            sys.exit(1)

        print("Verfügbare Benutzerkonten:")
        for i, user in enumerate(users):
            print(f" {i+1}. {user['name']} (Port: {user['port']})")

        while True:
            choice = input("Wähle einen Account (Nummer) oder 'ACCOUNTS' zum erneuten Anzeigen: ").strip()
            
            if choice.upper() == "ACCOUNTS":
                self._select_user()
                return
                
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(users):
                    return users[idx]
                print("Ungültige Auswahl!")
            except ValueError:
                print("Bitte eine Nummer eingeben!")

    def _show_help(self):
        print("\nVerfügbare Befehle:")
        print(" JOIN           - Dem Netzwerk beitreten")
        print(" MSG <Nachricht> - Nachricht senden")
        print(" IMG <Pfad>     - Bild senden")
        print(" WHO            - Online-Nutzer anzeigen")
        print(" AWAY           - Abwesenheitsmodus umschalten")
        print(" LEAVE          - Netzwerk verlassen")
        print(" HELP           - Diese Hilfe anzeigen")
        print("")

    def _process_command(self, command: str):
        if not command:
            return

        cmd = command.upper().strip()

        if cmd.startswith("JOIN"):
            if self.network:
                print("Sie sind bereits im Netzwerk")
                return

            self.current_user = self._select_user()
            udp_port = self.current_user["port"]
            tcp_port = udp_port + 10000

            self.network = ClientNetwork(
                username=self.current_user["name"],
                udp_port=udp_port,
                tcp_port=tcp_port
            )

            online_users = self.network.join_network()
            print(f"Angemeldet als {self.current_user['name']}")
            print(f"UDP-Port: {udp_port}, TCP-Port: {tcp_port}")
            print("Online-Nutzer:", ", ".join([u[0] for u in online_users]) if online_users else "Keine anderen Nutzer online")

        elif cmd.startswith("MSG"):
            if not self.network:
                print("Bitte zuerst JOIN verwenden!")
                return

            message = command[4:].strip()
            if not message:
                print("Bitte eine Nachricht nach MSG eingeben")
                return

            self.network.send_message(message)
            print(f"[Sie]: {message}")

        elif cmd.startswith("IMG"):
            if not self.network:
                print("Bitte zuerst JOIN verwenden!")
                return

            path = command[4:].strip()
            if not path:
                path = input("Bildpfad eingeben: ").strip()

            if not os.path.isfile(path):
                print("Datei nicht gefunden!")
                return

            self.network.send_image(path)

        elif cmd.startswith("WHO"):
            if not self.network:
                print("Bitte zuerst JOIN verwenden!")
                return

            online_users = self.network.get_online_users()
            if online_users:
                print("\nOnline-Nutzer:")
                for name, port in online_users:
                    print(f" - {name} (Port: {port})")
                print("")
            else:
                print("Keine anderen Nutzer online")

        elif cmd.startswith("AWAY"):
            if not self.network:
                print("Bitte zuerst JOIN verwenden!")
                return
            self.network.toggle_away_mode()

        elif cmd.startswith("LEAVE"):
            if self.network:
                self.network.stop()
            print("Auf Wiedersehen!")
            sys.exit(0)

        elif cmd.startswith("HELP"):
            self._show_help()

        else:
            print("Unbekannter Befehl. Tippen Sie HELP für verfügbare Befehle")

    def run(self):
        print("=== SLCP Chat Client ===")
        print("Tippen Sie HELP für Befehle\n")

        while True:
            try:
                command = input("> ").strip()
                self._process_command(command)
            except (EOFError, KeyboardInterrupt):
                print("\nAuf Wiedersehen!")
                if self.network:
                    self.network.stop()
                sys.exit(0)