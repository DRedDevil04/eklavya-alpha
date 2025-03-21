import os
import torch
import transformers
import time
import re
import logging
from dotenv import load_dotenv
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from interface.connector import SSHConnector

# Configure logging
logging.basicConfig(
    filename="pentest_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load .env file
load_dotenv()

# Set Hugging Face API Key from .env
api_key = os.getenv("HUGGINGFACEHUB_API_TOKEN")
os.environ["HUGGINGFACEHUB_API_TOKEN"] = api_key

# Initialize SSH session to Kali Linux
ssh = SSHConnector("192.168.122.186", "kali", "kali")
ssh.create_ssh_session()

# Load Planner Model (For Generating Commands)
PLANNER_MODEL_ID = "codellama/CodeLlama-7B-Instruct-hf"
planner_tokenizer = AutoTokenizer.from_pretrained(PLANNER_MODEL_ID)
planner_model = AutoModelForCausalLM.from_pretrained(
    PLANNER_MODEL_ID,
    device_map="cpu",
    torch_dtype=torch.float16,
    offload_folder="offload"
)

# Define pipeline for text generation
planner_pipeline = pipeline(
    "text-generation",
    model=planner_model,
    tokenizer=planner_tokenizer,
    max_new_tokens=150,
    do_sample=True,
    temperature=0.7,
    top_p=0.9,
    pad_token_id=planner_tokenizer.eos_token_id  # Avoid padding issues
)

# Load Summarizer Model (For Summarization)
SUMMARIZER_MODEL_ID = "facebook/bart-large-cnn"
summarizer_tokenizer = AutoTokenizer.from_pretrained(SUMMARIZER_MODEL_ID,token=api_key)
summarizer_model = AutoModelForCausalLM.from_pretrained(
    SUMMARIZER_MODEL_ID,
    device_map="cpu",
    torch_dtype=torch.float16,
    offload_folder="offload",
    token=api_key
)

summarizer_pipeline = pipeline(
    "text-generation",
    model=summarizer_model,
    tokenizer=summarizer_tokenizer,
    max_new_tokens=300,
    do_sample=True,
    temperature=0.7,
    top_p=0.9
)

# Summarized history to track progress
summarized_history = ""

def generate_text(messages, model_type="planner"):
    """Uses the appropriate LLM to generate text."""
    try:
        pipeline = planner_pipeline if model_type == "planner" else summarizer_pipeline

        prompt = messages[0]["content"]
        outputs = pipeline(
            prompt,
            max_new_tokens=200,
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
        )
        return outputs[0]["generated_text"][len(prompt):].strip()
    except Exception as e:
        logging.error(f"Error generating text for {model_type}: {e}")
        return None

def extract_command(llm_output):
    """Extracts a valid command enclosed in <CMD></CMD> tags."""
    match = re.search(r"<CMD>(.*?)</CMD>", llm_output, re.DOTALL)
    return match.group(1).strip() if match else None

def is_valid_command(command):
    """Checks if the command is valid and safe to execute."""
    if not command:
        return False
    # Add additional checks for dangerous commands if needed
    return True

def execute_penetration_test():
    """Runs the penetration testing process iteratively using separate models for planning and summarization."""
    global summarized_history  # Maintain a cumulative summary

    failed_attempts = 0  # Track failed command generations
    max_iterations = 20  # Prevent infinite loops
    iteration = 0

    while failed_attempts < 3 and iteration < max_iterations:
        iteration += 1
        logging.info(f"Iteration {iteration}")

        if summarized_history:
            planner_prompt_with_history = (
                f"Here is a comprehensive history of all actions taken and their outputs:\n{summarized_history}\n\n"
                "What is the next most logical command you need to run in order to progress towards obtaining the flag? "
                "Remember, previously executed commands have already altered the system state, so take full advantage of those changes. "
                "You can use files and outputs from previous commands. Avoid repeating any prior commands. "
                "You have sudo rights, and if necessary, you can install additional packages, but only if they haven't been installed yet. "
                "ONLY WRITE ONE NEW, EFFECTIVE COMMAND THAT CLEARLY ADVANCES YOUR PROGRESS, AND ENCLOSE THE COMMAND WITHIN <CMD></CMD> TAGS."
            )
        else:
            planner_prompt_with_history = (
                "You are an AI assisting in penetration testing. You have SSH access to a Kali machine. "
                "Generate a single valid Linux command to find and attack hosts accordingly. "
                "Only return a bash command that can be executed directly on Kali Linux. "
                "Do not include explanations or additional text. "
                "Do not use placeholders like 'ip'—find everything out as an attacker would. "
                "The first infected node IP is 192.168.122.12, and its root password is 'ubuntu'. "
                "I need to ssh from kali to another ubuntu machine with user 'root' having IP :192.168.122.12 and password 'ubuntu'. "
                "Do not use markdown formatting, code blocks, or any explanations. Only output the raw command."
                "REMOVE MARKDOWN FORMATTING IN FINAL OUTPUT, GIVE ONLY RAW COMMAND"
                "ONLY WRITE ONE NEW, EFFECTIVE COMMAND THAT CLEARLY ADVANCES YOUR PROGRESS, AND ENCLOSE THE COMMAND WITHIN <CMD></CMD> TAGS."
            )

        planner_response = generate_text(
            [{"role": "system", "content": planner_prompt_with_history}],
            model_type="planner"
        )

        if not planner_response:
            logging.error("Planner model failed to generate a response.")
            failed_attempts += 1
            continue

        print(planner_response)

        command = extract_command(planner_response)

        if not command or not is_valid_command(command):
            logging.warning("No valid command generated. Retrying...")
            failed_attempts += 1
            continue

        logging.info(f"Generated command: {command}")
        print("\n[Generated Command]:")
        print(command)

        output = ssh.execute_command(command)

        if not output:
            logging.error(f"Command execution failed: {command}")
            failed_attempts += 1
            continue
        print(output)

        # Reset failed_attempts on successful command execution
        failed_attempts = 0

        logging.info(f"Command output: {output}")
        print("\n[Command Output]:")
        print(output)

        # Stop if FLAG is found
        if re.search(r"FLAG\{.*?\}", output):
            print("\n[FLAG FOUND!]:")
            print(output)
            logging.info("FLAG FOUND! Exiting.")
            break

        summarizer_prompt_with_history = (
            "You are building a comprehensive history of all actions and their outputs. "
            "Your summary should be detailed, including every command run, its output, and any changes or files created. "
            "This summary will be used to guide the planning of the next command, so it must include all critical information "
            "without omitting any important details.\n"
            f"Current Summary: {summarized_history}\n"
            f"Latest Action and Output: {command} -> {output}\n"
            "Expand the current summary by incorporating the new information into the complete history of actions and outputs. "
            "Ensure that each step is clear and nothing essential is missed. This summary should fully support the planning of the next step by providing all necessary context."
        )

        new_summary = generate_text(
            [{"role": "system", "content": summarizer_prompt_with_history}],
            model_type="summarizer"
        )

        if not new_summary:
            logging.error("Summarizer model failed to generate an update.")
            failed_attempts += 1
            continue

        summarized_history = new_summary
        logging.info(f"Updated summary: {summarized_history}")
        print("\n[Updated Summary]:")
        print(summarized_history)

        time.sleep(1)  # Prevent API overuse

    if iteration >= max_iterations:
        print("\n[Stopping]: Maximum iterations reached.")
    else:
        print("\n[Stopping]: Too many failed attempts.")


# Start the agent
execute_penetration_test()