"""
Combine the Playwright browser recording with Edge TTS narration.

Per-segment strategy (replaces broken uniform slowdown):
  - playwright_demo.py writes scene_timings.json with a timestamp for each
    scene mark (e.g. "arch": 31.2, "arch_end": 110.5, "pdf": 125.0 …)
  - Each video segment [mark_start → mark_end] is extracted from demo_raw.webm
    and independently sped/slowed to match its narration clip duration
  - This keeps architecture on screen for exactly 77s of narration, uploads
    for exactly 27s, etc. — regardless of how long the raw recording took

Scene → clip mapping:
  intro       → 00_intro.mp3
  arch        → 01_architecture.mp3   (arch … arch_end, isolated from transition)
  arch_end    → 02_upload_pdf.mp3     (includes tab switch + PDF upload)
  csv         → 03_upload_csv.mp3
  excel       → 04_upload_excel.mp3
  question    → 05_question.mp3
  answer      → 06_answer.mp3
  sources     → 07_sources.mp3
  agent_trace → 08_agent_trace.mp3
  refusal     → 09_refusal.mp3
  happiness   → 10_happiness.mp3
  injection   → 11_injection.mp3
  api_docs    → 12_api_docs.mp3
  outro       → 13_outro.mp3

Run order:
  python demo/narration.py        ← generate audio clips
  python demo/playwright_demo.py  ← record browser video + scene_timings.json
  python demo/combine_demo.py     ← produce final video

Requirements: ffmpeg in PATH
"""
import json
import subprocess
import tempfile
from pathlib import Path

ASSETS      = Path(__file__).parent / "assets"
RAW_VIDEO   = ASSETS / "demo_raw.webm"
TIMINGS     = ASSETS / "scene_timings.json"
FINAL_VIDEO = ASSETS / "demo_final.mp4"

GAP_BETWEEN_CLIPS = 0.0   # no gap — avoids cumulative audio/video drift and -shortest truncation

# Ordered list: (mark_start, mark_end, narration_clip)
# arch_end→csv intentionally includes the tab-switch + PDF upload transition
SCENES = [
    ("intro",       "arch",        "00_intro.mp3"),
    ("arch",        "arch_end",    "01_architecture.mp3"),
    ("arch_end",    "csv",         "02_upload_pdf.mp3"),
    ("csv",         "excel",       "03_upload_csv.mp3"),
    ("excel",       "question",    "04_upload_excel.mp3"),
    ("question",    "answer",      "05_question.mp3"),
    ("answer",      "sources",     "06_answer.mp3"),
    ("sources",     "agent_trace", "07_sources.mp3"),
    ("agent_trace", "refusal",     "08_agent_trace.mp3"),
    ("refusal",     "happiness",   "09_refusal.mp3"),
    ("happiness",   "injection",   "10_happiness.mp3"),
    ("injection",   "api_docs",    "11_injection.mp3"),
    ("api_docs",    "outro",       "12_api_docs.mp3"),
    ("outro",       "end",         "13_outro.mp3"),
]

CLIPS = [s[2] for s in SCENES]


def get_duration(path: Path) -> float:
    """Get duration in seconds. Falls back to stream tags for webm."""
    r = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", str(path)],
        capture_output=True, text=True, check=True,
    )
    fmt = json.loads(r.stdout).get("format", {})
    if "duration" in fmt:
        return float(fmt["duration"])

    r2 = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(path)],
        capture_output=True, text=True, check=True,
    )
    for s in json.loads(r2.stdout).get("streams", []):
        dur = s.get("duration")
        if dur and dur != "N/A":
            return float(dur)
        tag = s.get("tags", {}).get("DURATION", "")
        if tag:
            p = tag.split(":")
            return float(p[0]) * 3600 + float(p[1]) * 60 + float(p[2])
    raise ValueError(f"Could not determine duration of {path}")


def build_silence(duration: float, path: Path):
    subprocess.run([
        "ffmpeg", "-y", "-f", "lavfi",
        "-i", "anullsrc=r=44100:cl=mono",
        "-t", str(duration), "-q:a", "9", str(path),
    ], capture_output=True, check=True)


def concatenate_audio(clips: list[Path]) -> tuple[Path, float]:
    """Concatenate narration clips with optional GAP_BETWEEN_CLIPS silence."""
    print("Building audio track…")

    silence: Path | None = None
    if GAP_BETWEEN_CLIPS > 0:
        silence = ASSETS / "_silence.mp3"
        build_silence(GAP_BETWEEN_CLIPS, silence)

    concat_list = ASSETS / "_audio_concat.txt"
    with open(concat_list, "w") as f:
        for i, clip in enumerate(clips):
            f.write(f"file '{clip.resolve()}'\n")
            if i < len(clips) - 1 and silence is not None:
                f.write(f"file '{silence.resolve()}'\n")

    out = ASSETS / "narration_normalized.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-af", "volume=5dB", "-ar", "44100", "-b:a", "192k", str(out),
    ], capture_output=True, check=True)

    duration = get_duration(out)
    cursor = 0.0
    print(f"\n  {'Clip':<28} {'Start':>8}  {'Duration':>9}  {'End':>8}")
    print(f"  {'-'*58}")
    for clip in clips:
        d = get_duration(clip)
        print(f"  {clip.name:<28} {cursor:>7.1f}s  {d:>8.2f}s  {cursor+d:>7.1f}s")
        cursor += d + GAP_BETWEEN_CLIPS
    print(f"\n  Total audio: {duration:.1f}s ({duration/60:.1f} min)")

    for tmp in [p for p in [silence, concat_list] if p is not None]:
        tmp.unlink(missing_ok=True)
    return out, duration


def extract_segment(seg_idx: int, raw: Path,
                    t_start: float, t_end: float,
                    target_duration: float) -> Path:
    """
    Extract [t_start, t_end] from raw video and speed it to target_duration.
    Returns path to the temp segment MP4.
    """
    raw_duration = t_end - t_start
    if raw_duration <= 0:
        raise ValueError(f"Segment {seg_idx}: start={t_start} >= end={t_end}")

    # setpts < 1 → speed up;  setpts > 1 → slow down
    setpts = target_duration / raw_duration
    out = ASSETS / f"_seg_{seg_idx:02d}.mp4"

    subprocess.run([
        "ffmpeg", "-y",
        "-ss", f"{t_start:.3f}", "-to", f"{t_end:.3f}",
        "-i", str(raw),
        "-vf", f"setpts={setpts:.6f}*PTS",
        "-r", "30",
        "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        "-an",
        str(out),
    ], capture_output=True, check=True)
    return out


def build_video_from_segments(timings: dict, clips: list[Path]) -> Path:
    """Extract + speed each scene segment, then concatenate."""
    print("\nPer-segment video processing…")
    print(f"\n  {'Scene':<14} {'Raw':>8}  {'Target':>8}  {'Speed':>7}  {'Clip'}")
    print(f"  {'-'*65}")

    seg_files = []
    for idx, (mark_start, mark_end, clip_name) in enumerate(SCENES):
        t_start = timings.get(mark_start)
        t_end   = timings.get(mark_end)
        clip    = ASSETS / clip_name

        if t_start is None or t_end is None:
            print(f"  ⚠️  Missing timing mark '{mark_start}' or '{mark_end}' — skipping")
            continue
        if not clip.exists():
            print(f"  ⚠️  Missing clip {clip_name} — skipping")
            continue

        raw_dur    = t_end - t_start
        target_dur = get_duration(clip)
        speed      = raw_dur / target_dur

        print(f"  {mark_start:<14} {raw_dur:>7.1f}s  {target_dur:>7.2f}s  {speed:>6.3f}×  {clip_name}")

        seg = extract_segment(idx, RAW_VIDEO, t_start, t_end, target_dur)
        seg_files.append(seg)

    if not seg_files:
        raise RuntimeError("No segments extracted — check scene_timings.json")

    # Concatenate all segments
    print(f"\n  Concatenating {len(seg_files)} segments…")
    concat_list = ASSETS / "_video_concat.txt"
    with open(concat_list, "w") as f:
        for s in seg_files:
            f.write(f"file '{s.resolve()}'\n")

    combined = ASSETS / "video_segmented.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
        "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        str(combined),
    ], capture_output=True, check=True)

    concat_list.unlink(missing_ok=True)
    for s in seg_files:
        s.unlink(missing_ok=True)

    return combined


def combine(video_path: Path, audio_path: Path):
    print("\nMerging video + audio…")
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


def fallback_uniform_slowdown(audio_duration: float):
    """Fallback when scene_timings.json is absent — uniform slowdown."""
    print("\n⚠️  scene_timings.json not found — falling back to uniform slowdown")
    video_duration = get_duration(RAW_VIDEO)
    slowdown = audio_duration / video_duration
    print(f"  Video: {video_duration:.1f}s → slowed {slowdown:.2f}× → {audio_duration:.1f}s")
    slowed = ASSETS / "video_slowed.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-i", str(RAW_VIDEO),
        "-vf", f"setpts={slowdown:.4f}*PTS",
        "-an", "-c:v", "libx264", "-crf", "22", "-preset", "fast",
        str(slowed),
    ], capture_output=True, check=True)
    return slowed


if __name__ == "__main__":
    if not RAW_VIDEO.exists():
        print(f"❌ Raw video not found: {RAW_VIDEO}")
        raise SystemExit(1)

    clips = [ASSETS / c for c in CLIPS if (ASSETS / c).exists()]
    missing = [c for c in CLIPS if not (ASSETS / c).exists()]
    if missing:
        print(f"⚠️  Missing clips: {missing}")
    print(f"Found {len(clips)}/{len(CLIPS)} narration clips\n")

    audio_path, audio_duration = concatenate_audio(clips)

    if TIMINGS.exists():
        timings = json.loads(TIMINGS.read_text())
        print(f"\nLoaded scene_timings.json ({len(timings)} marks)")
        video_path = build_video_from_segments(timings, clips)
    else:
        video_path = fallback_uniform_slowdown(audio_duration)

    combine(video_path, audio_path)
    video_path.unlink(missing_ok=True)

    print(f"\n✅ Done → {FINAL_VIDEO}")
    print("   Attach to your capstone submission.")
