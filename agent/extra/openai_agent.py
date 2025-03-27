import os
import numpy as np
import faiss
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
from langchain_openai import OpenAIEmbeddings
from interface.connector import SSHConnector
from agent.pentest_report import PentestReport
from agent.document_loader import DocumentLoader

# Load environment variables
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Initialize LangChain Components (OpenAI API)
llm = ChatOpenAI(model_name="gpt-4o-mini", openai_api_key=openai_api_key)
embedding_model = OpenAIEmbeddings(openai_api_key=openai_api_key)

# Load External JSON and Build FAISS Index
document_loader = DocumentLoader("./agent/pentest_commands.json", embedding_model)

# SSH Connection Details
TARGET_IP = "192.168.122.186"
USERNAME = "kali"
PASSWORD = "kali"
FAISS_THRESHOLD = 0.1  # Threshold for duplicate command detection

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
    "Do not use markdown formatting, code blocks, or any explanations. Only output the raw command."
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
    embedding = embedding_model.embed_query(command)

    # Check for duplicate command
    similar_commands, distances = document_loader.index.search(np.array(embedding, dtype=np.float32).reshape(1, -1), k=1)
    if similar_commands[0][0] != -1 and distances[0][0] < FAISS_THRESHOLD:
        print(f"⚠️ Duplicate command detected, skipping execution: {command}")
        continue

    # Execute command
    print(f"\n Generated Command: {command}")
    output = ssh.execute_command(command)
    print(f" Command Output:\n{output}")

    # Store in FAISS
    document_loader.index.add(np.array(embedding, dtype=np.float32).reshape(1, -1))

    # Log command execution in report
    report.log_command(command, output)

    # Stop execution if flag.txt is found
    # Stop execution if flag.txt or the flag format is found
    if "flag.txt" in output.lower() or "flag{" in output.lower():
        print("\n Flag found! Stopping penetration test.")
        break  # Ensure this exits the loop


    # Add response to conversation history
    conversation.memory.chat_memory.add_ai_message(output)

# Generate final report
report.generate_pdf()
print("\n Penetration Testing Report Generated: pentest_report.pdf")
