#!/bin/bash
echo "[*] Setting up Node 1 (Limited Privilege SSH User)..."
useradd -m -p $(openssl passwd -1 'dev1pass') dev1
apt update && apt install -y openssh-server
systemctl enable ssh && systemctl restart ssh
echo "[+] Node 1 Ready: SSH user created."
