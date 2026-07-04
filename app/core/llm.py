from functools import lru_cache
from langchain_ollama import OllamaEmbeddings
from langchain_openai import ChatOpenAI
from app.core.config import get_settings


@lru_cache
def get_llm() -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        base_url=s.llm_base_url,
        api_key=s.llm_api_key,
        model=s.llm_model,
        temperature=0,
    )


@lru_cache
def get_embeddings() -> OllamaEmbeddings:
    s = get_settings()
    return OllamaEmbeddings(model=s.embed_model)
