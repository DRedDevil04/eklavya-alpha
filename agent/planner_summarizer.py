import os
import logging
import re
import time
import gc
import torch
from dotenv import load_dotenv
from interface.connector import SSHConnector
from agent.planner.Planner import Planner
from agent.summariser.Summariser import Summarizer

torch.cuda.empty_cache()  # Clears the CUDA memory cache
gc.collect()  # Collects garbage to free memory


# Configure logging
logging.basicConfig(
    filename="pentest_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load environment variables
load_dotenv()

# Initialize SSH session to Kali Linux
ssh = SSHConnector("192.168.122.186", "kali", "kali")
ssh.create_ssh_session()

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
        planner_response = planner.generate_command(summarizer.get_summary())

        if not planner_response:
            logging.error("Planner model failed to generate a response.")
            failed_attempts += 1
            continue

        command = planner_response

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

        # Update summary
        summarizer.summarize(command, output)
        logging.info(f"Updated summary: {summarizer.get_summary()}")
        print("\n[Updated Summary]:", summarizer.get_summary())

        time.sleep(1)

    print("\n[Stopping]:", "Maximum iterations reached." if iteration >= max_iterations else "Too many failed attempts.")

# Start the agent
execute_penetration_test()
