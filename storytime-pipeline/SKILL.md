---
name: storytime-pipeline
description: SOP untuk membuat video storytime dari livestream — cari momen yapping/cerita menarik (1-10 menit), clipping sederhana tanpa perlu kreatif bikin skrip. Includes full video type taxonomy and hybrid chunking pipeline.
---

# Storytime Pipeline SOP

## Konsep
Cari momen streamer "yapping" / cerita menarik dari livestream. Durasi 1-10 menit. Tanpa perlu bikin skrip kreatif — ini murni clipping.

**Prinsip utama**: Script harus **standalone** — bisa jalan tanpa Hermes, tanpa LLM, tanpa API keys. Orang tinggal `python script.py input.srt` → dapet output. Fokus ke kerja dulu, GitHub/upload belakangan.

## Video Type Taxonomy (8 Types)

Semua chunk dari livestream diklasifikasikan ke salah satu jenis:

| Type | Deskripsi | Durasi |
|------|-----------|--------|
| `storytime` | Cerita personal di luar game — pengalaman, curhat, anekdot (VTuber style) | 1-10 menit |
| `reaction` | Letupan emosi singkat — gacha pull, rage moment, surprise | 5-60 detik |
| `lore` | Menceritakan ulang lore game, teori, backstory | 30-300 detik |
| `experience` | Opini personal, ulasan mendalam, video essay | 10-600 detik |
| `tutorial` | Tutorial, how-to, build-with-me, vibecoding | 10-600 detik |
| `shorts` | Klip bagus standalone — tidak nyambung narasi panjang | 10-60 detik |
| `shorts_story` | Rangkuman yapping ringan dalam 1 menit | 30-90 detik |
| `raw_clip` | Momen epik/kocak murni — tanpa narasi, cuma gameplay keren | 5-120 detik |

## Hybrid Chunking Pipeline

### Phase 1: Time-based Chunking
- Window: 2.5 menit per chunk (configurable)
- Smart cut di jeda bicara (>1.5 detik gap antar subtitle)
- Min 1.5 menit, max 5 menit per chunk
- Hasil: raw chunks (~40 chunks untuk 2 jam stream)

### Phase 2: Keyword-shift Refinement
- Hitung Jaccard similarity antara chunk berdekatan
- Jika similarity tinggi (shift < 0.7) → merge
- Jika similarity rendah (shift >= 0.7) → split di boundary
- Max merged duration: 10 menit

### Phase 3: Topic Labeling (Ratio-Based)
- Setiap chunk di-scan untuk keyword semua 8 video type
- **Ratio scoring**: `storytime_ratio = pos_hits / (pos_hits + neg_hits)`
- **Dual threshold**: setiap type punya `min_hits` (absolute) DAN `min_ratio` (percentage)
- Chunk harus memenuhi KEDUA threshold untuk dapat label
- Chunk dengan total hits < 3 → auto "unknown" (tidak cukup sinyal)
- **Context boosters**: keyword tertentu memberikan bonus besar (+3/+4) sebagai strong signal
  - "belum makan" → +3 untuk storytime
  - "pengalaman pribadi" → +4 untuk storytime
  - "gua ceritain" → +3 untuk storytime
- Setiap type punya `_min_score_to_label` — score minimum untuk override "unknown"
  - `tutorial`: 8 (banyak false positive dari kata casual)
  - `storytime`: 3
  - `reaction`: 2
  - `lore`: 3
  - `experience`: 4
  - `shorts`: 2
  - `shorts_story`: 3
  - `raw_clip`: 2

## Flow

### 1. Chunking (`topic_chunker.py`)
```
Input: SRT/VTT file
  → Parse segments
  → Time-based chunking (2.5 min windows)
  → Keyword-shift refinement
  → Topic labeling (8 types)
  → Output: chunks.json
```

```bash
python topic_chunker.py stream.id.srt --output chunks.json --target-minutes 2.5
```

Output JSON berisi: chunk_id, start_ts, end_ts, duration, label, label_score, label_signals, text_full

### 2. Storytime Selection
- Filter chunks dengan `label == "storytime"` dan `label_score >= 5`
- Review text_preview untuk confirm (bisa false positive)
- Pilih chunk dengan score tertinggi

### 3. Technician — Extract Clip (`video_cutter.py`)
- Input: timestamp start/end + source video
- Extract menggunakan ffmpeg dengan CUDA decode

```bash
python video_cutter.py source.mp4 --start 02:02:31 --end 02:03:12 --output storytime_040.mp4
```

Untuk AV1 source:
```bash
ffmpeg -hwaccel cuda -hwaccel_output_format cuda -ss START -i SOURCE -t DURATION -c:v h264_nvenc -preset p1 -b:v 8M -c:a aac -b:a 128k OUTPUT
```

**Penting**: Pakai `-t DURATION` bukan `-to END_TIME`. Stream copy tidak reliable untuk AV1.

### 4. Output
- Satu file MP4 per storytime clip
- Filename: `storytime_{chunk_id}_{start_time}.mp4`
- Metadata: timestamp, durasi, label, score

## Keyword Scoring Rules

### Ratio-Based Scoring
```
pos_hits = jumlah keyword positif yang match
neg_hits = jumlah counter-keyword yang match
total_hits = pos_hits + neg_hits
ratio = pos_hits / total_hits   (0.0 to 1.0)
net_score = pos_hits - neg_hits + booster_score
```
- Chunk dapat label jika: `pos_hits >= min_hits` DAN `ratio >= min_ratio` DAN `total_hits >= 3`
- Jika tidak memenuhi → label "unknown"

### Word Boundary Matching
- Keyword <4 chars → pakai `\b` word boundary regex (contoh: "api" tidak match "impact", "aim" tidak match "mungkin")
- Keyword >=4 chars → substring match biasa

### Context Boosters
- Keyword tertentu memberikan bonus besar sebagai strong signal
- "belum makan" → +3, "pengalaman pribadi" → +4, "gua ceritanya" → +3
- Booster ditambahkan ke net_score DAN di-count sebagai pos_hits

### Context-aware Scoring
- "cerita" di konteks gameplay (cerita game, lore) → negative via counter-keywords
- "cerita" di konteks personal (gua cerita, curhat) → positive via keywords
- "dulu" di konteks gameplay (main dulu, lihat dulu) → negative via context cancelers
- "dulu" di konteks personal (gua dulu, aku dulu) → positive via keywords

### First Person Bonus
- Jika chunk mengandung >=3 first-person markers ("gua", "aku", "saya", "gue") → +2 bonus untuk storytime types

### Min Score per Type
- `tutorial`: min score 8 (banyak false positive dari kata casual)
- `storytime`: min score 3, min_hits 3, min_ratio 0.50
- `reaction`: min score 2, min_hits 3, min_ratio 0.40
- `lore`: min score 3, min_hits 3, min_ratio 0.40
- `experience`: min score 4, min_hits 4, min_ratio 0.45
- `shorts`: min score 2, min_hits 3, min_ratio 0.35
- `shorts_story`: min score 3, min_hits 3, min_ratio 0.40
- `raw_clip`: min score 2, min_hits 3, min_ratio 0.35

## Script Architecture

Semua script di `hermes_skills/`:
- **Zero LLM dependency** — murni Python + regex
- **Config-driven** — keyword list di JSON file
- **CLI** — argparse dengan `--help`
- **Output JSON** — bisa di-chain ke script lain

```
hermes_skills/
├── topic_chunker.py          # Hybrid chunking + topic labeling
├── storytime_scanner.py      # Scan storytime-specific segments
├── storytime_keywords.json   # Keyword config untuk storytime
├── semanticchunker.py        # Time-based chunking (standalone)
├── video_cutter.py           # ffmpeg wrapper untuk cut video
└── technician.py             # Video processing pipeline
```

## Script Reference

- `scripts/topic_chunker.py` — Hybrid chunking + ratio-based topic labeling (standalone, no dependencies)
  ```bash
  python scripts/topic_chunker.py stream.id.srt --output chunks.json
  ```

## Pitfalls

1. **False positive "dulu"** — "investigate dulu", "main dulu" itu gameplay, bukan storytime. Counter-keyword: "main", "game", "skill" di dekat "dulu". Context cancelers: "dulu main", "dulu level", "dulu game", "investigate dulu", "lihat dulu".

2. **False positive "tutorial"** — kata "gimana", "cara", "bikin" muncul di konteks casual gaming. Solusi: min score threshold tinggi (8), word boundary matching, hapus keyword yang terlalu generic ("cara" → hanya "cara bikin", "cara ngoding", dll).

3. **Auto-generated SRT noise** — YouTube auto-caption sering salah transkrip. "api" bisa jadi "impact", "git" bisa jadi "gitu", "aim" bisa jadi "mungkin". Selalu pakai word boundary untuk keyword pendek. Hapus keyword yang terlalu pendek (<3 chars) dari counter-keywords.

4. **Chunk terlalu pendek** — Storytime butuh minimal 20-30 detik. Chunk <20s di storytime → auto-reject via min_duration.

5. **Storytime jarang di gaming stream** — Untuk stream gaming 2 jam, expect storytime hanya 1-3 chunks. Jangan paksa label — biarkan "unknown" untuk chunk yang tidak jelas.

6. **Daily life keywords penting** — Storytime di closing stream sering mengandung: "istirahat", "beli makan", "mau makan", "gua mau", "mikirnya", "belum makan dari kemarin". Tambah sebagai storytime keywords.

7. **Jangan over-engineer** — Fokus ke script yang jalan dulu. GitHub/upload belakangan. User preference: "chill man", "kejauhan mikirnya".

## Perbedaan dengan Pipeline Lain

| Aspekt | 5C Pipeline | Storytime Pipeline |
|--------|-------------|-------------------|
| Script | Perlu 5C full | Tidak perlu |
| Storyteller | Perlu | Tidak perlu |
| Editing | Complex | Minimal |
| Durasi | 10-15 menit | 1-10 menit |
| Goal | Satisfying narrative | Raw engaging moment |
| Chunking | Per-clip | Hybrid (time + keyword-shift) |
