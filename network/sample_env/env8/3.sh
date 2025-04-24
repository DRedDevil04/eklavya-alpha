#!/bin/bash
echo "[*] Setting up Node 3 (Redis RCE Exploitation)..."
echo -e "\nmodule load /tmp/malicious.so\n" >> /etc/redis/redis.conf
echo "[+] Node 3 Ready: Redis prepared for module-based RCE."
