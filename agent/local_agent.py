import os
import numpy as np
import faiss
from dotenv import load_dotenv
from langchain.llms import LlamaCpp  # Local LLM
from langchain.chains import ConversationChain
from langchain.embeddings import HuggingFaceEmbeddings  # Local embeddings
from interface.connector import SSHConnector
from agent.pentest_report import PentestReport
from document_loader import DocumentLoader  # Document Retrieval

# Load environment variables
load_dotenv()

# Initialize Local Models
llm = LlamaCpp(model_path="models/your-local-model.gguf")  # Update with your model path
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")  

# Load and Index Document (RAG)
document_loader = DocumentLoader("pentest_commands.pdf", embedding_model)

# FAISS Index (Ensure correct dimensions)
embedding_dim = 384  # all-MiniLM-L6-v2 embedding size
index = faiss.IndexFlatL2(embedding_dim)

# Add document embeddings to FAISS index
document_chunks = document_loader.text_chunks
embeddings = np.array([embedding_model.embed_query(chunk) for chunk in document_chunks], dtype=np.float32)
index.add(embeddings)

# SSH Details
TARGET_IP = "192.168.122.186"
USERNAME = "kali"
PASSWORD = "kali"
FAISS_THRESHOLD = 0.1  

# Initialize SSH and Report
ssh = SSHConnector(TARGET_IP, USERNAME, PASSWORD)
ssh.create_ssh_session()
report = PentestReport("pentest_report.pdf")

# Initialize conversation history
conversation = ConversationChain(llm=llm)

# System Prompt
system_prompt = (
    "You are an AI assisting in penetration testing. You have SSH access to a Kali machine. "
    "Generate a single valid Linux command to find and attack hosts accordingly. "
    "Only return a bash command that can be executed directly on Kali Linux. "
    "Use retrieved knowledge from external sources if needed. "
    "Find everything out as an attacker would. The first infected node IP is 192.168.122.12, "
    "root password is 'ubuntu'. SSH into the first node and read flag.txt in the root home directory."
)
conversation.memory.chat_memory.add_user_message(system_prompt)

# Main loop to execute penetration testing
while True:
    # Retrieve Relevant Context
    relevant_texts = document_loader.retrieve_relevant_text("pentesting command for attack")
    
    # Limit retrieved text to avoid exceeding model context length
    retrieved_context = " ".join(relevant_texts[:3])  # Use only top 3 chunks
    if retrieved_context:
        conversation.memory.chat_memory.add_user_message(f"Relevant Info: {retrieved_context}")

    # Generate attack command
    command = conversation.run("")
    command_embedding = np.array(embedding_model.embed_query(command), dtype=np.float32).reshape(1, -1)

    # FAISS Similarity Check (Prevents duplicate execution)
    distances, indices = index.search(command_embedding, k=1)
    if distances[0][0] < FAISS_THRESHOLD:
        print(f"Duplicate command detected, skipping execution: {command}")
        continue

    # Execute Command
    print(f"\n Generated Command: {command}")
    output = ssh.execute_command(command)
    print(f" Command Output:\n{output}")

    # Store in FAISS
    index.add(command_embedding)

    # Log command execution in the report
    report.log_command(command, output)

    # Stop execution if flag.txt is found
    if "flag.txt" in output:
        print("\n Flag found! Stopping penetration test.")
        break

    # Add response to conversation history
    conversation.memory.chat_memory.add_ai_message(output)

# Generate final report
report.generate_pdf()
print("\nPenetration Testing Report Generated: pentest_report.pdf")
