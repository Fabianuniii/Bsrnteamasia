# 📨 P2P Chat System – Dual Version (WSL & Windows)

## 📁 Projektüberblick

Ein Peer-to-Peer-Chat-System mit Broadcast-Erkennung, Client-Kommunikation über UDP und IPC (CLI ↔ Client) über TCP-Sockets.

### ✔️ Architekturkomponenten
- `broadcast_server.py` – empfängt UDP-Broadcasts (JOIN/AWAY)
- `client.py` – verwaltet Netzwerkkommunikation & IPC-Verbindung zur CLI
- `cli.py` – Benutzeroberfläche für Texteingabe, kommuniziert über TCP mit dem zugehörigen Client
- Konfigurierbar über `config.toml`

---

## 🌐 Dual-Version Setup

| Umgebung | Kommunikation | Startmethode         | Konfiguration              |
|----------|---------------|----------------------|----------------------------|
| 🐧 WSL     | Localhost (127.0.0.1) + UDP | Bash-Skript (`bash_start.sh`) | `config_wsl.toml` → `config.toml` |
| 🪟 Windows | 2 Hosts mit echten IPs + UDP | Batch-Datei (`start_windows.bat`) | `config_windows.toml` → `config.toml` |

---

## ⚙️ Konfigurationsdateien

> Die aktive Datei muss immer `config.toml` heißen (sie wird beim Start aus einer Vorlage kopiert).

### Beispielstruktur:

```toml
[network]
broadcast_ip = "127.255.255.255"
whoisport = 9999

[[clients]]
name = "Client1"
host_ip = "127.0.0.1"
udp_port = 10001
ipc_port = 5001

# ... Client2, Client3
