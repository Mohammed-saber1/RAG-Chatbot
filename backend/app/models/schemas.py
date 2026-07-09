"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user's question to ask about the uploaded documents.",
    )


class SourceInfo(BaseModel):
    """Information about a source document chunk used in the answer."""

    filename: str = Field(..., description="Original filename of the source document.")
    page: int | None = Field(None, description="Page number in the source document.")
    chunk_preview: str = Field(
        ..., description="Short preview of the relevant text chunk."
    )


class ChatResponse(BaseModel):
    """Response body for the chat endpoint (non-streaming)."""

    answer: str = Field(..., description="The AI-generated answer.")
    sources: list[SourceInfo] = Field(
        default_factory=list,
        description="Source document chunks used to generate the answer.",
    )


class UploadResponse(BaseModel):
    """Response body for the document upload endpoint."""

    filename: str = Field(..., description="Original filename of the uploaded document.")
    num_chunks: int = Field(
        ..., description="Number of text chunks created from the document."
    )
    status: str = Field(..., description="Upload processing status.")


class DocumentInfo(BaseModel):
    """Information about an uploaded document."""

    filename: str = Field(..., description="Original filename.")
    num_chunks: int = Field(..., description="Number of chunks indexed.")
    file_type: str = Field(..., description="File extension type.")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error description for the user.")
