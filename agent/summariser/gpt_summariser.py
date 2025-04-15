import os
import logging
import openai
import re
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
        """Summarize penetration testing history with CoT reasoning."""
        
        cot_prompt = (
            "You are summarizing penetration testing activity. Follow these steps:\n"
            "1. Analyze the new command and output for critical findings\n"
            "2. Identify connections to previous actions in the existing summary\n"
            "3. Determine what needs to be updated or maintained\n"
            "4. Organize information by priority and relevance\n"
            "5. Compose the updated summary\n\n"
            "Format your response as:\n"
            "<REASONING>\n"
            "1. [Step 1 analysis]\n"
            "2. [Step 2 connections]\n"
            "...\n"
            "</REASONING>\n"
            "<SUMMARY>\n[Updated summary here]\n</SUMMARY>"
            
            f"\n\nExisting Summary: {self.history_summary}\n"
            f"New Command: {command}\n"
            f"Command Output: {output}\n"
        )

        try:
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert penetration testing summarizer that uses explicit reasoning."},
                    {"role": "user", "content": cot_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            full_response = response.choices[0].message.content.strip()
            
            # Extract summary from structured response
            summary_match = re.search(r'<SUMMARY>\n?(.*?)\n?</SUMMARY>', full_response, re.DOTALL)
            if summary_match:
                new_summary = summary_match.group(1).strip()
                self.history_summary = new_summary
                
                # Log reasoning process for audit
                reasoning_match = re.search(r'<REASONING>\n?(.*?)\n?</REASONING>', full_response, re.DOTALL)
                if reasoning_match:
                    reasoning_steps = reasoning_match.group(1).strip()
                    logging.info(f"Summary Reasoning Steps:\n{reasoning_steps}")
                
                logging.info(f"Updated summary: {self.history_summary}")
                return self.history_summary

            # Fallback if XML tags missing
            logging.warning("CoT structure missing in response, using full response")
            self.history_summary = full_response
            return self.history_summary

        except Exception as e:
            logging.error(f"Error generating summary: {e}")
            return self.history_summary

    def get_summary(self):
        """Retrieve the current summarized history."""
        return self.history_summary