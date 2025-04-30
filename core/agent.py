import logging
import torch
import gc
import re
from core.planner import Planner
from core.summarizer import Summarizer
from core.todo import ToDoManager
from core.memory import MemoryManager
from core.phase_manager import PhaseManager
from interface.connector import SSHConnector
from core.task_reference import TaskReference
from trainer.ppo_trainer import RLHFTrainer
from log.logger import log
from validation.summarisation import evaluate_summary

torch.cuda.empty_cache()
gc.collect()

class PenTestAgent:
    def __init__(self,ip= "192.168.122.152", username="devam", password="ddgreat", train=False):
        """Initialize the PenTestAgent with required components."""
        # Connection to attacker machine
        self.ssh = SSHConnector("192.168.122.186", "kali", "kali")
        self.ssh.create_ssh_session()

        # Target info (victim machine)
        self.target_ip = ip
        self.target_username = username 
        self.target_password = password 

        self.planner = Planner()
        self.summarizer = Summarizer()
        self.todo = ToDoManager()
        self.memory = MemoryManager()
        self.phase = PhaseManager()
        self.task_reference = TaskReference()
        self.train = train
        self.summary = ""
        self.flags = set()
        self.command_count = 0
        # Adding SSH login to the ToDo list as the first task
        self.todo.update(f"SSH into target machine at {self.target_ip}.")

    def flag_found(self, text):
        """Check if the flag is found in the text (output or summary)."""
        # Regex pattern to match flag format
        match=re.search(r"flag\{.*?\}", text, re.IGNORECASE)
        if match:
            flag = match.group()  # Extract matched flag like 'flag{secret_value}'
            self.flags.add(flag)
        return bool(match)

    def run(self):
        log("[+] Starting penetration test agent...", color="green")

        # Check if SSH is connected first
        while len(self.flags) < 6 and self.command_count < 20:
            # Ensure SSH connection is established before proceeding
            if any("SSH into target machine" in task for task in self.todo.get_pending_tasks()):
                log("[>] Establishing SSH connection to target machine...", color="yellow")
                self.ssh.create_ssh_session()
                if not self.ssh.is_connected():
                    print("[!] SSH connection failed. Exiting test.")
                    return

                # Mark SSH connection task as done
                self.todo._mark_task_done(f"SSH into target machine at {self.target_ip}.")
                self.todo.update("SSH connection established.")
                log(f"[+] Updated ToDo list: {self.todo.get_pending_tasks()}", color="blue")  # Print the ToDo list after SSH

            current_phase = self.phase.get_phase()
            context = self.memory.retrieve_relevant_context(current_phase)
            planned_command, planned_input = self.planner.plan_next_step(
                current_phase=current_phase,
                context_summary=self.summary,
                todo_list=self.todo.get_pending_tasks(),
                target_ip=self.target_ip,
                username=self.target_username,
                password=self.target_password,
                memory=self.memory,
                task_reference=self.task_reference
            )

            if not planned_command:
                # Use TaskReference to get fallback task
                completed_tasks = self.todo.get_done_tasks()
                fallback_task = self.task_reference.suggest_next_task(current_phase, completed_tasks)
                if fallback_task:
                    log(f"[*] Using fallback task: {fallback_task}", color="yellow")
                    planned_command, planned_input = self.planner.nudge_with_task(fallback_task, current_phase)
                else:
                    log("[!] No tasks available. Ending test.", color="red")
                    break

            # Execute the planned command via SSH
            log(f"[>] Running command: {planned_command}", color="yellow")
            self.command_count += 1
            log(f"[>] Input data: {planned_input}", color="yellow")  # Debug the input data
            output = self.ssh.execute_command(planned_command, input_data=planned_input)
            log(f"[<] Command output: {output}", color="cyan")  # Debug the command output

            if output == "":
                log("[!] No output from the command. This might indicate a problem with SSH or the target machine.", color="red")

            # Summarize the command output
            summary = self.summarizer.summarize_command_output(planned_command, output, context,current_phase)
            self.summary=summary
            log(f"[+] Summary: {summary}", color="blue")  # Debug summary output
            
            # Evaluate the summary and store it in memory
            evaluate_summary(self.command_count, planned_command, summary)

            # Check for flag
            if self.flag_found(output) or self.flag_found(summary):
                log(f"[!!!] FLAG FOUND! 🎯\n\n{summary}", color="green")
                self.memory.store(summary, planned_command, output)

            # Update todo list with new tasks from the summary
            self.todo.update(summary)  # Assuming your new ToDoManager has an extract_and_add_tasks method
            self.phase.update_phase(summary)  # Update the phase based on the summary
            log(f"[+] Updated ToDo list: {self.todo.get_pending_tasks()}", color="blue")  # Print the updated ToDo list

            # Update memory with new summary, command, and output
            self.memory.store(summary, planned_command, output)

            log(f"[+] Completed tasks: {self.todo.get_done_tasks()}", color="green")  # Debug the completed task

        log("[+] Penetration test complete.", color="green")

    # def setup_training(self):
    #     self.trainer = RLHFTrainer(model=self.planner.llm.model, tokenizer=self.planner.llm.tokenizer)

    def step_train(self):
        pass

# Example usage
if __name__ == "__main__":
    try:
        agent = PenTestAgent()
        agent.run()
    except Exception as e:
        logging.error(f"Error during penetration testing: {e}")
