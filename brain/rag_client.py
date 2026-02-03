"""
RAG Client - connects to the shared RAG service for business term lookups
This module allows the brain to retrieve business context on demand
"""

from typing import List, Dict, Optional
import os
from sentence_transformers import SentenceTransformer
import chromadb

# Initialize embedding model (same as rag_service)
EMBEDDING_MODEL = SentenceTransformer('all-MiniLM-L6-v2')


class RAGClient:
    def __init__(self, db_path: str = "../rag_service/chroma_data"):
        """
        Initialize RAG client with path to the shared Chroma database
        
        Args:
            db_path: Path to the Chroma database created by rag_service
        """
        self.db_path = db_path
        
        # Only initialize if database exists
        if os.path.exists(db_path):
            try:
                self.client = chromadb.PersistentClient(path=db_path)
                self.collection = self.client.get_collection(name="business_terms")
                self.ready = True
                print(f"✓ RAG Client connected to: {db_path}")
            except Exception as e:
                print(f"⚠️  RAG Client failed to load: {e}")
                self.ready = False
        else:
            print(f"⚠️  RAG database not found at {db_path}")
            self.ready = False
    
    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """
        Retrieve relevant business terms for a query
        
        Args:
            query: User query
            top_k: Number of results to return
            
        Returns:
            List of dicts with term, definition, and relevance score
        """
        if not self.ready:
            return []
        
        try:
            # Embed the query
            query_embedding = EMBEDDING_MODEL.encode(query).tolist()
            
            # Search in collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k
            )
            
            # Format results
            retrieved = []
            if results['metadatas'] and results['metadatas'][0]:
                for i, metadata in enumerate(results['metadatas'][0]):
                    retrieved.append({
                        "term": metadata["term"],
                        "definition": metadata["definition"],
                        "relevance": 1 - (results['distances'][0][i] if 'distances' in results else 0)
                    })
            
            return retrieved
        except Exception as e:
            print(f"⚠️  RAG retrieval failed: {e}")
            return []
    
    def format_context(self, retrieved: List[Dict]) -> str:
        """Format retrieved terms as context string for the LLM"""
        if not retrieved:
            return ""
        
        context = "\n📚 **Business Context:**\n"
        for item in retrieved:
            context += f"  • **{item['term']}**: {item['definition']}\n"
        
        return context


# Global client instance
_rag_client: Optional[RAGClient] = None


def init_rag():
    """Initialize the global RAG client"""
    global _rag_client
    _rag_client = RAGClient()


def get_rag_client() -> RAGClient:
    """Get or initialize the RAG client"""
    global _rag_client
    if _rag_client is None:
        init_rag()
    return _rag_client


def lookup_business_context(query: str, top_k: int = 3) -> str:
    """
    Simple helper to lookup business context and get formatted string
    
    Args:
        query: What to search for
        top_k: Number of results
        
    Returns:
        Formatted context string to include in prompts
    """
    client = get_rag_client()
    retrieved = client.retrieve(query, top_k)
    return client.format_context(retrieved)
