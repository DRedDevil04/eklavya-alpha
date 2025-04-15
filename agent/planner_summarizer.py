import os
import logging
import re
import time
import gc
import torch
from dotenv import load_dotenv
from interface.connector import SSHConnector
from agent.planner.Planner import Planner
from agent.summariser.gpt_summariser import Summarizer

# Free CUDA memory & run garbage collection
torch.cuda.empty_cache()
gc.collect()

# Configure logging
logging.basicConfig(
    filename="pentest_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()

# Initialize SSH session to Kali Linux
try:
    ssh = SSHConnector("192.168.122.186", "kali", "kali")
    ssh.create_ssh_session()
except Exception as e:
    logging.error(f"Failed to establish SSH connection: {e}")
    exit(1)  # Exit if SSH connection fails

# Initialize Planner and Summarizer
planner = Planner()
summarizer = Summarizer()

def execute_penetration_test():
    """Run the penetration testing process iteratively using LLMs."""
    failed_attempts = 0
    max_iterations = 20
    iteration = 0

    while failed_attempts < 3 and iteration < max_iterations:
        iteration += 1
        logging.info(f"Iteration {iteration}")

        # Generate the next command
        for _ in range(3):  # Retry up to 3 times if command generation fails
            planner_response = planner.generate_command(summarizer.get_summary())

            if planner_response and re.match(r"^[a-zA-Z0-9\-\s\./]+$", planner_response.strip()):
                command = planner_response.strip()
                break
            logging.warning("Planner generated an invalid response. Retrying...")
            time.sleep(1)
        else:
            logging.error("Planner failed to generate a valid command after retries.")
            failed_attempts += 1
            continue

        logging.info(f"Generated command: {command}")
        print(f"\n[Generated Command]: {command}")

        try:
            output = ssh.execute_command(command)
            if not output.strip():
                raise RuntimeError("Empty output received.")
        except Exception as e:
            logging.error(f"Command execution failed: {command} | Error: {e}")
            failed_attempts += 1
            continue

        print(f"\n[Command Output]: {output}")

        if re.search(r"FLAG\{.*?\}", output):
            print("\n[FLAG FOUND!]:", output)
            logging.info("FLAG FOUND! Exiting.")
            break

        # Update summary
        summarizer.summarize(command, output)
        logging.info(f"Updated summary: {summarizer.get_summary()}")

        # Free unused memory
        gc.collect()

        time.sleep(1)

    print("\n[Stopping]:", "Maximum iterations reached." if iteration >= max_iterations else "Too many failed attempts.")

# Start the agent
execute_penetration_test()

