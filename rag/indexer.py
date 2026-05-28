# ============================================
# MANTHAN AI — Vector Indexing Engine
# File: rag/indexer.py
# ============================================

import os
import chromadb
from chromadb.config import Settings

# Persistent storage directory for ChromaDB vector embeddings
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "DB_STORE")

def chunk_code_content(documents: list[dict], chunk_size: int = 1000, chunk_overlap: int = 200) -> list[dict]:
    """
    Breaks large source code strings into smaller logical chunks for retrieval.
    """
    chunks = []
    for doc in documents:
        content = doc["content"]
        file_path = doc["file_path"]
        
        # Simple sliding-window line based chunking strategy for strict syntax handling
        lines = content.split("\n")
        current_chunk = []
        current_length = 0
        
        for line in lines:
            current_chunk.append(line)
            current_length += len(line) + 1 # +1 for newline character representation
            
            if current_length >= chunk_size:
                chunk_text = "\n".join(current_chunk)
                chunks.append({
                    "text": chunk_text,
                    "metadata": {"file_path": file_path}
                })
                # Sliding back window manually to sustain syntax overlap context
                overlap_lines = max(1, int(len(current_chunk) * (chunk_overlap / chunk_size)))
                current_chunk = current_chunk[-overlap_lines:]
                current_length = sum(len(l) + 1 for l in current_chunk)
                
        if current_chunk:
            chunks.append({
                "text": "\n".join(current_chunk),
                "metadata": {"file_path": file_path}
            })
            
    print(f"[Indexer] Splitted files into {len(chunks)} contextual code chunks.")
    return chunks

def index_codebase_to_vector_db(code_chunks: list[dict]):
    """
    Stores text chunks locally inside an explicit ChromaDB instance.
    Uses default internal sentence-transformers for fast local execution.
    """
    # Instantiate persistent database storage layer
    client = chromadb.PersistentClient(path=DB_PATH)
    
    # Getting or creating a standard repository reference collection
    collection = client.get_or_create_collection(name="manthan_ai_repo_store")
    
    # Extract structural components for DB processing arrays
    documents = [chunk["text"] for chunk in code_chunks]
    metadatas = [chunk["metadata"] for chunk in code_chunks]
    ids = [f"id_{i}" for i in range(len(code_chunks))]
    
    # Avoid pushing empty datasets to vectors space
    if not documents:
        print("[Indexer] Warning: Empty document pool passed. Indexing aborted.")
        return
        
    # Inject data matrices into local storage
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )
    print(f"[Indexer] Pipeline complete! Successfully loaded {len(documents)} vectors to ChromaDB cluster.")