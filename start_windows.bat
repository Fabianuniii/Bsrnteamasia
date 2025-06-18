@echo off
echo 🔄 Starte Chat-System für 192.168.2.209 (Fabian/Can) ...

copy /Y config_windows.toml config.toml

echo 🛰️  Starte Broadcast-Server ...
start cmd /k python broadcast_server.py

echo 👥 Starte Client Fabian ...
start cmd /k python client.py Fabian

echo 👥 Starte Client Can ...
start cmd /k python client.py Can

echo.
echo ✅ Hintergrundprozesse laufen.
echo 📣 Bitte öffne neue Terminals und führe jeweils aus:
echo     python cli.py Fabian
echo     python cli.py Can
echo.
