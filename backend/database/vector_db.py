import os
from pathlib import Path

try:
    import chromadb
    from chromadb.utils import embedding_functions
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    try:
        import fitz  # PyMuPDF
    except ImportError:
        fitz = None
except ImportError:
    chromadb = None
    embedding_functions = None
    RecursiveCharacterTextSplitter = None

from backend.config import PROJECT_ROOT

CHROMA_PATH = PROJECT_ROOT / "chroma_db"
_COLLECTION = None

def get_collection():
    """Lazily initialize the Chroma DB persistent collection to prevent slow boot."""
    global _COLLECTION
    if chromadb is None:
        return None
    if _COLLECTION is None:
        client = chromadb.PersistentClient(path=str(CHROMA_PATH))
        emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
        _COLLECTION = client.get_or_create_collection(name="infinite_memory", embedding_function=emb_fn)
    return _COLLECTION

def index_desktop_files() -> str:
    """Scans the user's Desktop for .txt and .pdf files to index into Infinite Memory."""
    collection = get_collection()
    if collection is None:
        return "Memory engine offline. Please install chromadb, langchain, and sentence-transformers."
        
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
    collection = get_collection()
    if collection is None:
        return ""
        
    if collection.count() == 0:
        return "" # Nothing indexed yet, don't crash.
        
    results = collection.query(query_texts=[query], n_results=n_results)
    
    if not results or not results["documents"] or not results["documents"][0]:
        return ""
        
    docs = results["documents"][0]
    metadatas = results["metadatas"][0]
    
    context = ""
    for txt, meta in zip(docs, metadatas):
        context += f"[Source: {meta.get('source', 'Unknown')}]: {txt}\n---\n"
    return context.strip()
