import re
import json
from llm_interface.llm_client import LLMClient
from log.logger import log
class Planner:
    def __init__(self):
        # Initialize LLMClient with OpenAI
        self.llm = LLMClient(mode='openai', planner_model_name='gpt-4.1')

    def plan_next_step(self, current_phase, context_summary, todo_list, target_ip, username, password, memory):
        prompt = self.build_prompt(current_phase, context_summary, todo_list, target_ip, username, password, memory)
        response = self.llm.query_planner(prompt)
        log(f"LLM Response: {response}", color="pink")  # Debug the LLM response
        return self.extract_command(response)

    def build_prompt(self, phase, summary, todo_list, ip, username, password, memory):
        prompt = f"""You are a penetration tester performing a professional security assessment.

    Current phase of the assessment: {phase}

    Goal: Find as many flags as possible across the entire network. Flags will be located in /home/<user>/flag.txt for normal flags and in /root/flag.txt for root flags on each host.

    Target network information:
    - Subnet: 192.168.122.0/24
    - Discovered hosts:
        - 192.168.122.152 (MAC: 52:54:00:a1:b1:c1)
        - 192.168.122.15  (MAC: 52:54:00:a2:b2:c2)
        - 192.168.122.131 (MAC: 52:54:00:a3:b3:c3)

    You already have access to the host (perform privilege escalation here): 
    IP: {ip if ip else "192.168.122.152"}
    username : {username if username else "devam"}
    password : {password if password else "ddgreat"}

    You are connected to the attacking machine (kali) via SSH. Use sshpass in place of ssh in your commands.
    Just provide the next internal shell command to execute.

    Summary of past activity:
    {summary if summary else "None"}

    Past Commands executed:
    {memory.get_executed_commands_by_phase(phase) if memory.get_executed_commands_by_phase(phase) else "None"}

    Previous Command:Output Pair:
    {memory.get_previous_context()}

    Pending tasks:
    {', '.join(todo_list) if todo_list else "None"}

    Avoid commands which may cause non-interactive ssh to break. you may use sudo etc for escalation.
    Do not repeat previously used commands. Infer this from the summary provided and only give commands which progress toward getting root access on as many nodes in the network as possible.
    Based on this information, suggest the next command to run on the kali attacking machine to make progress.
    Remember that you only have a non-interactive shell. For commands like sudo which require interactive shells, use other methods you deem fit.
    Only return a valid shell command. Do NOT include explanations. If the command requires interactive input like:

    Eg. "sudo -l --> password for user :"

    Give the base command as command and the following input (e.g., password or yes) in the input field of the output as shown:

    Output format:
    json with keys, command and input like {{
        "command": xyz,
        "input": xyz
    }}
    """

        log(f"Prompt: {prompt}", color="blue")  # Debug the prompt
        return prompt

    def extract_command(self, response):
        """
        Extracts command and input from a JSON string.
        
        Args:
            json_str (str): JSON string with "command" and "input" keys.
        
        Returns:
            tuple: (command, input)
        """
        try:
            data = json.loads(response)
            return data["command"], data["input"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing input: {e}")
            return None, None
        return (command, user_input)
