# ============================================
# MANTHAN AI — Repository Ingestion Engine
# File: repo/ingest.py
# ============================================

import os
import zipfile
import shutil
from pathlib import Path

# Valid code extensions jinhe AI read karega
VALID_EXTENSIONS = {'.py', '.ts', '.js', '.java', '.cpp', '.h', '.sql', '.html', '.css', '.json'}

def extract_zip(zip_path: str, extract_to: str) -> str:
    """
    Extracts the uploaded ZIP file to a temporary directory securely.
    """
    if not zipfile.is_zipfile(zip_path):
        raise ValueError("Invalid archive format. Please provide a valid .zip file.")
        
    # Purana data clear karke fresh extract karna
    if os.path.exists(extract_to):
        shutil.rmtree(extract_to)
    os.makedirs(extract_to, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
        
    print(f"[Ingest] Successfully extracted source tree to: {extract_to}")
    return extract_to

def parse_codebase(directory_path: str) -> list[dict]:
    """
    Traverses through the extracted directory and reads matching source files.
    Returns a list of dicts: [{"file_path": "...", "content": "..."}]
    """
    parsed_documents = []
    base_path = Path(directory_path)

    for root, dirs, files in os.walk(directory_path):
        # Ignore common boilerplate/heavy folders for optimization
        if any(ignored in root for ignored in ['__pycache__', 'node_modules', '.git', '.venv', 'dist']):
            continue

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in VALID_EXTENSIONS:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Store relative path for cleaner metadata context mapping
                    relative_path = file_path.relative_to(base_path)
                    parsed_documents.append({
                        "file_path": str(relative_path),
                        "content": content
                    })
                except Exception as e:
                    print(f"[Ingest] Warning: Failed to parse file {file_path}. Reason: {str(e)}")

    print(f"[Ingest] Parsing complete. Indexed {len(parsed_documents)} valid source files.")
    return parsed_documents