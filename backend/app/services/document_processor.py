"""Document processing service for PDF and TXT files.

Handles file validation, text extraction, and chunking for RAG ingestion.
"""

import logging
import os
import uuid
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.config import Settings


logger = logging.getLogger(__name__)

# Allow-list of permitted file extensions
ALLOWED_EXTENSIONS = {".pdf", ".txt"}

# Magic bytes for PDF validation
PDF_MAGIC_BYTES = b"%PDF"

# Maximum preview length for chunk metadata
MAX_PREVIEW_LENGTH = 200


class DocumentProcessorError(Exception):
    """Raised when document processing fails."""
    pass


class DocumentProcessor:
    """Processes uploaded documents into chunked LangChain Documents."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.upload_dir = Path(settings.upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def validate_file(
        self, filename: str, content: bytes, content_type: str | None
    ) -> str:
        """Validate an uploaded file's extension, size, and content.

        Args:
            filename: Original filename from the upload.
            content: Raw file bytes.
            content_type: MIME content type from the upload.

        Returns:
            The validated file extension.

        Raises:
            DocumentProcessorError: If validation fails.
        """
        # Extract and validate extension
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise DocumentProcessorError(
                f"File type '{ext}' is not allowed. "
                f"Accepted types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
            )

        # Validate file size
        max_bytes = self.settings.max_file_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise DocumentProcessorError(
                f"File exceeds maximum size of {self.settings.max_file_size_mb}MB."
            )

        if len(content) == 0:
            raise DocumentProcessorError("File is empty.")

        # Validate PDF magic bytes
        if ext == ".pdf" and not content[:4].startswith(PDF_MAGIC_BYTES):
            raise DocumentProcessorError(
                "File has .pdf extension but does not appear to be a valid PDF."
            )

        return ext

    def save_file(self, content: bytes, ext: str) -> str:
        """Save uploaded file with a UUID filename.

        Never uses the user-provided filename in the filesystem path.

        Args:
            content: Raw file bytes.
            ext: Validated file extension.

        Returns:
            The generated UUID filename used for storage.
        """
        safe_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = self.upload_dir / safe_filename

        # Verify the resolved path is within the upload directory
        resolved = file_path.resolve()
        upload_resolved = self.upload_dir.resolve()
        if not str(resolved).startswith(str(upload_resolved) + os.sep):
            raise DocumentProcessorError("Invalid file path detected.")

        with open(file_path, "wb") as f:
            f.write(content)

        logger.info("Saved uploaded file as: %s", safe_filename)
        return safe_filename

    def extract_text_from_pdf(self, file_path: Path) -> list[Document]:
        """Extract text from a PDF file, one document per page.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of LangChain Document objects, one per page.
        """
        documents = []
        try:
            reader = PdfReader(str(file_path))
            for page_num, page in enumerate(reader.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    documents.append(
                        Document(
                            page_content=text.strip(),
                            metadata={"page": page_num},
                        )
                    )
        except Exception as e:
            logger.error("Failed to extract text from PDF: %s", e)
            raise DocumentProcessorError(
                "Failed to process PDF file. The file may be corrupted or encrypted."
            ) from e

        if not documents:
            raise DocumentProcessorError(
                "No readable text found in the PDF. "
                "The file may contain only images or scanned content."
            )

        return documents

    def extract_text_from_txt(self, file_path: Path) -> list[Document]:
        """Extract text from a plain text file.

        Args:
            file_path: Path to the text file.

        Returns:
            List containing a single LangChain Document.
        """
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            logger.error("Failed to read text file: %s", e)
            raise DocumentProcessorError(
                "Failed to read text file."
            ) from e

        if not text.strip():
            raise DocumentProcessorError("Text file is empty.")

        return [Document(page_content=text.strip(), metadata={"page": 1})]

    def process_file(
        self, filename: str, content: bytes, content_type: str | None = None
    ) -> tuple[list[Document], str]:
        """Process an uploaded file: validate, save, extract, and chunk.

        Args:
            filename: Original filename from the upload.
            content: Raw file bytes.
            content_type: MIME content type from the upload.

        Returns:
            Tuple of (list of chunked Documents, original filename).
        """
        # Validate
        ext = self.validate_file(filename, content, content_type)

        # Save with UUID filename
        safe_filename = self.save_file(content, ext)
        file_path = self.upload_dir / safe_filename

        # Extract text based on file type
        if ext == ".pdf":
            raw_documents = self.extract_text_from_pdf(file_path)
        elif ext == ".txt":
            raw_documents = self.extract_text_from_txt(file_path)
        else:
            raise DocumentProcessorError(f"Unsupported file type: {ext}")

        # Add source metadata to all documents
        # Use the original filename in metadata for display, but NOT in file paths
        original_basename = Path(filename).name
        for doc in raw_documents:
            doc.metadata["source"] = original_basename

        # Split into chunks
        chunks = self.text_splitter.split_documents(raw_documents)

        # Add chunk index and preview to metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = i
            chunk.metadata["chunk_preview"] = chunk.page_content[:MAX_PREVIEW_LENGTH]

        logger.info(
            "Processed '%s': extracted %d pages, created %d chunks",
            original_basename,
            len(raw_documents),
            len(chunks),
        )

        return chunks, original_basename
