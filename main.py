import subprocess #damit können mehrere prozesse gleichzeitig laufen

def main():
    subprocess.Popen(["python3", "cli.py"]) #startet die cli in python

if __name__ == "__main__": #sorgt dafür dass main nur einmal ausgeführt wird
    main()
