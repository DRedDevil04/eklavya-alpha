import logging
import torch
import gc
from core.planner import Planner
from core.summarizer import Summarizer
from core.todo import ToDoManager
from core.memory import MemoryManager
from core.phase_manager import PhaseManager
from interface.connector import SSHConnector
from core.task_reference import TaskReference as get_fallback_task

torch.cuda.empty_cache()
gc.collect()

class PenTestAgent:
    def __init__(self):
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

    def run(self):
        print("[+] Starting penetration test agent...")

        while not self.todo.is_complete():
            current_phase = self.phase.get_phase()
            context = self.memory.retrieve_relevant_context(current_phase)

            planned_command = self.planner.plan_next_step(
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
            output = self.ssh.execute_command(planned_command)

            # Summarize the command output
            summary = self.summarizer.summarize_command_output(planned_command, output, context)

            # Update todo and memory
            self.todo.update(summary)
            self.memory.store(summary, planned_command, output)

            # Check for phase transition
            self.phase.check_transition(self.todo)

        print("[+] Penetration test complete.")


# Example usage
if __name__ == "__main__":
    try:
        agent = PenTestAgent()
        agent.run()
    except Exception as e:
        logging.error(f"Error during penetration testing: {e}")
