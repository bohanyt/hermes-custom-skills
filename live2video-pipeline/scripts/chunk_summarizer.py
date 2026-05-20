"""
CHUNK SUMMARIZER: Summarize tiap chunk transkrip
Simpan di hermes_skills/chunk_summarizer.py

Pakai model FREE (deepseek-v4-flash:free) via OpenRouter.
Delay antar request biar gak kena rate limit.

Cara pakai:
  python chunk_summarizer.py "path/to/chunks/chunks.json"
  python chunk_summarizer.py "path/to/chunks/chunks.json" --delay 3.5

Output:
  <chunks_folder>/
    ├── chunks.json              ← (updated dengan summary)
    ├── chunk_001.txt
    ├── chunk_001.summary.txt    ← summary chunk 1
    ├── chunk_002.txt
    ├── chunk_002.summary.txt    ← summary chunk 2
    └── all_summaries.json       ← semua summary dalam 1 file
"""

import argparse
import json
import sys
import time
from pathlib import Path

# ── import config ──────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

# ── config ─────────────────────────────────────────────────────────────
PROFILE = "secondary"
DELAY_BETWEEN_REQUESTS = 3.0   # detik (rate limit free tier)
MAX_RETRIES = 3
RETRY_DELAY = 10.0

# ── prompt template ────────────────────────────────────────────────────
SUMMARY_SYSTEM_PROMPT = """Kamu adalah asisten summarizer untuk pipeline produksi video YouTube.
Tugasmu: baca transkrip segmen video dan buatkan summary SINGKAT (1-2 kalimat, max 50 kata).

Fokus pada:
- Apa yang dibicarakan di segmen ini?
- Apa momen penting / menarik?
- Vibe/energinya gimana?

Format output: HANYA summary, tanpa prefix atau penjelasan tambahan."""

SUMMARY_USER_TEMPLATE = """Summarize transkrip ini dalam 1-2 kalimat (max 50 kata):

[[chunk_text]]"""


# ── functions ──────────────────────────────────────────────────────────
def summarize_chunk(chunk_text: str, chunk_id: str, delay: float = DELAY_BETWEEN_REQUESTS) -> str:
    """
    Summarize satu chunk via LLM.
    Return summary text.
    """
    messages = [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": SUMMARY_USER_TEMPLATE.replace("[[chunk_text]]", chunk_text)}
    ]

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"    [LLM] Calling API (attempt {attempt}/{MAX_RETRIES})...")
            response = call_llm(
                profile=PROFILE,
                messages=messages,
                max_tokens=200,
                temperature=0.3
            )
            summary = response.strip()
            print(f"    [LLM] ✅ Summary: {summary[:80]}...")
            return summary

        except RuntimeError as e:
            error_str = str(e)
            if "429" in error_str or "rate limit" in error_str.lower():
                wait = RETRY_DELAY * attempt
                print(f"    [LLM] ⚠️  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    [LLM] ❌ Error: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
                else:
                    return f"[SUMMARY ERROR: {e}]"

        except Exception as e:
            print(f"    [LLM] ❌ Unexpected error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
            else:
                return f"[SUMMARY ERROR: {e}]"

    return "[SUMMARY ERROR: Max retries reached]"


def process_chunks(chunks_json_path: str, delay: float = DELAY_BETWEEN_REQUESTS):
    """
    Baca chunks.json, summarize tiap chunk, simpan summary.
    """
    chunks_file = Path(chunks_json_path)
    if not chunks_file.exists():
        print(f"❌ File tidak ditemukan: {chunks_file}")
        sys.exit(1)

    chunks_dir = chunks_file.parent

    # Load chunks.json
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks_meta = json.load(f)

    print("=" * 60)
    print(f"CHUNK SUMMARIZER")
    print(f"Profile: {PROFILE}")
    print(f"Delay: {delay}s between requests")
    print(f"Total chunks: {len(chunks_meta)}")
    print("=" * 60)
    print()

    summaries = []
    total = len(chunks_meta)

    for i, chunk_meta in enumerate(chunks_meta):
        chunk_id = chunk_meta["chunk_id"]
        text_file = chunk_meta.get("text_file", f"{chunk_id}.txt")
        text_path = chunks_dir / text_file

        print(f"[{i+1}/{total}] Processing {chunk_id}...")

        # Baca teks chunk
        if not text_path.exists():
            print(f"  ⚠️  File tidak ditemukan: {text_path}")
            summary = "[TEXT FILE NOT FOUND]"
        else:
            with open(text_path, "r", encoding="utf-8") as f:
                chunk_text = f.read()

            # Skip header lines (yang mulai dengan #)
            lines = chunk_text.split("\n")
            content_lines = []
            skip_header = True
            for line in lines:
                if skip_header:
                    if line.startswith("#"):
                        continue
                    elif line.strip() == "":
                        continue
                    else:
                        skip_header = False
                        content_lines.append(line)
                else:
                    content_lines.append(line)
            chunk_text = "\n".join(content_lines).strip()

            if not chunk_text:
                print(f"  ⚠️  Empty chunk, skipping.")
                summary = "[EMPTY CHUNK]"
            else:
                print(f"  📝 Text length: {len(chunk_text)} chars, {len(chunk_text.split())} words")
                summary = summarize_chunk(chunk_text, chunk_id, delay)

        # Simpan summary
        summary_path = chunks_dir / f"{chunk_id}.summary.txt"
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"# {chunk_id}\n")
            f.write(f"# {chunk_meta.get('start_time', '?')} → {chunk_meta.get('end_time', '?')}\n")
            f.write("#" + "=" * 58 + "\n\n")
            f.write(summary)
        print(f"  📄 Saved: {summary_path}")

        # Update metadata
        chunk_meta["summary"] = summary
        chunk_meta["summary_file"] = f"{chunk_id}.summary.txt"
        summaries.append({
            "chunk_id": chunk_id,
            "start_time": chunk_meta.get("start_time"),
            "end_time": chunk_meta.get("end_time"),
            "duration_sec": chunk_meta.get("duration_sec"),
            "word_count": chunk_meta.get("word_count"),
            "summary": summary
        })

        # Delay antar request (kecuali chunk terakhir)
        if i < total - 1:
            print(f"  ⏳ Waiting {delay}s before next request...")
            time.sleep(delay)

        print()

    # Update chunks.json dengan summary
    with open(chunks_file, "w", encoding="utf-8") as f:
        json.dump(chunks_meta, f, ensure_ascii=False, indent=2)
    print(f"  📝 Updated: {chunks_file}")

    # Simpan all_summaries.json
    all_summaries_path = chunks_dir / "all_summaries.json"
    with open(all_summaries_path, "w", encoding="utf-8") as f:
        json.dump(summaries, f, ensure_ascii=False, indent=2)
    print(f"  📝 Saved: {all_summaries_path}")

    # Ringkasan
    print()
    print("=" * 60)
    print("✅ DONE!")
    print("=" * 60)
    print(f"  📂 Chunks dir: {chunks_dir}")
    print(f"  📊 Total chunks processed: {total}")
    print(f"  📄 Summaries: {all_summaries_path}")
    print(f"  ⏱️  Estimated time: {total * delay / 60:.1f} minutes")
    print()

    # Print all summaries (buat Orchestrator)
    print("=" * 60)
    print("ALL SUMMARIES (for Orchestrator):")
    print("=" * 60)
    for s in summaries:
        print(f"  {s['chunk_id']} ({s['start_time']} → {s['end_time']}): {s['summary']}")

    return chunks_dir


def main():
    parser = argparse.ArgumentParser(
        description="Summarize tiap chunk transkrip menggunakan LLM"
    )
    parser.add_argument("chunks_json", help="Path ke chunks.json")
    parser.add_argument(
        "--delay", "-d",
        type=float,
        default=DELAY_BETWEEN_REQUESTS,
        help=f"Delay antar request dalam detik (default: {DELAY_BETWEEN_REQUESTS})"
    )

    args = parser.parse_args()
    process_chunks(args.chunks_json, args.delay)


if __name__ == "__main__":
    main()
