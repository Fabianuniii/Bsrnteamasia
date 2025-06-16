import argparse
from broadcast_server import BroadcastServer

def main():
    parser = argparse.ArgumentParser(description="SLCP Chat System")
    parser.add_argument("--server", action="store_true", help="Als Server starten")
    args = parser.parse_args()

    if args.server:
        server = BroadcastServer(port=4000)  # Using whoisport from config
        try:
            server.start()
        except KeyboardInterrupt:
            server.stop()
    else:
       from cli import main as cli_main
       cli_main()

if __name__ == "__main__":
    main()