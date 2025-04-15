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
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=device
        )
        self.history = ""
        self.cot_counter = 1  # Track reasoning steps
        
    def generate_command(self, context=""):
        """Generate command with enhanced CoT handling"""
        for attempt in range(3):  # Add retry mechanism
            prompt = self._construct_prompt(context)
            inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)

            output = self.model.generate(
                **inputs, 
                max_new_tokens=150,  # Increased for better reasoning
                do_sample=True,
                temperature=0.5 if attempt > 0 else 0.3,  # Adjust temperature for retries
                top_p=0.95,
                repetition_penalty=1.25,
                pad_token_id=self.tokenizer.eos_token_id
            )

            generated_text = self.tokenizer.decode(output[0], skip_special_tokens=True).strip()
            command = self._extract_command(generated_text)
            
            if command and self._validate_cot_structure(generated_text):
                return command
            context += "\n[System] Please format your response with explicit numbered reasoning steps followed by a single <CMD> command"

        logging.error("Failed to generate valid CoT response")
        return None
    
    def _construct_prompt(self, context):
        """Enhanced CoT prompt with structured examples"""
        cot_example = (
            "Example of valid response:\n"
            "1. First identify open ports using basic scan\n"
            "2. Check for web server vulnerabilities\n"
            "3. Select appropriate scanning tool\n"
            "<CMD>nmap -sV 192.168.1.1</CMD>\n\n"
        )
        
        base_prompt = (
            f"You are a penetration testing expert. Analyze the scenario and:\n"
            f"1. List numbered reasoning steps (3-5 steps)\n"
            f"2. Provide EXACTLY ONE command in <CMD></CMD>\n"
            f"{cot_example}"
            f"Current context:\n{self.history[-1000:]}\n{context}\n"
            f"Thinking process:"
        )
        return base_prompt
        
    def _extract_command(self, llm_output):
        """Enhanced CoT validation and extraction"""
        # Check for proper CoT structure before extracting command
        if re.search(r'\n\d+\.\s+.+', llm_output):
            matches = re.findall(r"<CMD>\s*(.*?)\s*</CMD>", llm_output, re.DOTALL)
            if matches:
                return matches[-1].strip()
        return None

    def _validate_cot_structure(self, text):
        """Validate proper chain-of-thought formatting"""
        return bool(
            re.search(r'\n1\.\s+.+\n2\.\s+.+', text) and  # At least two reasoning steps
            re.search(r'<CMD>.*</CMD>', text)  # Command present
        )
    
    def update_history(self, command, output):
        """Update history with CoT-aware formatting"""
        self.history += f"\n[Command] {command}\n[Output] {output[:200]}"
    
    def get_history(self):
        """Retrieve the history of executed commands."""
        return self.history