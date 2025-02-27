#!/bin/bash

# Create users with specified passwords
sudo useradd -m -s /bin/bash josh
echo "josh:KJAHawe" | sudo chpasswd

sudo useradd -m -s /bin/bash john
echo "john:987654321" | sudo chpasswd

# Set SUID bit on Bash for privilege escalation
sudo chmod u+s /bin/bash

echo "Setup complete for Node 1."

