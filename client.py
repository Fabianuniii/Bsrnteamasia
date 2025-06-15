import socket
import threading

class Client:
    def __init__(self, username, udp_port):
        self.username = username
        self.udp_port = udp_port
        self.is_afk = False
        self._udp_listener_thread = None
        # Diese Userliste musst du eigentlich dynamisch holen; zum Testen kannst du das statisch machen:
        self._userlist = []  # Liste von (username, port), z.B. [('Michael', 12345), ('Can', 12347)]

    def set_userlist(self, userlist):
        """Nutzerliste updaten, z.B. nach JOIN oder WHO."""
        self._userlist = userlist

    def get_online_users(self):
        return self._userlist

    def _start_udp_listener(self):
        def udp_listener():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind(('localhost', self.udp_port))
            print(f"[Listener] Hört auf UDP-Port {self.udp_port}")
            while True:
                try:
                    data, addr = sock.recvfrom(2048)
                    msg = data.decode(errors='ignore')
                    print(f"\n[Nachricht empfangen]: {msg}")
                    print("> ", end="", flush=True)
                    # --- AFK-Autoreply Block ---
                    if self.is_afk and not msg.startswith("[AUTOREPLY]") and not msg.startswith(self.username):
                        sender = msg.split(":")[0].strip()
                        # Suche den Port des Senders aus der aktuellen Userliste
                        peer_port = None
                        for uname, uport in self.get_online_users():
                            if uname == sender:
                                peer_port = uport
                                break
                        if peer_port:
                            autoreply = f"[AUTOREPLY] {self.username} ist AFK. Melde mich später!"
                            reply_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            reply_sock.sendto(autoreply.encode(), ('localhost', peer_port))
                            reply_sock.close()
                except Exception as e:
                    print(f"Listener-Fehler: {e}")
                    break
        if not self._udp_listener_thread:
            self._udp_listener_thread = threading.Thread(target=udp_listener, daemon=True)
            self._udp_listener_thread.start()

    def send_msg(self, target_name, message):
        # Finde den Port des Empfängers in der Userliste
        peer_port = None
        for uname, uport in self.get_online_users():
            if uname.lower() == target_name.lower():
                peer_port = uport
                break
        if not peer_port:
            print("User nicht gefunden!")
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        msg = f"{self.username}: {message}"
        sock.sendto(msg.encode(), ('localhost', peer_port))
        sock.close()

    def set_afk(self):
        self.is_afk = True
        print("Du bist jetzt AFK. Nachrichten werden automatisch beantwortet.")

    def set_back(self):
        self.is_afk = False
        print("Willkommen zurück, du bist jetzt wieder aktiv.")

# So kannst du die Klasse importieren:
# from client import Client

# Unten NUR ZUM TESTEN (nicht im finalen CLI nutzen!):
if __name__ == "__main__":
    c = Client("Michael", 12345)
    c.set_userlist([('Can', 12347)])
    c._start_udp_listener()
    c.set_afk()
    # c.send_msg('Can', 'Hi')
    import time
    time.sleep(60)  # Damit Listener läuft
