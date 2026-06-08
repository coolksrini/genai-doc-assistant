"""
Combine the Playwright browser recording with Edge TTS narration into a
final narrated demo video.

Strategy:
  1. Concatenate all narration clips sequentially (0.8s gap between each).
     No overlap possible — each clip starts strictly after the previous ends.
  2. Slow the browser video to match the total audio duration using setpts.
     Screen recordings look fine at 1.5–2× slowdown.
  3. Apply EBU R128 loudnorm for consistent, broadcast-level volume.
  4. Merge video + audio → demo_final.mp4

Run order:
  python demo/narration.py        ← generate audio clips first
  python demo/playwright_demo.py  ← record browser video
  python demo/combine_demo.py     ← produce final video

Requirements: ffmpeg in PATH
"""
import json
import subprocess
import tempfile
from pathlib import Path

ASSETS      = Path(__file__).parent / "assets"
RAW_VIDEO   = ASSETS / "demo_raw.webm"
FINAL_VIDEO = ASSETS / "demo_final.mp4"

GAP_BETWEEN_CLIPS = 0.8   # seconds of silence between narration clips
VOLUME_TARGET_LUFS = -14   # EBU R128 target (YouTube/streaming standard)

# Ordered narration clips (edit text in narration.py, not here)
CLIPS = [
    "00_intro.mp3",
    "01_architecture.mp3",
    "02_health.mp3",
    "03_upload_pdf.mp3",
    "04_upload_csv.mp3",
    "05_upload_excel.mp3",
    "06_grounded_question.mp3",
    "07_refusal.mp3",
    "08_happiness.mp3",
    "09_safety.mp3",
    "10_api_docs.mp3",
    "11_outro.mp3",
]


def get_duration(path: Path) -> float:
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(json.loads(result.stdout)["format"]["duration"])


def build_silence(duration: float, path: Path):
    """Generate a silent audio clip of `duration` seconds."""
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=mono",
        "-t", str(duration),
        "-q:a", "9", str(path),
    ], capture_output=True, check=True)


def concatenate_audio(clips: list[Path]) -> tuple[Path, float]:
    """
    Concatenate clips with GAP_BETWEEN_CLIPS silence between each.
    Returns (path_to_mixed.mp3, total_duration_seconds).
    """
    print("Building audio track (sequential concatenation)…")

    # Build alternating list: clip, gap, clip, gap, ... clip
    silence_path = ASSETS / "_silence.mp3"
    build_silence(GAP_BETWEEN_CLIPS, silence_path)

    # Write ffmpeg concat file
    concat_list = ASSETS / "_concat_list.txt"
    with open(concat_list, "w") as f:
        for i, clip in enumerate(clips):
            f.write(f"file '{clip.resolve()}'\n")
            if i < len(clips) - 1:
                f.write(f"file '{silence_path.resolve()}'\n")

    mixed = ASSETS / "narration_sequential.mp3"
    subprocess.run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(mixed),
    ], capture_output=True, check=True)

    # Apply EBU R128 loudnorm (two-pass for accuracy)
    normalized = ASSETS / "narration_normalized.mp3"
    # Pass 1: measure
    result = subprocess.run([
        "ffmpeg", "-y", "-i", str(mixed),
        "-af", f"loudnorm=I={VOLUME_TARGET_LUFS}:TP=-1.5:LRA=11:print_format=json",
        "-f", "null", "-",
    ], capture_output=True, text=True)
    # Extract loudnorm JSON from stderr
    stderr = result.stderr
    start = stderr.rfind("{")
    end = stderr.rfind("}") + 1
    if start >= 0 and end > start:
        ln = json.loads(stderr[start:end])
        # Pass 2: apply with measured values
        subprocess.run([
            "ffmpeg", "-y", "-i", str(mixed),
            "-af", (
                f"loudnorm=I={VOLUME_TARGET_LUFS}:TP=-1.5:LRA=11"
                f":measured_I={ln['input_i']}"
                f":measured_TP={ln['input_tp']}"
                f":measured_LRA={ln['input_lra']}"
                f":measured_thresh={ln['input_thresh']}"
                f":offset={ln['target_offset']}"
                f":linear=true:print_format=none"
            ),
            "-ar", "44100", "-b:a", "192k",
            str(normalized),
        ], capture_output=True, check=True)
        out_audio = normalized
    else:
        # Fallback: simple volume boost
        subprocess.run([
            "ffmpeg", "-y", "-i", str(mixed),
            "-af", "volume=4dB",
            "-ar", "44100", "-b:a", "192k",
            str(normalized),
        ], capture_output=True, check=True)
        out_audio = normalized

    audio_duration = get_duration(out_audio)

    # Print per-clip timing table
    cursor = 0.0
    print(f"\n  {'Clip':<30} {'Start':>8}  {'Duration':>10}  {'End':>8}")
    print(f"  {'-'*60}")
    for clip in clips:
        dur = get_duration(clip)
        print(f"  {clip.name:<30} {cursor:>7.1f}s  {dur:>9.2f}s  {cursor+dur:>7.1f}s")
        cursor += dur + GAP_BETWEEN_CLIPS
    print(f"\n  Total audio duration: {audio_duration:.1f}s ({audio_duration/60:.1f} min)")

    # Cleanup temp files
    for tmp in [silence_path, concat_list, mixed]:
        tmp.unlink(missing_ok=True)

    return out_audio, audio_duration


def slow_video_to_match(audio_duration: float) -> Path:
    """
    Slow down the raw video so its duration matches the audio.
    Uses setpts for video and atempo for audio (though audio will be replaced).
    """
    video_duration = get_duration(RAW_VIDEO)
    slowdown = audio_duration / video_duration
    print(f"\n  Video: {video_duration:.1f}s → slowed {slowdown:.2f}× → {audio_duration:.1f}s")

    slowed = ASSETS / "video_slowed.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(RAW_VIDEO),
        "-vf", f"setpts={slowdown:.4f}*PTS",
        "-an",                          # drop original audio (there is none)
        "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        str(slowed),
    ], capture_output=True, check=True)
    return slowed


def combine(video_path: Path, audio_path: Path):
    """Merge slowed video + normalised audio → final MP4."""
    print("\nCombining video + audio…")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        "-movflags", "+faststart",
        str(FINAL_VIDEO),
    ], capture_output=True, check=True)
    size_mb = FINAL_VIDEO.stat().st_size / (1024 * 1024)
    print(f"  ✓ {FINAL_VIDEO.name} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    if not RAW_VIDEO.exists():
        print(f"❌ Raw video not found: {RAW_VIDEO}")
        print("   Run: python demo/playwright_demo.py first")
        raise SystemExit(1)

    clips = [ASSETS / c for c in CLIPS if (ASSETS / c).exists()]
    missing = [c for c in CLIPS if not (ASSETS / c).exists()]
    if missing:
        print(f"⚠️  Missing clips (skipped): {missing}")
    if not clips:
        print("No clips found — run: python demo/narration.py first")
        raise SystemExit(1)

    print(f"Found {len(clips)}/{len(CLIPS)} narration clips\n")

    audio_path, audio_duration = concatenate_audio(clips)
    slowed_video  = slow_video_to_match(audio_duration)
    combine(slowed_video, audio_path)

    # Cleanup temp video
    slowed_video.unlink(missing_ok=True)

    print(f"\n✅ Done → {FINAL_VIDEO}")
    print("   Upload to YouTube / Loom, or attach to your capstone submission.")
