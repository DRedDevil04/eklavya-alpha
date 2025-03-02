# connector.py
import paramiko

class SSHConnector:
    def __init__(self, kali_ip, password, username='root'):
        """
        Initialize the SSHConnector with server IP, password, and username.

        :param kali_ip: IP address of the server.
        :param password: Password for SSH authentication.
        :param username: SSH username (default is 'root').
        """
        self.kali_ip = kali_ip
        self.password = password
        self.username = username
        self.ssh_client = None
    
    def create_ssh_session(self):
        """
        Creates an SSH session to the server.
        """
        try:
            # Create an SSH client
            self.ssh_client = paramiko.SSHClient()
            
            # Automatically add the server's host key (this is insecure in production)
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect to the server
            self.ssh_client.connect(self.kali_ip, username=self.username, password=self.password)
            print("SSH session established.")
        except Exception as e:
            print(f"Failed to create SSH session: {str(e)}")
            self.ssh_client = None
    
    def execute_command(self, command):
        """
        Executes a command on the remote server.

        :param command: The command to execute on the remote server.
        :return: Output of the executed command.
        """
        if not self.ssh_client:
            return "SSH session is not established."
        
        try:
            # Execute the command
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            
            # Read the output of the command
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error:
                return f"Error: {error}"
            
            return output
        except Exception as e:
            return f"An error occurred while executing the command: {str(e)}"
    
    def close_session(self):
        """
        Closes the SSH session.
        """
        if self.ssh_client:
            self.ssh_client.close()
            print("SSH session closed.")
        else:
            print("No active SSH session to close.")

