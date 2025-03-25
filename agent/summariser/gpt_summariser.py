import os
import logging
import openai
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    filename="pentest_agent.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Load .env file
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Missing OPENAI_API_KEY in .env file!")

openai.api_key = openai_api_key


# Load Summarizer Model
class Summarizer:
    def __init__(self, model="gpt-4o-mini"):
        """Initialize the summarizer using OpenAI API."""
        self.model = model
        self.history_summary = ""

    def summarize(self, command, output):
        """Summarize penetration testing history, focusing on newly executed commands."""
        
        prompt = (
            "You are summarizing penetration testing activity.\n"
            "Update the summary with the latest command and output while keeping it concise.\n"
            "Ensure the summary is structured, avoiding duplication.\n\n"
            f"Previous Summary: {self.history_summary}\n\n"
            f"New Command: {command}\n"
            f"New Output: {output}\n"
            "Update the summary accordingly."
        )

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert penetration testing summarizer."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3  # Lower temperature for more consistent responses
            )

            new_summary = response.choices[0].message.content.strip()

            if new_summary:
                self.history_summary = new_summary  # Replace old summary with updated one
                logging.info(f"Updated summary: {self.history_summary}")

            return self.history_summary

        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            return self.history_summary

    def get_summary(self):
        """Retrieve the current summarized history."""
        return self.history_summary
