#!/bin/bash

echo "🔄 Starte Chat-System ..."

# 1. Konfigurationsdatei für WSL kopieren
cp config_wsl.toml config.toml

# 2. Broadcast-Server starten
echo "🛰️  Starte Broadcast-Server ..."
python3 broadcast_server.py &

# 3. Clients starten (aus config.toml: Michael, Fabian, Can)
echo "👥 Starte Clients ..."
python3 client.py Michael &  # Die Namen sind hier nur für den Prozess, der Client joint aber noch NICHT!
python3 client.py Fabian &
python3 client.py Can &

# 4. Hinweis für CLI-Start
echo ""
echo "✅ Alle Hintergrundprozesse laufen nun."
echo "📣 Bitte öffne drei neue Terminals und führe jeweils folgendes aus:"
echo "    python3 cli.py"
<<<<<<< HEAD
echo "      → und gib an welcher der folgenden User du bist: Fabian, Michael, Can"
echo ""
echo "ℹ️  Danach kannst du direkt im CLI Befehle wie 'JOIN', 'MSG', 'AWAY', 'WHO' usw. eingeben."
=======
echo ""
echo "ℹ️  Danach kannst du direkt im CLI mit JOIN <Name> beitreten."
>>>>>>> 512995f (Sprachlich vereinheitlicht)
