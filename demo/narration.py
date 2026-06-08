"""
Generate TTS narration audio clips for each demo scene using Edge TTS.

Each clip describes EXACTLY what is visible on screen at that moment.
Run: python demo/narration.py

After generating, check durations printed below — then update PAUSE values
in playwright_demo.py so each scene stays on screen at least that long.
"""
import asyncio
import edge_tts
from pathlib import Path

VOICE = "en-US-AndrewNeural"
OUTPUT_DIR = Path(__file__).parent / "assets"
OUTPUT_DIR.mkdir(exist_ok=True)

# Each entry: (filename, narration text)
# Narration describes ONLY what is visible on screen in that scene.
SCENES = [
    (
        "00_intro.mp3",
        """This is the GenAI Document Assistant — a Retrieval Augmented Generation system
        built for the Edureka GenAI and Machine Learning Capstone.
        The green banner confirms the system is online: the API is connected,
        the language model is available via Ollama, and the vector store is empty
        and ready for documents."""
    ),
    (
        "01_upload_pdf.mp3",
        """We upload the Attention Is All You Need paper — the two thousand seventeen
        Transformer architecture paper — as a PDF.
        The system reads each page, splits the text into two-hundred-token chunks,
        embeds each chunk using the nomic-embed-text model, and stores the vectors
        in ChromaDB. Two hundred and forty-seven chunks ingested."""
    ),
    (
        "02_upload_csv.mp3",
        """Now a CSV file — the Titanic passenger dataset.
        Each row becomes its own chunk, so we can search
        across individual passenger records by semantic similarity."""
    ),
    (
        "03_upload_excel.mp3",
        """And the World Happiness Report twenty twenty three as an Excel spreadsheet.
        Forty-two rows covering the top-ranked countries worldwide."""
    ),
    (
        "04_question.mp3",
        """We type our first question: What is the attention mechanism in the Transformer?
        This triggers the five-agent pipeline.
        The Planner validates the question, the Retriever searches ChromaDB
        for the most relevant chunks using cosine similarity,
        the Reasoning agent synthesises the context, the Response agent
        calls the language model with a strict instruction to answer only from
        the retrieved content, and the Verifier runs a second check."""
    ),
    (
        "05_answer.mp3",
        """The answer comes back grounded — drawn directly from the paper.
        The attention mechanism in the Transformer is a way for the model
        to draw global dependencies between input and output,
        relying entirely on attention rather than recurrence or convolutions."""
    ),
    (
        "06_sources.mp3",
        """The Sources panel shows exactly where the answer came from —
        chunk eighty-one of the Attention paper — with the raw excerpt visible.
        Every grounded answer includes this citation."""
    ),
    (
        "07_agent_trace.mp3",
        """The Agent Steps trace shows the full pipeline audit log.
        Planner analysed the question. Retriever found five chunks from the vector store.
        Reasoning synthesised the context. Response generated the grounded answer.
        Verifier confirmed it with a YES verdict."""
    ),
    (
        "08_refusal.mp3",
        """Now we ask something that isn't in any uploaded document —
        who won the twenty twenty six Champions League.
        The system does not guess.
        It returns: I could not find this information in the uploaded documents.
        The sources list is empty. No hallucination, no fabrication."""
    ),
    (
        "09_happiness.mp3",
        """Next we query the happiness data.
        The Retriever finds rows from the World Happiness Report Excel file,
        and the answer correctly identifies Finland as the top-ranked country."""
    ),
    (
        "10_injection.mp3",
        """Now we try a prompt injection attack —
        asking the system to ignore its previous instructions.
        The Planner detects the phrase immediately from its list of fifteen
        known injection patterns and blocks the request with a four-hundred error.
        The language model is never called."""
    ),
    (
        "11_api_docs.mp3",
        """The FastAPI backend exposes interactive Swagger documentation.
        Three endpoints: GET health for liveness and readiness checks,
        POST upload-document for document ingestion,
        and POST ask-questions to run the full agent pipeline."""
    ),
    (
        "12_outro.mp3",
        """That's the GenAI Document Assistant —
        upload any enterprise document in any format,
        ask any natural language question,
        and get answers grounded exclusively in your documents.
        Built with LangChain, LangGraph, ChromaDB, FastAPI, and Streamlit.
        Full source code, a hundred and twenty-two tests, and complete documentation
        are available on GitHub. Thank you."""
    ),
]


async def generate(filename: str, text: str) -> float:
    out = OUTPUT_DIR / filename
    communicate = edge_tts.Communicate(text=text, voice=VOICE, rate="+0%")
    await communicate.save(str(out))
    # Measure actual duration
    import subprocess, json
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(out)],
        capture_output=True, text=True
    )
    dur = float(json.loads(r.stdout)["format"]["duration"])
    return dur


async def main():
    print(f"Voice: {VOICE}\n")
    print(f"{'Clip':<25} {'Duration':>10}  Narration preview")
    print("-" * 75)
    total = 0.0
    for filename, text in SCENES:
        dur = await generate(filename, text)
        total += dur
        preview = text.strip().replace("\n", " ")[:55]
        print(f"{filename:<25} {dur:>9.2f}s  {preview}…")
    print("-" * 75)
    print(f"{'TOTAL':<25} {total:>9.2f}s  ({total/60:.1f} min)")
    print(f"\nAll clips saved to {OUTPUT_DIR}/")
    print("\nNow update playwright_demo.py PAUSE values to match these durations.")


if __name__ == "__main__":
    asyncio.run(main())
