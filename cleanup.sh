#!/bin/bash
echo "Alle Chat-zugehÃ¶rigen Prozesse stoppen..."
sudo pkill -f client.py
sudo pkill -f cli.py
sudo pkill -f broadcast_server.py
sleep 2

echo "Alle Portprozesse stoppen"
for port in {12345..12349} {17345..17351} 4000; do
    sudo fuser -k $port/tcp 2>/dev/null || true
    sudo fuser -k $port/udp 2>/dev/null || true
done
echo "Cleanup beendet."