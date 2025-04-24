#!/bin/bash
echo "[*] Setting up Node 2 (Misconfigured Sudo)..."
useradd -m -p $(openssl passwd -1 'dev2pass') dev2
echo "dev2 ALL=(ALL) NOPASSWD: /usr/bin/env" >> /etc/sudoers
echo "[+] Node 2 Ready: Sudo misconfiguration set."
