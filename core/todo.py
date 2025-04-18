import re

class ToDoManager:
    def __init__(self):
        self.done_tasks = []
        self.pending_tasks = ["SSH on target machine using IP"]  # Initial task list

    def update(self, summary):
        """Update the task list based on new information in the summary."""
        if any(keyword in summary.lower() for keyword in ["discovered", "found", "detected", "identified"]):
            new_tasks = self._extract_tasks(summary)
            self.pending_tasks.extend(new_tasks)  # Add new tasks if applicable
        self._mark_current_as_done()  # Mark the current task as done

    def get_pending_tasks(self):
        """Return the list of tasks that are yet to be done."""
        return self.pending_tasks

    def get_done_tasks(self):
        """Return the list of tasks that have been completed."""
        return self.done_tasks

    def is_complete(self):
        """Check if all tasks are complete."""
        return len(self.pending_tasks) == 0  # If no tasks are left, it's complete

    def _mark_current_as_done(self):
        """Move the first pending task to done tasks."""
        if self.pending_tasks:  # Prevent popping from an empty list
            task = self.pending_tasks.pop(0)
            self.done_tasks.append(task)

    def _extract_tasks(self, summary):
        """Extract tasks from the summary. Replace with more advanced logic if needed."""
        tasks = []
        summary = summary.lower()

        if "open port" in summary:
            tasks.append("Scan open ports for services")
        if "http" in summary:
            tasks.append("Enumerate HTTP service")
        if "ftp" in summary:
            tasks.append("Check for anonymous FTP access")
        if "ssh" in summary:
            tasks.append("Attempt SSH login on target machine")
        if "flag.txt" in summary or "flag" in summary:
            tasks.append("Find file named flag.txt on target machine")
            tasks.append("Read contents of flag.txt using cat")

        return tasks
