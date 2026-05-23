import os
from pathlib import Path
from backend.config import PROJECT_ROOT

CHROMA_PATH = PROJECT_ROOT / "chroma_db"
_CLIENT = None
_COLLECTION = None

def get_chroma_client():
    """Lazily initialize the Chroma DB client without loading embedding models."""
    global _CLIENT
    try:
        import chromadb
        if _CLIENT is None:
            _CLIENT = chromadb.PersistentClient(path=str(CHROMA_PATH))
        return _CLIENT
    except ImportError:
        return None

def is_memory_empty() -> bool:
    """Fast check to see if local indexed memory has any documents without loading SentenceTransformer."""
    client = get_chroma_client()
    if client is None:
        return True
    try:
        # Get collection without embedding function parameters
        collection = client.get_or_create_collection(name="infinite_memory")
        return collection.count() == 0
    except Exception:
        return True

def get_collection():
    """Lazily initialize the Chroma DB persistent collection and SentenceTransformer embedding model."""
    global _COLLECTION
    client = get_chroma_client()
    if client is None:
        return None
    if _COLLECTION is None:
        try:
            from chromadb.utils import embedding_functions
            emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
            _COLLECTION = client.get_or_create_collection(name="infinite_memory", embedding_function=emb_fn)
        except Exception:
            return None
    return _COLLECTION

def index_desktop_files() -> str:
    """Scans the user's Desktop for .txt and .pdf files to index into Infinite Memory."""
    try:
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        try:
            import fitz  # PyMuPDF
        except ImportError:
            fitz = None
    except ImportError:
        return "Memory engine offline. Please install chromadb, langchain, and sentence-transformers."

    collection = get_collection()
    if collection is None:
        return "Memory engine offline. Please initialize collection failed."
        
    desktop_path = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    if not desktop_path.exists():
        return "Could not locate Desktop."
        
    files = list(desktop_path.rglob("*.txt")) + list(desktop_path.rglob("*.pdf"))
    if not files:
        return "Found no .txt or .pdf files on the Desktop to memorize."
        
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    doc_id = 0
    added_count = 0
    for f in files:
        try:
            text = ""
            if f.suffix == ".txt":
                with open(f, "r", encoding="utf-8", errors="ignore") as file_obj:
                    text = file_obj.read()
            elif f.suffix == ".pdf" and fitz:
                doc = fitz.open(str(f))
                for page in doc:
                    text += page.get_text()
            
            if not text.strip():
                continue
                
            chunks = splitter.split_text(text)
            for chunk in chunks:
                collection.upsert(
                    documents=[chunk],
                    metadatas=[{"source": str(f.name)}],
                    ids=[f"doc_{str(f.name)}_{doc_id}"]
                )
                doc_id += 1
            added_count += 1
        except Exception:
            pass # Quietly skip files that can't be read (permissions, locks)
            
    return f"Successfully synchronized and memorized {added_count} files from your Desktop."

def query_memory(query: str, n_results: int = 3) -> str:
    """Finds the most relevant context from the local indexed memory."""
    if is_memory_empty():
        return ""
        
    collection = get_collection()
    if collection is None:
        return ""
        
    try:
        results = collection.query(query_texts=[query], n_results=n_results)
        if not results or not results["documents"] or not results["documents"][0]:
            return ""
            
        docs = results["documents"][0]
        metadatas = results["metadatas"][0]
        
        context = ""
        for txt, meta in zip(docs, metadatas):
            context += f"[Source: {meta.get('source', 'Unknown')}]: {txt}\n---\n"
        return context.strip()
    except Exception:
        return ""
