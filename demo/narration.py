"""
Generate TTS narration audio clips for each demo scene using Edge TTS.
Produces individual .mp3 files in demo/assets/ — one per scene.
Run: python demo/narration.py
"""
import asyncio
import edge_tts
from pathlib import Path

VOICE = "en-US-AndrewNeural"   # change to "en-US-AvaNeural" for female voice
OUTPUT_DIR = Path(__file__).parent / "assets"
OUTPUT_DIR.mkdir(exist_ok=True)

# Each scene: (filename, narration text)
SCENES = [
    (
        "00_intro.mp3",
        """Welcome to the GenAI Document Assistant — a capstone project for the
        Edureka PGP in Generative AI and Machine Learning.
        This system lets you upload enterprise documents in any format and ask
        natural language questions, with answers grounded exclusively in your documents.
        No hallucination. No guessing. Only what's actually in the documents."""
    ),
    (
        "01_architecture.mp3",
        """The system is built on a five-agent pipeline powered by LangChain and LangGraph.
        When you ask a question, it flows through five agents:
        the Planner validates your input, the Retriever finds relevant document chunks using
        cosine similarity, the Reasoning agent synthesises the context, the Response agent
        calls the LLM — instructed to answer only from retrieved content —
        and finally the Verifier runs a second pass to confirm grounding.
        All responses include source citations and a full agent trace."""
    ),
    (
        "02_health.mp3",
        """Let's start the application. The Streamlit interface connects to a FastAPI backend
        running locally. The health banner at the top confirms the API is connected,
        the LLM is available via Ollama, and the vector store is ready."""
    ),
    (
        "03_upload_pdf.mp3",
        """First, we upload the Attention Is All You Need paper — the seminal Transformer
        architecture paper — as a PDF. The system ingests it, splits it into
        two-hundred-token chunks with overlap, embeds each chunk using the
        nomic-embed-text model, and stores the vectors in ChromaDB.
        The result: two hundred and forty-seven searchable chunks in under five seconds."""
    ),
    (
        "04_upload_csv.mp3",
        """Now we upload the Titanic passenger dataset as a CSV file.
        Each row becomes a document chunk, so the system can retrieve
        specific passenger records by semantic similarity to your question."""
    ),
    (
        "05_upload_excel.mp3",
        """And the World Happiness Report twenty twenty three as an Excel file.
        The system supports PDF, TXT, CSV, Excel, JSON, and YAML —
        all formats enterprise teams actually use."""
    ),
    (
        "06_grounded_question.mp3",
        """Now let's ask a question. We ask: What is the attention mechanism in the Transformer?
        Watch the agent trace: the Planner validates the question, the Retriever fetches
        the most relevant chunks from the Attention paper, the Reasoning agent builds context,
        the Response agent generates a grounded answer, and the Verifier confirms it.
        The answer cites the exact source chunk from the paper."""
    ),
    (
        "07_refusal.mp3",
        """Now we ask a question that's outside any uploaded document —
        Who won the twenty twenty six Champions League?
        This isn't in any of our documents. The system doesn't guess.
        It returns the canonical refusal: I could not find this information
        in the uploaded documents. The sources list is empty. No hallucination."""
    ),
    (
        "08_happiness.mp3",
        """Let's query the happiness data. We ask: Which country ranked first
        in the World Happiness Report?
        The Retriever finds relevant rows from the Excel file,
        and the answer correctly identifies Finland as the top-ranked country."""
    ),
    (
        "09_safety.mp3",
        """The system includes safety controls. If a user tries to inject a prompt —
        for example, asking the system to ignore previous instructions —
        the Planner detects it immediately against fifteen known injection patterns
        and returns a four hundred bad request error before any LLM call is made."""
    ),
    (
        "10_api_docs.mp3",
        """The FastAPI backend exposes interactive documentation at slash docs.
        All three endpoints are documented: GET health, POST upload-document,
        and POST ask-questions. The health endpoint probes both the LLM and vector store
        and returns a structured status — always HTTP two hundred, never a five hundred
        on a degraded system."""
    ),
    (
        "11_outro.mp3",
        """The GenAI Document Assistant demonstrates a complete Generative AI and Agentic AI
        workflow: document ingestion, vector-based retrieval, multi-agent reasoning,
        grounding enforcement, and safe deployment.
        The full source code, one hundred and twenty-two tests across four layers,
        and comprehensive documentation are available on GitHub.
        Thank you for watching."""
    ),
]


async def generate(filename: str, text: str):
    out = OUTPUT_DIR / filename
    communicate = edge_tts.Communicate(text=text, voice=VOICE, rate="+5%")
    await communicate.save(str(out))
    duration = out.stat().st_size / 16000  # rough estimate: ~16KB/s for mp3
    print(f"✓ {filename}  (~{duration:.0f}s)")


async def main():
    print(f"Generating {len(SCENES)} narration clips with voice: {VOICE}\n")
    for filename, text in SCENES:
        await generate(filename, text)
    print(f"\nAll clips saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    asyncio.run(main())
