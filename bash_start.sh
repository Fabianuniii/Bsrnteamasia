#!/bin/bash

echo "Starte Chat-System ..."

# 1. Konfigurationsdatei für WSL kopieren
cp config_wsl.toml config.toml

# 2. Broadcast-Server starten
echo "Starte Broadcast-Server ..."
python3 broadcast_server.py &

# 3. Clients starten: Index 1, 2 und 3 aus config.toml
echo " Starte Clients 2 und 3 ..."
python3 client.py 1 &
python3 client.py 2 &
python3 client.py 3 &

# 4. Hinweis für CLI-Start
echo ""
echo "Alle Hintergrundprozesse laufen nun."
echo "Bitte öffne drei neue Terminals und führe jeweils folgendes aus:"
echo "    python3 cli.py 1"
echo "    python3 cli.py 2"
echo "    python3 cli.py 3"
echo ""
echo "Danach kannst du direkt im CLI Befehle wie 'JOIN', 'MSG', 'AWAY', 'WHO' usw. eingeben."
