"""Document upload and management router."""

import logging

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, status

from app.models.schemas import DocumentInfo, UploadResponse
from app.services.document_processor import DocumentProcessor, DocumentProcessorError


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post(
    "/upload",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document for RAG processing",
)
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="PDF or TXT file to upload"),
) -> UploadResponse:
    """Upload and process a document for the RAG pipeline.

    Accepts PDF and TXT files up to 10MB. The document is validated,
    text is extracted, split into chunks, and indexed in the vector store.
    """
    doc_processor: DocumentProcessor = request.app.state.doc_processor
    rag_service = request.app.state.rag_service

    # Read file content
    try:
        content = await file.read()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to read uploaded file.",
        )
    finally:
        await file.close()

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename is required.",
        )

    # Process the document
    try:
        chunks, original_filename = doc_processor.process_file(
            filename=file.filename,
            content=content,
            content_type=file.content_type,
        )
    except DocumentProcessorError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Ingest into vector store
    try:
        num_chunks = await rag_service.ingest_documents(chunks, original_filename)
    except Exception as e:
        logger.error("Failed to ingest document: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process document. Please try again.",
        )

    return UploadResponse(
        filename=original_filename,
        num_chunks=num_chunks,
        status="processed",
    )


@router.get(
    "",
    response_model=list[DocumentInfo],
    summary="List all uploaded documents",
)
async def list_documents(request: Request) -> list[DocumentInfo]:
    """Get a list of all uploaded and processed documents."""
    rag_service = request.app.state.rag_service
    docs = rag_service.get_document_list()

    return [
        DocumentInfo(
            filename=doc["filename"],
            num_chunks=doc["num_chunks"],
            file_type=doc["filename"].rsplit(".", 1)[-1] if "." in doc["filename"] else "unknown",
        )
        for doc in docs
    ]
