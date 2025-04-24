#!/bin/bash
echo "[*] Setting up Node 3 (Git History Leak)..."
echo "AWS_SECRET=abc123" > /var/www/html/secrets.txt
git add . && git commit -m "Added secrets"
echo "[+] Node 3 Ready: Git history contains sensitive info."
