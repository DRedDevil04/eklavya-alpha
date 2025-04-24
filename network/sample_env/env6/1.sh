#!/bin/bash
echo "[*] Setting up Node 1 (Weak SSH Access)..."
useradd -m -p $(openssl passwd -1 'chris123') chris
apt update && apt install -y openssh-server
systemctl enable ssh && systemctl restart ssh
echo "[+] Node 1 Ready: SSH enabled."
