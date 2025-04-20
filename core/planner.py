import re
from llm_interface.llm_client import LLMClient

class Planner:
    def __init__(self):
        # Initialize LLMClient with OpenAI
        self.llm = LLMClient(mode='openai', planner_model_name='gpt-4.1-mini')

    def plan_next_step(self, current_phase, context_summary, todo_list, target_ip, username, password):
        prompt = self.build_prompt(current_phase, context_summary, todo_list, target_ip, username, password)
        response = self.llm.query_planner(prompt)
        return prompt,self.extract_command(response)

    def build_prompt(self, phase, summary, todo_list, ip, username, password):
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

Pending tasks:
{', '.join(todo_list) if todo_list else "None"}

Do not repeat previously used commands. infer this from the summary provided and only give commands which progress toward the getting root access in as many nodes in the network.
Based on this information, suggest the next command to run on the kali attacking machine to make progress.
Only return a valid shell command. Do NOT include explanations."""
        return prompt

    def extract_command(self, response):
        """Extract and wrap the actual shell command from the LLM response using regex."""
        response = response.strip()
        match = re.search(r'(?:```(?:bash)?\s*)?([a-zA-Z0-9_\-\.]+(?:\s+[^\n`]+)?)', response)
        if match:
            command = match.group(1).strip()
            return f"{command}"
        return "echo 'No valid command found'"
