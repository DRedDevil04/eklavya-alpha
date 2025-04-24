#!/bin/bash
echo "[*] Setting up Node 3 (Kernel Exploit)..."
wget https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-4.10.tar.xz
tar -xf linux-4.10.tar.xz -C /usr/src/
echo "[+] Node 3 Ready: Vulnerable kernel version set for exploitation."
