#!/bin/bash
echo "Stoppt alle Chat relevanten Prozesse..."
sudo pkill -f client.py
sudo pkill -f cli.py
sudo pkill -f broadcast_server.py
sleep 2

echo "Stoppt alle Prozesse in den Chat Ports..."
for port in {12345..12349} {17345..17351} 4000; do
    sudo fuser -k $port/tcp 2>/dev/null || true
    sudo fuser -k $port/udp 2>/dev/null || true
done
echo "Cleanup erfolgreich"
