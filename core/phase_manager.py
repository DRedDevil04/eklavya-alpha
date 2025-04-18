class PhaseManager:
    def __init__(self):
        """Initialize the phases and set the starting phase."""
        self.phases = ["Enumeration", "Exploration", "Privilege Escalation"]
        self.current_index = 0

    def get_phase(self):
        """Return the current phase."""
        return self.phases[self.current_index]

    def check_transition(self, todo_manager):
        """
        Check if transition to the next phase is possible based on pending tasks
        and completion of phase-specific goals.
        """
        if not hasattr(todo_manager, 'get_pending_tasks'):
            raise ValueError("todo_manager must have a method 'get_pending_tasks'.")

        pending_tasks = todo_manager.get_pending_tasks()
        done_tasks = todo_manager.get_done_tasks()

        # Define goal-specific checks for each phase
        phase_goals = {
            "Enumeration": ["Scan open ports for services", "Enumerate HTTP service", "Attempt SSH login on target machine"],
            "Exploration": ["Find file named flag.txt on target machine", "Read contents of flag.txt using cat"],
            # Privilege Escalation goals could be added later
        }

        current_phase = self.get_phase()
        goals = phase_goals.get(current_phase, [])

        # Check if all goals for this phase are completed
        goals_done = all(goal in done_tasks for goal in goals)

        if len(pending_tasks) == 0 and goals_done and self.current_index < len(self.phases) - 1:
            self.current_index += 1
            print(f"[*] Transitioned to next phase: {self.get_phase()}")
            return True
        return False
