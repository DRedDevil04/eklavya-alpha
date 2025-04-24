#!/bin/bash
echo "[*] Setting up Node 2 (Redis Server with No Auth)..."
apt update && apt install -y redis-server
sed -i 's/^# *bind.*/bind 0.0.0.0/' /etc/redis/redis.conf
sed -i 's/^# *requirepass .*//' /etc/redis/redis.conf
systemctl restart redis
echo "[+] Node 2 Ready: Redis exposed without auth."
