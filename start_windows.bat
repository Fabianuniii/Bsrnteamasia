@echo off
echo 🔄 Starte Chat-System (Windows/192.168.2.209) ...

REM 1. Konfigurationsdatei kopieren
copy /Y config_windows.toml config.toml

REM 2. Broadcast-Server starten
echo 🛰️  Starte Broadcast-Server ...
start cmd /k python broadcast_server.py

REM 3. Clients per Index starten (hier: 2=Fabian, 3=Can)
echo 👥 Starte Client 2 (Fabian)
start cmd /k python client.py 2

echo 👥 Starte Client 3 (Can)
start cmd /k python client.py 3

echo.
echo ✅ Hintergrundprozesse laufen.
echo 📣 Bitte oeffne neue Terminals und fuehre jeweils aus:
echo     python cli.py 2
echo     python cli.py 3
echo und gib dann nach dem Verbindungsaufbau deinen gewuenschten Handle ein!
echo.