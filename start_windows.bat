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
echo 📣 Bitte oeffne neue Terminals und fuehre jeweils aus:
echo     python cli.py
echo       und gib an, welcher der folgenden User du bist: Fabian, Michael, Can
echo.