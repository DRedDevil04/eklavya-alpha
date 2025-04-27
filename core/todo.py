import re
import json

class ToDoManager:
    def __init__(self):
        self.done_tasks = []
        self.pending_tasks = ["SSH on target machine using IP"]  # Initial task list

    def update(self, summary_json):
        """Update the task list based on the summarizer JSON output."""
        try:
            parsed = json.loads(summary_json)
            new_task = parsed.get("todo", "").strip()
            if new_task:
                self.pending_tasks.append(new_task)
        except json.JSONDecodeError:
            print("Warning: Failed to parse summarizer output. Skipping todo update.")
        
        self._mark_task_done()

    def get_pending_tasks(self):
        """Return the list of tasks that are yet to be done."""
        return self.pending_tasks

    def get_done_tasks(self):
        """Return the list of tasks that have been completed."""
        return self.done_tasks

    def is_complete(self):
        """Check if all tasks are complete."""
        return len(self.pending_tasks) == 0  # If no tasks are left, it's complete

    def _mark_task_done(self):
        """Move the first pending task to done tasks."""
        if self.pending_tasks:
            task = self.pending_tasks.pop(0)
            self.done_tasks.append(task)
