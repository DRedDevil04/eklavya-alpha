import os
import logging
import torch
from transformers import AutoTokenizer, pipeline
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename="pentest_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load .env file
load_dotenv()

# Load Summarizer Model
class Summarizer:
    def __init__(self, model_id="codellama/CodeLlama-7B-Instruct-hf"):
        """Initialize the summarizer model."""
        self.device = torch.device("cpu")  # Ensuring it runs on CPU
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.pipeline = pipeline(
            "summarization",
            model=model_id,
            device=-1  # Ensure it runs on CPU
        )
        self.history_summary = ""
    
    def summarize(self, command, output):
        """Summarize penetration testing history, including the latest command and output."""
        prompt = (
            "Summarize the history of actions and outputs in detail, including every command run and any changes made.\n"
            "Summarize so that it is helpful for making decisions based on this summary."
            f"Current Summary: {self.history_summary}\n"
            f"Latest Action and Output: {command} -> {output}\n"
            "Expand the summary to include this new information."
        )
        
        try:
            summary_output = self.pipeline(prompt, max_length=600, min_length=50, do_sample=False)
            print("Summary OP: ", summary_output)
            new_summary = summary_output[0]['summary_text'] if summary_output else ""
            
            if new_summary:
                self.history_summary = new_summary
                logging.info(f"Updated summary: {self.history_summary}")
            
            return self.history_summary
        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            return self.history_summary
    
    def get_summary(self):
        """Retrieve the current summarized history."""
        return self.history_summary
