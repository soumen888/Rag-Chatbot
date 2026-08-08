import chromadb
from chromadb.utils import embedding_functions
import os
import re
import hashlib

class VectorDB:
    def __init__(self, db_path="./chroma_db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=self.db_path)
        
        # Use sentence-transformers locally
        print("[*] Loading local embedding model (all-MiniLM-L6-v2)...")
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )

    def sanitize_collection_name(self, name):
        # ChromaDB collection names must be 3-63 chars, alphanumeric or _ or -
        # and start/end with alphanumeric
        sanitized = re.sub(r'[^a-zA-Z0-9_-]', '_', name)
        sanitized = re.sub(r'_+', '_', sanitized)
        # Trim to length constraints
        if len(sanitized) > 60:
            sanitized = sanitized[:60]
        sanitized = sanitized.strip('_').strip('-')
        # Ensure it has at least 3 chars
        if len(sanitized) < 3:
            sanitized = "doc_db_" + sanitized
        return sanitized

    def get_or_create_collection(self, collection_name):
        safe_name = self.sanitize_collection_name(collection_name)
        return self.client.get_or_create_collection(
            name=safe_name,
            embedding_function=self.embedding_function
        )

    def add_chunks(self, collection_name, chunks):
        safe_name = self.sanitize_collection_name(collection_name)
        # Use safe_name directly to avoid double-sanitize
        collection = self.client.get_or_create_collection(
            name=safe_name,
            embedding_function=self.embedding_function
        )
        
        documents = []
        metadatas = []
        ids = []
        
        for chunk in chunks:
            documents.append(chunk["text"])
            
            # ChromaDB metadata must be str, int, float, or bool
            meta = {}
            for k, v in chunk["metadata"].items():
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v)
            metadatas.append(meta)
            
            # Use content hash for globally unique, deduplication-safe IDs
            # This ensures re-syncing the same messages won't create duplicates
            content_hash = hashlib.md5(chunk["text"].encode()).hexdigest()[:16]
            unique_id = f"{safe_name}_{content_hash}"
            ids.append(unique_id)
            
        # Insert in batches to prevent payload size limits
        batch_size = 100
        
        print(f"[*] Storing {len(chunks)} chunks in ChromaDB collection: {safe_name}")
        for i in range(0, len(ids), batch_size):
            collection.upsert(
                documents=documents[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size],
                ids=ids[i:i+batch_size]
            )
        print("[+] Storage completed successfully.")

    def query(self, collection_name, query_text, n_results=5):
        collection = self.get_or_create_collection(collection_name)
        
        # 1. Fetch semantic results
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        
        formatted_results = []
        seen_texts = set()
        
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0] if "distances" in results else [0]*len(docs)
            
            for doc, meta, dist in zip(docs, metas, distances):
                formatted_results.append({
                    "text": doc,
                    "metadata": meta,
                    "distance": dist
                })
                seen_texts.add(doc)
                
        # 2. For chat logs (Telegram/Discord), also fetch the absolute latest chronological chunks
        # This solves queries like 'latest news', 'what happened today', 'last 2H summary'
        safe_name = self.sanitize_collection_name(collection_name)
        if safe_name.startswith("tg_") or safe_name.startswith("ds_") or safe_name == "telegram_all":
            try:
                # Retrieve all items in the collection (max limit to avoid memory overhead, e.g. 100)
                all_data = collection.get(limit=100)
                if all_data and "documents" in all_data and all_data["documents"]:
                    recent_items = []
                    for doc, meta in zip(all_data["documents"], all_data["metadatas"]):
                        if doc in seen_texts:
                            continue
                        recent_items.append({
                            "text": doc,
                            "metadata": meta,
                            "distance": 0.0,
                            "timestamp": int(meta.get("timestamp", 0))
                        })
                    
                    # Sort by timestamp descending (newest first)
                    recent_items.sort(key=lambda x: x["timestamp"], reverse=True)
                    
                    # Append the top 5 newest chunks to the context
                    for item in recent_items[:5]:
                        formatted_results.append({
                            "text": item["text"],
                            "metadata": item["metadata"],
                            "distance": item["distance"]
                        })
            except Exception:
                pass
                
        return formatted_results

    def list_collections(self):
        return [c.name for c in self.client.list_collections()]

    def delete_collection(self, collection_name):
        safe_name = self.sanitize_collection_name(collection_name)
        try:
            self.client.delete_collection(name=safe_name)
            print(f"[+] Collection '{safe_name}' deleted successfully.")
            return True
        except Exception as e:
            print(f"[!] Error deleting collection '{safe_name}': {e}")
            return False
