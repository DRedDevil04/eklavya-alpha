import paramiko
import time

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
            self.ssh_client.connect(
                self.kali_ip,
                username=self.username,
                password=self.password,
                look_for_keys=False  # Disable key-based auth
            )
            print("SSH session established.")
        except Exception as e:
            print(f"Failed to create SSH session: {str(e)}")
            self.ssh_client = None
    
    def execute_command(self, command, input_data=None, timeout=5):
        """
        Executes a command on the remote server, optionally handling interactive input.

        :param command: The command to execute.
        :param input_data: Input to send if a prompt is detected (e.g., sudo password).
        :param timeout: Timeout in seconds to wait for output.
        :return: Output of the executed command.
        """
        if not self.ssh_client:
            return "SSH session is not established."
        
        try:
            # Execute command with PTY for interactive sessions
            stdin, stdout, stderr = self.ssh_client.exec_command(
                command,
                get_pty=True  # Allocate pseudo-terminal
            )
            
            output = ""
            start_time = time.time()
            
            # Read output in real-time to detect prompts
            while True:
                if stdout.channel.recv_ready():
                    chunk = stdout.channel.recv(1024).decode('utf-8')
                    output += chunk
                    
                    # Check for password prompt
                    if input_data and ("password" in output.lower() or "[sudo]" in output.lower()):
                        stdin.write(input_data + "\n")  # Send input
                        stdin.flush()
                        break  # Exit loop after sending input
                
                # Check if command has finished or timeout
                if stdout.channel.exit_status_ready() or (time.time() - start_time) > timeout:
                    break
                
                time.sleep(0.1)  # Avoid busy-waiting
            
            # Read remaining output
            output += stdout.read().decode('utf-8')
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