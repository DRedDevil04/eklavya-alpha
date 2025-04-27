import json

class TaskReference:
    def __init__(self, task_reference_file='data/task_reference.json'):
        self.task_reference_file = task_reference_file
        self.tasks = {}
        self.load_tasks()

    def load_tasks(self):
        """Load the task reference table from JSON."""
        try:
            with open(self.task_reference_file, 'r') as file:
                self.tasks = json.load(file)
        except FileNotFoundError:
            print(f"[ERROR] Task reference file '{self.task_reference_file}' not found.")
        except json.JSONDecodeError:
            print(f"[ERROR] JSON decode error in the task reference file '{self.task_reference_file}'.")
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred: {e}")

    def get_available_tasks(self, phase):
        """Retrieve tasks based on the current phase."""
        return self.tasks.get(phase, [])

    def get_task_by_category(self, category):
        """Retrieve all tasks within a specific category."""
        return {phase: tasks for phase, tasks in self.tasks.items() if category in tasks}

    def suggest_next_task(self, phase, completed_tasks):
        """Suggest the next task for the given phase by looking at incomplete tasks."""
        available_tasks = self.get_available_tasks(phase)
        remaining_tasks = [task for task in available_tasks if task not in completed_tasks]
        
        # Return the first remaining task, or None if no tasks remain
        return remaining_tasks[0] if remaining_tasks else None

    def print_task_reference(self):
        """Print all tasks for debugging or review."""
        for phase, tasks in self.tasks.items():
            print(f"{phase}: {', '.join(tasks)}")

# Example usage:
if __name__ == "__main__":
    task_ref = TaskReference()
    task_ref.print_task_reference()

    # Assuming 'Enumeration' phase and we completed 'Port Scanning'
    next_task = task_ref.suggest_next_task('Enumeration', ['Port Scanning'])
    if next_task:
        print(f"\nSuggested next task: {next_task}")
    else:
        print("\nNo tasks remaining for the current phase.")