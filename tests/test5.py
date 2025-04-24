import re
def extract_command(response):
        """
        Extracts a command and optional input from an LLM response.
        Returns a tuple (command, input) or (command, None) if no input is found.

        Example Input:
            "sshpass -p 'ddgreat' ssh -tt devam@192.168.122.97 'sudo -l' <INP>ddgreat</INP>"
        
        Returns:
            ("sshpass -p 'ddgreat' ssh -tt devam@192.168.122.97 'sudo -l'", "ddgreat")
        """
        response = response.strip()
        
        # Extract input (if exists)
        input_match = re.search(r'<INP>(.*?)<INP>', response)
        user_input = input_match.group(1) if input_match else None
        print("User Input: ", user_input)  # Debug the user input
        print(input_match)  # Debug the regex match
        # Remove <INP> tags from the command
        command = re.sub(r'<INP>.*?<INP>', '', response).strip()

        # Clean up command (remove code blocks if present)
        command = re.sub(r'^```(?:bash)?|```$', '', command).strip()
        print("Command: ", command)  # Debug the command
        # Default fallback if no command is detected
        if not command:
            return ("echo 'No valid command found'", None)
        
        return (command, user_input)
extract_command(response='''sshpass -p 'ddgreat' ssh devam@192.168.122.97 'sudo -l' <INP>ddgreat<INP>''')