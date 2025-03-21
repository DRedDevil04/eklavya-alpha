from interface.connector import SSHConnector

ssh=SSHConnector("192.168.122.186","kali","kali")

ssh.create_ssh_session()
command='ssh -T root@192.168.122.12'
output = ssh.execute_command(command)

# Print the output
print("Command Output:")
print(output)
