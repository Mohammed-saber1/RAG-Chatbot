"""RAG (Retrieval-Augmented Generation) service.

Handles document embedding, vector storage, retrieval, and LLM-powered
question answering using Mistral AI.
"""

import json
import logging
from collections.abc import AsyncGenerator
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.config import Settings
from app.models.schemas import SourceInfo


logger = logging.getLogger(__name__)

# System prompt that constrains the LLM to answer only from provided context
SYSTEM_PROMPT = """You are a helpful AI assistant that answers questions based ONLY on the provided document context.

STRICT RULES:
1. Answer the question using ONLY the information found in the context below.
2. If the context does not contain enough information to answer the question, respond with: "I don't know based on the provided documents."
3. Do NOT make up information or use knowledge from outside the provided context.
4. When answering, be clear, concise, and accurate.
5. If you reference specific information, mention which source document it came from.
6. Maintain a professional and helpful tone.

CONTEXT FROM UPLOADED DOCUMENTS:
{context}
"""


class RAGService:
    """Retrieval-Augmented Generation service using ChromaDB and Mistral AI."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._embeddings: HuggingFaceEmbeddings | None = None
        self._vector_store: Chroma | None = None
        self._llm: ChatMistralAI | None = None
        self._document_registry: dict[str, int] = {}

    async def initialize(self) -> None:
        """Initialize embeddings, vector store, and LLM.

        Called once during application startup.
        """
        logger.info("Initializing RAG service...")

        # Initialize local embeddings model
        logger.info("Loading embedding model: %s", self.settings.embedding_model)
        self._embeddings = HuggingFaceEmbeddings(
            model_name=self.settings.embedding_model,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

        # Initialize ChromaDB vector store with persistence
        logger.info(
            "Initializing ChromaDB at: %s", self.settings.chroma_persist_dir
        )
        self._vector_store = Chroma(
            collection_name="rag_documents",
            embedding_function=self._embeddings,
            persist_directory=self.settings.chroma_persist_dir,
        )

        # Initialize Mistral LLM
        api_key = self.settings.resolve_mistral_key()
        logger.info("Initializing Mistral LLM: %s", self.settings.mistral_model)
        self._llm = ChatMistralAI(
            model=self.settings.mistral_model,
            api_key=api_key,
            temperature=0.1,
            max_tokens=2048,
            streaming=True,
        )

        # Load existing document registry from vector store metadata
        self._load_document_registry()

        logger.info("RAG service initialized successfully")

    def _load_document_registry(self) -> None:
        """Load document info from the existing vector store collection."""
        if self._vector_store is None:
            return

        try:
            collection = self._vector_store._collection
            if collection.count() > 0:
                results = collection.get(include=["metadatas"])
                if results and results["metadatas"]:
                    seen: dict[str, int] = {}
                    for meta in results["metadatas"]:
                        source = meta.get("source", "unknown")
                        if source not in seen:
                            seen[source] = 0
                        seen[source] += 1
                    self._document_registry = seen
                    logger.info(
                        "Loaded %d existing documents from vector store",
                        len(seen),
                    )
        except Exception as e:
            logger.warning("Could not load document registry: %s", e)

    async def ingest_documents(
        self, chunks: list[Document], source_filename: str
    ) -> int:
        """Add document chunks to the vector store.

        Args:
            chunks: List of LangChain Document objects to embed and store.
            source_filename: Original filename for tracking.

        Returns:
            Number of chunks ingested.
        """
        if not self._vector_store:
            raise RuntimeError("RAG service not initialized")

        if not chunks:
            return 0

        # Add chunks to vector store
        self._vector_store.add_documents(chunks)

        # Update registry
        self._document_registry[source_filename] = (
            self._document_registry.get(source_filename, 0) + len(chunks)
        )

        logger.info(
            "Ingested %d chunks from '%s'", len(chunks), source_filename
        )
        return len(chunks)

    def _retrieve_relevant_chunks(self, query: str) -> list[Document]:
        """Retrieve the most relevant document chunks for a query.

        Args:
            query: The user's question.

        Returns:
            List of relevant Document objects.
        """
        if not self._vector_store:
            raise RuntimeError("RAG service not initialized")

        # Check if we have any documents
        if self._vector_store._collection.count() == 0:
            return []

        # Retrieve the top-k chunks
        filtered = self._vector_store.similarity_search(
            query, k=self.settings.top_k_results
        )

        logger.info(
            "Retrieved %d chunks for query: '%s'",
            len(filtered),
            query[:100],
        )

        return filtered

    def _build_context(self, chunks: list[Document]) -> str:
        """Build context string from retrieved chunks.

        Args:
            chunks: List of relevant Document objects.

        Returns:
            Formatted context string for the LLM prompt.
        """
        if not chunks:
            return "No relevant documents found."

        context_parts = []
        for i, chunk in enumerate(chunks, start=1):
            source = chunk.metadata.get("source", "Unknown")
            page = chunk.metadata.get("page", "N/A")
            context_parts.append(
                f"[Source {i}: {source}, Page {page}]\n{chunk.page_content}"
            )

        return "\n\n---\n\n".join(context_parts)

    def _extract_sources(self, chunks: list[Document]) -> list[SourceInfo]:
        """Extract source information from retrieved chunks.

        Args:
            chunks: List of relevant Document objects.

        Returns:
            List of SourceInfo objects for citation display.
        """
        sources = []
        seen = set()

        for chunk in chunks:
            source = chunk.metadata.get("source", "Unknown")
            page = chunk.metadata.get("page")
            preview = chunk.metadata.get(
                "chunk_preview", chunk.page_content[:200]
            )

            # Deduplicate by source + page
            key = f"{source}:{page}"
            if key not in seen:
                seen.add(key)
                sources.append(
                    SourceInfo(
                        filename=source,
                        page=page,
                        chunk_preview=preview,
                    )
                )

        return sources

    async def query_stream(
        self, question: str
    ) -> AsyncGenerator[str, None]:
        """Stream an answer to a question using RAG.

        Retrieves relevant chunks, constructs a prompt, and streams
        the LLM response as Server-Sent Events (SSE).

        Args:
            question: The user's question.

        Yields:
            SSE-formatted strings: text tokens and a final sources payload.
        """
        if not self._llm:
            raise RuntimeError("RAG service not initialized")

        # Retrieve relevant context
        chunks = self._retrieve_relevant_chunks(question)

        # Build the context and prompt
        context = self._build_context(chunks)
        system_message = SystemMessage(content=SYSTEM_PROMPT.format(context=context))
        human_message = HumanMessage(content=question)

        # Extract sources for citation
        sources = self._extract_sources(chunks)

        # Stream the LLM response
        try:
            async for chunk in self._llm.astream(
                [system_message, human_message]
            ):
                if chunk.content:
                    # Send text token as SSE event
                    event_data = json.dumps(
                        {"type": "token", "content": chunk.content}
                    )
                    yield f"data: {event_data}\n\n"

            # Send sources as final SSE event
            sources_data = json.dumps(
                {
                    "type": "sources",
                    "sources": [s.model_dump() for s in sources],
                }
            )
            yield f"data: {sources_data}\n\n"

            # Send done event
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error("Error during LLM streaming: %s", e)
            error_data = json.dumps(
                {
                    "type": "error",
                    "content": "An error occurred while generating the response. Please try again.",
                }
            )
            yield f"data: {error_data}\n\n"

    def get_document_list(self) -> list[dict[str, Any]]:
        """Get the list of all uploaded documents with their chunk counts.

        Returns:
            List of document info dictionaries.
        """
        return [
            {"filename": name, "num_chunks": count}
            for name, count in self._document_registry.items()
        ]

    def has_documents(self) -> bool:
        """Check if any documents have been ingested."""
        return bool(self._document_registry)
