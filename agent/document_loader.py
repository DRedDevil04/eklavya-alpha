import faiss
import json
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings  # Use Hugging Face embeddings

class DocumentLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")  # Local model
        self.text_chunks = self.load_json_document()
        self.index = self.build_faiss_index()

    def load_json_document(self):
        """Loads penetration testing commands from a JSON file."""
        try:
            with open(self.file_path, "r") as file:
                command_dict = json.load(file)
            commands = [{"category": cat, "command": cmd} for cat, cmds in command_dict.items() for cmd in cmds]
            print(f"✅ Loaded {len(commands)} commands from JSON.")
            return commands
        except Exception as e:
            print(f" Error loading JSON file: {e}")
            return []

    def build_faiss_index(self):
        """Creates FAISS index for fast retrieval."""
        # Detect embedding dimension dynamically
        sample_embedding = self.embedding_model.embed_query("test command")
        dimension = len(sample_embedding)
        print(f"Detected embedding dimension: {dimension}")

        index = faiss.IndexFlatL2(dimension)

        if not self.text_chunks:
            print("⚠️ No commands to index. FAISS index is empty.")
            return index

        embeddings = []
        for i, chunk in enumerate(self.text_chunks):
            try:
                emb = self.embedding_model.embed_query(chunk["command"])
                embeddings.append(emb)
                print(f"Embedded command {i+1}/{len(self.text_chunks)}.")
            except Exception as e:
                print(f" Error embedding command {i+1}: {e}")

        if embeddings:
            embeddings = np.array(embeddings, dtype=np.float32).reshape(-1, dimension)  # Ensure correct shape
            index.add(embeddings)
            print(f"FAISS index populated with {index.ntotal} commands.")
        else:
            print(" No embeddings generated. FAISS index remains empty.")

        return index

    def retrieve_relevant_text(self, query):
        """Finds relevant command using FAISS similarity search."""
        if self.index.ntotal == 0:
            print("⚠️ FAISS index is empty. No relevant results found.")
            return []

        query_embedding = np.array(self.embedding_model.embed_query(query), dtype=np.float32).reshape(1, -1)
        distances, indices = self.index.search(query_embedding, k=1)

        if indices.size == 0 or indices[0].size == 0:
            print("⚠️ No relevant results found.")
            return []

        retrieved_commands = [self.text_chunks[i]["command"] for i in indices[0] if i >= 0]
        print(f"✅ FAISS Retrieved Command: {retrieved_commands[0] if retrieved_commands else 'None'}")

        return retrieved_commands
