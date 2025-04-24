#!/bin/bash
echo "[*] Setting up Node 2 (Misconfigured NFS)..."
apt install -y nfs-kernel-server
mkdir -p /srv/nfs/home
chmod 777 /srv/nfs/home
echo "/srv/nfs/home *(rw,no_root_squash)" >> /etc/exports
exportfs -a
systemctl restart nfs-kernel-server
echo "[+] Node 2 Ready: NFS misconfiguration enabled."
