class UI:
    def __init__(self, network):
        self.network = network

    def start(self):
        print("👋 Willkommen beim SLCP Walking Skeleton")
        print("Gib Nachrichten ein. Tippe 'exit' zum Beenden.")
        while True:
            user_input = input("> ")
            if user_input.lower() == "exit":
                self.network.stop()
                print("Beendet.")
                break
            else:
                self.network.send(user_input)
