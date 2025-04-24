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
            response = openai.ChatCompletion.create(
                model=self.planner_model,
                messages=[
                    {"role": "system", "content": "You are an expert penetration tester."},
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
                    Summarize outputs and assign the commands(based on previous context and output of the command) a reward score(range -10 to 10) for RLHF training.
                    Output only in the following json format:
                    {
                        "summary": summary of the command,
                        "reward": reward(-10 to 10)
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