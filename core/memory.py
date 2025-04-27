import os
import json
from datetime import datetime

class MemoryManager:
    def __init__(self, session_dir="data/sessions"):
        """Initializes a new session and prepares the memory file."""
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_path = os.path.join(session_dir, self.session_id)
        os.makedirs(self.session_path, exist_ok=True)
        self.memory_file = os.path.join(self.session_path, "memory.json")
        self.memory = self._load_memory()  # Load existing memory if it exists

    def _load_memory(self):
        """Load memory from the file if it exists, otherwise initialize an empty list."""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading memory file: {e}")
                return []  # Return an empty memory if loading fails
        return []

    def store(self, summary, command, output):
        """Store a new memory entry with the command, output, and updated summary."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "command": command,
            "output": output,
            "summary": summary
        }
        self.memory.append(entry)
        self._save_memory()

    def get_executed_commands_by_phase(self, phase):
        """Retrieve all summaries that are relevant to the given phase."""
        # Enhance this with more specific filtering if needed
        relevant_entries = [
            entry["summary"] for entry in self.memory if phase.lower() in entry["summary"].lower()
        ]
        return relevant_entries

    def get_previous_context(self):
        """Retrieve the latest memory entry's command and output."""
        if self.memory:
            latest_entry = self.memory[-1]
            return f'{latest_entry["command"]}: {latest_entry["output"]}'
        return None

    def retrieve_relevant_context(self,phase):
        """Return a list of unique commands executed during the given phase."""
        return list({
            entry["command"] 
            for entry in self.memory 
        })

    def _save_memory(self):
        """Save the current memory to the JSON file."""
        try:
            with open(self.memory_file, "w") as f:
                json.dump(self.memory, f, indent=4)
        except IOError as e:
            print(f"Error saving memory: {e}")

