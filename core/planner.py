import re
import json
from llm_interface.llm_client import LLMClient
from log.logger import log
class Planner:
    def __init__(self):
        # Initialize LLMClient with OpenAI
        self.llm = LLMClient(mode='openai', planner_model_name='gpt-4.1')

    def plan_next_step(self, current_phase, context_summary, todo_list, target_ip, username, password, memory,task_reference=None):

        task_suggestions = []
        if task_reference:
            available_tasks = task_reference.get_available_tasks(current_phase)
            if available_tasks:
                task_suggestions = available_tasks
        prompt = self.build_prompt(current_phase, context_summary, todo_list, target_ip, username, password, memory,task_suggestions)
        response = self.llm.query_planner(prompt)
        log(f"LLM Response: {response}", color="pink")  # Debug the LLM response
        return self.extract_command(response)

    def build_prompt(self, phase, summary, todo_list, ip, username, password, memory,task_suggestions=None):

        task_suggestion_text = ""
        if task_suggestions:
            task_suggestion_text = f"\nRecommended tasks for {phase} phase: {', '.join(task_suggestions)}"

        prompt = f"""
        
        IMPORTANT NOTICE: Command should be such that it can run on Strictly non-interactive shell.

    Think Step by Step:
    - First, analyze the current phase of the assessment.
    - Then, consider the context summary and the tasks that are pending.

    Current phase of the assessment: {phase}{task_suggestion_text}

    Summary of past activity:
    {summary if summary else "None"}

    Past Commands executed:
    {memory.get_executed_commands_by_phase(phase) if memory.get_executed_commands_by_phase(phase) else "None"}

    Previous Command:Output Pair:
    {memory.get_previous_context()}

    Pending tasks:
    {', '.join(todo_list) if todo_list else "None"}
    TAKE VERY GOOD CARE ABOUT THE SSH, YOU ARE NOT ON THE HOST, YOU ARE EXECUTING COMMANDS ON THE ATTACKING MACHINE.
    Output raw JSON without any formatting
    """

        log(f"Prompt: {prompt}", color="blue")  # Debug the prompt
        return prompt

    def extract_command(self, response):
        """
        Extracts command and input from a JSON string.

        Args:
            json_str (str): JSON string with "command" and "input" keys.

        Returns:
            tuple: (command, input)
        """
        try:
            data = json.loads(response)
            return data["command"], data["input"]
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Error parsing input: {e}")
            return None, None
        return (command, user_input)
    
    def nudge_with_task(self, fallback_task, current_phase):
        """
        Use a fallback task to nudge the LLM when it fails to produce a command.
        
        Args:
            fallback_task (str): The fallback task to suggest.
            current_phase (str): The current penetration testing phase.
            
        Returns:
            tuple: (command, input)
        """
        # Create a prompt specifically for the fallback task
        prompt = f"""You are a penetration tester performing a professional security assessment.

        The current phase is: {current_phase}
        
        You need to complete this specific task: {fallback_task}
        
        Please provide a specific command to execute for this task. Return your response as a JSON object with 'command' and 'input' keys.
        """
        
        response = self.llm.query_planner(prompt)
        log(f"Fallback LLM Response: {response}", color="pink")
        return self.extract_command(response)