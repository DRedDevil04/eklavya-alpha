#!/bin/bash
echo "[*] Setting up Node 2 (Git Repository Leak)..."
apt update && apt install -y apache2 git
cd /var/www/html && git init && touch secrets.txt && git add . && git commit -m "Initial commit"
echo "[+] Node 2 Ready: Git repo exposed via Apache."
