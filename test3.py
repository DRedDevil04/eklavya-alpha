from transformers import AutoTokenizer, AutoModelForCausalLM, AutoModelForSeq2SeqLM, pipeline
import torch
import gc 

torch.cuda.empty_cache()  # Clears the CUDA memory cache
gc.collect()  # Collects garbage to free memory

PLANNER_MODEL_ID = "codellama/CodeLlama-7B-Instruct-hf"

# Load Tokenizer and Model
planner_tokenizer = AutoTokenizer.from_pretrained(PLANNER_MODEL_ID)
planner_model = AutoModelForCausalLM.from_pretrained(
    PLANNER_MODEL_ID,
    device_map="auto",  # Ensure it is on GPU
    torch_dtype=torch.float16,
)

# Test Model Response
input_text = "How are you?"
inputs = planner_tokenizer(input_text, return_tensors="pt").to("cuda")
outputs = planner_model.generate(**inputs, max_new_tokens=30)  # Reduced tokens for faster response
response = planner_tokenizer.decode(outputs[0], skip_special_tokens=True)


print(response)


MODEL_ID = "facebook/bart-large-cnn"
summarizer = pipeline("summarization", model=MODEL_ID, device=-1)  # device=-1 ensures CPU usage

print("Doing Summarization:\n")

summary = summarizer(response, max_length=100, min_length=20, length_penalty=2.0)[0]['summary_text']
print("Summary:", summary)
