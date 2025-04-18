import re
from llm_interface.llm_client import LLMClient

class Planner:
    def __init__(self):
        # Initialize LLMClient with OpenAI
        self.llm = LLMClient(mode='openai', planner_model_name='gpt-4.1-mini')

    def plan_next_step(self, current_phase, context_summary, todo_list, target_ip, username, password):
        prompt = self.build_prompt(current_phase, context_summary, todo_list, target_ip, username, password)
        response = self.llm.query_planner(prompt)
        return self.extract_command(response)

    def build_prompt(self, phase, summary, todo_list, ip, username, password):
        prompt = f"""You are a penetration tester performing a professional security assessment.

Current phase: {phase}

Target machine information:
- IP address: {ip}
- SSH username: {username}
- SSH password: {password}

You are already connected to the target machine via SSH, so there is no need to include SSH in your commands. 
Just provide the next internal shell command to execute (e.g., `uname -a`, `ls`, `nmap`, etc.).

Summary of past activity:
{summary if summary else "None"}

Pending tasks:
{', '.join(todo_list) if todo_list else "None"}

Based on this information, suggest the next command to run on the kali attacking machine to make progress.
Only return a valid shell command. Do NOT include explanations or SSH commands."""
        return prompt

    def extract_command(self, response):
        """Extract and wrap the actual shell command from the LLM response using regex."""
        response = response.strip()
        match = re.search(r'(?:```(?:bash)?\s*)?([a-zA-Z0-9_\-\.]+(?:\s+[^\n`]+)?)', response)
        if match:
            command = match.group(1).strip()
            return f"{command}"
        return "echo 'No valid command found'"
