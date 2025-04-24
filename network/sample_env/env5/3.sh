#!/bin/bash
echo "[*] Setting up Node 3 (Cron Privilege Escalation)..."
echo "* * * * * root /tmp/root_script.sh" >> /etc/crontab
chmod +x /tmp/root_script.sh
echo "[+] Node 3 Ready: Cron job allows root shell."
