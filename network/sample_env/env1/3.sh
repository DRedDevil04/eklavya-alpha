#!/bin/bash

# Create user with specified password
sudo useradd -m -s /bin/bash dave
echo "dave:38irjd02i" | sudo chpasswd

# Install vsftpd (vulnerable version)
sudo apt update
sudo apt install -y vsftpd

# Configure vsftpd to be vulnerable (allow anonymous access, run as root)
echo "anonymous_enable=YES" | sudo tee -a /etc/vsftpd.conf
echo "local_enable=YES" | sudo tee -a /etc/vsftpd.conf
echo "write_enable=YES" | sudo tee -a /etc/vsftpd.conf
echo "anon_root=/var/ftp" | sudo tee -a /etc/vsftpd.conf

# Restart vsftpd
sudo systemctl restart vsftpd

echo "Setup complete for Node 3."

