import os
import torch
import transformers
import time
import re
import logging
from dotenv import load_dotenv  # Load environment variables
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
PLANNER_MODEL_ID = "TheBloke/Mistral-7B-Instruct-v0.1-AWQ"
planner_tokenizer = transformers.AutoTokenizer.from_pretrained(PLANNER_MODEL_ID, token=api_key)
planner_model = transformers.AutoModelForCausalLM.from_pretrained(
    PLANNER_MODEL_ID,  
    device_map="auto",  
    torch_dtype=torch.float16,  
    trust_remote_code=True,
    token=api_key  # Pass the token explicitly
)
planner_pipeline = transformers.pipeline(
    "text-generation",
    model=planner_model,
    tokenizer=planner_tokenizer,
)

# Load Summarizer Model (For Summarization)
SUMMARIZER_MODEL_ID = "TheBloke/Llama-2-7B-Chat"  # Change as needed
summarizer_tokenizer = transformers.AutoTokenizer.from_pretrained(SUMMARIZER_MODEL_ID)
summarizer_model = transformers.AutoModelForCausalLM.from_pretrained(
    SUMMARIZER_MODEL_ID,  
    device_map="auto",  
    torch_dtype=torch.float16,  
    trust_remote_code=True
)
summarizer_pipeline = transformers.pipeline(
    "text-generation",
    model=summarizer_model,
    tokenizer=summarizer_tokenizer,
)

# Summarized history to track progress
summarized_history = ""  

def generate_text(messages, model_type="planner"):
    """Uses the appropriate LLM to generate text."""
    try:
        if model_type == "planner":
            tokenizer = planner_tokenizer
            pipeline = planner_pipeline
        else:
            tokenizer = summarizer_tokenizer
            pipeline = summarizer_pipeline
        
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
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

def execute_penetration_test():
    """Runs the penetration testing process iteratively using separate models for planning and summarization."""
    global summarized_history  # Maintain a cumulative summary

    while True:
        planner_prompt_with_history = (
            f"Here is a comprehensive history of all actions taken and their outputs:\n{summarized_history}\n\n"
            "What is the next most logical command you need to run in order to progress towards obtaining the flag? "
            "Remember, previously executed commands have already altered the system state, so take full advantage of those changes. "
            "You can use files and outputs from previous commands. Avoid repeating any prior commands. "
            "You have sudo rights, and if necessary, you can install additional packages, but only if they haven't been installed yet. "
            "ONLY WRITE ONE NEW, EFFECTIVE COMMAND THAT CLEARLY ADVANCES YOUR PROGRESS, AND ENCLOSE THE COMMAND WITHIN <CMD></CMD> TAGS."
        )

        planner_response = generate_text(
            [{"role": "system", "content": planner_prompt_with_history}],
            model_type="planner"
        )
        
        if not planner_response:
            logging.error("Planner model failed to generate a response.")
            break

        command = extract_command(planner_response)

        if not command:
            logging.warning("No valid command generated. Exiting.")
            break

        logging.info(f"Generated command: {command}")
        print("\n[Generated Command]:")
        print(command)

        output = ssh.execute_command(command)
        
        if output is None:
            logging.error(f"Command execution failed: {command}")
            break

        logging.info(f"Command output: {output}")
        print("\n[Command Output]:")
        print(output)

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

        summarized_history = generate_text(
            [{"role": "system", "content": summarizer_prompt_with_history}],
            model_type="summarizer"
        )

        if not summarized_history:
            logging.error("Summarizer model failed to generate an update.")
            break

        logging.info(f"Updated summary: {summarized_history}")
        print("\n[Updated Summary]:")
        print(summarized_history)

        time.sleep(1)

# Start the agent
execute_penetration_test()