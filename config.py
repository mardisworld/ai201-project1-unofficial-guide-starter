import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.1-8b-instant")

# --- Embeddings ---
EMBEDDING_MODEL = "all-mpnet-base-v2"

# --- Vector store ---
CHROMA_COLLECTION = "rulesbot"
CHROMA_PATH = "./chroma_db"

# --- Retrieval ---
N_RESULTS = 7 # adjusting to improve performance of gernating answers with limited context window. 

# --- Documents ---
DOCS_PATH = "./documents"
