#!/bin/bash
echo "[*] Setting up Node 1 (Web Admin Access)..."
useradd -m -p $(openssl passwd -1 'webadmin') admin
apt update && apt install -y openssh-server
systemctl enable ssh && systemctl restart ssh
echo "[+] Node 1 Ready: Web admin with SSH access."
