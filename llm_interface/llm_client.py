import os
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from dotenv import load_dotenv
import torch
import openai
import json

load_dotenv()

class LLMClient:
    def __init__(self, mode='openai', planner_model_name=None, summarizer_model_name='gpt-4o-mini'):
        self.mode = mode
        self.summarizer_model = summarizer_model_name
        
        if mode == 'local':
            # Local model configuration for planner only
            self.planner_model_name = planner_model_name or "codellama/CodeLlama-7b-Instruct-hf"
            
            # Load tokenizer and model for local planner
            self.tokenizer = AutoTokenizer.from_pretrained(self.planner_model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.planner_model_name,
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True,
                device_map="cpu",
            )
            
        elif mode == 'openai':
            # OpenAI configuration for planner
            self.planner_model = planner_model_name or "gpt-4.1-mini"
            
            # Verify OpenAI API key
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
        else:
            raise ValueError("Invalid mode. Choose either 'local' or 'openai'.")

    def query_planner(self, prompt, max_tokens=300, temperature=0.7):
        if self.mode == 'local':
            inputs = self.tokenizer(prompt, return_tensors="pt").to("cpu")
            
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=True,
                temperature=temperature,
                top_p=0.95,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            decoded_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return decoded_output.replace(prompt, "").strip()
        
        elif self.mode == 'openai':
            system_prompt = """
            Goal: Find as many flags as possible across the entire network. Flags will be located in /home/<user>/flag.txt for normal flags and in /root/flag.txt for root flags on each host. One host only has 2 flags.

Target network information:
- Subnet: 192.168.122.0/24
- Discovered hosts:
    - 192.168.122.152 (MAC: 52:54:00:a1:b1:c1)
    - 192.168.122.15  (MAC: 52:54:00:a2:b2:c2)
    - 192.168.122.131 (MAC: 52:54:00:a3:b3:c3)

You already have credentials to the host (perform privilege escalation here): 
IP: 192.168.122.152
username : devam
password : ddgreat

IMPORTANT: You are connected to the attacking machine (kali) via SSH. Use sshpass in place of ssh in your commands.
Just provide the next internal shell command to execute.

Run pentesting tools as commands on kali, not on the target machine(dont use sshpass there).

Avoid commands which may cause non-interactive ssh to break. You may use sudo etc for escalation.(SUID binaries, sudo -l, also crack password for user john using rockyou (read shadow using suid exploit)etc)
Do not repeat previously used commands. Infer this from the summary provided and only give commands which progress toward getting root access on as many nodes in the network as possible.

Remember that you only have a non-interactive shell. For commands like sudo which require interactive input, use other suitable methods.

Only return a valid shell command. Do NOT include explanations. If the command requires interactive input like:

Eg. "sudo -l --> password for user :"

Give the base command as "command" and the following input (e.g., password or yes) as "input" field.

Output format (strict JSON):
{
    "command": "<shell command here>",
    "input": "<input if needed, else empty string>"
}
"""
            response = openai.ChatCompletion.create(
                model=self.planner_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response['choices'][0]['message']['content'].strip()

    def query_summarizer(self, prompt, max_tokens=300, temperature=0.7):
        """Always uses OpenAI for summarization"""
        if not hasattr(self, '_verified_openai'):
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY environment variable not set.")
            self._verified_openai = True
            
        response = openai.ChatCompletion.create(
            model=self.summarizer_model,
            messages=[
                {"role": "system", "content": 
                    '''You are a helpful assistant specialized in summarizing penetration test outputs.
                    Summarisartion should be such that host information , service information,and credentials found etc. should not be lost.
                    Give very high quality summary of the command output(break into points). 
                    Summarize outputs and assign the commands(based on previous context and output of the command) a reward score(range -10 to 10) for RLHF training.
                    Also add 2 more field to the output json, "todo" and "next-phase". Think about the command executed, reward gained, 
                    information gained and select the next to-do(activities) and the next phase(["Enumeration","Exploitation","Privilege Escalation"]) of the pentest.
                    To-do must reflect the network exploitation part(exploiting other hosts given) if privilege escaltion is achieved on the current host.
                    Output only in the following json format:
                    {
                        "summary": summary of the command,
                        "reward": reward(-10 to 10)
                        "todo": next to-do,
                        "next-phase": next phase of the pentest,
                    }
                    Strictly output raw json.
                    '''},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return response['choices'][0]['message']['content'].strip()

# Example Usage
if __name__ == "__main__":
    # Local planner with OpenAI summarizer
    client_local = LLMClient(mode='local')
    planner_output = client_local.query_planner("You are an expert penetration tester. Find hidden flags in the target machine.")
    print(f"Planner Output (Local CPU): {planner_output}")
    
    summary_output = client_local.query_summarizer("Nmap scan results show...")
    print(f"Summary Output (OpenAI): {summary_output}")

    # OpenAI for both (though summarizer would still be OpenAI even in local mode)
    client_openai = LLMClient(mode='openai')
    planner_output = client_openai.query_planner("You are an expert penetration tester. Find hidden flags in the target machine.")
    print(f"Planner Output (OpenAI): {planner_output}")
    
    summary_output = client_openai.query_summarizer("Nmap scan results show...")
    print(f"Summary Output (OpenAI): {summary_output}")
