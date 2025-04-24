#!/bin/bash
echo "[*] Setting up Node 1 (Dev SSH Access)..."
useradd -m -p $(openssl passwd -1 'gitdev') dev
apt update && apt install -y openssh-server
systemctl enable ssh && systemctl restart ssh
echo "[+] Node 1 Ready: SSH access enabled."
