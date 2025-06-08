## @file cli.py
# @brief Command Line Interface für den Chat.
# @details Ermöglicht die Eingabe und Verabeitung von Benutzerkommandos.

import sys #Ermöglicht Terminierung des Programms.

def cli_help(): #help ist eine Python Funktion deswegen das cli davor.
    """
    @brief Das ist eine Übersicht über die verfügbaren Commands. 
    """
    print("Verfügbare Kommandos:")
    print(" JOIN           Dem Netzwerk beitreten")
    print(" MSG [Text]     Sendet Nachricht")
    print(" IMG [Pfad]     Sendet Bild")
    print(" LEAVE          Das Netwerk verlassen")
    print(" WHO            Nutzerliste ausgeben")


def process_command(command):
    """
    @brief Verarbeitet ein einzelnes Benutzerkommando.
    @param command Das eingegebene Kommando als String.
    """
    if command.startswith("JOIN"):
        print("JOIN-Kommando verarbeitet (PLATZHALTER)")
    elif command.startswith("MSG"):
        print("MSG-Kommando verarbeitet (PLATZHALTER)")
    elif command.startswith("WHO"):
        print("WHO-Kommando verarbeitet im KNOWNUSERS Format")
    elif command.startswith("IMG"):
        print("IMG-Kommando verarbeitet")
    elif command.startswith("LEAVE"):
         print("Bye!")
         sys.exit(0)
    elif command.startswith("HELP"):
        cli_help()
    else:
        print("Unbekanntes Kommando. Mit HELP bekommst du Hilfe.")

def main():
    """
    @brief Hauptfunktion der CLI. Liest Benutzereingaben und verarbeitet sie.
    """
    print("Hallo!!! Tippen Sie HELP ein um alle Kommandos zu bekommen")
    while True: #Schleife damit das Programm nicht terminieren kann ohne validen Input.
        try:
            user_input = input("> ").strip()  # Eingabe einlesen und Leerzeichen entfernen
            if not user_input:
                continue  # Falls nichts eingegeben wurde, nochmal fragen
            process_command(user_input)       # Kommando verarbeiten
        except (EOFError, KeyboardInterrupt): #Fängt STRG + Z und STRG + C ab
            print("\nBeende CLI.")
            break

if __name__ == "__main__":
    main()
