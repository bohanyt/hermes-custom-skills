# Live2Video Pipeline

Modular Python scripts untuk memotong livestream YouTube menjadi video pendek berdasarkan tipe konten.

## Flow

```
Livestream.mp4 + stream.id.srt
        │
        ▼
┌─────────────────────┐
│  srt_cleaner.py     │  Bersihkan auto-generated SRT
│  (noise removal,    │  - Hapus [Music], [Applause], dll
│   merge segments)   │  - Fix repeated words
│                     │  - Merge short-gap segments
└─────────┬───────────┘
          │ cleaned.srt
          ▼
┌─────────────────────┐
│  topic_chunker.py   │  Chunk + label transkrip
│  (hybrid chunking,  │  - Time-based chunking (2.5min windows)
│   ratio scoring)    │  - Keyword-shift refinement
│                     │  - Ratio-based topic labeling
└─────────┬───────────┘
          │ chunks.json
          ▼
┌─────────────────────┐
│  pipeline_cutter.py │  Cut video per label
│  (ffmpeg wrapper)   │  - Per-label encode presets
│                     │  - CUDA support
└─────────┬───────────┘
          │
          ▼
    cuts/
    ├── storytime/    ← Cerita personal
    ├── reaction/     ← Letupan emosi
    ├── lore/         ← Lore game
    ├── experience/   ← Opini/ulasan
    ├── raw_clip/     ← Momen epik
    ├── shorts/       ← Klip pendek
    └── ...
```

## Requirements

- Python 3.10+
- FFmpeg (with NVENC support recommended for AV1 sources)
- No API keys needed — 100% offline

## Quick Start

### Full pipeline (one command)

```bash
python pipeline_runner.py video.mp4 stream.id.srt
```

### Step by step

```bash
# Step 1: Clean SRT
python srt_cleaner.py stream.id.srt --output cleaned.srt

# Step 2: Chunk + label
python topic_chunker.py cleaned.srt --output chunks.json

# Step 3: Cut specific labels
python pipeline_cutter.py chunks.json video.mp4 --label storytime --label reaction

# Or cut all labels
python pipeline_cutter.py chunks.json video.mp4 --all
```

### CUDA acceleration (for AV1 sources)

```bash
python pipeline_runner.py video.mp4 stream.id.srt --cuda
```

### Dry run

```bash
python pipeline_runner.py video.mp4 stream.id.srt --dry-run
```

## Scripts

### `srt_cleaner.py` — Bersihkan SRT

Bersihkan auto-generated SRT dari YouTube.

```bash
python srt_cleaner.py input.srt [--output cleaned.srt] [--merge-gap 0.5] [--min-duration 0.3]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--output` | `input_cleaned.srt` | Output file |
| `--merge-gap` | `0.5` | Merge segments dengan gap < N detik |
| `--min-duration` | `0.3` | Hapus segment < N detik |
| `--no-remove-tags` | false | Jangan hapus [Music], dll |
| `--no-fix-repeats` | false | Jangan fix repeated words |

**Contoh hasil:** 1444 segments → 528 segments (63% reduction)

### `topic_chunker.py` — Chunk + Label

Hybrid chunking (time-based + keyword-shift) dengan ratio-based labeling.

```bash
python topic_chunker.py cleaned.srt --output chunks.json [--target-minutes 2.5] [--shift-threshold 0.7]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--output` | `chunks.json` | Output JSON |
| `--target-minutes` | `2.5` | Time window per chunk |
| `--shift-threshold` | `0.7` | Topic shift threshold (0-1) |

**Video Type Labels:**

| Label | Description | Min Hits | Min Ratio |
|-------|-------------|----------|-----------|
| `storytime` | Cerita personal di luar game | 3 | 50% |
| `reaction` | Letupan emosi (gacha/rage) | 3 | 40% |
| `lore` | Lore game, teori | 3 | 40% |
| `experience` | Opini/ulasan mendalam | 4 | 45% |
| `tutorial` | Tutorial/coding | 5 | 50% |
| `shorts` | Klip bagus standalone | 3 | 35% |
| `shorts_story` | Yapping ringkas ~1 menit | 3 | 40% |
| `raw_clip` | Momen epik/kocak murni | 3 | 35% |
| `unknown` | Tidak cukup sinyal | — | — |

**Scoring:**
- Setiap keyword match = +1 hit
- Counter keyword match = -1 hit
- `ratio` = positive_hits / total_hits
- Label diberikan jika `hits >= min_hits` AND `ratio >= min_ratio` AND `total_hits >= 3`

### `pipeline_cutter.py` — Cut Video

Cut video berdasarkan label dari chunks.json.

```bash
python pipeline_cutter.py chunks.json video.mp4 --label storytime [--output-dir cuts/] [--cuda] [--dry-run]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--label` | — | Label filter (bisa dipanggil berkali-kali) |
| `--all` | — | Cut semua chunk bukan unknown |
| `--min-score` | `0` | Minimal score |
| `--min-duration` | `0` | Minimal durasi (detik) |
| `--max-duration` | `99999` | Maksimal durasi (detik) |
| `--output-dir` | `cuts/` | Output directory |
| `--cuda` | false | CUDA hardware acceleration |
| `--dry-run` | false | Print commands tanpa execute |

**Encode presets per label:**

| Label | Codec | Preset | CRF | Audio |
|-------|-------|--------|-----|-------|
| storytime | libx264 | slow | 18 | AAC 192k |
| reaction | libx264 | medium | 22 | AAC 128k |
| lore | libx264 | slow | 20 | AAC 192k |
| experience | libx264 | slow | 19 | AAC 192k |
| raw_clip | libx264 | fast | 23 | AAC 128k |
| shorts | libx264 | medium | 22 | AAC 128k |
| tutorial | libx264 | slow | 19 | AAC 192k |

### `pipeline_runner.py` — Orchestrator

Jalankan seluruh pipeline dalam satu command.

```bash
python pipeline_runner.py video.mp4 stream.id.srt [--output-dir output/] [--cuda] [--dry-run]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--output-dir` | `<video_dir>/pipeline_output/` | Output directory |
| `--labels` | all | Labels spesifik |
| `--skip-clean` | false | Skip SRT cleaning |
| `--chunk-only` | false | Hanya chunking, tanpa cut |
| `--cuda` | false | CUDA acceleration |
| `--dry-run` | false | Print commands saja |
| `--target-minutes` | `2.5` | Chunk window size |
| `--shift-threshold` | `0.7` | Topic shift threshold |

## Output Structure

```
pipeline_output/
├── cleaned.srt              # SRT yang sudah dibersihkan
├── chunks.json              # Chunks dengan label + scores
└── cuts/
    ├── storytime/
    │   ├── chunk_040_storytime_02-02-31_079.mp4
    │   └── ...
    ├── reaction/
    │   ├── chunk_001_reaction_00-00-01_040.mp4
    │   └── ...
    ├── lore/
    ├── raw_clip/
    └── ...
```

## chunks.json Format

```json
{
  "source": "stream.id.srt",
  "total_chunks": 40,
  "chunks": [
    {
      "chunk_id": "chunk_040",
      "start_ts": "02:02:31.079",
      "end_ts": "02:03:12.199",
      "start_sec": 7351.079,
      "end_sec": 7392.199,
      "duration_sec": 41.1,
      "word_count": 45,
      "label": "storytime",
      "score": 9,
      "ratio": 1.0,
      "hits": 6,
      "signals": ["+belum makan", "+makan", "+istirahat", "+beli makan", "+gua mau", "+mikirnya"],
      "text_preview": "Hmm. Oh, ya udah sekali...",
      "text_full": "Hmm. Oh, ya udah sekali. Hmm...",
      "ffmpeg_cut": "ffmpeg -ss 02:02:31.079 -i input.mp4 -t 41.1 -c:v libx264 ..."
    }
  ]
}
```

## Tips

1. **Untuk AV1 sources**: selalu pakai `--cuda` flag. AV1 software decode sangat lambat.
2. **Tuning chunk size**: naikkan `--target-minutes` untuk storytime (3-5 menit), turunkan untuk reaction (1-2 menit).
3. **Tuning threshold**: turunkan `--shift-threshold` (0.5-0.6) untuk lebih banyak chunks, naikkan (0.8-0.9) untuk lebih sedikit.
4. **Review dulu**: jalankan `--chunk-only` dan cek `chunks.json` sebelum cut video.
5. **Custom keywords**: edit `VIDEO_TYPE_SIGNATURES` di `topic_chunker.py` untuk tambah/hapus keyword.

## License

MIT
