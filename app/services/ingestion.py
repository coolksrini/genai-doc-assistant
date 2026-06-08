import json
from pathlib import Path
import pandas as pd
import yaml
from PyPDF2 import PdfReader
from langchain_core.documents import Document
from app.utils.logging import get_logger

logger = get_logger(__name__)

SUPPORTED_FORMATS = {".pdf", ".txt", ".csv", ".xlsx", ".json", ".yaml", ".yml"}


def load_document(file_path: str | Path, filename: str) -> list[Document]:
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix not in SUPPORTED_FORMATS:
        raise ValueError(f"Unsupported format: {suffix}")

    if suffix == ".pdf":
        return _load_pdf(path, filename)
    elif suffix == ".txt":
        return _load_txt(path, filename)
    elif suffix == ".csv":
        return _load_csv(path, filename)
    elif suffix == ".xlsx":
        return _load_excel(path, filename)
    elif suffix == ".json":
        return _load_json(path, filename)
    elif suffix in (".yaml", ".yml"):
        return _load_yaml(path, filename)

    return []


def _meta(filename: str, page: int = 0) -> dict:
    return {"source": filename, "page": page}


def _load_pdf(path: Path, filename: str) -> list[Document]:
    reader = PdfReader(str(path))
    docs = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if text.strip():
            docs.append(Document(page_content=text, metadata=_meta(filename, i)))
    logger.info("Loaded PDF", extra={"doc_name": filename, "pages": len(docs)})
    return docs


def _load_txt(path: Path, filename: str) -> list[Document]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return [Document(page_content=text, metadata=_meta(filename))]


def _load_csv(path: Path, filename: str) -> list[Document]:
    df = pd.read_csv(path)
    docs = []
    for i, row in df.iterrows():
        docs.append(Document(page_content=str(row.to_dict()), metadata=_meta(filename, i)))
    return docs


def _load_excel(path: Path, filename: str) -> list[Document]:
    df = pd.read_excel(path, engine="openpyxl")
    docs = []
    for i, row in df.iterrows():
        docs.append(Document(page_content=str(row.to_dict()), metadata=_meta(filename, i)))
    return docs


def _load_json(path: Path, filename: str) -> list[Document]:
    data = json.loads(path.read_text(encoding="utf-8"))
    text = json.dumps(data, indent=2)
    return [Document(page_content=text, metadata=_meta(filename))]


def _load_yaml(path: Path, filename: str) -> list[Document]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    text = yaml.dump(data, default_flow_style=False)
    return [Document(page_content=text, metadata=_meta(filename))]
