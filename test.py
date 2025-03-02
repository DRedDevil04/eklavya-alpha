from interface.connector import SSHConnector

ssh=SSHConnector("192.168.122.93","kali","kali")

ssh.create_ssh_session()
command='uname -a'
output = ssh.execute_command(command)

# Print the output
print("Command Output:")
print(output)
