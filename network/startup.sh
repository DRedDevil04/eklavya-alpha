#! /bin/bash
sudo virsh net-start dev
sudo virsh start kali
sudo virsh start node1-linux
sudo virsh start node2-linux
sudo virsh start node3-linux
sudo iptables --flush
sudo iptables -t nat -A POSTROUTING -s 192.168.133.0/24 -d 192.168.122.0/24 -o virbr0 -j MASQUERADE
