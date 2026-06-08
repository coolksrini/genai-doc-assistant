"""
Combine the Playwright browser recording with Edge TTS narration into a
final narrated demo video.

Pipeline:
  demo/assets/demo_raw.webm   (browser video, no audio)
  demo/assets/XX_scene.mp3    (narration clips, one per scene)
       ↓
  demo/assets/demo_final.mp4  (narrated, H.264, ready to share)

Scenes are mapped to timestamps — edit SCENE_TIMINGS to match your recording.
Run:
  python demo/narration.py    ← generate audio clips first
  python demo/playwright_demo.py  ← record browser video first
  python demo/combine_demo.py ← then produce final video

Requirements: ffmpeg in PATH
"""
import subprocess
import json
from pathlib import Path

ASSETS = Path(__file__).parent / "assets"
RAW_VIDEO = ASSETS / "demo_raw.webm"
FINAL_VIDEO = ASSETS / "demo_final.mp4"

# Map each narration clip to the timestamp (seconds) where it starts in the video.
# Adjust these times to match your actual recording — use VLC or ffprobe to check.
SCENE_TIMINGS = [
    # (start_sec, narration_file)
    # Timings calibrated to Playwright demo pacing (PAUSE values in playwright_demo.py)
    # Adjust these if your recording runs faster/slower — use VLC to check timestamps
    (0,    "00_intro.mp3"),      # 0s  — app loading, health banner
    (8,    "01_architecture.mp3"), # 8s  — app fully loaded, explain pipeline
    (20,   "02_health.mp3"),     # 20s — zoom on health banner
    (32,   "03_upload_pdf.mp3"), # 32s — uploading Attention paper
    (52,   "04_upload_csv.mp3"), # 52s — uploading Titanic CSV
    (65,   "05_upload_excel.mp3"), # 65s — uploading Happiness Excel
    (80,   "06_grounded_question.mp3"), # 80s — asking about Transformer
    (118,  "07_refusal.mp3"),    # 118s — Champions League refusal
    (142,  "08_happiness.mp3"),  # 142s — Finland happiness question
    (160,  "09_safety.mp3"),     # 160s — injection attempt blocked
    (177,  "10_api_docs.mp3"),   # 177s — FastAPI Swagger docs
    (202,  "11_outro.mp3"),      # 202s — back to Streamlit, closing remarks
]


def get_duration(path: Path) -> float:
    """Get duration of a media file using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json",
         "-show_format", str(path)],
        capture_output=True, text=True
    )
    info = json.loads(result.stdout)
    return float(info["format"]["duration"])


def build_audio_track(total_duration: float) -> Path:
    """
    Build a single audio track by placing each narration clip at its timestamp.
    Uses ffmpeg's amix + adelay filters.
    """
    print("Building audio track…")
    inputs = []
    filter_parts = []

    for i, (start_sec, clip_name) in enumerate(SCENE_TIMINGS):
        clip_path = ASSETS / clip_name
        if not clip_path.exists():
            print(f"  ⚠️  Missing clip: {clip_name} — skipping")
            continue
        inputs += ["-i", str(clip_path)]
        delay_ms = int(start_sec * 1000)
        filter_parts.append(f"[{i + 1}:a]adelay={delay_ms}|{delay_ms}[a{i}]")

    if not filter_parts:
        print("No audio clips found — producing silent video")
        return None

    n = len(filter_parts)
    mix_inputs = "".join(f"[a{i}]" for i in range(n))
    filter_complex = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={n}:duration=longest[aout]"

    audio_path = ASSETS / "narration_mixed.mp3"
    cmd = (
        ["ffmpeg", "-y", "-i", str(RAW_VIDEO)]
        + inputs
        + ["-filter_complex", filter_complex,
           "-map", "[aout]",
           "-t", str(total_duration),
           "-ar", "44100",
           str(audio_path)]
    )
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"  ✓ Mixed audio: {audio_path.name}")
    return audio_path


def combine(audio_path: Path, total_duration: float):
    """Merge video + audio into final MP4."""
    print("Combining video + audio…")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(RAW_VIDEO),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-crf", "23",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-t", str(total_duration),
        "-movflags", "+faststart",
        str(FINAL_VIDEO),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    size_mb = FINAL_VIDEO.stat().st_size / (1024 * 1024)
    print(f"  ✓ Final video: {FINAL_VIDEO.name} ({size_mb:.1f} MB)")


def make_silent_mp4():
    """Convert webm to mp4 without audio (fallback)."""
    print("Converting to MP4 (silent)…")
    cmd = [
        "ffmpeg", "-y",
        "-i", str(RAW_VIDEO),
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-movflags", "+faststart",
        str(FINAL_VIDEO),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    size_mb = FINAL_VIDEO.stat().st_size / (1024 * 1024)
    print(f"  ✓ Silent MP4: {FINAL_VIDEO.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    if not RAW_VIDEO.exists():
        print(f"❌ Raw video not found: {RAW_VIDEO}")
        print("   Run: python demo/playwright_demo.py first")
        raise SystemExit(1)

    total_duration = get_duration(RAW_VIDEO)
    print(f"Video duration: {total_duration:.1f}s ({total_duration/60:.1f} min)\n")

    clips_present = [ASSETS / clip for _, clip in SCENE_TIMINGS
                     if (ASSETS / clip).exists()]

    if clips_present:
        audio_path = build_audio_track(total_duration)
        if audio_path:
            combine(audio_path, total_duration)
        else:
            make_silent_mp4()
    else:
        print("No narration clips found — generating silent MP4")
        print("Run: python demo/narration.py first to generate audio")
        make_silent_mp4()

    print(f"\n✅ Done: {FINAL_VIDEO}")
    print("   Share this file or upload to YouTube/Loom for your capstone submission.")
