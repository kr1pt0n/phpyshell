# ⚡ Phpyshell

<div align="center">

![License](https://img.shields.io/badge/License-MIT-success?style=for-the-badge)
![PHP](https://img.shields.io/badge/PHP-7.4+-777BB4?style=for-the-badge\&logo=php)
![Platform](https://img.shields.io/badge/Platform-Kali%20Linux-557C94?style=for-the-badge\&logo=kalilinux)
![Python](https://img.shields.io/badge/Python-3.x-blue?style=for-the-badge\&logo=python)

**WebShell ligera, interactiva y potente para auditorías de seguridad y administración remota.**

</div>

---

## ✨ Características

* ⚡ Comunicación interactiva en tiempo real.
* 📤 Subida de archivos integrada.
* 📥 Descarga de archivos.
* 🔍 Detección automática de WebShells y Uploaders.
* 💻 Consola remota con comandos del sistema.
* 🪶 Código ligero y fácil de desplegar.

---

# 📂 Estructura

```text
phpyshell/
│
├── shell.php          # WebShell
├── uploader.php       # Uploader
├── server.py          # Cliente de comunicación
└── README.md
```

---

# 🚀 Instalación

## 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/kr1pt0n/phpyshell.git
cd phpyshell
```

---

## 2️⃣ Subir los archivos PHP al servidor

Ejemplo:

```text
http://192.168.20.10:8000/path/shell.php

http://192.168.20.10:8000/path/uploader.php
```

---

## 3️⃣ Configurar los endpoints

Editar `server.py`

```python
ENDPOINTS = [
    "http://192.168.20.10:8000/path/shell.php",
    "http://192.168.20.10:8000/path/uploader.php"
]
```

---

## 4️⃣ Ejecutar

```bash
python3 server.py
```

---

# 🖥️ Ejemplo de ejecución

```text
============================================================
                  WEBSHELL INTERACTIVA
============================================================

[*] Iniciando análisis dinámico de comportamiento PHP...

[+] Webshell Confirmado:
    http://192.168.20.10:8000/path/shell.php

[+] Uploader Confirmado:
    http://192.168.20.10:8000/path/uploader.php

============================================================
               RESUMEN DE DISPONIBILIDAD
============================================================

 Webshells operativas (GET/system):  1
 Uploaders operativos (POST/move):   1

============================================================

[*] Canal interactivo establecido en:
    http://192.168.20.10:8000/path/shell.php

[+] Conectado con éxito como:
    servidor\administrator

(servidor\administrator) C:\path>
```

---

# 📤 Subir archivos

Desde la consola:

```text
upload <archivo_local> <nombre_remoto>
```

o utilizando `curl`

```bash
curl -F "file=@/ruta/de/tu/archivo/local" http://192.168.20.10:8000/path/uploader.php
```

---

# 📥 Descargar archivos

```text
download <archivo_remoto> <nombre_local>
```

---

# ⌨️ Comandos disponibles

| Comando    | Descripción        |
| ---------- | ------------------ |
| `upload`   | Subir archivos     |
| `download` | Descargar archivos |
| `clear`    | Limpiar pantalla   |
| `exit`     | Salir              |

---

# ⚠️ Aviso

Este proyecto está destinado **únicamente para auditorías autorizadas, investigación y entornos de laboratorio**.

El uso no autorizado contra sistemas de terceros puede ser ilegal.

---

# 📄 Licencia

MIT License.
