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
            torch_dtype=torch.float16,
            device_map=device
        )
        self.history = ""
        
    def generate_command(self, context=""):
        """Generate a penetration testing command based on prior actions."""
        prompt = self._construct_prompt(context)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        output = self.model.generate(
            **inputs, 
            max_new_tokens=50, 
            do_sample=True, 
            temperature=0.2, 
            repetition_penalty=1.2,
            pad_token_id=self.tokenizer.eos_token_id
        )
        generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True)
        print("generated_text : ",generated_text)
        return self._extract_command(generated_text)
    
    def _construct_prompt(self, context):
        """Constructs the input prompt with history."""
        if context:
            return (
                "You are assisting in penetration testing via SSH on Kali Linux. "
                "You have to perform the penetration test on 192.168.122.0/24 subnet."
                f"Here is a history of all actions taken and their outputs:\n{context}\n\n"
                    "What is the next logical command to run? "
                    "Generate ONLY ONE NEW COMMAND within <CMD></CMD> tags.")
        return ("You are assisting in penetration testing via SSH on Kali Linux. "
                "You have to perform the penetration test on 192.168.122.0/24 subnet. You have the Access to 192.168.122.12, password is ubuntu and user is root"
                "Assume you are running commands on kali machine, perform pentest on the network and gather flags"
                "Generate a single valid Linux command. "
                "Return only the command enclosed within <CMD></CMD>.")
    
    def _extract_command(self, llm_output):
        """Extract a command enclosed in <CMD></CMD> tags."""
        llm_output=llm_output.strip()
        #print("llm op is : ", repr(llm_output))
        match = re.findall(r"<CMD>\s*(.*?)\s*</CMD>", llm_output, re.DOTALL)
        #print("match : " ,match)
        return match[1].strip() if match else None
    
    def update_history(self, command, output):
        """Update the history with the executed command and output."""
        self.history += f"\n{command} -> {output}"
    
    def get_history(self):
        """Retrieve the history of executed commands."""
        return self.history
