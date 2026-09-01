# DocuMind AI

DocuMind AI is an end-to-end document question-answering application built around a hybrid Retrieval-Augmented Generation (RAG) pipeline. Users can upload documents, search their contents, ask questions in natural language, and receive LLM-generated answers grounded in retrieved document context with source information.

## Highlights

- Multi-format document ingestion for PDF, DOCX, TXT, HTML, and Markdown.
- OCR fallback for image-based PDFs.
- Recursive character-based chunking with overlap and document metadata.
- Hybrid retrieval using FAISS dense vector search and BM25 lexical search.
- Reciprocal Rank Fusion (RRF) to combine dense and lexical retrieval results.
- Cross-Encoder reranking to improve the final retrieval ordering.
- Context-aware document Q&A with selectable document filtering.
- Source attribution for generated answers.
- LLM provider abstraction with Gemini, OpenAI, and Groq support.
- Query history and analytics.
- Multi-document asynchronous processing with WebSocket progress updates.
- React frontend with document upload, chat, document management, analytics, settings, and PWA support.
- Dockerized FastAPI backend suitable for deployment on platforms such as Railway.

## Architecture

```text
                         ┌─────────────────────────┐
                         │      React Frontend     │
                         │ Upload / Chat / Search  │
                         │ Docs / Analytics / PWA  │
                         └────────────┬────────────┘
                                      │ REST + WebSocket
                                      ▼
                         ┌─────────────────────────┐
                         │      FastAPI Backend    │
                         │   Routers + Services    │
                         └────────────┬────────────┘
                                      │
                    ┌─────────────────┴─────────────────┐
                    │                                   │
                    ▼                                   ▼
          ┌──────────────────┐                ┌──────────────────┐
          │ Document Ingest  │                │   PostgreSQL     │
          │ PDF/DOCX/TXT/    │                │ Metadata / Query │
          │ HTML/Markdown    │                │    Analytics      │
          └────────┬─────────┘                └──────────────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Text Extraction  │
          │ + OCR Fallback   │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Recursive        │
          │ Chunking         │
          └────────┬─────────┘
                   │
                   ▼
          ┌─────────────────────────────┐
          │ Embedding Generation        │
          │ all-MiniLM-L6-v2            │
          └─────────────┬───────────────┘
                        │
                        ▼
          ┌─────────────────────────────┐
          │ FAISS Vector Store          │
          └─────────────┬───────────────┘
                        │
              Query    / \    Query
                     /     \
                    ▼       ▼
              FAISS         BM25
             Dense Search  Lexical Search
                    \       /
                     \     /
                      ▼   ▼
                ┌──────────────┐
                │ RRF Fusion   │
                └──────┬───────┘
                       ▼
                ┌──────────────┐
                │ Cross-Encoder│
                │  Reranking   │
                └──────┬───────┘
                       ▼
                ┌──────────────┐
                │ LLM Answer   │
                │ + Sources    │
                └──────────────┘
```

## RAG Pipeline

### 1. Document ingestion

Uploaded files are validated, stored, and processed. The backend currently supports:

- PDF
- DOCX
- TXT
- HTML
- Markdown

PDFs are first processed with text extraction and fall back to OCR for image-based documents when OCR dependencies are available.

### 2. Chunking

Extracted text is normalized and split with a recursive character text splitter using approximately 1000-character chunks and 200-character overlap. Chunk metadata includes document ID, chunk ID, chunk index, and document metadata.

### 3. Embeddings

Document and query text are embedded using:

`sentence-transformers/all-MiniLM-L6-v2`

Embeddings are normalized before insertion/search in FAISS so inner-product similarity behaves as cosine similarity.

### 4. Hybrid retrieval

For each query, DocuMind combines:

- Dense semantic retrieval with FAISS.
- Lexical retrieval with BM25.

The two ranked result sets are merged with Reciprocal Rank Fusion (RRF).

### 5. Reranking

The fused candidate set is reranked with:

`cross-encoder/ms-marco-MiniLM-L-6-v2`

The highest-ranked results are then used as context for answer generation.

### 6. Answer generation

The application sends the retrieved context and user question to the configured LLM provider. The current provider service supports:

- Google Gemini
- OpenAI
- Groq

A provider priority/fallback mechanism is implemented so an available provider can be selected when the preferred provider is unavailable.

## Evaluation

RAG quality was evaluated with RAGAS over three evaluation runs, using the reported averages:

| Metric | Average |
|---|---:|
| Faithfulness | 91.8% |
| Answer Relevance | 89.8% |

These evaluation results are external to the current GitHub codebase and are reported here based on the project's evaluation runs.

## Features

### Document management

- Upload one or multiple documents.
- Track processing status.
- View document metadata.
- Preview and access processed document content.
- Delete documents.
- Rebuild the vector store from stored documents.

### Search and Q&A

- Semantic + lexical hybrid search.
- Cross-Encoder reranking.
- Search within selected documents.
- Context-aware follow-up questions.
- Source document attribution.
- Configurable retrieval and generation parameters.

### Analytics

The backend stores query history and tracks:

- Total queries.
- Total documents.
- Average response time.
- Query/answer history.
- Basic popularity/similarity tracking.

### Real-time processing

Multi-document uploads can be processed asynchronously with WebSocket progress events for stages such as extraction, chunking, embedding/indexing, completion, and errors.

### Frontend

The React application provides:

- Drag-and-drop document uploads.
- Chat interface.
- Document management.
- Analytics dashboard.
- Settings panel.
- Lazy loading for non-critical views.
- PWA/service-worker support.
- Responsive UI animations and notifications.

## Tech Stack

### Backend

- Python
- FastAPI
- SQLAlchemy
- PostgreSQL
- FAISS
- Sentence Transformers
- BM25 (`rank-bm25`)
- Cross-Encoder
- LangChain text splitters
- Pydantic
- WebSockets
- PyTesseract + pdf2image for OCR

### Frontend

- React
- Vite
- React Router
- Zustand
- Tailwind CSS
- Framer Motion
- Axios
- Recharts
- React Dropzone
- React Markdown
- Vite PWA plugin

### Deployment

- Docker
- Uvicorn
- Railway-compatible backend configuration

## Project Structure

```text
DocuMind-RAG/
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routers/
│   │   ├── services/
│   │   │   ├── chunking.py
│   │   │   ├── document_processor.py
│   │   │   ├── embedding.py
│   │   │   ├── llm.py
│   │   │   ├── rag_service.py
│   │   │   └── vector_store.py
│   │   ├── utils/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── styles/
│   │   └── App.jsx
│   └── package.json
│
└── README.md
```

## Local Setup

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL
- Git
- Poppler for PDF OCR workflows
- Tesseract OCR for image-based PDFs

### 1. Clone the repository

```bash
git clone https://github.com/praveeshpeddagoni/DocuMind-RAG.git
cd DocuMind-RAG
```

### 2. Configure the backend

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment.

Windows:

```bash
.venv\Scripts\activate
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create `backend/.env`:

```env
ENVIRONMENT=development

DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/document_qa

GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key

GEMINI_MODEL=gemini-3.5-flash
OPENAI_MODEL=gpt-4o
GROQ_MODEL=llama3-8b-8192

USE_GPU=true
POPPLER_PATH=/usr/bin
```

Only the LLM provider keys you plan to use are required.

### 4. Start the backend

From `backend/`:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

```text
http://localhost:8000
```

FastAPI documentation:

```text
http://localhost:8000/docs
```

### 5. Start the frontend

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Vite will print the local frontend URL in the terminal.

## API Overview

The backend exposes API routes under the `/api/v1` prefix.

Important endpoints include:

```text
POST /api/v1/documents/upload
POST /api/v1/documents/upload-with-progress
GET  /api/v1/documents/
GET  /api/v1/documents/{document_id}
GET  /api/v1/documents/{document_id}/content
GET  /api/v1/documents/{document_id}/preview
DELETE /api/v1/documents/{document_id}

POST /api/v1/documents/search
POST /api/v1/documents/reset-vector-store

POST /api/v1/query/ask
POST /api/v1/query/ask-with-context
POST /api/v1/query/search
GET  /api/v1/query/history

GET  /api/v1/documents/rag-stats
```

The exact available analytics/system endpoints can be inspected from the FastAPI OpenAPI documentation at `/docs`.

## Upload Limits

The backend currently enforces a maximum upload size of **20 MB per file**.

Supported extensions:

```text
.pdf
.docx
.txt
.html
.md
```

## Persistence

The application stores:

- Original documents on disk.
- Processed text on disk.
- FAISS index data on disk.
- Chunk metadata alongside the vector store.
- Application metadata and query analytics in PostgreSQL.

The production configuration uses `/tmp/documind` for application data paths, so persistent storage should be configured appropriately for the deployment environment.

## Docker

The backend includes a production Dockerfile.

Build:

```bash
cd backend
docker build -t documind-backend .
```

Run:

```bash
docker run -p 8000:8000 --env-file .env documind-backend
```

The container starts FastAPI with Uvicorn on port `8000`.

## Production Deployment Notes

The repository contains deployment configuration for a Railway-style backend deployment.

For production:

1. Set `ENVIRONMENT=production`.
2. Provide a production `DATABASE_URL`.
3. Configure the required LLM API keys.
4. Provide persistent storage for uploaded documents and vector-store data when required.
5. Configure the frontend origin instead of using a permissive CORS configuration.
6. Verify OCR system dependencies (Tesseract and Poppler) in the deployment image.

The current backend production configuration intentionally disables GPU usage and uses CPU execution.

## Testing

The backend requirements include tooling for:

- Pytest
- Async API testing
- Coverage

Run tests from the backend directory:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

## Design Notes

The core retrieval path is intentionally hybrid:

```text
Query
  ↓
FAISS semantic search
  +
BM25 lexical search
  ↓
Reciprocal Rank Fusion
  ↓
Cross-Encoder reranking
  ↓
Top context chunks
  ↓
LLM generation
  ↓
Answer + sources
```

This combination is designed to capture both semantic similarity and exact lexical matches before the final reranking stage.

## Known Implementation Notes

- The backend currently supports a 20 MB upload limit even though some frontend text still references 50 MB. The backend limit is authoritative.
- Query-answer generation is provider-configurable, while Gemini is the default provider priority in the current service.
- Evaluation scores in this README are from external RAGAS evaluation runs and are not generated by the current GitHub application at runtime.

## License

Add the project's preferred license here before publishing under an explicit open-source license.
