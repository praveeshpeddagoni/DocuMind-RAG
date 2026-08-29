import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService

def test_hybrid_rerank():
    print("🚀 Initializing RAG Service with Hybrid Search & Reranking...")
    rag = RAGService()
    
    # Test query to verify semantic and keyword matching + reranking
    test_query = "binary search"
    
    print(f"\n🔍 Running search and rerank for query: '{test_query}'")
    response = rag.search_documents(query=test_query, top_k=3)
    
    if response['success']:
        print(f"\n✅ Search successful! Found {response['results_count']} results:\n")
        for i, res in enumerate(response['results'], 1):
            print(f"--- Result {i} ---")
            print(f"Rerank Score: {res.get('rerank_score', 'N/A')}")
            print(f"Document Name: {res.get('document_name', 'Unknown')}")
            print(f"Text snippet: {res.get('text', '')[:200]}...\n")
    else:
        print(f"❌ Search failed: {response.get('error')}")

if __name__ == "__main__":
    test_hybrid_rerank()