# ============================================
# MANTHAN AI — Context Retrieval Engine
# File: rag/retriever.py
# ============================================

import os
import chromadb

# ChromaDB persistence directory pathway tracking
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "DB_STORE")

def retrieve_code_context(query: str, max_results: int = 3) -> str:
    """
    Queries the persistent ChromaDB collection to fetch the most relevant 
    code blocks matching the developer's question or context requirement.
    """
    if not os.path.exists(DB_PATH):
        print("[Retriever] Warning: Vector database path does not exist yet.")
        return ""

    try:
        # Initialize client referencing local persistent database instances
        client = chromadb.PersistentClient(path=DB_PATH)
        
        # Accessing existing codebase matrices
        collection = client.get_or_create_collection(name="manthan_ai_repo_store")
        
        # Querying vector embeddings space using internal semantic token algorithms
        results = collection.query(
            query_texts=[query],
            n_results=max_results
        )
        
        # Format matching chunks cleanly as context blocks
        context_blocks = []
        if "documents" in results and results["documents"]:
            for i, doc_content in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if "metadatas" in results and results["metadatas"] else {}
                file_origin = metadata.get("file_path", "Unknown File")
                
                block = f"--- Source File: {file_origin} ---\n{doc_content}\n"
                context_blocks.append(block)
                
        if not context_blocks:
            return ""
            
        formatted_context = "\n".join(context_blocks)
        print(f"[Retriever] Successfully retrieved {len(context_blocks)} code patches for current task query context.")
        return formatted_context

    except Exception as e:
        print(f"[Retriever] Error mapping semantic vectors matrices: {str(e)}")
        return ""