#!/bin/bash
echo "[*] Setting up Node 3 (Privilege Escalation via Shadow File)..."
chmod 777 /etc/shadow
echo "[+] Node 3 Ready: Writable /etc/shadow enabled."
