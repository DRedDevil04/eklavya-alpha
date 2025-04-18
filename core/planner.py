import re
from llm_interface.llm_client import LLMClient

class Planner:
    def __init__(self):
        # Initialize LLMClient with the 'local' mode and CodeLlama model
        #self.llm = LLMClient(mode='local', planner_model_name='codellama/CodeLlama-7B-Instruct-hf')
        self.llm = LLMClient(mode='openai', planner_model_name='gpt-4.1-mini')

    def plan_next_step(self, current_phase, context_summary, todo_list, target_ip, username, password):
        prompt = self.build_prompt(current_phase, context_summary, todo_list, target_ip, username, password)
        response = self.llm.query_planner(prompt)
        return self.extract_command(response)

    def build_prompt(self, phase, summary, todo_list, ip, username, password):
        prompt = f"""You are a penetration tester currently in the '{phase}' phase.

Target machine details:
- IP address: {ip}
- SSH username: {username}
- SSH password: {password}

Summary of previous activity:
{summary}

To-do list:
{', '.join(todo_list) if todo_list else "None"}

Based on the above, suggest the next command to execute on the target machine.
Only return the command line (no explanation)."""
        return prompt

    def extract_command(self, response):
        """Extract and wrap the actual shell command from the LLM response using regex."""
        print("Response from LLM:", response)

        response = response.strip()

        # Match a shell command possibly inside code block, optionally starting with bash
        match = re.search(r'(?:```(?:bash)?\s*)?([a-zA-Z0-9_\-\.]+(?:\s+[^\n`]+)?)', response)

        if match:
            command = match.group(1).strip()
            print("Extracted command:", command)
            return f"{command}"

        return "echo 'No valid command found'"
