#!/bin/bash
echo "[*] Setting up Node 1 (SSH Access)..."
useradd -m -p $(openssl passwd -1 'redisuser') redis
apt update && apt install -y openssh-server
systemctl enable ssh && systemctl restart ssh
echo "[+] Node 1 Ready: SSH set for lateral movement."
