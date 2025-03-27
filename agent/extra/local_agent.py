import os
import numpy as np
import faiss
from dotenv import load_dotenv
from langchain_community.llms import LlamaCpp
from langchain.chains import ConversationChain
from langchain_huggingface import HuggingFaceEmbeddings
from interface.connector import SSHConnector
from agent.extra.pentest_report import PentestReport
from agent.extra.document_loader import DocumentLoader  # Document Retrieval

# Load environment variables
load_dotenv()

# Initialize Local Models
llm = LlamaCpp(model_path="/home/bhagat/.lmstudio/models/PrunaAI/mistralai-Mistral-7B-Instruct-v0.2-GGUF-smashed/Mistral-7B-Instruct-v0.2.Q4_K_S.gguf")  # Update with your model path
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Load and Index Document (RAG)
document_loader = DocumentLoader("./agent/pentest_commands.json")

# Ensure FAISS Index is Correct
embedding_dim = 384  # sentence-transformers/all-MiniLM-L6-v2 embedding size
index = faiss.IndexFlatL2(embedding_dim)

# Add document embeddings to FAISS index
if document_loader.text_chunks:
    embeddings = np.array([embedding_model.embed_query(chunk["command"]) for chunk in document_loader.text_chunks], dtype=np.float32)
    index.add(embeddings)

# SSH Details
TARGET_IP = "192.168.122.186"
USERNAME = "kali"
PASSWORD = "kali"
FAISS_THRESHOLD = 0.1  

# Initialize SSH and Report
ssh = SSHConnector(TARGET_IP, USERNAME, PASSWORD)
ssh.create_ssh_session()
report = PentestReport("./agent/pentest_report.pdf")

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
    "Do not use markdown formatting, code blocks, or any explanations. Only output the raw command."
    "Give only and only command , no extra information. ONLY PROVIDE THE RAW COMMAND WHICH CAN BE RUN ON THE TERMINAL"
)
conversation.memory.chat_memory.add_user_message(system_prompt)

# Main loop to execute penetration testing
while True:
    # Retrieve Relevant Context from FAISS
    relevant_texts = document_loader.retrieve_relevant_text("pentesting command for attack")
    
    # Append retrieved context to the conversation
    if relevant_texts:
        retrieved_context = " ".join(relevant_texts)
        conversation.memory.chat_memory.add_user_message(f"Relevant Information: {retrieved_context}")

    # Generate command
    command = conversation.run("")
    embedding = np.array(embedding_model.embed_query(command), dtype=np.float32).reshape(1, -1)

    # Check for duplicate command in FAISS
    distances, indices = index.search(embedding, k=1)
    if indices[0][0] != -1 and distances[0][0] < FAISS_THRESHOLD:
        print(f"⚠️ Duplicate command detected, skipping execution: {command}")
        continue

    # Execute command
    print(f"\n✅ Generated Command: {command}")
    output = ssh.execute_command(command)
    print(f"📜 Command Output:\n{output}")

    # Store in FAISS
    index.add(embedding)

    # Log command execution in report
    report.log_command(command, output)

    # Stop execution if flag.txt or a flag format is found
    if "flag.txt" in output.lower() or "flag{" in output.lower():
        print("\n🏁 Flag found! Stopping penetration test.")
        break  # Ensure this exits the loop

    # Add response to conversation history
    conversation.memory.chat_memory.add_ai_message(output)

# Generate final report
report.generate_pdf()
print("\n📄 Penetration Testing Report Generated: pentest_report.pdf")
