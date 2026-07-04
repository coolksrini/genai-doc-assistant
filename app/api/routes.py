import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.llm import get_llm
from app.services.ingestion import load_document, SUPPORTED_FORMATS
from app.services.chunking import chunk_documents
from app.services.embedding import get_vector_store
from app.agents.graph import build_graph
from app.utils.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

DATA_DIR = Path("data/uploads")
DATA_DIR.mkdir(parents=True, exist_ok=True)

VERSION = "1.0.0"


# ---------- Response models ----------

class HealthResponse(BaseModel):
    status: str          # "ok" | "degraded"
    version: str
    llm: str             # "available" | "unavailable"
    vector_store: str    # "ready" | "empty" | "unavailable"


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunk_count: int
    status: str


class QuestionRequest(BaseModel):
    question: str
    top_k: int = 5


class DocumentInfo(BaseModel):
    filename: str
    chunk_count: int


class AnswerResponse(BaseModel):
    question: str
    answer: str
    is_grounded: bool
    sources: list[dict]
    agent_trace: list[str]


# ---------- Routes ----------

@router.get("/health", response_model=HealthResponse)
def health():
    """Liveness + readiness probe. Always returns HTTP 200; status field signals degradation."""
    s = get_settings()

    # LLM probe
    llm_status = "available"
    try:
        get_llm().invoke("ping")
    except Exception as exc:
        logger.warning("LLM health check failed", extra={"error": str(exc)})
        llm_status = "unavailable"

    # Vector store probe
    vs_status = "unavailable"
    try:
        store = get_vector_store()
        vs_status = "empty" if store.collection_empty() else "ready"
    except Exception as exc:
        logger.warning("Vector store health check failed", extra={"error": str(exc)})

    overall = "ok" if llm_status == "available" and vs_status != "unavailable" else "degraded"

    logger.info("Health check", extra={"status": overall, "llm": llm_status, "vector_store": vs_status})
    return HealthResponse(status=overall, version=VERSION, llm=llm_status, vector_store=vs_status)


@router.get("/list-documents", response_model=list[DocumentInfo])
def list_documents():
    """List all ingested documents with their chunk counts."""
    try:
        store = get_vector_store()
        return store.list_documents()
    except Exception as exc:
        logger.error("Failed to list documents", extra={"error": str(exc)})
        raise HTTPException(status_code=500, detail="Could not retrieve document list.")


@router.post("/upload-document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    s = get_settings()
    suffix = Path(file.filename).suffix.lower()

    if suffix not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix}'. Accepted formats: {', '.join(sorted(SUPPORTED_FORMATS))}",
        )

    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > s.max_file_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds the {s.max_file_size_mb}MB limit. Received: {size_mb:.1f}MB",
        )

    doc_id = str(uuid.uuid4())
    save_path = DATA_DIR / f"{doc_id}{suffix}"
    save_path.write_bytes(content)

    try:
        docs = load_document(save_path, file.filename)
        chunks = chunk_documents(docs)
        store = get_vector_store()
        store.add_chunks(chunks)
    except Exception as exc:
        logger.error("Ingestion failed", extra={"error": str(exc), "doc_name": file.filename})
        raise HTTPException(status_code=500, detail="Document ingestion failed. Please check the file is not corrupted.")

    logger.info("Document ingested", extra={"document_id": doc_id, "doc_name": file.filename, "chunks": len(chunks)})
    return UploadResponse(document_id=doc_id, filename=file.filename, chunk_count=len(chunks), status="ingested")


@router.post("/ask-questions", response_model=AnswerResponse)
async def ask_questions(request: QuestionRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question must not be empty.")

    store = get_vector_store()
    if store.collection_empty():
        raise HTTPException(status_code=503, detail="No documents have been ingested yet. Please upload a document first.")

    try:
        graph = build_graph()
        result = graph.invoke({
            "question": request.question,
            "top_k": request.top_k,
            "plan": [],
            "chunks": [],
            "context": "",
            "answer": "",
            "sources": [],
            "is_grounded": False,
            "agent_trace": [],
        })
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Agent pipeline failed", extra={"error": str(exc)})
        raise HTTPException(status_code=503, detail="LLM service is unavailable. Please ensure Ollama is running.")

    return AnswerResponse(
        question=result["question"],
        answer=result["answer"],
        is_grounded=result["is_grounded"],
        sources=result.get("sources", []),
        agent_trace=result.get("agent_trace", []),
    )
