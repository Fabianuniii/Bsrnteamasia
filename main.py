import sys
from network import Network
from ui import UI

def main():
    if len(sys.argv) < 2:
        print("Benutzung: python main.py <dein_username>")
        return
    
    username = sys.argv[1]
    
    network = Network(username)
    ui = UI(network)
    ui.start()

if __name__ == "__main__":
    main()
