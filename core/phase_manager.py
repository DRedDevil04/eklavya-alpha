class PhaseManager:
    def __init__(self):
        """Initialize the phases and set the starting phase."""
        self.phases = ["Enumeration", "Exploration", "Privilege Escalation"]
        self.current_phase = "Enumeration"

    def get_phase(self):
        """Return the current phase."""
        return self.current_phase

    def update_phase(self, summary_json):
        """
        Update the current phase based on summarizer output JSON.
        """
        try:
            import json
            summary = json.loads(summary_json)
        except json.JSONDecodeError:
            print("[Error] Could not decode summarizer JSON.")
            return

        next_phase = summary.get("next-phase", "").strip()

        if next_phase and next_phase in self.phases:
            if next_phase != self.current_phase:
                print(f"[*] Phase changed from {self.current_phase} to {next_phase}")
                self.current_phase = next_phase
        else:
            print(f"[Warning] '{next_phase}' is not a valid phase.")

