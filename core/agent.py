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
from core.task_reference import TaskReference as get_fallback_task
from trainer.ppo_trainer import RLHFTrainer

torch.cuda.empty_cache()
gc.collect()

class PenTestAgent:
    def __init__(self, train=False):
        """Initialize the PenTestAgent with required components."""
        # Connection to attacker machine
        self.ssh = SSHConnector("192.168.122.186", "kali", "kali")
        self.ssh.create_ssh_session()

        # Target info (victim machine)
        self.target_ip = "192.168.122.12"
        self.target_username = "root"
        self.target_password = "ubuntu"

        self.planner = Planner()
        self.summarizer = Summarizer()
        self.todo = ToDoManager()
        self.memory = MemoryManager()
        self.phase = PhaseManager()
        self.train = train
        # Adding SSH login to the ToDo list as the first task
        self.todo.update(f"SSH into target machine at {self.target_ip}.")

    def flag_found(self, text):
        """Check if the flag is found in the text (output or summary)."""
        return bool(re.search(r"flag\{.*?\}", text, re.IGNORECASE))

    def run(self):
        print("[+] Starting penetration test agent...")

        # Check if SSH is connected first
        while not self.todo.is_complete() or not self.flag_found(""):
            # Ensure SSH connection is established before proceeding
            if "SSH into target machine" in self.todo.get_pending_tasks():
                print("[>] Establishing SSH connection to target machine...")
                self.ssh.create_ssh_session()
                if not self.ssh.is_connected():
                    print("[!] SSH connection failed. Exiting test.")
                    return

                # Mark SSH connection task as done
                self.todo.update("SSH connection established.")
                print(f"[+] Updated ToDo list: {self.todo.get_pending_tasks()}")  # Print the ToDo list after SSH

            current_phase = self.phase.get_phase()
            context = self.memory.retrieve_relevant_context(current_phase)

            prompt,planned_command = self.planner.plan_next_step(
                current_phase=current_phase,
                context_summary=context,
                todo_list=self.todo.get_pending_tasks(),
                target_ip=self.target_ip,
                username=self.target_username,
                password=self.target_password
            )

            if not planned_command:
                fallback_task = get_fallback_task(current_phase, self.todo.get_done_tasks())
                if fallback_task:
                    print(f"[*] Using fallback task: {fallback_task}")
                    planned_command = self.planner.nudge_with_task(fallback_task)
                else:
                    print("[!] No tasks available. Ending test.")
                    break

            # Execute the planned command via SSH
            print(f"[>] Running command: {planned_command}")
            output = self.ssh.execute_command(planned_command)
            print(f"[<] Command output: {output}")  # Debug the command output

            if output == "":
                print("[!] No output from the command. This might indicate a problem with SSH or the target machine.")
            
            # Summarize the command output
            summary = self.summarizer.summarize_command_output(planned_command, output, context)
            print(f"[+] Summary: {summary}")  # Debug summary output

            # Check for flag
            if self.flag_found(output) or self.flag_found(summary):
                print(f"[!!!] FLAG FOUND! 🎯\n\n{summary}")
                self.memory.store(summary, planned_command, output)
                break

            # Update todo list with new tasks from the summary
            self.todo.update(summary)  # Update with any new tasks discovered
            print(f"[+] Updated ToDo list: {self.todo.get_pending_tasks()}")  # Print the updated ToDo list

            # Update memory with new summary, command, and output
            self.memory.store(summary, planned_command, output)

            # Check for phase transition
            self.phase.check_transition(self.todo)

            print(f"[+] Completed task: {self.todo.get_done_tasks()[-1]}")  # Debug the completed task

        print("[+] Penetration test complete.")


        def setup_training(self):
            self.trainer = RLHFTrainer(model = self.planner.llm.model, tokenizer = self.planner.llm.tokenizer)
        
        def step_train(self):
            pass
        

# Example usage
if __name__ == "__main__":
    try:
        agent = PenTestAgent()
        agent.run()
    except Exception as e:
        logging.error(f"Error during penetration testing: {e}")
