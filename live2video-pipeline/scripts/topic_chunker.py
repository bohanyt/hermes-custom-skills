#!/usr/bin/env python3
"""
topic_chunker.py v2 — Hybrid chunking + ratio-based topic labeling

Flow:
  1. Parse SRT/VTT → segments
  2. Time-based chunking (2.5 min window, smart cut at silence gaps)
  3. Keyword-shift refinement (merge similar adjacent chunks)
  4. Ratio-based topic labeling (storytime_ratio = st_hits / total_hits)
  5. Output: chunks.json dengan label, score, ratio, dan ffmpeg commands

Usage:
  python topic_chunker.py <file.srt> [--output chunks.json] [--target-minutes 2.5]

Scoring:
  - Setiap chunk di-scan untuk keyword semua video type
  - storytime_ratio = storytime_hits / (storytime_hits + gameplay_hits)
  - Label diberikan berdasarkan ratio tertinggi DAN absolute hits > minimum
  - Chunk dengan total hits < 3 → "unknown" (tidak cukup sinyal)

Video Type Labels:
  storytime     — Cerita personal di luar game (ratio > 0.5, min 3 hits)
  reaction      — Letupan emosi singkat (gacha/rage/surprise)
  lore          — Lore game, teori, backstory
  experience    — Opini personal, ulasan mendalam
  tutorial      — Tutorial, how-to, coding
  shorts        — Klip bagus standalone (< 60 detik)
  shorts_story  — Yapping ringkas (~ 1 menit)
  raw_clip      — Momen epik/kocak murni
  unknown       — Tidak cukup sinyal untuk label apapun
"""

import re
import json
import argparse
import sys
from pathlib import Path
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════════════════════════
# DATA
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Segment:
    start_sec: float
    end_sec: float
    text: str

@dataclass
class Chunk:
    chunk_id: str
    start_sec: float
    end_sec: float
    text: str
    segments: list = field(default_factory=list)
    # Label results
    label: str = "unknown"
    label_score: float = 0.0
    label_ratio: float = 0.0
    label_hits: int = 0
    label_signals: list = field(default_factory=list)
    # All type scores (for debugging)
    all_scores: dict = field(default_factory=dict)

    @property
    def duration(self):
        return self.end_sec - self.start_sec

    @property
    def start_ts(self):
        return _sec_to_ts(self.start_sec)

    @property
    def end_ts(self):
        return _sec_to_ts(self.end_sec)

    @property
    def word_count(self):
        return len(self.text.split())


# ─── Video Type Definitions ───────────────────────────────────────────────────

# Setiap type punya: keywords (positive), counter_keywords (negative), min_hits, min_ratio
# Scoring: hit keyword → +1, hit counter → -1
# Ratio = positive_hits / (positive_hits + abs(counter_hits))

VIDEO_TYPES = {

    "storytime": {
        "description": "Cerita personal di luar game — pengalaman, curhat, anekdot",
        "min_hits": 3,           # minimal 3 keyword hits (turun dari 4)
        "min_ratio": 0.50,       # minimal 50% dari total hits adalah storytime
        "min_duration": 20,      # minimal 20 detik
        "max_duration": 600,     # maximal 10 menit
        "keywords": [
            # Strong (+2 each)
            "pengalaman pribadi", "cerita pribadi", "curhat",
            "gua ceritain", "aku ceritain", "gua mau cerita",
            "jadi ceritanya", "ceritanya gini", "begini ceritanya",
            "gua dulu", "aku dulu", "gua pernah", "aku pernah",
            "memalukan", "malu banget",
            "belum makan", "belum tidur",
            # Medium (+1 each)
            "pengalaman", "kejadian", "peristiwa",
            "ngakak", "geli",
            "stress", "stres", "cemas", "sedih", "nangis", "menangis",
            "marah", "kesel", "jengkel", "capek", "lelah", "cape",
            "lapar", "ngantuk", "mimpi", "insomnia",
            "sakit", "demam", "dokter", "rumah sakit",
            "keluarga", "pacar", "mantan", "gebetan", "crush",
            "jomblo", "nikah",
            "sekolah", "kuliah", "kampus",
            "kantor", "bos",
            "liburan", "jalan-jalan",
            "ulang tahun", "ultah",
            "kaget", "speechless", "gak percaya", "nggak percaya",
            "heran", "pusing", "overwhelm",
            "gua sadar", "aku sadar", "gua mikir", "aku mikir",
            "gua rasa", "aku rasa",
            "jujur", "sebenarnya",
            "masak", "belanja", "kopi",
            "laptop", "rumah", "kos", "kost",
            "makan", "tidur",
            # Daily life / personal context (+1 each)
            "istirahat", "beli makan", "mau makan", "mau tidur",
            "lapar", "ngantuk", "capek", "lelah",
            "rumah", "kos", "kost", "kamar",
            "gua mau", "aku mau", "gua lagi", "aku lagi",
            "mikirnya", "rasanya", "sebenarnya",
            # Storytelling markers (+2 each)
            "jadi gini", "dengerin dulu", "ini ceritanya",
            "masalahnya", "intinya",
            "ceritanya",
        ],
        "counter_keywords": [
            # Gameplay context → negative signal
            "skill", "attack", "damage", "hp", "boss", "battle", "fight",
            "enemy", "quest", "mission", "level", "exp", "xp",
            "gacha", "pull", "banner", "rarity", "loot", "drop",
            "equip", "inventory", "heal", "shield", "combo", "ultimate",
            "dodge", "roll", "respawn", "spawn", "map", "item", "weapon",
            "armor", "character", "unlock", "chest", "gold", "coin",
            "gem", "crystal", "material", "resource",
            "anomali", "domain", "expansion", "loading", "lag", "fps",
            "grafik", "animasi", "cinematic", "dialog", "npc", "cutscene",
            "mana", "stamina", "defense", "guard", "special", "target",
            "kill", "die", "dead", "teleport", "tower", "portal",
            "open world", "mmorpg", "rpg", "moba",
            # Context cancelers
            "dulu main", "dulu level", "dulu game",
            "investigate dulu", "lihat dulu", "main dulu",
        ],
        "context_boosters": [
            # Kalau ada ini, bonus +3 (strong storytime signal)
            ("gua ceritain", 3),
            ("aku ceritain", 3),
            ("jadi ceritanya", 3),
            ("belum makan", 3),
            ("belum tidur", 3),
            ("pengalaman pribadi", 4),
            ("cerita pribadi", 4),
        ],
    },

    "reaction": {
        "description": "Letupan emosi singkat — gacha pull, rage moment, surprise",
        "min_hits": 3,
        "min_ratio": 0.40,
        "min_duration": 5,
        "max_duration": 60,
        "keywords": [
            "oh my god", "omg", "astaga",
            "gila", "gila sih", "gila banget",
            "anjir", "anjing", "bangsat", "sialan",
            "waduh", "wadaw",
            "kaget", "shock", "speechless",
            "nggak percaya", "gak percaya", "ngakak",
            "ketawa", "hahaha", "wkwk", "wkwkwk",
            "no way", "hell no", "hell yes",
            "nice", "mantap", "keren",
            "sumpah", "seriously",
            "what the", "what the hell", "wtf",
            "boom", "meledak", "ledak",
            "ssr", "legendary", "rare", "epic",
            "rage", "kesel", "frustrasi",
        ],
        "counter_keywords": [
            "jadi gini", "ceritanya", "dulu",
            "tutorial", "how to", "cara",
        ],
    },

    "lore": {
        "description": "Menceritakan ulang lore game, teori, backstory",
        "min_hits": 3,
        "min_ratio": 0.40,
        "min_duration": 30,
        "max_duration": 300,
        "keywords": [
            "lore", "backstory", "cerita game", "storyline",
            "plot", "narrative", "narasi",
            "teori", "theory", "teoriin",
            "jadi ceritanya", "cerita karakter",
            "sebenarnya", "actually",
            "did you know", "fun fact",
            "latar belakang", "origin", "asal",
            "sejarah", "history",
            "misteri", "mystery", "rahasia",
            "tersembunyi", "hidden", "easter egg",
            "developer", "dev", "pembuat",
            "referensi", "reference", "inspirasi",
            "based on", "terinspirasi",
            "katanya", "konon", "rumor",
            "jadi gini", "maksudnya", "artinya",
        ],
        "counter_keywords": [
            "gua dulu", "aku dulu", "pengalaman pribadi",
            "curhat", "cerita pribadi",
        ],
    },

    "experience": {
        "description": "Opini personal, ulasan mendalam, video essay style",
        "min_hits": 4,
        "min_ratio": 0.45,
        "min_duration": 60,
        "max_duration": 600,
        "keywords": [
            "menurut gua", "menurut aku", "menurut saya",
            "gua rasa", "aku rasa", "gua pikir", "aku pikir",
            "opini", "pendapat", "ulasan", "review",
            "bagus", "jelek", "mantap", "buruk",
            "rekomendasi", "recommend", "saran",
            "tips", "trik", "tips and trik",
            "perbandingan", "compare", "vs", "versus",
            "terbaik", "the best", "worst", "terburuk",
            "rating", "rate", "bintang",
            "worth it", "sepadan", "value",
            "harga", "price", "murah", "mahal",
            "gratis", "free", "bayar", "paid",
            "overall", "secara keseluruhan",
            "kesimpulan", "conclusion", "kesimpulannya",
            "plus minus", "kelebihan", "kekurangan",
            "pro", "kontra", "pro kontra",
            "jujur", "honestly", "to be honest", "sejujurnya",
        ],
        "counter_keywords": [
            "dulu", "cerita gua", "cerita aku",
        ],
    },

    "tutorial": {
        "description": "Tutorial, how-to, build-with-me, vibecoding",
        "min_hits": 5,
        "min_ratio": 0.50,
        "min_duration": 30,
        "max_duration": 600,
        "keywords": [
            "tutorial", "how to",
            "cara bikin", "cara buat", "cara ngoding", "cara setup",
            "cara install", "cara deploy", "cara konfigurasi",
            "langkah", "tahap", "tahapan",
            "install", "setup", "konfigurasi",
            "ngoding",
            "vibecoding", "vibe coding",
            "python", "javascript", "typescript",
            "react", "nextjs", "vue",
            "database", "deploy",
            "framework", "library",
            "debug", "debugging",
            "terminal", "command line", "cli",
            "vscode", "belajar coding", "belajar program",
        ],
        "counter_keywords": [
            "gimana ya", "gimana sih",
            "main", "game", "skill",
        ],
    },

    "shorts": {
        "description": "Klip bagus standalone — tidak nyambung narasi panjang",
        "min_hits": 3,
        "min_ratio": 0.35,
        "min_duration": 10,
        "max_duration": 60,
        "keywords": [
            "oh my god", "omg", "astaga",
            "gila", "anjir", "waduh",
            "kaget", "shock", "speechless",
            "ngakak", "ketawa", "hahaha",
            "no way", "hell no", "hell yes",
            "nice", "mantap", "keren",
            "boom", "meledak",
            "ssr", "legendary",
            "rage", "kesel",
        ],
        "counter_keywords": [
            "jadi gini", "ceritanya", "dulu",
            "tutorial", "how to",
        ],
    },

    "shorts_story": {
        "description": "Rangkuman yapping ringan dalam 1 menit",
        "min_hits": 3,
        "min_ratio": 0.40,
        "min_duration": 30,
        "max_duration": 90,
        "keywords": [
            "jadi gini", "ceritanya", "dulu",
            "pengalaman", "kejadian",
            "ngakak", "ketawa", "geli",
            "lucu", "aneh", "unik",
        ],
        "counter_keywords": [
            "skill", "damage", "boss", "quest",
            "tutorial", "how to",
        ],
    },

    "raw_clip": {
        "description": "Momen epik/kocak murni — tanpa narasi, cuma gameplay yang keren",
        "min_hits": 3,
        "min_ratio": 0.35,
        "min_duration": 5,
        "max_duration": 120,
        "keywords": [
            "keren", "epic", "peak", "cinema",
            "absolute cinema", "cinematic",
            "wow", "wah", "wih",
            "smooth", "clean", "polished",
            "satisfying", "dope", "fire",
            "insane", "crazy", "nuts",
            "clip", "highlight", "best moment",
            "montage", "compilation",
            "no way", "unreal",
            "boom", "meledak", "ledak",
            "combo", "perfect", "flawless",
            "savage", "brutal",
        ],
        "counter_keywords": [
            "jadi gini", "ceritanya", "dulu",
            "tutorial", "how to",
            "gua dulu", "aku dulu",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def _sec_to_ts(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}"

def _ts_to_sec(ts):
    parts = ts.replace(",", ".").split(":")
    if len(parts) == 3:
        return float(parts[0]) * 3600 + float(parts[1]) * 60 + float(parts[2])
    elif len(parts) == 2:
        return float(parts[0]) * 60 + float(parts[1])
    return 0.0

def parse_transcript(file_path):
    with open(file_path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    ext = Path(file_path).suffix.lower()
    if ext == ".srt":
        return _parse_srt(content)
    return _parse_vtt(content)

def _parse_srt(content):
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
        text = " ".join(l.strip() for l in lines[ts_line+1:] if l.strip())
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            segments.append(Segment(_ts_to_sec(m.group(1)), _ts_to_sec(m.group(2)), text))
    return segments

def _parse_vtt(content):
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
        text = " ".join(l.strip() for l in lines[ts_idx+1:] if l.strip())
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            segments.append(Segment(_ts_to_sec(m.group(1)), _ts_to_sec(m.group(2)), text))
    return segments


# ═══════════════════════════════════════════════════════════════════════════════
# CHUNKING
# ═══════════════════════════════════════════════════════════════════════════════

def time_chunk(segments, target_min=2.5, min_min=1.0, max_min=5.0):
    """Phase 1: Time-based chunking with smart cut at silence gaps"""
    if not segments:
        return []

    chunks = []
    target_sec = target_min * 60
    min_sec = min_min * 60
    max_sec = max_min * 60
    silence_threshold = 1.5

    i = 0
    chunk_id = 1

    while i < len(segments):
        chunk_start = segments[i].start_sec
        target_end = chunk_start + target_sec
        min_end = chunk_start + min_sec
        max_end = chunk_start + max_sec

        best_j = None
        best_gap = 0.0

        for j in range(i, len(segments)):
            if segments[j].end_sec > max_end:
                break
            if segments[j].end_sec < min_end:
                continue
            if j + 1 < len(segments):
                gap = segments[j+1].start_sec - segments[j].end_sec
                if gap >= silence_threshold and gap > best_gap:
                    best_gap = gap
                    best_j = j

        if best_j is None:
            closest = float("inf")
            for j in range(i, len(segments)):
                if segments[j].end_sec > max_end:
                    break
                dist = abs(segments[j].end_sec - target_end)
                if dist < closest:
                    closest = dist
                    best_j = j
            if best_j is None:
                best_j = len(segments) - 1

        chunk_segs = segments[i:best_j+1]
        text = " ".join(s.text for s in chunk_segs)
        chunks.append(Chunk(
            chunk_id=f"chunk_{chunk_id:03d}",
            start_sec=chunk_segs[0].start_sec,
            end_sec=chunk_segs[-1].end_sec,
            text=text,
            segments=[{"start": s.start_sec, "end": s.end_sec, "text": s.text} for s in chunk_segs],
        ))
        i = best_j + 1
        chunk_id += 1

    return chunks


def detect_topic_shift(chunk_a, chunk_b):
    """Jaccard similarity between two chunks"""
    words_a = set(chunk_a.text.lower().split())
    words_b = set(chunk_b.text.lower().split())
    if not words_a or not words_b:
        return 0.5
    intersection = words_a & words_b
    union = words_a | words_b
    return 1.0 - (len(intersection) / len(union)) if union else 0


def refine_chunks(chunks, shift_threshold=0.7):
    """Phase 2: Merge adjacent chunks with similar topics"""
    if len(chunks) <= 1:
        return chunks

    refined = []
    i = 0
    while i < len(chunks):
        current = chunks[i]
        while i + 1 < len(chunks):
            next_chunk = chunks[i + 1]
            shift = detect_topic_shift(current, next_chunk)
            if shift < shift_threshold and (current.duration + next_chunk.duration) < 600:
                current.end_sec = next_chunk.end_sec
                current.text = current.text + " " + next_chunk.text
                current.segments.extend(next_chunk.segments)
                i += 1
            else:
                break
        refined.append(current)
        i += 1

    for idx, chunk in enumerate(refined):
        chunk.chunk_id = f"chunk_{idx+1:03d}"
    return refined


# ═══════════════════════════════════════════════════════════════════════════════
# SCORING — Ratio-based
# ═══════════════════════════════════════════════════════════════════════════════

def _count_keyword_hits(text_lower, keywords):
    """Count how many keywords match in text. Returns (hits, matched_list)"""
    hits = 0
    matched = []
    for kw in keywords:
        if kw in text_lower:
            hits += 1
            matched.append(kw)
    return hits, matched


def _count_counter_hits(text_lower, counter_keywords):
    """Count counter keyword matches. Returns (hits, matched_list)"""
    hits = 0
    matched = []
    for kw in counter_keywords:
        if kw in text_lower:
            hits += 1
            matched.append(kw)
    return hits, matched


def score_chunk(chunk):
    """
    Score satu chunk untuk semua video type.
    Returns dict: {type: {score, ratio, hits, signals}}
    """
    text_lower = chunk.text.lower()
    results = {}

    for vtype, vdef in VIDEO_TYPES.items():
        # Count positive hits
        pos_hits, pos_matched = _count_keyword_hits(text_lower, vdef["keywords"])
        # Count counter hits
        neg_hits, neg_matched = _count_counter_hits(text_lower, vdef.get("counter_keywords", []))

        # Context boosters
        booster_score = 0
        booster_signals = []
        for booster_kw, booster_weight in vdef.get("context_boosters", []):
            if booster_kw in text_lower:
                booster_score += booster_weight
                booster_signals.append(f"+{booster_weight}:{booster_kw}")

        # Total score
        total_hits = pos_hits + neg_hits
        net_score = pos_hits - neg_hits + booster_score

        # Ratio: positive / total (0.0 to 1.0)
        if total_hits > 0:
            ratio = pos_hits / total_hits
        else:
            ratio = 0.0

        # Duration penalty
        dur = chunk.duration
        min_dur = vdef.get("min_duration", 0)
        max_dur = vdef.get("max_duration", float("inf"))
        dur_penalty = ""
        if dur < min_dur:
            dur_penalty = f"too_short({dur:.0f}s<{min_dur}s)"
        elif dur > max_dur:
            dur_penalty = f"too_long({dur:.0f}s>{max_dur}s)"

        signals = [f"+{kw}" for kw in pos_matched[:10]]
        signals += [f"-{kw}" for kw in neg_matched[:5]]
        signals += booster_signals
        if dur_penalty:
            signals.append(dur_penalty)

        results[vtype] = {
            "score": net_score,
            "ratio": round(ratio, 3),
            "pos_hits": pos_hits,
            "neg_hits": neg_hits,
            "total_hits": total_hits,
            "signals": signals,
        }

    return results


def label_chunk(chunk):
    """Label chunk berdasarkan ratio-based scoring"""
    all_scores = score_chunk(chunk)
    chunk.all_scores = all_scores

    # Find best type: highest score that meets min_hits and min_ratio
    best_type = "unknown"
    best_score = 0
    best_ratio = 0
    best_hits = 0
    best_signals = []

    # Sort by score descending
    sorted_types = sorted(all_scores.items(), key=lambda x: x[1]["score"], reverse=True)

    for vtype, scores in sorted_types:
        vdef = VIDEO_TYPES[vtype]
        min_hits = vdef.get("min_hits", 0)
        min_ratio = vdef.get("min_ratio", 0)

        # Check if meets thresholds
        if scores["pos_hits"] >= min_hits and scores["ratio"] >= min_ratio:
            # Additional: total hits must be >= 3 (enough signal)
            if scores["total_hits"] >= 3:
                best_type = vtype
                best_score = scores["score"]
                best_ratio = scores["ratio"]
                best_hits = scores["pos_hits"]
                best_signals = scores["signals"]
                break

    chunk.label = best_type
    chunk.label_score = best_score
    chunk.label_ratio = best_ratio
    chunk.label_hits = best_hits
    chunk.label_signals = best_signals

    return chunk


def label_all_chunks(chunks):
    return [label_chunk(c) for c in chunks]


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

def export_results(chunks, output_path, srt_path=""):
    result = {
        "source": srt_path,
        "total_chunks": len(chunks),
        "chunks": []
    }

    for c in chunks:
        entry = {
            "chunk_id": c.chunk_id,
            "start_ts": c.start_ts,
            "end_ts": c.end_ts,
            "start_sec": round(c.start_sec, 3),
            "end_sec": round(c.end_sec, 3),
            "duration_sec": round(c.duration, 1),
            "word_count": c.word_count,
            "label": c.label,
            "score": c.label_score,
            "ratio": c.label_ratio,
            "hits": c.label_hits,
            "signals": c.label_signals[:15],
            "text_preview": c.text[:300] + ("..." if len(c.text) > 300 else ""),
            "text_full": c.text,
        }
        # Add ffmpeg cut command
        entry["ffmpeg_cut"] = (
            f"ffmpeg -ss {c.start_ts} -i input.mp4 -t {c.duration:.1f} "
            f"-c:v libx264 -c:a aac {c.chunk_id}_{c.label}.mp4"
        )
        result["chunks"].append(entry)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def print_summary(chunks, result):
    """Print human-readable summary"""
    print(f"\n{'='*70}")
    print(f"  TOPIC CHUNK RESULTS — {len(chunks)} chunks")
    print(f"{'='*70}")

    # Label distribution
    label_counts = {}
    for c in chunks:
        label_counts[c.label] = label_counts.get(c.label, 0) + 1

    print(f"\n📊 Label Distribution:")
    for label, count in sorted(label_counts.items(), key=lambda x: -x[1]):
        desc = VIDEO_TYPES.get(label, {}).get("description", "")
        print(f"   {label:15s} — {count:3d} chunks  ({desc})")

    # Per-chunk detail
    print(f"\n{'─'*70}")
    print(f"  CHUNK DETAILS")
    print(f"{'─'*70}")

    for c in chunks:
        dur_m = int(c.duration // 60)
        dur_s = int(c.duration % 60)
        ratio_pct = c.label_ratio * 100

        # Color-code label
        label_icon = {
            "storytime": "📖", "reaction": "💥", "lore": "📜",
            "experience": "🎓", "tutorial": "🔧", "shorts": "⚡",
            "shorts_story": "🗣️", "raw_clip": "🎬", "unknown": "❓",
        }.get(c.label, "  ")

        print(f"\n  {label_icon} {c.chunk_id}  [{c.start_ts} → {c.end_ts}] ({dur_m}m{dur_s}s)")
        print(f"     Label: {c.label:12s} | Score: {c.label_score:+.0f} | Ratio: {ratio_pct:.0f}% | Hits: {c.label_hits}")
        if c.label_signals:
            sig_str = ", ".join(c.label_signals[:8])
            print(f"     Signals: {sig_str}")
        preview = c.text[:150].replace('\n', ' ')
        print(f"     {preview}...")

    print(f"\n{'='*70}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def process_transcript(srt_path, output_path="chunks.json", target_minutes=2.5, shift_threshold=0.7):
    print("=" * 60)
    print("TOPIC CHUNKER v2 — Hybrid Chunking + Ratio-Based Labeling")
    print("=" * 60)

    # Step 1: Parse
    print(f"\n📂 Parsing: {srt_path}")
    segments = parse_transcript(srt_path)
    total_dur = segments[-1].end_sec - segments[0].start_sec if segments else 0
    print(f"   {len(segments)} segments, {_sec_to_ts(total_dur)} total")

    # Step 2: Time-based chunking
    print(f"\n🔪 Time-based chunking (~{target_minutes} min windows)...")
    chunks = time_chunk(segments, target_minutes)
    print(f"   {len(chunks)} raw chunks")

    # Step 3: Keyword-shift refinement
    print(f"\n🔄 Keyword-shift refinement (threshold={shift_threshold})...")
    chunks = refine_chunks(chunks, shift_threshold)
    print(f"   {len(chunks)} refined chunks")

    # Step 4: Topic labeling
    print(f"\n🏷️  Ratio-based topic labeling...")
    chunks = label_all_chunks(chunks)

    # Export
    result = export_results(chunks, output_path, srt_path)
    print(f"\n💾 Saved: {output_path}")

    # Summary
    print_summary(chunks, result)

    return chunks


def main():
    parser = argparse.ArgumentParser(
        description="Hybrid chunking + ratio-based topic labeling untuk transkrip livestream",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python topic_chunker.py stream.id.srt
  python topic_chunker.py stream.id.srt --output my_chunks.json
  python topic_chunker.py stream.id.srt --target-minutes 3 --shift-threshold 0.6
        """
    )
    parser.add_argument("srt_file", help="Path to SRT or VTT subtitle file")
    parser.add_argument("--output", "-o", default="chunks.json", help="Output JSON file")
    parser.add_argument("--target-minutes", "-t", type=float, default=2.5,
                        help="Time window size in minutes (default: 2.5)")
    parser.add_argument("--shift-threshold", "-s", type=float, default=0.7,
                        help="Topic shift threshold 0-1 (default: 0.7)")

    args = parser.parse_args()
    process_transcript(args.srt_file, args.output, args.target_minutes, args.shift_threshold)


if __name__ == "__main__":
    main()
