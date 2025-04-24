#!/bin/bash
echo "[*] Setting up Node 3 (Privilege Escalation via SUID)..."
useradd -m -p $(openssl passwd -1 'root123') rootuser
chmod u+s /bin/bash
echo "[+] Node 3 Ready: SUID misconfiguration active."
