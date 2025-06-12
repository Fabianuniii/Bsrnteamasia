import argparse
from broadcast_server import BroadcastServer
from cli import ChatCLI

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
        cli = ChatCLI()
        cli.run()

if __name__ == "__main__":
    main()