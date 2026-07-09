# DocQuery AI — RAG Chatbot

DocQuery AI is a full-stack Retrieval-Augmented Generation (RAG) chatbot. It allows you to upload PDF and TXT documents, embedding them locally to build a knowledge base, and then answers your questions based strictly on that context using the Mistral AI API.

## 🌟 Features

* **Strict RAG Pipeline**: Answers are generated *only* from your uploaded documents. If the answer isn't in the text, the AI will honestly reply, "I don't know based on the provided documents."
* **Source Citations**: Every answer includes clickable references to the specific documents and pages used.
* **Real-time Streaming**: Responses stream in token-by-token (SSE) for a fast, ChatGPT-like experience.
* **Premium UI**: Dark-mode glassmorphism design with responsive sidebars, micro-animations, and clean typography.
* **Local Embeddings**: Document embeddings are generated completely locally (using `sentence-transformers/all-MiniLM-L6-v2`) via ChromaDB, meaning your documents are never sent to a third-party API just for ingestion—saving costs and improving privacy. Only the relevant chunks are sent to Mistral during a query.

## 🏗️ Architecture

* **Backend**: FastAPI, LangChain, ChromaDB, PyPDF
* **Frontend**: React 19, Vite, Vanilla CSS
* **LLM**: Mistral AI (`mistral-large-latest`)

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
3. Edit the `.env` file and add your **Mistral API Key**.
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

1. Ensure your `MISTRAL_API_KEY` is exported in your terminal session, or create a `.env` file in the root directory.
2. Run Docker Compose:
   ```bash
   docker-compose up --build
   ```
3. The app will be available at `http://localhost:5173`.

## 🔒 Security Features Implemented

* **No Hardcoded Secrets**: Multi-tiered configuration requires API keys via environment variables or explicitly ignored local text files.
* **Safe DOM Injection**: React `textContent` is used exclusively. No dangerous HTML rendering.
* **File Validation**: Strict allow-lists for file extensions, 10MB size limits, and magic-byte checks for PDFs.
* **Path Traversal Protection**: Uploaded files are immediately renamed to secure UUIDs; user-supplied filenames are kept only as metadata.
* **Restricted CORS & Headers**: Explicit `ALLOWED_ORIGINS`, Content-Security-Policy (CSP), and nosniff headers enforced by FastAPI middleware.
