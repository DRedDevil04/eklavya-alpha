import os
import torch
import time
import re
import logging
import openai
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, BitsAndBytesConfig
from interface.connector import SSHConnector

# Load API Keys from .env file
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Set Hugging Face API Key from .env
api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = api_key

# Configure logging
logging.basicConfig(
    filename="pentest_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Initialize SSH session to Kali Linux
ssh = SSHConnector("192.168.122.186", "kali", "kali")
ssh.create_ssh_session()

# Load Mistral 7B Model for Planning
PLANNER_MODEL_ID = "codellama/CodeLlama-7B-Instruct-hf"

# bnb_config = BitsAndBytesConfig(
#     load_in_4bit=True,
#     bnb_4bit_compute_dtype=torch.float16,  # Ensures 16-bit precision
#     bnb_4bit_use_double_quant=True
# )

planner_tokenizer = AutoTokenizer.from_pretrained(PLANNER_MODEL_ID, token=api_key)

planner_model = AutoModelForCausalLM.from_pretrained(
    PLANNER_MODEL_ID,
    device_map="auto",  # Auto-assign to GPU or CPU
   # quantization_config=bnb_config
)

planner_pipeline = pipeline(
    "text-generation",
    model=planner_model,
    tokenizer=planner_tokenizer,
    max_new_tokens=150,
    do_sample=False,
    pad_token_id=planner_tokenizer.eos_token_id
)

summarized_history = ""

def generate_text(messages, model_type="planner"):
    """Generate text using Mistral 7B for planning."""
    try:
        if model_type == "planner":
            prompt = messages[0]["content"]
            outputs = planner_pipeline(prompt, max_new_tokens=200, do_sample=False)
            return outputs[0]["generated_text"][len(prompt):].strip() if outputs else None
    except Exception as e:
        logging.error(f"Error generating text for {model_type}: {e}")
        return None

def summarize_text_with_openai(text):
    """Summarize penetration testing command history using OpenAI API."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",  # Fixed incorrect model name
            messages=[
                {"role": "system", "content": "You are a cybersecurity expert summarizing penetration testing actions."},
                {"role": "user", "content": f"Summarize this penetration testing command history:\n{text}"}
            ],
            max_tokens=300,
            temperature=0.2
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logging.error(f"OpenAI API Error: {e}")
        return None

def extract_command(llm_output):
    """Extract a valid command enclosed in <CMD></CMD> tags."""
    match = re.search(r"<CMD>(.*?)</CMD>", llm_output, re.DOTALL)
    return match.group(1).strip() if match else None

def is_valid_command(command):
    """Check if the command is valid."""
    return bool(command)

def execute_penetration_test():
    """Run the penetration testing process iteratively using Mistral 7B and OpenAI API."""
    global summarized_history

    failed_attempts = 0
    max_iterations = 20
    iteration = 0

    while failed_attempts < 3 and iteration < max_iterations:
        iteration += 1
        logging.info(f"Iteration {iteration}")

        planner_prompt_with_history = (
            f"Here is a history of all actions taken and their outputs:\n{summarized_history}\n\n"
            "What is the next logical command to run to progress towards obtaining the flag? "
            "Consider the system state from prior commands and avoid repetition. "
            "You have sudo rights and can install packages if needed. "
            "Generate ONLY ONE NEW COMMAND within <CMD></CMD> tags."
        ) if summarized_history else (
            "You are assisting in penetration testing via SSH on Kali Linux. "
            "Generate a single valid Linux command for finding and attacking hosts. "
            "Only return a raw bash command—NO explanations, markdown, or placeholders. "
            "The first infected node IP is 192.168.122.12, with root password 'ubuntu'. "
            "SSH into 192.168.122.12 as root using the password 'ubuntu'. "
            "Return only the command enclosed within <CMD></CMD>."
        )

        planner_response = generate_text(
            [{"role": "system", "content": planner_prompt_with_history}],
            model_type="planner"
        )

        if not planner_response:
            logging.error("Planner model failed to generate a response.")
            failed_attempts += 1
            continue

        command = extract_command(planner_response)

        if not command or not is_valid_command(command):
            logging.warning("No valid command generated. Retrying...")
            failed_attempts += 1
            continue

        logging.info(f"Generated command: {command}")
        print(f"\n[Generated Command]: {command}")

        output = ssh.execute_command(command)

        if not output:
            logging.error(f"Command execution failed: {command}")
            failed_attempts += 1
            continue

        print(f"\n[Command Output]: {output}")

        if re.search(r"FLAG\{.*?\}", output):
            print("\n[FLAG FOUND!]:", output)
            logging.info("FLAG FOUND! Exiting.")
            break

        summarizer_prompt_with_history = (
            "Summarize the history of actions and outputs in detail, including every command run and any changes made.\n"
            f"Current Summary: {summarized_history}\n"
            f"Latest Action and Output: {command} -> {output}\n"
            "Expand the summary to include this new information."
        )

        new_summary = summarize_text_with_openai(summarizer_prompt_with_history)

        if not new_summary:
            logging.error("Summarizer model failed to generate an update.")
            failed_attempts += 1
            continue

        summarized_history = new_summary
        logging.info(f"Updated summary: {summarized_history}")
        print("\n[Updated Summary]:", summarized_history)

        time.sleep(1)

    print("\n[Stopping]:", "Maximum iterations reached." if iteration >= max_iterations else "Too many failed attempts.")

# Start the agent
execute_penetration_test()
