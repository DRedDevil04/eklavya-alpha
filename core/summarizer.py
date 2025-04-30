from llm_interface.llm_client import LLMClient

class Summarizer:
    def __init__(self):
        # Initialize LLMClient in OpenAI mode with summarizer model
        self.llm = LLMClient(mode='openai', summarizer_model_name='gpt-4o-mini')

    def summarize_command_output(self, command, output, previous_summary="", phase=None):
        """
        Summarizes command output and appends to previous summary.
        Truncates excessive output and enforces concise, structured summary.
        """
        output = self._truncate_output(output, max_lines=40)

        prompt = f"""You are an assistant helping summarize the progress of an automated penetration testing agent.

Target network information:
- Subnet: 192.168.122.0/24
- Discovered hosts:
    - 192.168.122.152 (MAC: 52:54:00:a1:b1:c1)
    - 192.168.122.15  (MAC: 52:54:00:a2:b2:c2)
    - 192.168.122.131 (MAC: 52:54:00:a3:b3:c3)

{f"Current phase: {phase}" if phase else ""}

Previous summary:
{previous_summary if previous_summary else "None"}

Command just executed:
{command}
Command output (truncated if long):
{output}

Please update the summary with this new information in a structured, concise format. Focus on key discoveries, actions taken, and their relevance to penetration testing. Use clear points or short paragraphs for readability.
Strictly obey the JSON Format given"""

        return self.llm.query_summarizer(prompt, max_tokens=300)

    def _truncate_output(self, text, max_lines=100):
        """Truncate output to prevent LLM context overload."""
        lines = text.strip().splitlines()
        if len(lines) > max_lines:
            return "\n".join(lines[:max_lines]) + "\n[Output truncated]"
        return text
