import time
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router
from app.utils.logging import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="GenAI Document Assistant",
    description="RAG-powered document Q&A using autonomous AI agents",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- Request logging middleware (T035) ----------

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "HTTP request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "elapsed_ms": elapsed_ms,
        },
    )
    return response


# ---------- Exception handlers (T036) ----------

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = [f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}" for e in exc.errors()]
    logger.warning("Request validation failed", extra={"errors": errors, "path": request.url.path})
    return JSONResponse(status_code=422, content={"detail": "; ".join(errors)})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTP exception",
        extra={"status": exc.status_code, "detail": exc.detail, "path": request.url.path},
    )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    # Log full type for internal debugging, never expose to client
    logger.error(
        "Unhandled exception",
        extra={"exc_type": type(exc).__name__, "error": str(exc), "path": request.url.path},
    )
    return JSONResponse(status_code=500, content={"detail": "An unexpected error occurred."})


app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
