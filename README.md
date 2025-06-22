# P2P Chat System – Dual Version (WSL & Windows)

## Projektüberblick

Ein Peer-to-Peer-Chat-System mit Broadcast-Erkennung, Client-Kommunikation über UDP und IPC (CLI ↔ Client) über TCP-Sockets und automatischem WHO-Update.

## Features

- Broadcast-Discovery und Online-Anzeige aller Nutzer
- CLI und GUI strikt getrennt: Chat läuft als eigener Client-Prozess, die Bedienung erfolgt per CLI (Terminal)
- Text- und Bildnachrichten an einzelne Nutzer
- Abwesenheitsmodus mit automatischem Autoreply
- Handle/Username on-the-fly ändern
- Plattformübergreifend: Getestet unter Linux/WSL und Windows

---

### Architekturkomponenten
- `broadcast_server.py` – empfängt UDP-Broadcasts (JOIN/AWAY)
- `client.py` – verwaltet Netzwerkkommunikation & IPC-Verbindung zur CLI
- `cli.py` – Benutzeroberfläche für Texteingabe, kommuniziert über TCP mit dem zugehörigen Client
- Konfigurierbar über `config.toml`
- Starten entweder über `start_windows.bat` für Windows Maschinen oder `bash.sh` für Linux.

---

##  Dual-Version Setup

| Umgebung | Kommunikation | Startmethode         | Konfiguration              |
|----------|---------------|----------------------|----------------------------|
| 🐧 WSL     | Localhost (127.0.0.1) + UDP | Bash-Skript (`bash_start.sh`) | `config_wsl.toml` → `config.toml` |
| 🪟 Windows | 2 Hosts mit echten IPs + UDP | Batch-Datei (`start_windows.bat`) | `config_windows.toml` → `config.toml` |

---

### 1. Vorbereitung

- Python 3.x installieren (empfohlen: 3.10 oder neuer)
- Optional: Toml per `pip install toml`
- Repository klonen und ins Verzeichnis wechseln

```bash
git clone <https://github.com/Fabianuniii/Bsrnteamasia>
cd <Name des Wunschverzeichnis>

### 2. Dateirechte für Bash-Skripte setzen (nur unter Linux/WSL)
Falls `bash_start.sh` oder `cleanup.sh` nicht ausführbar sind, führe folgendes aus:

```bash
chmod +x bash_start.sh
chmod +x cleanup.sh

### 3. Start unter WSL / Linux
```bash
./bash_start.sh

Das Skript kopiert die passende Config, startet den Broadcast-Server und die Client-Prozesse im Hintergrund.

Danach drei neue Terminals öffnen und jeweils
python3 cli.py 1
python3 cli.py 2
python3 cli.py 3
ausführen.
Jeder Nutzer steuert seinen eigenen Chat über die CLI.

### 4. Start unter Windows
Konfiguriere echte IPs in config_windows.toml (siehe Beispiel).

Kopiere config_windows.toml als config.toml

Starte per Doppelklick auf start_windows.bat

Dann jeweils ein Terminal pro Nutzer und CLI wie oben!

### 5. Beenden und Aufräumen
```bash
./cleanup.sh

## Konfigurationsdateien

Die aktiven Einstellungen stehen immer in config.toml.
Du kannst zwischen Varianten (config_wsl.toml, config_windows.toml) wechseln,
indem du die passende Datei als config.toml kopierst.

Wichtige Parameter:

[network] – broadcast_ip, whoisport

[storage] – Bildpfad

[[users]] – Nutzer (IP, Ports, Handle)



### Beispielstruktur:
Beispiel config.toml
```toml

[network]
broadcast_ip = "255.255.255.255"
whoisport = 33333

[storage]
imagepath = "bilder/"

[[users]]
name = "Michael"
handle = "Michael"
host_ip = "127.0.0.1"
port = 12345
ipc_port = 17345
image_ipc_port = 18045

[[users]]
name = "Fabian"
handle = "Fabian"
host_ip = "127.0.0.1"
port = 12346
ipc_port = 17346
image_ipc_port = 18046

[[users]]
name = "Can"
handle = "Can"
host_ip = "127.0.0.1"
port = 12347
ipc_port = 17347
image_ipc_port = 18047

Beispiel config_windows.toml

```toml

[network]
broadcast_ip = "192.168.0.255"
whoisport = 33333

[storage]
imagepath = "bilder/"

[[users]]
name = "Michael"
handle = "Michael"
host_ip = "192.168.0.10"
port = 12345
ipc_port = 17345
image_ipc_port = 18045

[[users]]
name = "Fabian"
handle = "Fabian"
host_ip = "192.168.0.11"
port = 12346
ipc_port = 17346
image_ipc_port = 18046

[[users]]
name = "Can"
handle = "Can"
host_ip = "192.168.0.12"
port = 12347
ipc_port = 17347
image_ipc_port = 18047

Beispiel config_wsl.toml
```toml

[network]
broadcast_ip = "255.255.255.255"
whoisport = 33333

[storage]
imagepath = "bilder/"

[[users]]
name = "Michael"
handle = "Michael"
host_ip = "127.0.0.1"
port = 12345
ipc_port = 17345
image_ipc_port = 18045

[[users]]
name = "Fabian"
handle = "Fabian"
host_ip = "127.0.0.1"
port = 12346
ipc_port = 17346
image_ipc_port = 18046

[[users]]
name = "Can"
handle = "Can"
host_ip = "127.0.0.1"
port = 12347
ipc_port = 17347
image_ipc_port = 18047

### Befehle in der CLI

| Befehl              | Bedeutung                            |
| ------------------- | ------------------------------------ |
| JOIN                | Dem Chat beitreten                   |
| MSG <Handle> <Text> | Nachricht an User senden             |
| AWAY \[Nachricht]   | Abwesenheit einschalten (+Autoreply) |
| BACK                | Zurück aus Abwesenheit               |
| IMG <Handle> <Pfad> | Bild an Nutzer senden                |
| WHO                 | Online-Liste anzeigen                |
| LEAVE               | Chat verlassen                       |
| HANDLE <Name>       | Eigenen Anzeigenamen/Handle ändern   |
| AUTOREPLY <Text>    | Autoreply-Text setzen/ändern         |
| HELP                | Hilfe/alle Befehle anzeigen          |

### Entwickler-Hinweise & Tipps
Client und CLI sind getrennte Prozesse:
Erst client.py, dann pro Nutzer eine CLI (cli.py) verbinden.

Werden Skripte nicht ausgeführt?
Rechte mit chmod +x <Dateiname> setzen.

Probleme mit Ports oder Firewall?
UDP/TCP-Ports freigeben! (siehe Config)

### Dateiübersicht
| Datei                | Zweck                           |
| -------------------- | ------------------------------- |
| broadcast\_server.py | Discovery-Server (UDP)          |
| client.py            | Netzwerk/Chat-Client            |
| cli.py               | Kommandozeile für User          |
| config.toml          | Aktive Konfiguration            |
| bash\_start.sh       | Startskript für WSL/Linux       |
| start\_windows.bat   | Startskript für Windows         |
| cleanup.sh           | Alle Prozesse und Ports beenden |
