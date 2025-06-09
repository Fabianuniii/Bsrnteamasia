import argparse
from client import Network
from cli import start_cli  # falls CLI in eigener Datei cli.py ist
def main():
    parser = argparse.ArgumentParser(description="SLCP Chat Client")
    parser.add_argument("--username", type=str, required=True, help="Dein Nutzername")
    parser.add_argument("--tcp-port", type=int, required=True, help="TCP-Port für Bildempfang (1024-65535)")
    args = parser.parse_args()
    if not (1024 <= args.tcp_port <= 65535):
        print("Bitte einen TCP-Port zwischen 1024 und 65535 angeben!")
        return
    client = Network(username=args.username, tcp_port=args.tcp_port)
    start_cli(client)
if __name__ == "__main__":
    main()