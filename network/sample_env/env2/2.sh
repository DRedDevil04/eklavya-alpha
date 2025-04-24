#!/bin/bash
echo "[*] Setting up Node 2 (SSH Key Reuse)..."
useradd -m -p $(openssl passwd -1 'devops123') devops
mkdir -p /home/devops/.ssh
echo "ssh-rsa AAAA... attacker_public_key" > /home/devops/.ssh/authorized_keys
chown -R devops:devops /home/devops/.ssh
chmod 600 /home/devops/.ssh/authorized_keys
echo "[+] Node 2 Ready: SSH Key Reuse set up."
