#!/usr/bin/env python3
"""
storytime_scanner.py — Scan SRT transkrip cari segmen storytime/anecdote

Usage:
    python storytime_scanner.py <file.srt> [--output results.json] [--min-score 0.5]

Output: JSON file dengan ranked list storytime segments + timestamps untuk cut.
"""

import re
import sys
import json
import argparse
from dataclasses import dataclass, field, asdict
from typing import Optional


# ─── Data ────────────────────────────────────────────────────────────────────

@dataclass
class SubtitleEntry:
    index: int
    start_sec: float
    end_sec: float
    text: str

@dataclass
class StorytimeSegment:
    start_sec: float
    end_sec: float
    text: str
    score: float
    matched_keywords: list = field(default_factory=list)
    label: str = ""

    @property
    def duration(self) -> float:
        return self.end_sec - self.start_sec

    @property
    def start_ts(self) -> str:
        return _sec_to_ts(self.start_sec)

    @property
    def end_ts(self) -> str:
        return _sec_to_ts(self.end_sec)


# ─── Keyword Scoring ─────────────────────────────────────────────────────────

# Keywords yang indikator storytime / personal anecdote (Bahasa Indonesia + campuran)
STORYTIME_KEYWORDS = {
    # Personal life
    "dulu": 2, "dahulu": 2, "jaman dulu": 3, "masa lalu": 2,
    "pengalaman": 3, "cerita": 2, "kejadian": 2, "peristiwa": 2,
    "memalukan": 3, "malu": 2, "malu-malu": 2,
    "lucu": 1, "ngakak": 2, "ketawa": 1, "geli": 1,
    "gila": 1, "aneh": 1, "unik": 1, "unik banget": 2,
    "stress": 2, "stres": 2, "cemas": 2, "khawatir": 2,
    "sedih": 2, "nangis": 2, "menangis": 2,
    "marah": 2, "kesel": 2, "jengkel": 2, "kesal": 2,
    "capek": 2, "lelah": 2, "cape": 2, "ngantuk": 2,
    "lapar": 2, "belum makan": 3, "belum tidur": 3,
    "tidur": 1, "bangun": 1, "mimpi": 2, "insomnia": 3,
    "sakit": 2, "demam": 2, "flu": 2, "batuk": 2, "pilek": 2,
    "dokter": 2, "rumah sakit": 2, "obat": 1,

    # Family & relationships
    "ibu": 1, "ayah": 1, "bapak": 1, "mama": 1, "papa": 1,
    "kakak": 1, "adik": 1, "om ": 1, "tante": 1,
    "nenek": 2, "kakek": 2, "keluarga": 2,
    "pacar": 2, "mantan": 2, "gebetan": 2, "crush": 2,
    "jomblo": 2, "single": 1, "nikah": 2, "kawin": 2,
    "teman": 1, "sobat": 1, "sahabat": 2,

    # Work & school
    "sekolah": 2, "kuliah": 2, "kampus": 2, "kerja": 1,
    "kantor": 2, "bos": 2, "karyawan": 2, "magang": 2,
    "interview": 2, "wawancara": 2, "gagal": 2, "menang": 1,

    # Personal stories / reflections
    "pengalaman pribadi": 4, "curhat": 3, "cerita pribadi": 4,
    "pengalaman gua": 4, "pengalaman aku": 4,
    "gua ceritain": 3, "aku ceritain": 3,
    "jadi ceritanya": 3, "ceritanya gini": 3,
    "gua mau cerita": 4, "denger-denger": 2,
    "gua dulu": 3, "aku dulu": 3,
    "gua pernah": 3, "aku pernah": 3,
    "pertama kali": 2, "terakhir kali": 2,
    "yang pertama": 1, "yang terakhir": 1,
    "sebelum": 1, "sesudah": 1, "dahulu": 2,
    "kemarin": 1, "tadi": 1, "besok": 1, "lusa": 1,

    # Life events
    "liburan": 2, "jalan-jalan": 2, "libur": 1,
    "ulang tahun": 2, "ultah": 2,
    "hadiah": 1, "kejutan": 2, "kaget": 2, "shock": 2,
    "speechless": 2, "gak percaya": 3, "nggak percaya": 3,
    "heran": 2, "bingung": 1, "pusing": 2, "overwhelm": 2,

    # Social / chat / online
    "chat": 1, "wa ": 1, "whatsapp": 1, "dm ": 2,
    "instagram": 1, "tiktok": 1, "subscribe": 1, "subscriber": 1,
    "donasi": 2, "gift": 1, "sponsor": 1, "brand": 1,

    # Food & daily life
    "makan": 1, "nasi": 1, "mie": 1, "kopi": 1,
    "masak": 2, "belanja": 2, "pasar": 1, "mall": 1,

    # Tech / setup (personal context)
    "laptop": 1, "hp ": 1, "handphone": 1, "komputer": 1,
    "setup": 1, "meja": 1, "kursi": 1, "kamar": 1,
    "rumah": 1, "kos": 1, "kost": 1,

    # Transportation
    "sepeda": 1, "mobil": 1, "motor": 1, "bus": 1,
    "kereta": 1, "pesawat": 1, "ojol": 1, "grab": 1,

    # Self-reflection
    "gua sadar": 2, "aku sadar": 2,
    "gua mikir": 2, "aku mikir": 2,
    "gua rasa": 2, "aku rasa": 2,
    "sebenarnya": 1, "jujur": 2, "jujurly": 2,

    # Storytelling markers
    "jadi gini": 3, "jadi ceritanya": 3, "begini ceritanya": 3,
    "gua ceritain ya": 4, "dengerin dulu": 3,
    "ini ceritanya": 3, "ceritanya": 2,
    "masalahnya": 2, "intinya": 2, "pokoknya": 1,
}

# Keywords yang indikator GAMEPLAY (negative score)
GAMEPLAY_KEYWORDS = {
    "skill": -1, "attack": -1, "damage": -1, "hp": -2,
    "boss": -1, "battle": -1, "fight": -1, "enemy": -1,
    "quest": -2, "mission": -1, "level": -1, "exp": -2,
    "xp": -2, "rank": -1, "score": -1, "achievement": -1,
    "gacha": -2, "pull": -1, "banner": -1, "rarity": -2,
    "loot": -2, "drop": -1, "equip": -1, "inventory": -2,
    "shop": -1, "upgrade": -1, "craft": -1, "build": -1,
    "heal": -1, "shield": -1, "combo": -1, "ultimate": -1,
    "dodge": -1, "roll": -1, "respawn": -2, "spawn": -1,
    "map": -1, "item": -1, "weapon": -1, "armor": -1,
    "character": -1, "unlock": -1, "lock": -1, "key": -1,
    "chest": -1, "gold": -1, "coin": -1, "gem": -1,
    "crystal": -1, "material": -1, "resource": -1,
    "anomali": -1, "domain": -1, "expansion": -1,
    "loading": -1, "lag": -1, "fps": -2, "frame": -1,
    "grafik": -1, "animasi": -1, "cinematic": -1,
    "dialog": -1, "npc": -2, "cutscene": -1,
    "health": -1, "mana": -2, "stamina": -1,
    "defense": -1, "guard": -1, "normal attack": -2,
    "special": -1, "target": -1, "aim": -1, "shoot": -1,
    "kill": -1, "die": -1, "dead": -1,
    "reward": -1, "reward": -1, "claim": -1,
    "teleport": -1, "tower": -1, "portal": -1,
    "open world": -2, "mmorpg": -2, "mmo": -2,
    "rpg": -1, "fps": -2, "moba": -2,
}


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _sec_to_ts(sec: float) -> str:
    """Convert seconds to HH:MM:SS.mmm"""
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"


def _ts_to_sec(ts: str) -> float:
    """Convert HH:MM:SS.mmm to seconds"""
    parts = ts.replace(",", ".").split(":")
    return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])


def parse_srt(filepath: str) -> list[SubtitleEntry]:
    """Parse SRT file into list of SubtitleEntry"""
    entries = []
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()

    # Split by double newline (SRT blocks)
    blocks = re.split(r'\n\s*\n', content.strip())

    for block in blocks:
        lines = block.strip().split("\n")
        if len(lines) < 3:
            continue

        # Line 1: index
        try:
            idx = int(lines[0].strip())
        except ValueError:
            continue

        # Line 2: timestamp
        ts_match = re.match(
            r'(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,\.]\d{3})',
            lines[1].strip()
        )
        if not ts_match:
            continue

        start_sec = _ts_to_sec(ts_match.group(1))
        end_sec = _ts_to_sec(ts_match.group(2))

        # Line 3+: text
        text = " ".join(lines[2:]).strip()
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        if text:
            entries.append(SubtitleEntry(
                index=idx,
                start_sec=start_sec,
                end_sec=end_sec,
                text=text
            ))

    return entries


def chunk_entries(
    entries: list[SubtitleEntry],
    chunk_sec: float = 60.0,
    overlap_sec: float = 15.0
) -> list[StorytimeSegment]:
    """Chunk subtitle entries into overlapping windows"""
    if not entries:
        return []

    segments = []
    total_duration = entries[-1].end_sec

    start = entries[0].start_sec
    while start < total_duration:
        end = start + chunk_sec

        # Collect entries in this window
        chunk_texts = []
        for e in entries:
            if e.start_sec >= start and e.start_sec < end:
                chunk_texts.append(e.text)
            elif e.end_sec > start and e.start_sec < end:
                chunk_texts.append(e.text)

        if chunk_texts:
            text = " ".join(chunk_texts)
            segments.append(StorytimeSegment(
                start_sec=start,
                end_sec=min(end, total_duration),
                text=text,
                score=0.0
            ))

        start += chunk_sec - overlap_sec

    return segments


def score_segment(segment: StorytimeSegment) -> StorytimeSegment:
    """Score a segment for storytime likelihood"""
    text_lower = segment.text.lower()
    score = 0.0
    matched = []

    # Storytime keywords (positive)
    for keyword, weight in STORYTIME_KEYWORDS.items():
        if keyword in text_lower:
            score += weight
            matched.append(f"+{weight}:{keyword}")

    # Gameplay keywords (negative)
    for keyword, weight in GAMEPLAY_KEYWORDS.items():
        if keyword in text_lower:
            score += weight  # weight is negative
            matched.append(f"{weight}:{keyword}")

    # Bonus: longer coherent text = more likely storytime
    word_count = len(segment.text.split())
    if word_count > 30:
        score += 1
    if word_count > 60:
        score += 2

    # Bonus: contains first-person markers
    first_person = ["gua ", "aku ", "saya ", "gue "]
    fp_count = sum(1 for fp in first_person if fp in text_lower)
    if fp_count >= 3:
        score += 2
        matched.append("+2:first_person_dense")

    # Penalty: too short
    if word_count < 10:
        score -= 3
        matched.append("-3:too_short")

    segment.score = score
    segment.matched_keywords = matched
    return segment


def scan_storytime(
    srt_path: str,
    chunk_sec: float = 60.0,
    overlap_sec: float = 15.0,
    min_score: float = 3.0,
    min_duration: float = 20.0,
    max_duration: float = 300.0,
) -> list[StorytimeSegment]:
    """Main scan function: parse → chunk → score → filter → rank"""

    print(f"📂 Parsing SRT: {srt_path}")
    entries = parse_srt(srt_path)
    print(f"   {len(entries)} subtitle entries parsed")

    print(f"🔪 Chunking ({chunk_sec}s windows, {overlap_sec}s overlap)...")
    segments = chunk_entries(entries, chunk_sec, overlap_sec)
    print(f"   {len(segments)} chunks created")

    print(f"📊 Scoring segments...")
    segments = [score_segment(s) for s in segments]

    # Filter
    filtered = [
        s for s in segments
        if s.score >= min_score
        and s.duration >= min_duration
        and s.duration <= max_duration
    ]

    # Sort by score descending
    filtered.sort(key=lambda s: s.score, reverse=True)

    # Label
    for i, s in enumerate(filtered):
        s.label = f"storytime_{i+1:02d}"

    print(f"✅ {len(filtered)} storytime segments found (score >= {min_score})")
    return filtered


def export_results(
    segments: list[StorytimeSegment],
    output_path: str,
    srt_path: str = "",
):
    """Export results to JSON"""
    result = {
        "scanner": "storytime_scanner v1.0",
        "source_srt": srt_path,
        "total_segments": len(segments),
        "segments": []
    }

    for s in segments:
        result["segments"].append({
            "label": s.label,
            "start_sec": round(s.start_sec, 3),
            "end_sec": round(s.end_sec, 3),
            "start_ts": s.start_ts,
            "end_ts": s.end_ts,
            "duration_sec": round(s.duration, 1),
            "score": s.score,
            "matched_keywords": s.matched_keywords,
            "text_preview": s.text[:300] + ("..." if len(s.text) > 300 else ""),
            "text_full": s.text,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"💾 Results saved: {output_path}")


def print_summary(segments: list[StorytimeSegment]):
    """Print human-readable summary to console"""
    if not segments:
        print("\n❌ No storytime segments found. Try lowering --min-score")
        return

    print(f"\n{'='*70}")
    print(f"  STORYTIME SEGMENTS — {len(segments)} found")
    print(f"{'='*70}")

    for s in segments:
        dur_min = int(s.duration // 60)
        dur_sec = int(s.duration % 60)
        print(f"\n  📖 {s.label}  [{s.start_ts} → {s.end_ts}] ({dur_min}m{dur_sec}s)  score={s.score:.0f}")
        print(f"     Keywords: {', '.join(s.matched_keywords[:8])}")
        # Print text preview (first 200 chars)
        preview = s.text[:200].replace('\n', ' ')
        print(f"     {preview}...")

    print(f"\n{'='*70}")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Scan SRT transkrip cari segmen storytime/anecdote",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python storytime_scanner.py stream.id.srt
  python storytime_scanner.py stream.id.srt --output results.json --min-score 2.0
  python storytime_scanner.py stream.id.srt --chunk 45 --overlap 10
        """
    )
    parser.add_argument("srt_file", help="Path to SRT subtitle file")
    parser.add_argument("--output", "-o", default="storytime_results.json",
                        help="Output JSON file (default: storytime_results.json)")
    parser.add_argument("--min-score", type=float, default=3.0,
                        help="Minimum storytime score threshold (default: 3.0)")
    parser.add_argument("--chunk", type=float, default=60.0,
                        help="Chunk window size in seconds (default: 60)")
    parser.add_argument("--overlap", type=float, default=15.0,
                        help="Overlap between chunks in seconds (default: 15)")
    parser.add_argument("--min-duration", type=float, default=20.0,
                        help="Minimum segment duration in seconds (default: 20)")
    parser.add_argument("--max-duration", type=float, default=300.0,
                        help="Maximum segment duration in seconds (default: 300)")

    args = parser.parse_args()

    segments = scan_storytime(
        srt_path=args.srt_file,
        chunk_sec=args.chunk,
        overlap_sec=args.overlap,
        min_score=args.min_score,
        min_duration=args.min_duration,
        max_duration=args.max_duration,
    )

    print_summary(segments)
    export_results(segments, args.output, args.srt_file)


if __name__ == "__main__":
    main()
