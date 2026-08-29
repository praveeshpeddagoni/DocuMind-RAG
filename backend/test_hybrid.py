import sys
import os

# Ensure backend directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.rag_service import RAGService

def test_search():
    print("🚀 Initializing RAG Service for testing...")
    rag = RAGService()
    
    # Test query containing specific technical keywords or concepts from your PDFs
    test_query = "Binary Search"  # Change this to a term or question relevant to your uploaded PDFs
    
    print(f"\n🔍 Running hybrid search for query: '{test_query}'")
    response = rag.search_documents(query=test_query, top_k=3)
    
    if response['success']:
        print(f"\n✅ Search successful! Found {response['results_count']} results:\n")
        for i, res in enumerate(response['results'], 1):
            print(f"--- Result {i} ---")
            print(f"Score: {res.get('similarity_score', 'N/A')}")
            print(f"Document ID: {res.get('document_id', 'Unknown')}")
            print(f"Text snippet: {res.get('text', '')[:200]}...\n")
    else:
        print(f"❌ Search failed: {response.get('error')}")

if __name__ == "__main__":
    test_search()