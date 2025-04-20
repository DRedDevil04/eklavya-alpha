# import os
# from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
# from dotenv import load_dotenv
# import torch
# import openai

# load_dotenv()

# class LLMClient:
#     def __init__(self, mode='local', planner_model_name=None, summarizer_model_name=None):
#         self.mode = mode
#         self.planner_model_name = planner_model_name or "codellama/CodeLlama-7b-Instruct-hf"
        
#         if mode == 'local':
#             # Load tokenizer
#             self.tokenizer = AutoTokenizer.from_pretrained(self.planner_model_name)
            
#             # Load model with CPU optimizations
#             self.model = AutoModelForCausalLM.from_pretrained(
#                 self.planner_model_name,
#                 torch_dtype=torch.float16,       # FP16 for memory efficiency
#                 low_cpu_mem_usage=True,          # Prevents memory spikes
#                 device_map="cpu",                # Force CPU-only
#             )
            
#             # Alternative: 8-bit quantization (even lower memory)
#             # self.model = AutoModelForCausalLM.from_pretrained(
#             #     self.planner_model_name,
#             #     load_in_8bit=True,               # 8-bit quantization
#             #     device_map="cpu",
#             # )
            
#         elif mode == 'openai':
#             openai.api_key = os.getenv("OPENAI_API_KEY")
#             if not openai.api_key:
#                 raise ValueError("OPENAI_API_KEY environment variable not set.")

#     # def query_planner(self, prompt, max_tokens=150, temperature=0.7):
#     #     """Generate a response using the local model (CPU-optimized)."""
#     #     if self.mode == 'local':
#     #         inputs = self.tokenizer(prompt, return_tensors="pt").to("cpu")
            
#     #         outputs = self.model.generate(
#     #             **inputs,
#     #             max_new_tokens=max_tokens,
#     #             do_sample=True,
#     #             temperature=temperature,
#     #             top_p=0.95,
#     #             pad_token_id=self.tokenizer.eos_token_id
#     #         )
            
#     #         decoded_output = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
#     #         return decoded_output.replace(prompt, "").strip()
        
#     #     else:
#     #         raise ValueError("Planner is only available in 'local' mode.")

#     def query_planner(self, prompt):
#         if self.mode == 'openai':
#             response = openai.ChatCompletion.create(
#                 model="gpt-4.1-mini",
#                 messages=[
#                     {"role": "system", "content": "You are a helpful assistant."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=200,
#                 temperature=0.7
#             )
#             return response['choices'][0]['message']['content']

#     def query_summarizer(self, prompt, max_tokens=300, temperature=0.7):
#         """Query OpenAI for summarization."""
#         if self.mode == 'openai':
#             response = openai.chat.completions.create(
#                 model="gpt-4o-mini",  # or "gpt-4"
#                 messages=[
#                     {"role": "system", "content": "You are a helpful assistant specialized in summarizing penetration test outputs."},
#                     {"role": "user", "content": prompt}
#                 ],
#                 max_tokens=max_tokens,
#                 temperature=temperature
#             )
#             return response.choices[0].message.content.strip()
#         else:
#             raise ValueError("Summarizer is only available in 'openai' mode.")

# # Example Usage
# if __name__ == "__main__":
#     # Local CPU mode (optimized)
#     client = LLMClient(mode='local')
#     planner_output = client.query_planner("You are an expert penetration tester. Find hidden flags in the target machine.")
#     print(f"Planner Output (Local CPU): {planner_output}")

#     # OpenAI mode (if API key is set)
#     # client_openai = LLMClient(mode='openai')
#     # summary = client_openai.query_summarizer("Summarize the following findings...")
#     # print(f"Summary (OpenAI): {summary}")


import os
import openai
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class LLMClient:
    def __init__(self, mode='openai', planner_model_name=None, summarizer_model_name=None):
        self.mode = mode
        # Set default models
        self.planner_model = planner_model_name or "gpt-4.1-mini"
        self.summarizer_model = summarizer_model_name or "gpt-4o-mini"

        if self.mode != 'openai':
            raise ValueError("Only 'openai' mode is supported in this version.")

        # Set OpenAI API key from the environment
        openai.api_key = os.getenv("OPENAI_API_KEY")
        if not openai.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")

    def query_planner(self, prompt, max_tokens=300, temperature=0.7):
        # Use the correct method name for OpenAI's Chat API
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
        # Use the correct method name for OpenAI's Chat API
        response = openai.ChatCompletion.create(
            model=self.summarizer_model,
            messages=[
                {"role": "system", "content": 
                    ''' You are a helpful assistant specialized in summarizing penetration test outputs. 
                        Summarize outputs and assign the commands(based on previous context and output of the command) a reward score(range -10 to 10) for RLHF training .
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
