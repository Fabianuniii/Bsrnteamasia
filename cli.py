import sys
import threading
import toml
import os
from client import (
    join_broadcast_server, get_online_users,
    udp_listener, tcp_img_server,
    send_msg_to_online, send_img_to_online_tcp
)

# Load configuration
with open("config.toml", "r") as f:
    config = toml.load(f)

current_user = None
listener_thread = None
tcp_server_thread = None

def cli_help():
    print("Available commands:")
    print(" JOIN           Join the network")
    print(" MSG [text]     Send message to all")
    print(" IMG [path]     Send image to all (via TCP)")
    print(" LEAVE          Leave the network")
    print(" WHO            Show online users")
    print(" HELP           Show this help")

def process_command(command):
    global current_user, listener_thread, tcp_server_thread
    
    if command.startswith("JOIN"):
        check = 0
        while check == 0:
            print("Type ACCOUNTS to see all available usernames.")
            username_input = input("Which user account do you want to use: ")
            found = False
            
            if username_input == "ACCOUNTS":
                for user in config["users"]:
                    print(user["name"])
                    
            for user in config["users"]:
                if user["name"].lower() == username_input.lower():
                    current_user = user
                    image_folder = config.get("image_path", "./images/")
                    
                    if listener_thread is None:
                        listener_thread = threading.Thread(
                            target=udp_listener, 
                            args=(user["port"],), 
                            daemon=True
                        )
                        listener_thread.start()
                    
                    if tcp_server_thread is None:
                        tcp_port = user["port"] + 10000
                        tcp_server_thread = threading.Thread(
                            target=tcp_img_server, 
                            args=(tcp_port, image_folder), 
                            daemon=True
                        )
                        tcp_server_thread.start()
                    
                    # Register with broadcast server
                    online_list = join_broadcast_server(current_user["name"], current_user["port"])
                    print("Current online users:", [n for n, p in online_list])
                    print(f"Successfully logged in as {user['name']} (UDP-Port: {user['port']}, IMG-TCP-Port: {user['port']+10000})")
                    found = True
                    check = 1
                    break
                    
            if not found:
                print("User not found. Please try again with a valid name!")
                
    elif command.startswith("MSG"):
        if current_user is None:
            print("Please use JOIN first!")
            return
            
        message = command[4:].strip()
        if not message:
            print("Please enter a message after MSG, e.g. MSG Hello World!")
            return
            
        send_msg_to_online(current_user["name"], message, current_user["port"])
        
    elif command.startswith("IMG"):
        if current_user is None:
            print("Please use JOIN first!")
            return
            
        img_path = command[4:].strip()
        if not img_path:
            img_path = input("Path to image file: ").strip()
            
        if not os.path.isfile(img_path):
            print("File not found!")
            return
            
        send_img_to_online_tcp(current_user["name"], img_path, current_user["port"])
        
    elif command.startswith("WHO"):
        online_list = get_online_users()
        print("Online USERS:")
        for uname, uport in online_list:
            print(f"- {uname} (Port {uport})")
            
    elif command.startswith("LEAVE"):
        print("Goodbye!")
        sys.exit(0)
        
    elif command.startswith("HELP"):
        cli_help()
        
    else:
        print("Unknown command. Type HELP for available commands.")

def main():
    print("Welcome! Type HELP for a list of commands")
    while True:
        try:
            user_input = input("> ").strip()
            if not user_input:
                continue
            process_command(user_input)
        except (EOFError, KeyboardInterrupt):
            print("\nClosing CLI.")
            break

if __name__ == "__main__":
    main()