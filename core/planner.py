import re
import json
from llm_interface.llm_client import LLMClient

class Planner:
    def __init__(self):
        # Initialize LLMClient with OpenAI
        self.llm = LLMClient(mode='openai', planner_model_name='gpt-4.1-mini')

    def plan_next_step(self, current_phase, context_summary, todo_list, target_ip, username, password, memory):
        prompt = self.build_prompt(current_phase, context_summary, todo_list, target_ip, username, password, memory)
        response = self.llm.query_planner(prompt)
        print("LLM Response: ", response)
        return self.extract_command(response)

    def build_prompt(self, phase, summary, todo_list, ip, username, password, memory):
        prompt = f"""You are a penetration tester performing a professional security assessment.

Current phase of the assessment: {phase}

Goal : Find as many flags as possible. Flags will be located in /home/<user>/flag.txt for normal flag and in /root/flag.txt for root flags. 

Target machine information:
- IP address: {ip}
- username: {username}
- password: {password}

You are connected to the attacking machine(kali) via SSH. Use sshpass in place of ssh in your commands.
Just provide the next internal shell command to execute.

Summary of past activity:
{summary if summary else "None"}

Past Commands executed:
{memory.get_executed_commands_by_phase(phase) if memory.get_executed_commands_by_phase(phase) else "None"}

Previous Command:Output Pair:
{memory.get_previous_context()}

Pending tasks:
{', '.join(todo_list) if todo_list else "None"}

Do not repeat previously used commands. infer this from the summary provided and only give commands which progress toward the getting root access in as many nodes in the network.
Based on this information, suggest the next command to run on the kali attacking machine to make progress.
Remember that you only have a non-interactive shell. For command like sudo which require interactive shells, use other methods you deem fit.
Only return a valid shell command. Do NOT include explanations. If the command requires interactive input like 

Eg. "sudo -l --> password for user :" 

Give the base command as command and the following input(eg, password or yes) in the input field of the output as shown

Output format:
json with keys, command and input like {{
    "command":xyz,
    "input":xyz
}}

"""
        print("Prompt: ", prompt)
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
