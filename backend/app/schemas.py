# backend/app/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str = Field(..., description="The query string for RAG retrieval")
    top_k: Optional[int] = Field(default=5, description="Number of results to retrieve")
    score_threshold: Optional[float] = Field(default=0.3, description="Minimum similarity threshold")
    document_ids: Optional[List[str]] = Field(default=None, description="Filter search to specific documents")
    max_tokens: Optional[int] = Field(default=256, description="Max tokens for LLM output")
    temperature: Optional[float] = Field(default=0.2, description="Sampling temperature")

class SourceInfo(BaseModel):
    document_name: str
    page: Optional[int] = None
    similarity_score: float
    content: str
    retrieved_via: Optional[str] = "vector"

class QueryResponse(BaseModel):
    success: bool
    answer: str
    sources: List[SourceInfo]
    llm_used: str
    response_time: float
    context_chunks_count: int
    error: Optional[str] = None