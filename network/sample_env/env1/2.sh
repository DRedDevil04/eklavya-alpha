#!/bin/bash

# Create user with specified password
sudo useradd -m -s /bin/bash john
echo "john:987654321" | sudo chpasswd

# Add user 'john' to sudoers with full privileges
echo "john ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/john

echo "Setup complete for Node 2."

