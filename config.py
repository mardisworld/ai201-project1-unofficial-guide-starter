import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")  # stronger synthesis: reliably combines evidence spread across multiple/lower-ranked chunks

# --- Embeddings ---
EMBEDDING_MODEL = "all-mpnet-base-v2"

# --- Vector store ---
CHROMA_COLLECTION = "rulesbot"
CHROMA_PATH = "./chroma_db"

# --- Retrieval ---
N_RESULTS = 10 # increase retrieval depth so the model has more candidate evidence to combine.

# --- Documents ---
DOCS_PATH = "./documents"
