"""
@file broadcast_server.py
@brief Implementierung des Discovery-Servers für das Simple Local Chat Protocol (SLCP).

Dieses Modul stellt den Discovery-Dienst bereit, der Broadcast-Nachrichten (z. B. JOIN, WHO, LEAVE) empfängt und verarbeitet, um die Liste der online-Benutzer zu verwalten und an Clients weiterzugeben.
"""

import toml
import socket
import threading

# Lese die Broadcast-IP (und Port) aus config.toml
try:
    config = toml.load("config.toml")
    BROADCAST_IP = config["network"]["broadcast_ip"]
    WHOIS_PORT = config["network"]["whoisport"]
    USERS = config["users"]
except Exception:
    BROADCAST_IP = "192.168.2.255"  # Fallback für LAN
    WHOIS_PORT = 4000
    USERS = []

def find_user_idx(ip, port):
    """
    @brief Findet den Benutzerindex anhand von IP und Port.
    @param ip String, die IP-Adresse des Benutzers.
    @param port Integer, der Port des Benutzers.
    @return Integer, der Index des Benutzers in der Konfiguration, oder None, wenn nicht gefunden.
    """
    for idx, user in enumerate(USERS, 1):
        if user["host_ip"] == ip and user["port"] == port:
            return idx
    return None

class BroadcastServer:
    """
    @class BroadcastServer
    @brief Verwaltet den Discovery-Dienst für SLCP, empfängt und verarbeitet Broadcast-Nachrichten.
    """
    def __init__(self, port=WHOIS_PORT, broadcast_ip=BROADCAST_IP):
        """
        @brief Initialisiert den Broadcast-Server.
        @param port Integer, der Port für Broadcast-Nachrichten (Standard: WHOIS_PORT).
        @param broadcast_ip String, die Broadcast-IP-Adresse (Standard: BROADCAST_IP).
        """
        self.port = port
        self.broadcast_ip = broadcast_ip
        # Jetzt: {(ip, port): {"handle":..., "afk": False}}
        self.online_users = {}  # { (ip, port): {"handle": "Fabian", "afk": False} }
        self.running = False
        self.sock = None

    def start(self):
        """
        @brief Startet den Broadcast-Server und lauscht auf eingehende Nachrichten.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        try:
            self.sock.bind(('0.0.0.0', self.port))
            self.running = True
            print(f"[Broadcast-Server] läuft auf Port: {self.port}") # Ab hier gehen print statements los.

            while self.running:
                try:
                    data, addr = self.sock.recvfrom(1024)
                    msg = data.decode().strip()

                    if msg.startswith("JOIN "):
                        parts = msg.split(" ")
                        if len(parts) >= 3:
                            handle = parts[1]
                            user_port = int(parts[2])
                            key = (addr[0], user_port)
                            if key not in self.online_users:
                                print(f"[INFO] Nutzer @ {addr[0]}:{user_port} ist jetzt Online als: '{handle}'.")
                            else:
                                print(f"[INFO] Nutzer @ {addr[0]}:{user_port} hat seinen Handle aktualisiert: '{handle}'.")
                            self.online_users[key] = {"handle": handle, "afk": False}

                    elif msg.startswith("LEAVE "):
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            # Finde alle passenden Einträge mit diesem Handle (theoretisch nur einen)
                            to_remove = [k for k, v in self.online_users.items() if v["handle"] == handle]
                            for k in to_remove:
                                self.online_users.pop(k, None)
                            print(f"[INFO] {handle} hat den Chat verlassen.")

                    elif msg.startswith("AWAY "):
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            # Setze AFK für alle mit diesem Handle
                            for v in self.online_users.values():
                                if v["handle"] == handle:
                                    v["afk"] = True
                            print(f"[INFO] {handle} ist nun weg (AFK).")

                    elif msg.startswith("BACK "):
                        parts = msg.split(" ")
                        if len(parts) >= 2:
                            handle = parts[1]
                            for v in self.online_users.values():
                                if v["handle"] == handle:
                                    v["afk"] = False
                            print(f"[INFO] {handle} ist zurück.")

                    elif msg.startswith("WHO"):
                        if self.online_users:
                            user_list = []
                            for (ip, port), info in self.online_users.items():
                                status = " [AFK]" if info.get("afk", False) else ""
                                user_list.append(f"{info['handle']} {ip} {port}{status}")
                            reply = "KNOWUSERS " + ", ".join(user_list) + "\n"
                        else:
                            reply = "KNOWUSERS\n"
                        self.sock.sendto(reply.encode(), addr)

                except Exception as e:
                    if self.running:
                        print(f"[Broadcast-Server Error]: {e}")
        except OSError as e:
            print(f"[Error] Server konnte nicht gestartet werden: {e}")

    def stop(self):
        """
        @brief Stoppt den Broadcast-Server und schließt den Socket.
        """
        self.running = False
        if self.sock:
            self.sock.close()

def run_broadcast_server():
    """
    @brief Hauptfunktion zum Starten des Broadcast-Servers.
    """
    server = BroadcastServer()
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()

if __name__ == "__main__":
    run_broadcast_server()