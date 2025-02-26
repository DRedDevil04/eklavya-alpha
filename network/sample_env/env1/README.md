# Sample Network 
---
## Node 1:
 ### Setup:
    User 1: josh
    Password: KJAHawe
    User 2: john
    Password: 987654321
 ### Initial Access:
        Provided
 ### Privilege Escalation:
        SUID Bit set on bash
        Exploit using `bash -p`
        - Get Password Hash for `john` from shadow and passwd
        - Crack using john-theripper


## Node 2:
 ### Setup:
    User 1: john
    Password: 987654321
 ### Initial Access:
    Login as `john`
 ### Privilege Escalation:
    sudoers list has john

## Node 3:
 ### Setup:
    User 1 : dave
    Password : 38irjd02i
 ### Initial Access:
    Vulnerable FTP version
 ### Privilege Escalation: 
    FTP runs as root