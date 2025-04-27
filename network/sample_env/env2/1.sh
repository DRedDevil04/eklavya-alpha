#!/bin/bash
echo "[*] Setting up Node 1 (Weak SSH Access)..."
useradd -m -p $(openssl passwd -1 'admin123') admin
useradd -m -p $(openssl passwd -1 'sam123') sam
echo "[+] Node 1 Ready: SSH enabled, weak credentials set."
