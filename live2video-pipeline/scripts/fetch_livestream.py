"""
YT-DLP WRAPPER: Download Livestream + Auto-Caption + Metadata
Simpan di hermes_skills/fetch_livestream.py

Cara pakai:
  python fetch_livestream.py "https://youtube.com/watch?v=XXXXX"
  python fetch_livestream.py "https://youtube.com/watch?v=XXXXX" --output "custom_folder_name"

Output:
  raw_footages/<nama_video>/
    ├── <nama_video>.mp4          ← video (best quality)
    ├── <nama_video>.id.vtt       ← transkrip Indonesia (auto-generated)
    ├── <nama_video>.en.vtt       ← transkrip English (auto-generated)
    └── metadata.json             ← URL, title, channel, duration, timestamp
"""

import argparse
import subprocess
import sys
import os
import time
import json
import re
from pathlib import Path
from datetime import datetime, timezone

# ── paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent.resolve()
YT_DLP = str(SCRIPT_DIR / "yt-dlp.exe")
RAW_FOOTAGES = SCRIPT_DIR.parent / "raw_footages"

# ── helpers ────────────────────────────────────────────────────────────
def sanitize(name: str) -> str:
    """Bersihin nama folder dari karakter ilegal Windows."""
    return re.sub(r'[<>:"/\\|?*]', '_', name).strip()

def run_ytdlp(args: list, max_retries: int = 5, timeout: int = 7200) -> bool:
    """
    Jalankan yt-dlp dengan retry otomatis kena 429.
    Delay naik eksponensial: 10s, 20s, 40s, 80s, 160s.
    Timeout default 2 jam (buat livestream panjang).
    """
    for attempt in range(1, max_retries + 1):
        cmd = [YT_DLP] + args
        print(f"\n[yt-dlp] Attempt {attempt}/{max_retries}")
        print(f"[yt-dlp] Command: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            print(f"[yt-dlp] ⚠️  Timeout ({timeout}s). Retrying...")
            wait = 10 * (2 ** (attempt - 1))
            time.sleep(wait)
            continue

        if result.returncode == 0:
            print("[yt-dlp] ✅ Success")
            return True

        output = result.stderr + result.stdout

        # Deteksi 429 Too Many Requests
        if "429" in output or "Too Many Requests" in output:
            wait = 10 * (2 ** (attempt - 1))
            print(f"[yt-dlp] ⚠️  Rate limited (429). Waiting {wait}s before retry...")
            time.sleep(wait)
            continue

        # Error lain, cetak dan stop
        print(f"[yt-dlp] ❌ Error:\n{output}")
        return False

    print("[yt-dlp] ❌ Max retries reached. Gagal.")
    return False

# ── main logic ─────────────────────────────────────────────────────────
def fetch_livestream(url: str, custom_name: str = None):
    """
    1. Ambil metadata dulu (judul video) → buat folder
    2. Download video (best quality)
    3. Download auto-caption (tanpa translate)
    """

    # Step 1: Ambil metadata untuk nama folder
    print("=" * 60)
    print("STEP 1: Fetching metadata...")
    print("=" * 60)

    meta_args = [
        "--print", "%(title)s\n%(channel)s\n%(duration_string)s\n%(id)s",
        "--no-download",
        url
    ]
    meta_result = subprocess.run(
        [YT_DLP] + meta_args,
        capture_output=True, text=True, timeout=120
    )

    if meta_result.returncode != 0 or not meta_result.stdout.strip():
        print(f"❌ Gagal ambil metadata: {meta_result.stderr}")
        sys.exit(1)

    meta_lines = meta_result.stdout.strip().split("\n")
    title = meta_lines[0] if len(meta_lines) > 0 else "unknown"
    channel = meta_lines[1] if len(meta_lines) > 1 else "unknown"
    duration = meta_lines[2] if len(meta_lines) > 2 else "unknown"
    video_id = meta_lines[3] if len(meta_lines) > 3 else "unknown"

    folder_name = sanitize(custom_name if custom_name else title)
    output_dir = RAW_FOOTAGES / folder_name
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📁 Output folder: {output_dir}")
    print(f"📹 Title: {title}")
    print(f"👤 Channel: {channel}")
    print(f"⏱️  Duration: {duration}")

    # Simpan metadata.json
    metadata = {
        "url": url,
        "video_id": video_id,
        "title": title,
        "channel": channel,
        "duration": duration,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "folder": str(output_dir)
    }
    meta_file = output_dir / "metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"📝 Metadata saved: {meta_file}")

    # Template output di dalam folder
    out_template = str(output_dir / "%(title)s.%(ext)s")

    # Step 2: Download video
    print("\n" + "=" * 60)
    print("STEP 2: Downloading video (best quality)...")
    print("=" * 60)

    video_args = [
        "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "--merge-output-format", "mp4",
        "--output", out_template,
        "--no-overwrites",
        # Rate limit protection
        "--sleep-requests", "2",
        "--sleep-interval", "5",
        "--max-sleep-interval", "15",
        # Retry built-in
        "--retries", "10",
        "--fragment-retries", "10",
        url
    ]

    if not run_ytdlp(video_args):
        print("❌ Download video gagal.")
        sys.exit(1)

    # Step 3: Download auto-caption (original, tanpa translate)
    print("\n" + "=" * 60)
    print("STEP 3: Downloading auto-captions (original, no translate)...")
    print("=" * 60)

    # yt-dlp akan coba download auto-sub untuk bahasa Indonesia + English
    # Kalau gak ada auto-generated, yt-dlp skip otomatis
    sub_args = [
        "--write-auto-subs",           # Download auto-generated subtitles
        "--sub-lang", "id,en",         # Indonesia + English (paling relevan)
        "--sub-format", "vtt",         # Format VTT
        "--convert-subs", "vtt",       # Pastikan output VTT
        "--output", out_template,
        "--no-overwrites",
        "--skip-download",             # Jangan download video lagi
        # Rate limit protection
        "--sleep-requests", "2",
        "--sleep-interval", "5",
        "--max-sleep-interval", "15",
        "--retries", "10",
        url
    ]

    if not run_ytdlp(sub_args):
        print("⚠️  Download caption gagal, tapi video udah berhasil.")
        print("   Coba jalanin lagi nanti dengan URL yang sama.")

    # Step 4: Ringkasan
    print("\n" + "=" * 60)
    print("✅ DONE! Isi folder:")
    print("=" * 60)
    for f in sorted(output_dir.iterdir()):
        size_mb = f.stat().st_size / (1024 * 1024)
        if size_mb >= 1:
            print(f"  📄 {f.name} ({size_mb:.1f} MB)")
        else:
            print(f"  📄 {f.name} ({f.stat().st_size / 1024:.1f} KB)")

    print(f"\n📂 Folder: {output_dir}")
    print(f"🔗 URL: {url}")
    print(f"📝 Metadata: {meta_file}")
    return output_dir

# ── CLI entry ──────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Download YouTube livestream + auto-captions ke raw_footages/"
    )
    parser.add_argument("url", help="URL YouTube livestream/video")
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Custom nama folder (default: judul video)"
    )

    args = parser.parse_args()
    fetch_livestream(args.url, args.output)

if __name__ == "__main__":
    main()
