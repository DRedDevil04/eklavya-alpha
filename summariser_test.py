from agent.summariser.Summariser import Summarizer

# Initialize the summarizer
summarizer = Summarizer()

# Sample command and output
command = "nmap -sS -p- --open -T5 192.168.122.0/24"
output = '''Starting Nmap 7.94SVN ( https://nmap.org ) at 2025-03-25 03:26 EDT

Nmap scan report for ubuntu (192.168.122.12)
Host is up (0.00050s latency).
Not shown: 65534 closed tcp ports (reset)
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.8 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey: 
|   256 33:29:64:75:94:0e:86:6c:f6:bf:c1:4c:65:b5:5c:83 (ECDSA)
|_  256 be:5c:24:10:23:d7:a6:9c:a6:6e:80:8d:24:7e:34:bf (ED25519)
MAC Address: 52:54:00:65:5B:DF (QEMU virtual NIC)
Device type: general purpose
Running: Linux 4.X|5.X
OS CPE: cpe:/o:linux:linux_kernel:4 cpe:/o:linux:linux_kernel:5
OS details: Linux 4.15 - 5.8
Network Distance: 1 hop
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel

TRACEROUTE
HOP RTT     ADDRESS
1   0.50 ms ubuntu (192.168.122.12)

OS and Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
Nmap done: 256 IP addresses (3 hosts up) scanned in 27.72 seconds
'''

# Generate summary
summary = summarizer.summarize(command, output)

# Check if summary is generated
if summary:
    print("Summarization successful:", summary)
else:
    print("Summarization failed.")
