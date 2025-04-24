#!/bin/bash
echo "[*] Setting up Node 2 (Exposed Docker Daemon)..."
apt update && apt install -y docker.io
systemctl enable docker && systemctl start docker
sed -i 's|ExecStart=/usr/bin/dockerd -H fd://|ExecStart=/usr/bin/dockerd -H tcp://0.0.0.0:2375|' /lib/systemd/system/docker.service
systemctl daemon-reexec && systemctl restart docker
echo "[+] Node 2 Ready: Docker daemon exposed on TCP port 2375."
