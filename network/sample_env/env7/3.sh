#!/bin/bash
echo "[*] Setting up Node 3 (Docker Group Privilege Escalation)..."
usermod -aG docker attacker
echo "[+] Node 3 Ready: Attacker added to docker group."
