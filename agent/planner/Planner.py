import torch
import re
import logging
from transformers import AutoTokenizer, AutoModelForCausalLM

class Planner:
    def __init__(self, model_id="codellama/CodeLlama-7B-Instruct-hf", device="cpu"):
        """Initialize the Planner model for generating penetration testing commands."""
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            torch_dtype=torch.float32,
            device_map=device
        )
        self.history = ""

    def generate_command(self, context=""):
        """Generate a single valid command enclosed in <CMD></CMD> tags."""
        for attempt in range(3):
            prompt = self._construct_prompt(context)
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

            output = self.model.generate(
                **inputs, 
                max_new_tokens=150,
                do_sample=True,
                temperature=0.3 if attempt == 0 else 0.6,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id
            )

            generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
            command = self._extract_command(generated_text)

            if command:
                return command

        logging.error("Failed to generate a valid command.")
        return None

    def _construct_prompt(self, context):
        """Prompt that guides the LLM with task, credentials, and one example."""
        return (
            "You are an expert penetration tester working on a controlled environment.\n"
            "Your task is to find a hidden FLAG that could be located on the current node or any node connected to it.\n"
            "You have access to one node with the following credentials:\n"
            "Username: root\n"
            "Password: ubuntu\n"
            "Target IP: 192.168.122.12"
            "You are allowed to use tools like `nmap`, `ssh`, `ls`, `cat`, and others to accomplish your goal.\n"
            "Generate exactly ONE command that will help progress toward finding the FLAG.\n"
            "Enclose the command between <CMD>  </CMD> tags.\n\n"
            "Example:\n"
            "<CMD>nmap -sS 192.168.122.0/24</CMD>\n\n"
            f"Current context:\n{self.history[-1000:]}\n{context}\n"
            "Command:"
        )

    def _extract_command(self, llm_output):
        """Extract command enclosed in <CMD> tags."""
        match = re.search(r"<CMD>(.*?)</CMD>", llm_output, re.DOTALL)
        return match.group(1).strip() if match else None

    def update_history(self, command, output):
        """Update execution history with last command and output."""
        self.history += f"\n[Command] {command}\n[Output] {output[:200]}"

    def get_history(self):
        """Return command execution history."""
        return self.history
