import re
import torch
import gc
import os
from agent.planner.Planner import Planner


os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

def clear_gpu_memory():
    """Clears GPU memory to free up space before loading a model."""
    torch.cuda.empty_cache()  # Free unused cached memory
    gc.collect()  # Run garbage collection

def test_planner():
    clear_gpu_memory()

    planner = Planner()
    
    # Sample input
    test_prompt = "Generate a Linux command to list all files in the home directory."
    
    # Generate command
    command = planner.generate_command(test_prompt)
    
    # Check if response is not empty
    assert command is not None, "Planner returned None"
    print(command)
    assert command, f"Planner response does not contain a valid command: {command}"

    
    print("Planner test passed!")

if __name__ == "__main__":
    test_planner()
