# RAG-Chatbot

RAG-Chatbot is a full-stack Retrieval-Augmented Generation (RAG) application. It allows you to upload PDF and TXT documents, embedding them locally to build a knowledge base, and then answers your questions based strictly on that context using the Mistral AI API. 
The primary goal of this project is to create a secure, fast, and highly accurate document Q&A assistant that completely eliminates AI hallucination by forcing the LLM to rely *only* on the provided documents.

https://github.com/Mohammed-saber1/RAG-Chatbot/raw/main/Demo-Video.mp4

## 🌟 Key Features

* **Strict RAG Pipeline**: Answers are generated *only* from your uploaded documents. If the answer isn't in the text, the AI will honestly reply, "I don't know based on the provided documents."
* **Markdown Rendering**: Responses from the AI are fully parsed and rendered as Markdown in the UI, supporting bold text, lists, and tables.
* **Source Citations**: Every answer includes clickable references to the specific documents and pages used. The UI cleanly separates the answer from the sources to maintain readability.
* **Real-time Streaming**: Responses stream in token-by-token (SSE) for a fast, ChatGPT-like experience.
* **Premium UI**: Dark-mode glassmorphism design with responsive sidebars, micro-animations, and clean typography.
* **Local Embeddings**: Document embeddings are generated completely locally (using `sentence-transformers/all-MiniLM-L6-v2`) via ChromaDB. This means your documents are never sent to a third-party API just for ingestion—saving costs and improving privacy. Only the relevant retrieved chunks are sent to Mistral during a query.

## 🏗️ Architecture & Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **RAG Orchestration**: LangChain
- **Vector Database**: ChromaDB (Persistent local storage)
- **Embeddings**: HuggingFace (`sentence-transformers/all-MiniLM-L6-v2`)
- **Document Processing**: PyPDF
- **LLM**: Mistral AI (`mistral-large-latest`)

### Frontend
- **Framework**: React 19 + Vite
- **Styling**: Vanilla CSS (CSS Variables, Flexbox, CSS Grid)
- **Markdown Parsing**: `react-markdown`, `remark-gfm`

## 🧠 How the RAG Pipeline Works

1. **Document Upload**: Users upload PDF or TXT files via the UI.
2. **Parsing & Chunking**: The backend uses PyPDF to extract text and splits it into manageable chunks (e.g., 1000 characters) to preserve context while fitting into the LLM context window.
3. **Local Embedding**: Each chunk is converted into a vector embedding using a local HuggingFace model running on the CPU.
4. **Vector Storage**: Embeddings and metadata (filename, page number) are stored in a local ChromaDB instance.
5. **Retrieval**: When a user asks a question, the query is embedded, and ChromaDB performs a similarity search to find the most relevant chunks.
6. **Prompt Construction**: The backend constructs a strict prompt containing the retrieved chunks and commands the LLM to answer *only* using that context.
7. **Streaming Generation**: Mistral AI generates the answer, which is streamed back to the frontend via Server-Sent Events (SSE).

## 🚀 Quick Start (Local Development)

This guide assumes you are using Anaconda with an environment named `gen-venv` that has the required dependencies.

### 1. Backend Setup

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Create your environment configuration:
   ```bash
   cp .env.example .env
   ```
3. Edit the `.env` file and add your **Mistral API Key**:
   ```env
   MISTRAL_API_KEY=your_actual_key_here
   ```
4. Activate your environment and start the server:
   ```bash
   conda activate gen-venv
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

### 2. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the Vite dev server:
   ```bash
   npm run dev
   ```
4. Open your browser to `http://localhost:5173`.

## 🐳 Docker Deployment

You can run the entire stack using Docker Compose.

1. Ensure your `MISTRAL_API_KEY` is exported in your terminal session, or create a `.env` file in the root directory:
   ```bash
   export MISTRAL_API_KEY="your-api-key"
   ```
2. Run Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. The app will be available at `http://localhost:5173`.

## 🔒 Security Features Implemented

* **No Hardcoded Secrets**: Multi-tiered configuration requires API keys via environment variables or explicitly ignored local text files.
* **Safe DOM Injection**: The frontend uses `react-markdown` to safely render AI output without using dangerous inner HTML injection.
* **File Validation**: Strict allow-lists for file extensions, 10MB size limits, and magic-byte checks for PDFs.
* **Path Traversal Protection**: Uploaded files are immediately renamed to secure UUIDs; user-supplied filenames are kept only as metadata.
* **Restricted CORS & Headers**: Explicit `ALLOWED_ORIGINS`, Content-Security-Policy (CSP), and nosniff headers enforced by FastAPI middleware.

## 📂 Project Structure

```text
RAG-Chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI application entry point
│   │   ├── config.py         # Pydantic settings & env validation
│   │   ├── routers/          # API endpoint routes (chat, docs, etc.)
│   │   ├── services/         # Core business logic (RAG pipeline)
│   │   └── models/           # Pydantic schemas (requests/responses)
│   ├── chroma_db/            # Local persistent vector database (auto-generated)
│   ├── uploads/              # Temporary document storage (auto-generated)
│   └── Dockerfile.backend
├── frontend/
│   ├── src/
│   │   ├── components/       # React components (ChatInterface, Sidebar, etc.)
│   │   ├── App.jsx           # Main application component
│   │   ├── index.css         # Global styling and design system
│   │   └── main.jsx          # React DOM mounting
│   ├── index.html            # Vite entry point
│   └── Dockerfile.frontend
└── docker-compose.yml        # Docker composition for easy deployment
```
