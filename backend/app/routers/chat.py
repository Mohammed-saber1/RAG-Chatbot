"""Chat router with Server-Sent Events (SSE) streaming."""

import logging

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post(
    "",
    summary="Send a question and receive a streamed answer",
    response_class=StreamingResponse,
)
async def chat(request: Request, body: ChatRequest) -> StreamingResponse:
    """Ask a question about the uploaded documents.

    Returns a Server-Sent Events (SSE) stream containing:
    - `token` events: individual text tokens of the AI response
    - `sources` event: document sources used to generate the answer
    - `done` event: signals the end of the stream
    """
    rag_service = request.app.state.rag_service

    # Check if any documents have been uploaded
    if not rag_service.has_documents():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents have been uploaded yet. Please upload a document first.",
        )

    logger.info("Chat query received: '%s'", body.question[:100])

    # Return SSE streaming response
    return StreamingResponse(
        rag_service.query_stream(body.question),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
