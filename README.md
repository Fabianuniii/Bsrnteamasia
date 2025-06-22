#  BSRN Chat-System

Ein dezentrales, textbasiertes Chat-Programm mit Bildübertragung – entwickelt im Rahmen des Projekts *Betriebssysteme und Rechnernetze* (SoSe 2025).

##  Funktionen

- Peer-to-Peer Architektur (kein zentraler Server)
- Kommunikation über SLCP (Simple Local Chat Protocol)
- Versand von **Textnachrichten** und **Bildern**
- CLI für jeden Nutzer
- Discovery via UDP Broadcast
- Direkte Client-Kommunikation via UDP/TCP
- Konfigurierbar über `.toml`-Dateien
- Unterstützung für Windows, Linux, WSL

---

##  1. Vorbereitung

- Python 3.x installieren (empfohlen: ≥ 3.10)
- Optional: `toml`-Modul installieren:
  ```bash
  pip install toml
  ```
- Repository klonen und ins Verzeichnis wechseln:
  ```bash
  git clone https://github.com/Fabianuniii1/Bsrnteamasia
  cd Bsrnteamasia
  cd Code
  ```
- venv und requirements.txt installieren
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
---

## 2. Start unter WSL / Linux

### Dateirechte setzen (nur beim ersten Mal):

```bash
chmod +x bash_start.sh
chmod +x cleanup.sh
```

### Starten:

```bash
./bash_start.sh
```

Das Skript:
- kopiert `config_wsl.toml` nach `config.toml`
- startet den Broadcast-Server und die Clients im Hintergrund

### Dann pro Nutzer jeweils ein Terminal öffnen und:

```bash
python3 cli.py 1
python3 cli.py 2
python3 cli.py 3
```

Jede `cli.py`-Instanz steuert genau **einen Nutzer**.

---

## 3. Start unter Windows

1. Echte IPs in `config_windows.toml` eintragen

2. Auf den Host A client.py 1 starten und manuell in die 
    ```
    start_windows.bat
     ```
    eintragen und danach auf dem Host B die client.py 2 & 3 und es dort manuell eintragen.

3. Starte:
   ```bash
   .\start_windows.bat
   ```

Danach öffne pro Nutzer ein Terminal und führe aus:

```bash
python cli.py 1
python cli.py 2
python cli.py 3
```

---

## 4. Beenden & Aufräumen für WSL

Beende alle Prozesse und Ports:

```bash
./cleanup.sh
```

---

## 5. Konfigurationsdateien

Die aktive Konfiguration steht immer in:

```plaintext
config.toml
```

`config_wsl.toml` & `config_windows.toml` wird jeweils in die `config.toml` kopiert,
je nachdem welches Betriebssystem den Code ausführt.

---

### Wichtige Parameter:

| Sektion     | Beschreibung                                                  |
|-------------|---------------------------------------------------------------|
| `[network]` | `broadcast_ip`, `whoisport`                                   |
| `[storage]` | `imagepath`, `bild_pfad`                                      |
| `[features]`| `autoreply_enabled`, `autoreply`                              |
| `[[users]]` | Handle, Host-IP, Ports (`port`, `ipc_port`, `image_ipc_port`) |

---

## 6. Unterstützte SLCP-Befehle

| Befehl     | Beschreibung                                     |
|------------|--------------------------------------------------|
| `JOIN`     | Anmeldung beim Discovery-Dienst                  |
| `LEAVE`    | Chat verlassen                                   |
| `WHO`      | Liste aktiver Nutzer anfordern                   |
| `MSG`      | Textnachricht an anderen Nutzer senden           |
| `IMG`      | Bildnachricht an anderen Nutzer senden           |
| `AWAY`     | Abwesenheitsmodus aktivieren                     |
| `BACK`     | Abwesenheitsmodus beenden                        |
| `HANDLE`   | Eigenen Namen ändern                             |
| `AUTOREPLY`| Automatische Antwort setzen                      |
---

## 7. Architektur (Kurzfassung)

- **`cli.py`**  
  Kommandozeilen-Schnittstelle: verarbeitet Eingaben, kommuniziert mit dem Client über TCP

- **`client.py`**  
  Netzwerkkommunikation, Message-Passing, Bildübertragung

- **`broadcast_server.py`**  
  Discovery-Dienst für Nutzer (JOIN, LEAVE, WHO, KNOWUSERS)

- **IPC via TCP**  
  Jeder CLI-Nutzer hat seinen eigenen Port (`ipc_port`)

---

## 8. Projektstruktur

```plaintext
├── Code/
│   ├── client.py
│   ├── cli.py
│   ├── broadcast_server.py
│   ├── bash_start.sh
│   ├── cleanup.sh
│   ├── start_windows.bat
│   ├── config.toml
│   ├── config_wsl.toml
│   ├── config_windows.toml
│   └── requirements.txt
│
├── Doku/
│   ├── BSRN High Level Doku.pdf
│   ├── Doxygen Dokumentation.pdf
│   └── .gitignore
```

---

## 9. Dokumentation

- **BSRN High Level Doku.pdf**  
  > Architektur, Ziele, Funktionsweise, CLI-Befehle, Herausforderungen

- **Doxygen Dokumentation.pdf**  
  > Vollständige API-Dokumentation aus dem Quellcode

---

## 10. Abhängigkeiten

```txt
toml==0.10.2 
```

Installieren mit:

```bash
pip install -r requirements.txt
```

---

## Kontakt

> Dieses Projekt wurde im Rahmen des Moduls **„Betriebssysteme und Rechnernetze“** an der Frankfurt UAS (SS 2025) entwickelt. 
Für jegliche Fragen
``` 
nguyenmichaelgiahuy@gmail.com
```
