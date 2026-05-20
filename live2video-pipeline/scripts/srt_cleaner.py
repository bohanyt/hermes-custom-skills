#!/usr/bin/env python3
"""
srt_cleaner.py — Bersihkan auto-generated SRT dari YouTube

Masalah umum YouTube auto-generated SRT:
- Repeated words ("the the", "I I")
- [Music], [Applause], [Laughter] tags
- Overlapping timestamps
- Terlalu banyak short segments (< 0.5 detik)
- Inconsistent formatting

Usage:
  python srt_cleaner.py input.srt [--output cleaned.srt] [--merge-gap 0.5] [--min-duration 0.3]

Options:
  --output FILE      — Output file (default: input_cleaned.srt)
  --merge-gap SEC    — Merge segments dengan gap < SEC detik (default: 0.5)
  --min-duration SEC — Hapus segment dengan durasi < SEC detik (default: 0.3)
  --remove-tags      — Hapus [Music], [Applause], dll (default: True)
  --no-remove-tags   — Jangan hapus tags
  --fix-repeats      — Fix repeated words (default: True)
  --no-fix-repeats   — Jangan fix repeated words
  --stats            — Print statistik before/after
"""

import re
import argparse
import sys
from pathlib import Path


# ─── Parser ───────────────────────────────────────────────────────────────────

def parse_srt(content):
    """Parse SRT content into list of (index, start_sec, end_sec, text)"""
    content = re.sub(r"(\d{2}:\d{2}:\d{2}),(\d{3})", r"\1.\2", content)
    blocks = re.split(r"\n\s*\n", content.strip())
    segments = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        start_idx = 1 if re.match(r"^\d+$", lines[0].strip()) else 0
        ts_line = None
        for i in range(start_idx, len(lines)):
            if "-->" in lines[i]:
                ts_line = i
                break
        if ts_line is None:
            continue
        m = re.match(r"(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}\.\d{3})", lines[ts_line])
        if not m:
            continue
        start_sec = _ts_to_sec(m.group(1))
        end_sec = _ts_to_sec(m.group(2))
        text = " ".join(l.strip() for l in lines[ts_line+1:] if l.strip())
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            segments.append((len(segments)+1, start_sec, end_sec, text))
    return segments


def parse_vtt(content):
    """Parse VTT content"""
    content = re.sub(r"^WEBVTT.*?\n\n", "", content, flags=re.DOTALL)
    blocks = re.split(r"\n\n+", content.strip())
    segments = []
    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 2:
            continue
        ts_idx = None
        for i, line in enumerate(lines):
            if "-->" in line:
                ts_idx = i
                break
        if ts_idx is None:
            continue
        m = re.match(r"(\d{1,2}:\d{2}:\d{2}\.\d{3})\s*-->\s*(\d{1,2}:\d{2}:\d{2}\.\d{3})", lines[ts_idx])
        if not m:
            m = re.match(r"(\d{1,2}:\d{2}\.\d{3})\s*-->\s*(\d{1,2}:\d{2}\.\d{3})", lines[ts_idx])
        if not m:
            continue
        start_sec = _ts_to_sec(m.group(1))
        end_sec = _ts_to_sec(m.group(2))
        text = " ".join(l.strip() for l in lines[ts_idx+1:] if l.strip())
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            segments.append((len(segments)+1, start_sec, end_sec, text))
    return segments


def _ts_to_sec(ts):
    parts = ts.split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return 0.0


def _sec_to_ts(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


# ─── Cleaners ─────────────────────────────────────────────────────────────────

NOISE_TAGS = [
    r"\[Music\]", r"\[music\]",
    r"\[Applause\]", r"\[applause\]",
    r"\[Laughter\]", r"\[laughter\]",
    r"\[Singing\]", r"\[singing\]",
    r"\[Cheering\]", r"\[cheering\]",
    r"\[Crying\]", r"\[crying\]",
    r"\[Gasping\]", r"\[gasping\]",
    r"\[Sighing\]", r"\[sighing\]",
    r"\[Whistling\]", r"\[whistling\]",
    r"\[Wind noise\]", r"\[wind noise\]",
    r"\[Typing\]", r"\[typing\]",
    r"\[Phone ringing\]", r"\[phone ringing\]",
    r"\[Birds chirping\]", r"\[birds chirping\]",
    r"\[Dog barking\]", r"\[dog barking\]",
    r"\[Thunder\]", r"\[thunder\]",
    r"\[Rain\]", r"\[rain\]",
    r"\[Fireworks\]", r"\[fireworks\]",
    r"\[Gunshot\]", r"\[gunshot\]",
    r"\[Explosion\]", r"\[explosion\]",
    r"\[.*\]",  # Catch-all untuk [anything]
]


def remove_noise_tags(text):
    """Hapus [Music], [Applause], dll"""
    for pattern in NOISE_TAGS:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def fix_repeated_words(text):
    """Fix repeated words: 'the the' → 'the', 'I I' → 'I'"""
    # Repeated single words (case-insensitive)
    text = re.sub(r"\b(\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    # Repeated two-word phrases
    text = re.sub(r"\b(\w+\s+\w+)\s+\1\b", r"\1", text, flags=re.IGNORECASE)
    return text


def fix_overlapping_timestamps(segments):
    """Fix overlapping timestamps"""
    fixed = []
    for i, (idx, start, end, text) in enumerate(segments):
        if i > 0 and start < fixed[-1][2]:
            # Overlap: adjust start to previous end
            start = fixed[-1][2]
        if end <= start:
            # Invalid: skip or fix
            end = start + 0.5
        fixed.append((idx, start, end, text))
    return fixed


def merge_short_segments(segments, merge_gap=0.5):
    """Merge segments dengan gap < merge_gap detik"""
    if not segments:
        return []

    merged = [segments[0]]
    for i in range(1, len(segments)):
        prev_idx, prev_start, prev_end, prev_text = merged[-1]
        curr_idx, curr_start, curr_end, curr_text = segments[i]

        gap = curr_start - prev_end
        if gap < merge_gap:
            # Merge: extend end, combine text
            merged[-1] = (prev_idx, prev_start, curr_end, prev_text + " " + curr_text)
        else:
            merged.append(segments[i])

    return merged


def remove_short_segments(segments, min_duration=0.3):
    """Hapus segment dengan durasi < min_duration"""
    return [(idx, start, end, text) for idx, start, end, text in segments if (end - start) >= min_duration]


# ─── Writer ───────────────────────────────────────────────────────────────────

def write_srt(segments, output_path):
    """Write segments to SRT file"""
    with open(output_path, "w", encoding="utf-8") as f:
        for i, (idx, start, end, text) in enumerate(segments, 1):
            f.write(f"{i}\n")
            f.write(f"{_sec_to_ts(start)} --> {_sec_to_ts(end)}\n")
            f.write(f"{text}\n\n")


# ─── Stats ────────────────────────────────────────────────────────────────────

def print_stats(segments_before, segments_after, label=""):
    """Print before/after statistics"""
    total_dur_before = sum(e - s for _, s, e, _ in segments_before) if segments_before else 0
    total_dur_after = sum(e - s for _, s, e, _ in segments_after) if segments_after else 0
    words_before = sum(len(t.split()) for _, _, _, t in segments_before)
    words_after = sum(len(t.split()) for _, _, _, t in segments_after)
    avg_dur_before = total_dur_before / len(segments_before) if segments_before else 0
    avg_dur_after = total_dur_after / len(segments_after) if segments_after else 0

    print(f"\n  📊 Stats {label}:")
    print(f"     Segments: {len(segments_before)} → {len(segments_after)} ({len(segments_after) - len(segments_before):+d})")
    print(f"     Duration: {total_dur_before:.0f}s → {total_dur_after:.0f}s")
    print(f"     Words:    {words_before} → {words_after} ({words_after - words_before:+d})")
    print(f"     Avg dur:  {avg_dur_before:.2f}s → {avg_dur_after:.2f}s")


# ─── Main ─────────────────────────────────────────────────────────────────────

def clean_srt(
    input_path,
    output_path=None,
    merge_gap=0.5,
    min_duration=0.3,
    remove_tags=True,
    fix_repeats=True,
    stats=True,
):
    """Main cleaning pipeline"""

    input_path = Path(input_path)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        sys.exit(1)

    if output_path is None:
        output_path = input_path.with_suffix(".cleaned.srt")
    else:
        output_path = Path(output_path)

    # Parse
    with open(input_path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    ext = input_path.suffix.lower()
    if ext == ".srt":
        segments = parse_srt(content)
    else:
        segments = parse_vtt(content)

    segments_before = list(segments)

    # Step 1: Remove noise tags
    if remove_tags:
        segments = [(idx, start, end, remove_noise_tags(text)) for idx, start, end, text in segments]
        # Remove empty segments
        segments = [(idx, start, end, text) for idx, start, end, text in segments if text]

    # Step 2: Fix repeated words
    if fix_repeats:
        segments = [(idx, start, end, fix_repeated_words(text)) for idx, start, end, text in segments]

    # Step 3: Fix overlapping timestamps
    segments = fix_overlapping_timestamps(segments)

    # Step 4: Remove short segments
    segments = remove_short_segments(segments, min_duration)

    # Step 5: Merge short-gap segments
    segments = merge_short_segments(segments, merge_gap)

    # Re-index
    segments = [(i+1, start, end, text) for i, (idx, start, end, text) in enumerate(segments)]

    # Write
    write_srt(segments, output_path)

    print(f"✅ Cleaned: {output_path}")
    print(f"   {len(segments_before)} → {len(segments)} segments")

    if stats:
        print_stats(segments_before, segments_after=segments)

    return output_path


def main():
    parser = argparse.ArgumentParser(
        description="Bersihkan auto-generated SRT dari YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python srt_cleaner.py stream.id.srt
  python srt_cleaner.py stream.id.srt --output cleaned.srt --merge-gap 1.0
  python srt_cleaner.py stream.id.srt --no-remove-tags --no-fix-repeats
        """
    )
    parser.add_argument("input", help="Path ke file .srt atau .vtt")
    parser.add_argument("--output", "-o", default=None, help="Output file")
    parser.add_argument("--merge-gap", type=float, default=0.5,
                        help="Merge gap threshold dalam detik (default: 0.5)")
    parser.add_argument("--min-duration", type=float, default=0.3,
                        help="Minimal durasi segment dalam detik (default: 0.3)")
    parser.add_argument("--remove-tags", action="store_true", default=True,
                        help="Hapus [Music], [Applause], dll (default: True)")
    parser.add_argument("--no-remove-tags", action="store_true", help="Jangan hapus tags")
    parser.add_argument("--fix-repeats", action="store_true", default=True,
                        help="Fix repeated words (default: True)")
    parser.add_argument("--no-fix-repeats", action="store_true", help="Jangan fix repeated words")
    parser.add_argument("--stats", action="store_true", default=True, help="Print statistik")
    parser.add_argument("--no-stats", action="store_true", help="Jangan print statistik")

    args = parser.parse_args()

    clean_srt(
        input_path=args.input,
        output_path=args.output,
        merge_gap=args.merge_gap,
        min_duration=args.min_duration,
        remove_tags=not args.no_remove_tags,
        fix_repeats=not args.no_fix_repeats,
        stats=not args.no_stats,
    )


if __name__ == "__main__":
    main()
