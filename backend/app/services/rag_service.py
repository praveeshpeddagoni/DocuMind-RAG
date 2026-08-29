from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio
from datetime import datetime
import numpy as np
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder

from app.services.embedding import EmbeddingService
from app.services.chunking import ChunkingService
from app.services.vector_store import VectorStore
from app.services.document_processor import DocumentProcessor

from app.schemas import QueryRequest  # Ensure QueryRequest is imported at the top
from langchain_google_genai import ChatGoogleGenerativeAI


class RAGService:
    """Main service that orchestrates the RAG pipeline with Hybrid Search."""

    def __init__(self):
        """Initialize RAG service with all components."""
        print("🔧 Initializing RAG Service...")

        # Initialize components
        self.embedding_service = EmbeddingService()
        self.reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.chunking_service = ChunkingService(chunk_size=1000, chunk_overlap=200)
        self.vector_store = VectorStore(self.embedding_service)

        print("✅ RAG Service initialized successfully")

    def process_and_store_document(
        self,
        file_path: str,
        document_id: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline: extract text, chunk, embed, and store.
        """
        print(f"📄 Processing document: {document_id}")

        try:
            # Step 1: Extract text from document
            text, char_count = DocumentProcessor.process_document(file_path)

            if not text.strip():
                return {
                    'success': False,
                    'error': 'No text could be extracted from document',
                    'document_id': document_id
                }

            # Step 2: Chunk the text
            doc_metadata = metadata or {}
            doc_metadata.update({
                'file_path': str(file_path),
                'char_count': char_count,
                'filename': Path(file_path).name
            })

            chunks = self.chunking_service.chunk_text(
                text=text,
                document_id=document_id,
                metadata=doc_metadata
            )

            # Step 3: Add chunks to vector store
            chunks_added = self.vector_store.add_chunks(chunks)

            result = {
                'success': True,
                'document_id': document_id,
                'char_count': char_count,
                'chunks_created': len(chunks),
                'chunks_added': chunks_added,
                'metadata': doc_metadata
            }

            print(f"✅ Successfully processed document {document_id}")
            return result

        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }
            print(f"❌ Error processing document {document_id}: {e}")
            return error_result

    async def process_and_store_document_with_progress(
        self,
        file_path: str,
        document_id: str,
        metadata: Dict[str, Any] = None,
        client_id: str = None,
        websocket_manager = None
    ) -> Dict[str, Any]:
        """
        Complete pipeline with real-time progress updates.
        """
        print(f"📄 Processing document: {document_id}")

        async def send_progress(stage: str, progress: int, details: str = ""):
            if client_id and websocket_manager:
                await websocket_manager.send_json(client_id, {
                    "type": "document_progress",
                    "document_id": document_id,
                    "stage": stage,
                    "progress": progress,
                    "details": details,
                    "timestamp": datetime.utcnow().isoformat()
                })

        try:
            # Step 1: Extract text (0-30%)
            await send_progress("extracting", 10, "Starting text extraction...")
            text, char_count = DocumentProcessor.process_document(file_path)
            await send_progress("extracting", 30, f"Extracted {char_count} characters")

            if not text.strip():
                await send_progress("error", 0, "No text could be extracted")
                return {
                    'success': False,
                    'error': 'No text could be extracted from document',
                    'document_id': document_id
                }

            # Step 2: Chunk the text (30-50%)
            await send_progress("chunking", 40, "Splitting into chunks...")
            doc_metadata = metadata or {}
            doc_metadata.update({
                'file_path': str(file_path),
                'char_count': char_count,
                'filename': Path(file_path).name
            })

            chunks = self.chunking_service.chunk_text(
                text=text,
                document_id=document_id,
                metadata=doc_metadata
            )
            await send_progress("chunking", 50, f"Created {len(chunks)} chunks")

            # Step 3: Generate embeddings (50-90%)
            await send_progress("embedding", 60, "Generating embeddings...")

            batch_size = 10
            chunks_added = 0

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                self.vector_store.add_chunks(batch)
                chunks_added += len(batch)

                progress = 60 + int((chunks_added / len(chunks)) * 30)
                await send_progress(
                    "embedding",
                    progress,
                    f"Embedded {chunks_added}/{len(chunks)} chunks"
                )

                await asyncio.sleep(0.1)

            # Step 4: Complete (90-100%)
            await send_progress("indexing", 95, "Finalizing vector store...")
            await asyncio.sleep(0.2)

            result = {
                'success': True,
                'document_id': document_id,
                'char_count': char_count,
                'chunks_created': len(chunks),
                'chunks_added': chunks_added,
                'metadata': doc_metadata
            }

            await send_progress("complete", 100, f"Successfully processed {len(chunks)} chunks")
            print(f"✅ Successfully processed document {document_id}")
            return result

        except Exception as e:
            await send_progress("error", 0, str(e))
            error_result = {
                'success': False,
                'error': str(e),
                'document_id': document_id
            }
            print(f"❌ Error processing document {document_id}: {e}")
            return error_result

    def search_documents(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3,
        document_ids: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Hybrid search combining dense vector search (FAISS), lexical search (BM25),
        Cross-Encoder reranking, and source retrieval tagging.
        """
        print(f"🔍 Searching for: '{query}'")
        if document_ids:
            print(f"📌 Filtering to {len(document_ids)} selected documents")

        try:
            # 1. Fetch vector search results and tag origin
            vector_results = self.vector_store.search(
                query=query,
                top_k=top_k * 4,
                score_threshold=score_threshold,
                document_ids=document_ids,
            )

            for item in vector_results:
                item["retrieved_via"] = "vector"

            # Get all available chunks from vector store for BM25 pool
            all_chunks = getattr(self.vector_store, "chunks", [])

            if document_ids and all_chunks:
                filtered_corpus = [
                    c for c in all_chunks if c.get("document_id") in document_ids
                ]
            else:
                filtered_corpus = all_chunks

            bm25_results = []
            if filtered_corpus:
                tokenized_corpus = [
                    c.get("text", "").lower().split() for c in filtered_corpus
                ]
                bm25 = BM25Okapi(tokenized_corpus)
                tokenized_query = query.lower().split()
                bm25_raw_scores = bm25.get_scores(tokenized_query)
                top_bm25_indices = np.argsort(bm25_raw_scores)[::-1][: top_k * 4]

                for idx in top_bm25_indices:
                    if bm25_raw_scores[idx] > 0:
                        chunk_data = dict(filtered_corpus[idx])
                        chunk_data["score"] = float(bm25_raw_scores[idx])
                        chunk_data["retrieved_via"] = "bm25"
                        bm25_results.append(chunk_data)

                # Combine using Reciprocal Rank Fusion
                fusion_candidates = self._reciprocal_rank_fusion(
                    vector_results, bm25_results
                )[:20]
            else:
                fusion_candidates = vector_results[:20]

            # 2. Apply Cross-Encoder Reranking
            if fusion_candidates and hasattr(self, "reranker"):
                pairs = [[query, res.get("text", "")] for res in fusion_candidates]
                rerank_scores = self.reranker.predict(pairs)

                for i, res in enumerate(fusion_candidates):
                    res["similarity_score"] = float(rerank_scores[i])
                    res["rerank_score"] = float(rerank_scores[i])

                final_results = sorted(
                    fusion_candidates, key=lambda x: x["rerank_score"], reverse=True
                )[:top_k]
            else:
                final_results = fusion_candidates[:top_k]

            return {
                "success": True,
                "query": query,
                "results_count": len(final_results),
                "results": final_results,
                "filtered_by_documents": document_ids is not None,
                "vector_store_stats": self.vector_store.get_stats(),
            }

        except Exception as e:
            print(f"❌ Hybrid Search & Rerank error: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "results": [],
            }

    def _reciprocal_rank_fusion(
        self,
        vector_results: List[Dict[str, Any]],
        bm25_results: List[Dict[str, Any]],
        k: int = 60,
    ) -> List[Dict[str, Any]]:
        """
        Fuses vector and BM25 search results using Reciprocal Rank Fusion (RRF)
        and tracks whether items were retrieved via vector, BM25, or both.
        """
        rrf_scores = {}
        docs_map = {}
        sources_map = {}

        # Process Vector Results
        for rank, item in enumerate(vector_results):
            doc_id = item.get("id") or item.get("chunk_id") or hash(item.get("text", ""))
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
            docs_map[doc_id] = item
            sources_map.setdefault(doc_id, set()).add("vector")

        # Process BM25 Results
        for rank, item in enumerate(bm25_results):
            chunk_data = item.get("chunk", item)
            doc_id = (
                chunk_data.get("id")
                or chunk_data.get("chunk_id")
                or hash(chunk_data.get("text", ""))
            )
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

            if doc_id not in docs_map:
                docs_map[doc_id] = chunk_data

            sources_map.setdefault(doc_id, set()).add("bm25")

        # Combine scores and tag final 'retrieved_via' source
        fused_results = []
        for doc_id, score in sorted(
            rrf_scores.items(), key=lambda x: x[1], reverse=True
        ):
            doc = docs_map[doc_id]
            doc["rrf_score"] = float(score)

            sources = sources_map[doc_id]
            if "vector" in sources and "bm25" in sources:
                doc["retrieved_via"] = "hybrid (both)"
            elif "vector" in sources:
                doc["retrieved_via"] = "vector"
            else:
                doc["retrieved_via"] = "bm25"

            fused_results.append(doc)

        return fused_results


def generate_answer(self, query: str, context: str, request: QueryRequest) -> str:
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.5-flash-lite",
        max_output_tokens=request.max_tokens,
        temperature=request.temperature
    )

    prompt = f"""
    Answer the user's question concisely using ONLY the provided context.
    Keep the answer short, under 3 bullet points, and do not repeat raw context.

    Context:
    {context}

    Question:
    {query}
    """

    response = llm.invoke(prompt)

    # FIX: Extract string content safely
    if hasattr(response, "content"):
        content = response.content
        if isinstance(content, list):
            # Handles list of dicts/blocks if returned by modern LangChain outputs
            return "".join([c.get("text", "") if isinstance(c, dict) else str(c) for c in content])
        return str(content)

    return str(response)

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive RAG service statistics."""
        return {
            'vector_store_stats': self.vector_store.get_stats(),
            'embedding_model': self.embedding_service.model_name,
            'chunk_size': self.chunking_service.chunk_size,
            'chunk_overlap': self.chunking_service.chunk_overlap
        }