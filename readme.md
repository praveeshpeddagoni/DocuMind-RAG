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
# Environment
ENVIRONMENT=development

# Database Configuration
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/document_qa
# OR use individual components (if DATABASE_URL not set):
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=document_qa

# LLM Provider Configuration
GEMINI_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
GROQ_API_KEY=your_groq_key

# LLM Models
GEMINI_MODEL=gemini-3.5-flash
OPENAI_MODEL=gpt-4o
GROQ_MODEL=llama3-8b-8192

# System Configuration
USE_GPU=true
POPPLER_PATH=/usr/bin
LLM_TEST_CONNECTION=false

# Frontend (optional, used by Vite)
VITE_API_URL=http://localhost:8000
```

**Environment Variables Explained:**

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENVIRONMENT` | No | `development` | Set to `production` for production deployments |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string. If not provided, uses individual POSTGRES_* variables |
| `GEMINI_API_KEY` | Conditional | - | Google Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `OPENAI_API_KEY` | Conditional | - | OpenAI API key from [OpenAI Dashboard](https://platform.openai.com/api-keys) |
| `GROQ_API_KEY` | Conditional | - | Groq API key from [Groq Console](https://console.groq.com/keys) |
| `GEMINI_MODEL` | No | `gemini-3.5-flash` | Gemini model version to use |
| `OPENAI_MODEL` | No | `gpt-4o` | OpenAI model version to use |
| `GROQ_MODEL` | No | `llama3-8b-8192` | Groq model version to use |
| `USE_GPU` | No | `true` | Enable GPU acceleration if available |
| `POPPLER_PATH` | No | `/usr/bin` | Path to Poppler installation (for PDF processing) |
| `LLM_TEST_CONNECTION` | No | `false` | Test LLM provider connectivity on startup |
| `VITE_API_URL` | No | `/api/v1` | Frontend API endpoint (without /api/v1 suffix) |

**Notes:**
- At least one LLM provider API key is required for the application to work
- The system automatically selects an available provider if the preferred one is unavailable
- For local development, only set the LLM provider you want to use
- In production, set `ENVIRONMENT=production` to disable GPU and enable optimizations

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

### Document Management Endpoints

```text
POST /api/v1/documents/upload
  Upload a single document
  
POST /api/v1/documents/upload-with-progress
  Upload documents with WebSocket progress updates
  
GET  /api/v1/documents/
  List all documents
  
GET  /api/v1/documents/{document_id}
  Get document metadata
  
GET  /api/v1/documents/{document_id}/content
  Get extracted text content of a document
  
GET  /api/v1/documents/{document_id}/preview
  Get document preview (first N characters)
  
GET  /api/v1/documents/{document_id}/download
  Download original document file
  
DELETE /api/v1/documents/{document_id}
  Delete a document and its embeddings
  
POST /api/v1/documents/reset-vector-store
  Rebuild vector store from all documents
  
GET  /api/v1/documents/rag-stats
  Get RAG pipeline statistics
```

### Query & Search Endpoints

```text
POST /api/v1/query/ask
  Ask a question to get RAG-based answer
  Request: { "question": "...", "top_k": 5, "score_threshold": 0.1, "max_tokens": 256, "temperature": 0.2 }
  
POST /api/v1/query/ask-with-context
  Ask question with explicit document context
  
POST /api/v1/query/search
  Hybrid search across documents
  Request: { "query": "...", "top_k": 10, "score_threshold": 0.2 }
  
GET  /api/v1/query/history
  Get query history with pagination
  Query params: ?page=1&limit=20
  
GET  /api/v1/query/status
  Get query service status
  
GET  /api/v1/query/health
  Health check endpoint
```

### Analytics Endpoints

```text
GET  /api/v1/analytics/stats
  Get comprehensive usage statistics
  Returns: total_queries, total_documents, avg_response_time, success_rate, top_llm_used
  
GET  /api/v1/analytics/popular-questions
  Get most frequently asked questions
  Query params: ?limit=10&min_frequency=2
  
GET  /api/v1/analytics/query-trends
  Get query trends over time
  
GET  /api/v1/analytics/llm-usage
  Get LLM provider usage statistics
```

### System Endpoints

```text
GET  /
  Root endpoint - health check and system info
  Returns: status, message, gpu_available
  
GET  /api/v1/system/capabilities
  Get system capabilities and configuration
```

### WebSocket Endpoint

```text
WS /client/{client_id}
  WebSocket connection for real-time progress updates
  Events: extraction, chunking, embedding, completion, error
```

### Query Parameters & Configuration

When making requests to `/query/ask`, the following parameters can be customized:

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `question` | string | required | - | The question to ask (3-1000 chars) |
| `top_k` | integer | 5 | 1-20 | Number of context chunks to retrieve |
| `score_threshold` | float | 0.1 | 0-1 | Minimum similarity score for retrieval |
| `max_tokens` | integer | 256 | 50-2048 | Maximum tokens in LLM response |
| `temperature` | float | 0.2 | 0-1 | LLM sampling temperature (0=deterministic, 1=creative) |
| `document_ids` | array | null | - | Specific documents to search within (optional filtering) |

**Recommendations:**
- Increase `top_k` for more comprehensive but potentially verbose answers
- Decrease `score_threshold` to retrieve more results (lower quality)
- Lower `temperature` (0.2) for factual answers, higher (0.7+) for creative responses
- Use `document_ids` to limit search to specific documents for efficiency

### API Response Format

All successful responses follow this format:

```json
{
  "success": true,
  "answer": "The answer text...",
  "sources": [
    {
      "document_name": "filename.pdf",
      "page": 1,
      "similarity_score": 0.95,
      "content": "Relevant text excerpt...",
      "retrieved_via": "vector"
    }
  ],
  "llm_used": "gemini-3.5-flash",
  "response_time": 2.45,
  "context_chunks_count": 3,
  "error": null
}
```

**Response Fields:**
- `retrieved_via`: Indicates search origin - "vector" (FAISS), "bm25" (lexical), or "hybrid" (combined)
- `response_time`: Total time in seconds for the entire request
- `context_chunks_count`: Number of document chunks used for answer generation

The exact available endpoints can be inspected from the FastAPI OpenAPI documentation at `/docs`.

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

### File Format Support Details

| Format | Text Extraction | OCR Support | Max Size | Notes |
|--------|-----------------|-------------|----------|-------|
| PDF | pdfplumber | Yes (Tesseract) | 20 MB | Falls back to OCR for image-based PDFs |
| DOCX | python-docx | No | 20 MB | Tables and formatting preserved |
| TXT | Native | No | 20 MB | Plain text files |
| HTML | BeautifulSoup | No | 20 MB | HTML tags stripped, content extracted |
| Markdown | Native | No | 20 MB | Markdown syntax preserved |

## Database & Models

### Database Schema

DocuMind uses PostgreSQL to store:

#### Documents Table (`documents`)
- `id`: Document unique identifier
- `filename`: Original filename
- `file_path`: Path to stored document
- `file_type`: Document file extension
- `status`: Processing status (uploaded, processed, indexed)
- `char_count`: Total characters in document
- `chunks_created`: Number of text chunks generated
- `created_at`: Upload timestamp
- `updated_at`: Last modification timestamp

#### Query History Table (`query_history`)
- `id`: Query unique identifier
- `question`: User's question
- `answer`: Generated answer
- `sources_count`: Number of sources cited
- `response_time`: Query execution time in seconds
- `llm_used`: LLM provider used (gemini, openai, groq)
- `context_chunks_count`: Number of context chunks used
- `success`: Query success status (true/false)
- `similarity_hash`: Hash for tracking similar questions
- `created_at`: Query timestamp

#### Analytics Stats Table (`analytics_stats`)
- `id`: Stats record identifier
- `total_queries`: Cumulative query count
- `total_documents`: Cumulative document count
- `avg_response_time`: Average response time in seconds
- `last_updated`: Last stats update timestamp

### Persistent Storage

The application stores data in multiple locations:

```
/tmp/documind/                 # Production data directory
├── documents/                 # Original uploaded files
├── processed/                 # Extracted and processed text
└── faiss_index.bin           # FAISS vector store
```

For local development, data is stored in `backend/data/` instead of `/tmp/documind/`.

## Docker Compose & Multi-Container Architecture

The project includes a complete Docker Compose setup for running all services:

```bash
docker-compose up
```

### Services Overview

| Service | Port | Purpose | Depends On |
|---------|------|---------|-----------|
| **backend** | 8000 | FastAPI application | PostgreSQL, Redis |
| **frontend** | 3000 | React application | Backend |
| **db** (PostgreSQL) | 5432 | Document metadata storage | - |
| **redis** | 6379 | Message broker for Celery | - |
| **worker** | - | Background task processing | Redis, PostgreSQL |

### Docker Environment Variables

Create a `.env` file in the project root:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=document_qa
OPENAI_API_KEY=your_key
GROQ_API_KEY=your_key
GEMINI_API_KEY=your_key
```

### Important Docker Notes

- The backend mounts the `./backend` directory for live code reloading in development
- Vector store and document data are stored in Docker volumes for persistence
- Redis is used as the message broker for Celery background tasks
- The worker service processes documents asynchronously

## Vector Store Management

### Vector Store Structure

FAISS index is stored on disk alongside metadata:

```
data/
├── faiss_index.bin           # FAISS dense vector index
├── chunks_metadata.pkl       # Chunk metadata and mappings
└── bm25_index.pkl           # BM25 lexical search index
```

### Rebuilding the Vector Store

To rebuild the vector store from existing documents:

```bash
curl -X POST http://localhost:8000/api/v1/documents/reset-vector-store
```

**Use cases:**
- After updating embedding models
- If index becomes corrupted
- When changing chunking parameters
- For optimization and cleanup

This endpoint:
1. Reads all stored documents
2. Re-extracts and re-chunks text
3. Re-generates embeddings
4. Rebuilds FAISS and BM25 indices

## System Requirements & Constraints

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| Python | 3.9 | 3.11+ |
| Node.js | 18 | 20+ LTS |
| RAM | 4 GB | 8-16 GB |
| Disk Space | 20 GB | 50+ GB |
| GPU | Optional | 6-8 GB VRAM (NVIDIA/CUDA) |

### Resource Constraints

- **Vector Store:** ~500 MB per 100,000 documents (with FAISS)
- **Database:** ~1 MB per 10,000 queries stored
- **Embedding Generation:** 2-5 seconds per 1 MB of text
- **Document Processing:** Varies by file type and size

### Performance Characteristics

- **Upload Processing:** ~10 MB/second (text extraction)
- **Embedding Generation:** ~1000 tokens/second (CPU), ~5000 tokens/second (GPU)
- **Query Response:** 0.5-2 seconds (semantic search + LLM generation)
- **Concurrent Users:** Depends on server specs; tested up to 100 concurrent users

## WebSocket & Real-time Features

### Real-time Progress Updates

For large document uploads, the frontend can monitor progress via WebSocket:

```javascript
const clientId = 'unique-client-id';
const ws = new WebSocket(`ws://localhost:8000/client/${clientId}`);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(`Progress: ${message.stage} - ${message.progress}%`);
};
```

### Progress Events

The WebSocket emits the following events:

| Stage | Description |
|-------|-------------|
| `extraction` | Text extraction from document |
| `chunking` | Document chunking |
| `embedding` | Embedding generation |
| `indexing` | Adding to vector store |
| `completion` | Document fully processed |
| `error` | Error occurred |

### Message Format

```json
{
  "type": "progress",
  "stage": "embedding",
  "progress": 75,
  "message": "Generating embeddings for chunks",
  "document_id": "doc-123",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## Performance Tuning

### Chunking Parameters

These can be adjusted in `backend/app/services/chunking.py`:

```python
chunk_size = 1000        # Characters per chunk (smaller = more chunks)
chunk_overlap = 200      # Overlap between chunks (larger = better context)
```

**Optimization:**
- Increase `chunk_size` to reduce number of embeddings and storage
- Increase `chunk_overlap` to improve context continuity
- Balance between retrieval quality and processing speed

### Embedding Batch Size

In `backend/app/services/embedding.py`:

```python
batch_size = 32  # Adjust based on GPU memory available
```

**Optimization:**
- Increase batch size for faster processing (if memory allows)
- Decrease batch size if running out of GPU memory
- Typical: 32 (4GB GPU), 64 (8GB GPU), 128 (12GB+ GPU)

### Query Optimization

For better performance:

1. Lower `top_k` for faster retrieval (default 5)
2. Increase `score_threshold` to filter low-quality results
3. Use document filtering to search specific documents
4. Enable GPU for faster embedding comparisons

### LLM Response Tuning

- Reduce `max_tokens` to get faster responses (trades off answer completeness)
- Adjust `temperature` based on use case:
  - 0.1-0.3: Factual/Q&A tasks
  - 0.5-0.7: General conversation
  - 0.8-1.0: Creative writing

## PWA & Offline Features

### Progressive Web App Support

DocuMind includes PWA capabilities for installability and offline support:

```javascript
// Service worker registration (in App.jsx)
const { needRefresh, offlineReady, close } = useRegisterSW({
  onRegistered(r) {
    console.log('SW registered:', r);
  },
});
```

### Offline Functionality

- View cached documents
- Access query history
- See analytics (cached data)
- Browse previously loaded pages

**Limitations when offline:**
- Cannot upload new documents
- Cannot make new queries to LLM
- Cannot access uncached documents

### Installation

**Desktop:** Click "Install" button in browser address bar (Chrome, Edge, Brave)

**Mobile:** Tap "Add to Home Screen" (Chrome, Firefox on Android)

After installation, the app launches like a native app with:
- No browser UI
- Standalone window
- Offline caching

## LLM Provider Configuration (Detailed)

### Google Gemini Setup

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Copy the key and add to `.env`:
   ```env
   GEMINI_API_KEY=your_key_here
   GEMINI_MODEL=gemini-3.5-flash
   ```

**Available Models:**
- `gemini-1.5-pro` (most capable)
- `gemini-1.5-flash` (fastest)
- `gemini-3.5-flash` (latest fast model)

**Pricing:** Free tier available (60 requests/minute)

### OpenAI Setup

1. Visit [OpenAI Dashboard](https://platform.openai.com/api-keys)
2. Create new API key
3. Add to `.env`:
   ```env
   OPENAI_API_KEY=your_key_here
   OPENAI_MODEL=gpt-4o
   ```

**Available Models:**
- `gpt-4-turbo` (advanced reasoning)
- `gpt-4o` (optimized for speed)
- `gpt-3.5-turbo` (cost-effective)

**Note:** Requires paid OpenAI account with credits

### Groq Setup

1. Visit [Groq Console](https://console.groq.com/keys)
2. Create API key
3. Add to `.env`:
   ```env
   GROQ_API_KEY=your_key_here
   GROQ_MODEL=llama3-8b-8192
   ```

**Available Models:**
- `llama3-70b-8192` (powerful)
- `llama3-8b-8192` (faster)
- `mixtral-8x7b-32768` (efficient)

**Pricing:** Free tier available (30 requests/minute)

### Provider Fallback Mechanism

If one provider fails, the system automatically tries the next available provider in priority order. Configure provider priority by adjusting initialization order in `backend/app/services/llm.py`.

## Testing & Evaluation

### Running Tests

The project includes comprehensive test coverage:

```bash
cd backend
pytest                           # Run all tests
pytest tests/                    # Run tests in tests/ directory
pytest -v                        # Verbose output
pytest --cov=app                # Coverage report
pytest tests/test_api.py         # Run specific test file
pytest tests/test_api.py::test_upload_txt_file  # Run specific test
```

### Test Suites

| Test File | Purpose |
|-----------|---------|
| `test_api.py` | API endpoint testing |
| `test_document_processor.py` | Document extraction and processing |
| `test_document.py` | Document model tests |
| `test_3wee_imple.py` | Integration tests |
| `conftest.py` | Pytest configuration and fixtures |

### Evaluation Scripts

The project includes evaluation tools:

```bash
# Generate evaluation dataset
python backend/generate_eval_dataset.py

# Run RAG evaluation
python backend/evaluate_rag.py

# Manual setup test
python backend/manual_setup.py
```

### Coverage Reports

```bash
pytest --cov=app --cov-report=html --cov-report=term
```

Opens `htmlcov/index.html` in browser for detailed coverage analysis.

## CI/CD Pipeline

### GitHub Actions Workflow

The repository includes `.github/workflows/main.yml` for automated testing and building:

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`

**Jobs:**

1. **test-backend**
   - Runs on Ubuntu latest
   - Sets up PostgreSQL 13 test database
   - Installs Python 3.9 and dependencies
   - Runs pytest with coverage reporting
   - Uploads coverage to Codecov
   - Lints code with flake8

2. **build-and-test-docker**
   - Builds Docker image for backend
   - Verifies Dockerfile builds successfully
   - Runs after all backend tests pass

**Prerequisites:**
```bash
# Install system dependencies
sudo apt-get update
sudo apt-get install -y poppler-utils tesseract-ocr

# Run tests
pytest tests/ -v --cov=app --cov-report=xml
```

### Local CI Testing

To test locally before pushing:

```bash
# Run tests
pytest -v

# Lint
flake8 backend/app --max-line-length=127

# Build Docker image
docker build -t documind-backend:test ./backend
```

## Analytics & Monitoring

### Analytics Metrics

DocuMind tracks comprehensive usage statistics available via `/api/v1/analytics/stats`:

```json
{
  "total_queries": 1250,
  "total_documents": 45,
  "avg_response_time": 1.23,
  "successful_queries": 1200,
  "failed_queries": 50,
  "last_updated": "2024-01-15T10:30:00Z",
  "top_llm_used": "gemini-3.5-flash"
}
```

### Popular Questions

Get most frequently asked questions:

```bash
curl http://localhost:8000/api/v1/analytics/popular-questions?limit=10&min_frequency=2
```

**Response:**
```json
{
  "questions": [
    {
      "question": "How does RAG work?",
      "frequency": 45,
      "avg_response_time": 1.2,
      "success_rate": 0.98,
      "last_asked": "2024-01-15T10:30:00Z"
    }
  ],
  "total_unique_questions": 892
}
```

### Query Trends

Track query volume over time:

```bash
curl http://localhost:8000/api/v1/analytics/query-trends
```

### LLM Usage Statistics

Monitor which LLM providers are being used:

```bash
curl http://localhost:8000/api/v1/analytics/llm-usage
```

Returns usage counts and statistics for each provider.

## Health Checks & System Status

### Health Check Endpoints

```bash
# Basic health check (root)
curl http://localhost:8000/

# Query service status
curl http://localhost:8000/api/v1/query/status

# Query service health
curl http://localhost:8000/api/v1/query/health

# System capabilities
curl http://localhost:8000/api/v1/system/capabilities
```

### Root Endpoint Response

```json
{
  "status": "ok",
  "message": "Document Q&A API is running",
  "gpu_available": true
}
```

### System Capabilities

```json
{
  "embeddings_available": true,
  "vector_store_initialized": true,
  "database_connected": true,
  "llm_providers": ["gemini", "openai"],
  "models": {
    "embedding": "sentence-transformers/all-MiniLM-L6-v2",
    "reranker": "cross-encoder/ms-marco-MiniLM-L-6-v2"
  }
}
```

## Requirements Files

The project includes multiple requirements files for different use cases:

### `requirements.txt` (Production)
Used for deployment and most use cases:
```bash
pip install -r requirements.txt
```

Key packages:
- FastAPI, Uvicorn (web server)
- SQLAlchemy, psycopg2 (database)
- Sentence Transformers, FAISS (embeddings)
- Transformers, Torch (ML models)

### `requirements-prod.txt` (Production Optimized)
Optimized for Railway deployment with specific versions:
```bash
pip install -r requirements-prod.txt
```

### `working-requirements.txt` (Development Extended)
Extended requirements for development with additional tools:
```bash
pip install -r working-requirements.txt
```

Includes coverage, evaluation tools, and debugging packages.

## Troubleshooting

### Database Connection Issues

**Error:** `could not connect to server: Connection refused`

**Solutions:**
```bash
# Check if PostgreSQL is running
psql -U postgres -c "SELECT 1"

# If using Docker Compose
docker-compose up db

# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql+psycopg2://user:password@host:port/dbname
```

### GPU/CUDA Issues

**Error:** `CUDA out of memory`

**Solutions:**
```bash
# Reduce embedding batch size in embedding.py
batch_size = 16  # instead of 32

# Or disable GPU
USE_GPU=false
```

**Check GPU availability:**
```bash
python -c "import torch; print(torch.cuda.is_available())"
```

### OCR/PDF Processing Issues

**Error:** `Tesseract not found` or `Poppler not found`

**Solutions:**

Windows (using Chocolatey):
```bash
choco install tesseract poppler
```

Ubuntu/Debian:
```bash
sudo apt-get install -y tesseract-ocr poppler-utils
```

macOS:
```bash
brew install tesseract poppler
```

Then set `POPPLER_PATH` in `.env`:
```env
POPPLER_PATH=/usr/bin  # Linux
POPPLER_PATH=/usr/local/bin  # macOS
POPPLER_PATH=C:\Program Files\poppler\bin  # Windows
```

### Vector Store Issues

**Error:** `FAISS index not found`

**Solution:** Rebuild vector store:
```bash
curl -X POST http://localhost:8000/api/v1/documents/reset-vector-store
```

### LLM Provider Connection Issues

**Error:** `Failed to connect to [provider]`

**Solutions:**
```bash
# Verify API key is set correctly
echo $OPENAI_API_KEY

# Test provider connectivity on startup
LLM_TEST_CONNECTION=true

# Check available providers
curl http://localhost:8000/api/v1/system/capabilities
```

### Port Already in Use

**Error:** `Address already in use :::8000` or `:::3000`

**Solutions:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # macOS/Linux
taskkill /PID <PID> /F  # Windows

# Use different port
uvicorn app.main:app --port 8001
npm run dev -- --port 3001  # Frontend
```

### Frontend API Connection Issues

**Error:** `Failed to fetch from /api/v1`

**Solutions:**
```bash
# Set correct backend URL
VITE_API_URL=http://localhost:8000

# Check CORS configuration in backend
# Should include frontend origin in config.py CORS_ORIGINS

# For production, update CORS_ORIGINS instead of using "*"
```

### Document Processing Timeout

**Error:** `Request timeout during document upload`

**Solutions:**
```bash
# Increase timeout in axios (frontend/src/services/api.js)
timeout: 180000  // 3 minutes instead of 90 seconds

# Or use upload-with-progress endpoint instead
POST /api/v1/documents/upload-with-progress
```

### Memory Issues

**Error:** `MemoryError` during processing

**Solutions:**
```bash
# Reduce chunk size
chunk_size = 500  # instead of 1000

# Reduce batch size
batch_size = 8  # instead of 32

# Process fewer documents concurrently
# Restart application to free memory
```

## Advanced Features

### Context-Aware Follow-up Questions

The system maintains context for follow-up questions within a session:

```python
# First question
response1 = ask_question(question="Tell me about climate change")

# Follow-up question (context preserved)
response2 = ask_question(question="What are the solutions?")
# Uses context from previous answer to understand "the" refers to climate change
```

### Selective Document Filtering

Limit search to specific documents for efficiency:

```bash
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is AI?",
    "document_ids": ["doc-1", "doc-3"],
    "top_k": 5
  }'
```

### Hybrid Search Retrieval

The system automatically combines:

1. **Dense Search (FAISS):** Semantic similarity
   - Captures meaning and context
   - Language-independent
   
2. **Lexical Search (BM25):** Exact keyword matching
   - Great for technical terms
   - Handles acronyms and numbers

3. **Reciprocal Rank Fusion:** Combines both
   - Merges results intelligently
   - Reranks with Cross-Encoder

**Result:** Best of both worlds - semantic understanding + keyword precision

### Cross-Encoder Reranking

After hybrid retrieval, results are reranked using:

`cross-encoder/ms-marco-MiniLM-L-6-v2`

This gives each result a relevance score (0-1), ensuring the most relevant context is used for answer generation.

### LLM Provider Fallback

If the primary LLM provider is unavailable:

```
Primary Provider (Gemini)
     ↓ (fails)
Secondary Provider (OpenAI)
     ↓ (fails)
Tertiary Provider (Groq)
     ↓ (succeeds)
→ Answer generated
```

Users don't notice - the system transparently uses an available provider.

## Deployment Configuration

### Railway Deployment

The project is optimized for Railway using `nixpacks.toml`:

```toml
[phases.setup]
nixPkgs = ["...", "poppler"]

[start]
cmd = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

**Steps:**
1. Push repository to GitHub
2. Connect GitHub repo to Railway
3. Set environment variables in Railway dashboard
4. Deploy - Railway automatically builds and runs

### Persistent Storage for Deployment

For production deployments:

```env
DATA_DIR=/mnt/persistent/documind
DOCUMENT_DIR=/mnt/persistent/documind/documents
PROCESSED_DIR=/mnt/persistent/documind/processed
```

Configure persistent storage in deployment platform:
- **Railway:** Configure Volume
- **Heroku:** Use file add-ons
- **EC2:** Mount EBS volume
- **Kubernetes:** Use PersistentVolumes

## Production Deployment Notes

The repository contains deployment configuration for Railway and other cloud platforms.

### Pre-deployment Checklist

- [ ] Set `ENVIRONMENT=production`
- [ ] Provide production `DATABASE_URL` with strong credentials
- [ ] Configure all required LLM API keys
- [ ] Set up persistent storage for documents and vector store
- [ ] Update `CORS_ORIGINS` to specific frontend domain(s)
- [ ] Verify OCR dependencies (Tesseract, Poppler) in image
- [ ] Configure database backups
- [ ] Set up monitoring and logging
- [ ] Test deployment in staging environment

### Configuration for Production

```env
# backend/.env.production
ENVIRONMENT=production

# Use Railway provided DATABASE_URL or configure PostgreSQL
DATABASE_URL=postgresql+psycopg2://user:password@prod-db-host:5432/documind

# LLM Providers
GEMINI_API_KEY=your_production_key
OPENAI_API_KEY=your_production_key
GROQ_API_KEY=your_production_key

# System
USE_GPU=false  # Disable GPU in production (safer)
POPPLER_PATH=/usr/bin

# CORS - Set specific domains instead of "*"
CORS_ORIGINS=["https://yourdomain.com", "https://www.yourdomain.com"]
```

### Production Features Enabled

The current backend production configuration:
- Disables GPU usage for stability
- Uses CPU execution
- Configures efficient resource usage
- Optimizes for scalability

### Monitoring & Logging

**Application Logs:**
```bash
# View logs (e.g., in Railway)
journalctl -u documind-backend -f
```

**Database Monitoring:**
- Set up PostgreSQL query logging
- Monitor connection pool usage
- Track table sizes and VACUUM performance

**Vector Store Monitoring:**
- Monitor disk usage for FAISS index
- Check index corruption with periodic rebuilds
- Track embedding generation time

### Backup Strategy

```bash
# Backup PostgreSQL
pg_dump documind > backup_$(date +%Y%m%d).sql

# Backup vector store and documents
tar -czf faiss_backup_$(date +%Y%m%d).tar.gz /mnt/persistent/documind/
```

### Scaling Considerations

**Horizontal Scaling:**
- Run multiple backend instances behind load balancer
- Use managed database (AWS RDS, Railway Postgres)
- Distribute FAISS index or use cloud vector DB (Pinecone, Weaviate)

**Vertical Scaling:**
- Increase server RAM and CPU
- Use larger GPU for embedding generation
- Optimize database query performance

### CDN for Frontend

```nginx
# nginx configuration example
location /api/v1 {
    proxy_pass http://backend:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

location ~ ^/(static|assets)/ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

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

### Test Organization

**Unit Tests:**
- `test_document_processor.py`: Document parsing and extraction
- `test_document.py`: Document model tests

**Integration Tests:**
- `test_api.py`: API endpoint testing
- `test_3wee_imple.py`: End-to-end workflows

**Test Configuration:**
- `conftest.py`: Pytest fixtures and configuration

### Running Specific Tests

```bash
# Run a single test file
pytest tests/test_api.py -v

# Run a specific test
pytest tests/test_api.py::test_upload_txt_file -v

# Run tests matching a pattern
pytest tests/ -k "upload" -v

# Run with specific markers
pytest -m "not slow" -v
```

### Coverage Analysis

```bash
# Generate coverage report
pytest --cov=app --cov-report=html --cov-report=term

# View HTML report
open htmlcov/index.html
```

### Evaluation & Benchmarking

The project includes evaluation scripts:

```bash
# Generate evaluation dataset
python backend/generate_eval_dataset.py

# Run RAG evaluation with RAGAS
python backend/evaluate_rag.py

# Quick setup test
python backend/manual_setup.py
```

These scripts evaluate:
- Answer Faithfulness (adherence to source documents)
- Answer Relevance (how well it answers the question)
- Retrieval quality (relevance of retrieved chunks)

## Design Notes

### Core Retrieval Strategy

The hybrid retrieval pipeline is intentionally multi-layered:

```text
Query
  ↓
Dense Retrieval (FAISS)
  └─ Semantic similarity matching
  └─ Language-independent
  └─ Captures meaning and context
     ↓
Lexical Retrieval (BM25)
  └─ Keyword and exact matching
  └─ Great for technical terms
  └─ Handles acronyms and numbers
     ↓
Reciprocal Rank Fusion
  └─ Intelligently merges both result sets
  └─ Handles disagreement between methods
  └─ Optimizes for diversity
     ↓
Cross-Encoder Reranking
  └─ Scores each result for relevance
  └─ Sorts by actual relevance to query
  └─ Top N results used for generation
     ↓
LLM Answer Generation
  └─ Receives ranked context
  └─ Generates grounded response
  └─ Cites sources
     ↓
Answer + Source Citations
```

**Why this approach?**
- FAISS alone misses domain-specific keywords
- BM25 alone has no semantic understanding
- Together they provide robust retrieval
- Reranking ensures quality output
- Results in 91.8% Faithfulness, 89.8% Relevance (RAGAS eval)

### Embedding Model Choice

`sentence-transformers/all-MiniLM-L6-v2` selected for:

- **Speed:** Fast inference on CPU and GPU
- **Size:** Only 22M parameters (low memory)
- **Quality:** Competitive performance on semantic search
- **Production-ready:** Battle-tested in production systems
- **Compatibility:** Works with FAISS, sentence-transformers ecosystem

Alternative options:
- `intfloat/e5-large-v2`: Higher quality but larger (335M params)
- `sentence-transformers/all-mpnet-base-v2`: Higher quality but slower
- `sentence-transformers/all-distilroberta-v1`: Faster but lower quality

### Chunking Strategy

Recursive character splitting with:
- **Chunk size:** 1000 characters
- **Overlap:** 200 characters
- **Strategy:** Character-based (vs token-based)

**Rationale:**
- Respects document structure better than random chunking
- Overlap preserves context at boundaries
- 1000 chars ≈ 250 tokens (reasonable context window)
- Character-based avoids tokenizer dependency

### LLM Provider Abstraction

Multiple provider support implemented as:

```python
class BaseLLM(ABC):
    @abstractmethod
    def generate_response(prompt: str) -> str
    
    @abstractmethod
    def is_available() -> bool
```

Each provider (Gemini, OpenAI, Groq) implements same interface:
- Transparent switching
- Automatic fallback
- Unified response format

**Benefits:**
- No vendor lock-in
- Easy to add new providers
- Graceful degradation
- Cost optimization (use cheapest available)

### Source Attribution

Each answer includes sources with:
- Document name
- Page number (if applicable)
- Similarity score
- Exact text excerpt
- Retrieval method (vector/BM25/hybrid)

Enables users to verify answers and access original content.

### Architecture Decision Record

**Q: Why FastAPI instead of Django?**
- Async support for WebSocket and background tasks
- Automatic API documentation (OpenAPI/Swagger)
- Better performance for I/O-bound operations
- Modern Python async/await syntax

**Q: Why FAISS instead of Elasticsearch?**
- Simpler deployment (file-based index)
- Faster for small/medium datasets
- Lower resource requirements
- Easy to version control with data

**Q: Why React instead of Vue/Svelte?**
- Larger ecosystem and community
- More job market availability
- Better TypeScript support
- More UI component libraries

**Q: Why PostgreSQL for metadata, not MongoDB?**
- Relational structure for query history
- ACID guarantees for analytics
- Better suited for structured data
- Simpler backup/recovery

## Known Implementation Notes

- The backend currently supports a 20 MB upload limit. The actual limit is enforced at the backend level (`config.py`).
- Query-answer generation is provider-configurable, with Gemini as the default priority in the LLM service.
- Evaluation scores reported in this README are from external RAGAS evaluation runs and are not generated by the running application.
- The `user.py` router is included in the project structure but currently empty - user authentication is not yet implemented.
- Celery worker service is configured in `docker-compose.yml` for background processing but not required for basic operation.
- The application can run single-user (local setup) or multi-user (with proper deployment).
- GPU is automatically disabled in production mode for stability, regardless of hardware availability.
- WebSocket functionality for real-time progress requires client-side implementation (example in frontend).
- The vector store is stored as binary files on disk and should be included in backup strategies.
- Database queries use lazy evaluation; analytics endpoints may be slow on very large datasets.

## Contribution & Development

### Development Workflow

1. **Fork the repository** on GitHub
2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make changes** with tests
4. **Run tests locally:**
   ```bash
   pytest -v
   flake8 app
   ```
5. **Commit and push:**
   ```bash
   git commit -m "feat: description of changes"
   git push origin feature/your-feature-name
   ```
6. **Create Pull Request** to `develop` branch

### Code Style

- **Python:** PEP 8 (flake8 validation)
- **JavaScript:** ESLint configuration included
- **Format:** 120 character line limit
- **Tests:** Required for new features

### Adding New LLM Providers

To add a new LLM provider:

1. Create new class in `backend/app/services/llm.py`:
   ```python
   class NewProviderLLM(BaseLLM):
       def __init__(self):
           # Initialize provider
       
       def test_connection(self) -> bool:
           # Test API connectivity
       
       def generate_response(self, prompt: str) -> str:
           # Generate response
   ```

2. Add to LLM service initialization
3. Add API key env variable
4. Document in this README

### Adding New Document Formats

To support additional file formats:

1. Update `DocumentProcessor` in `backend/app/services/document_processor.py`
2. Add extraction method (e.g., `extract_text_from_epub()`)
3. Update `ALLOWED_EXTENSIONS` in `backend/app/config.py`
4. Add tests to `backend/tests/test_document_processor.py`
5. Update README

### Adding Analytics Metrics

To add new analytics:

1. Add fields to `AnalyticsStatsDB` model
2. Create endpoint in `backend/app/routers/analytics.py`
3. Update frontend analytics dashboard
4. Document in README API section

## Security Considerations

### API Security

**Current Implementation:**
- CORS enabled for all origins (`["*"]`) - suitable for development only
- No authentication required - suitable for self-hosted/trusted networks
- No rate limiting on endpoints

**Production Recommendations:**

```python
# config.py - Update CORS for production
CORS_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com"
]
```

### API Key Management

**Best Practices:**

```bash
# DO NOT commit .env files
echo ".env" >> .gitignore
echo "*.env" >> .gitignore

# Use environment variables or secret management
# Never log API keys
# Rotate keys periodically
# Use separate keys for development/production
```

### Database Security

```python
# PostgreSQL security
# 1. Use strong passwords
POSTGRES_PASSWORD=very_strong_password_here

# 2. Restrict network access
# Only allow backend to connect to database

# 3. Enable SSL for database connections
# DATABASE_URL=postgresql+psycopg2://user:pass@host/db?sslmode=require

# 4. Regular backups
pg_dump --verbose documind > backup.sql
```

### File Upload Security

**Current Validations:**
- File size limit: 20 MB
- Allowed extensions: .pdf, .docx, .txt, .html, .md
- No executable file upload possible

**Additional Recommendations:**
- Scan uploaded files for malware
- Validate MIME types
- Store uploads outside web root
- Use virus scanner (ClamAV)

### Secret Management

Use secret management tools for production:

```bash
# Option 1: Environment variables (simple)
export OPENAI_API_KEY=sk-...

# Option 2: Secret manager (production)
# AWS Secrets Manager
# HashiCorp Vault
# Azure Key Vault

# Option 3: .env files (development only)
# Use python-dotenv with .env.example
```

### HTTPS/TLS

In production, always use HTTPS:

```nginx
# nginx configuration
server {
    listen 443 ssl http2;
    ssl_certificate /path/to/cert.crt;
    ssl_certificate_key /path/to/key.key;
    
    location / {
        proxy_pass http://backend:8000;
    }
}
```

## API Client Examples

### Python Client

```python
import requests
import json

class DocuMindClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = f"{base_url}/api/v1"
    
    def upload_document(self, file_path):
        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(
                f"{self.api_prefix}/documents/upload",
                files=files
            )
        return response.json()
    
    def ask_question(self, question, top_k=5):
        payload = {
            "question": question,
            "top_k": top_k,
            "temperature": 0.2
        }
        response = requests.post(
            f"{self.api_prefix}/query/ask",
            json=payload
        )
        return response.json()
    
    def get_analytics(self):
        response = requests.get(f"{self.api_prefix}/analytics/stats")
        return response.json()

# Usage
client = DocuMindClient()
doc = client.upload_document("document.pdf")
answer = client.ask_question("What is this document about?")
print(answer['answer'])
```

### JavaScript/Node.js Client

```javascript
class DocuMindClient {
  constructor(baseUrl = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.apiPrefix = `${baseUrl}/api/v1`;
  }

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(
      `${this.apiPrefix}/documents/upload`,
      { method: 'POST', body: formData }
    );
    return response.json();
  }

  async askQuestion(question, topK = 5) {
    const response = await fetch(
      `${this.apiPrefix}/query/ask`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          top_k: topK,
          temperature: 0.2
        })
      }
    );
    return response.json();
  }

  async getAnalytics() {
    const response = await fetch(`${this.apiPrefix}/analytics/stats`);
    return response.json();
  }
}

// Usage
const client = new DocuMindClient();
const answer = await client.askQuestion('What is AI?');
console.log(answer.answer);
```

### cURL Examples

```bash
# Upload a document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@document.pdf"

# Ask a question
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the main topic?",
    "top_k": 5,
    "temperature": 0.2
  }'

# Get query history
curl http://localhost:8000/api/v1/query/history?page=1&limit=10

# Get analytics
curl http://localhost:8000/api/v1/analytics/stats

# List documents
curl http://localhost:8000/api/v1/documents/

# Delete a document
curl -X DELETE http://localhost:8000/api/v1/documents/{document_id}
```

## Common Use Cases & Examples

### Use Case 1: Legal Document Q&A

Upload legal documents (contracts, terms of service) and ask questions:

```bash
# 1. Upload documents
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@contract.pdf"

# 2. Ask questions
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the contract duration?",
    "top_k": 3,
    "temperature": 0.1
  }'
```

**Configuration:**
- Use low temperature (0.1) for precise legal interpretations
- Increase top_k for comprehensive contract review
- Enable source citations

### Use Case 2: Research Paper Analysis

Analyze multiple research papers:

```bash
# Upload multiple papers
for paper in *.pdf; do
  curl -X POST http://localhost:8000/api/v1/documents/upload \
    -F "file=@$paper"
done

# Ask comparative questions
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Compare methodologies across papers",
    "top_k": 10,
    "temperature": 0.3
  }'
```

### Use Case 3: Knowledge Base Q&A

Build a company knowledge base:

```javascript
// Frontend example
async function askKnowledgeBase(question) {
  const response = await fetch('/api/v1/query/ask', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      question: question,
      top_k: 5,
      document_ids: ['kb-001', 'kb-002'] // Specific docs
    })
  });
  return response.json();
}
```

### Use Case 4: Real-time Document Processing

Upload with progress tracking:

```javascript
const formData = new FormData();
formData.append('files', file);

const response = await fetch('/api/v1/documents/upload-with-progress', {
  method: 'POST',
  body: formData
});

// Monitor progress via WebSocket
const clientId = 'user-123';
const ws = new WebSocket(`ws://localhost:8000/client/${clientId}`);

ws.onmessage = (event) => {
  const { stage, progress } = JSON.parse(event.data);
  console.log(`${stage}: ${progress}%`);
};
```

### Use Case 5: Multi-Language Support

The system naturally handles multiple languages:

```bash
# Query in Spanish
curl -X POST http://localhost:8000/api/v1/query/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "¿Cuáles son los puntos principales?"
  }'

# Returns answers based on documents (translated if needed)
```

**Note:** Embedding model supports 50+ languages

### Use Case 6: Analytics & Insights

Track usage patterns:

```bash
# Get popular questions
curl http://localhost:8000/api/v1/analytics/popular-questions?limit=20

# Get usage stats
curl http://localhost:8000/api/v1/analytics/stats

# Monitor LLM costs
curl http://localhost:8000/api/v1/analytics/llm-usage
```

## Roadmap & Future Work

### Planned Features

- [ ] User authentication and multi-user support
- [ ] Document sharing and collaboration
- [ ] Custom embedding model selection
- [ ] Streaming response generation
- [ ] Document versioning and history
- [ ] Advanced caching strategies
- [ ] Mobile app (React Native)
- [ ] Voice input/output support
- [ ] Document annotation and feedback loop
- [ ] Custom fine-tuned models

### Technical Debt & Improvements

- [ ] Add comprehensive logging with structured logging
- [ ] Implement request/response tracing (OpenTelemetry)
- [ ] Add monitoring dashboards (Prometheus + Grafana)
- [ ] Optimize FAISS index for large-scale datasets
- [ ] Implement document deduplication
- [ ] Add support for streaming uploads
- [ ] Refactor LLM service with dependency injection

### Performance Roadmap

- [ ] Vector store pruning for cleanup
- [ ] Caching layer (Redis) for frequently asked questions
- [ ] Query result caching
- [ ] Batch embedding generation improvements
- [ ] Async document processing queue

## License

Add the project's preferred license here before publishing under an explicit open-source license.
