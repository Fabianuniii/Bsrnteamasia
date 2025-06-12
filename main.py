import subprocess
import argparse
import threading
from broadcast_server import run_broadcast_server

def start_broadcast_server():
    run_broadcast_server()

def main():
    # Start broadcast server in a separate thread
    server_thread = threading.Thread(target=start_broadcast_server, daemon=True)
    server_thread.start()
    
    # Start the CLI
    subprocess.run(["python", "cli.py"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start the chat system")
    parser.add_argument("--no-server", action="store_true", help="Don't start the broadcast server")
    args = parser.parse_args()
    
    if not args.no_server:
        main()
    else:
        # Just start the CLI if server is already running elsewhere
        subprocess.run(["python", "cli.py"])