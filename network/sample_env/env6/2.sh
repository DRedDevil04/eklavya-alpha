#!/bin/bash
echo "[*] Setting up Node 2 (Vulnerable Sudo)..."
useradd -m -p $(openssl passwd -1 'dave123') dave
echo "[+] Node 2 Ready: Sudo misconfiguration for CVE-2021-3156."
