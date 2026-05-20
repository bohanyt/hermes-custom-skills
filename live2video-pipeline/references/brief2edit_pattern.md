# brief2edit.py — Regex Fallback Extraction

## Purpose
Convert `production_brief.json` → `edit_plan.json` for technician.py.
Uses regex fallback when LLM response JSON is malformed.

## Problem
The Orchestrator saves LLM responses as `raw_response` string. This string often contains:
- Escaped quotes inside JSON values (`\"`)
- Truncated output
- Markdown code fences (```json ... ```)

Standard `json.loads()` fails on these.

## Solution
Use regex to extract key fields directly from the raw string:

```python
import re

starts = re.findall(r'"start_time":\s*"([^"]+)"', raw)
ends = re.findall(r'"end_time":\s*"([^"]+)"', raw)
juduls = re.findall(r'"judul_saran":\s*"([^"]+)"', raw)
hooks = re.findall(r'"hook":\s*"([^"]+)"', raw)
jeniss = re.findall(r'"jenis":\s*"([^"]+)"', raw)
vibes = re.findall(r'"vibe":\s*"([^"]+)"', raw)
```

## Full Script
See `hermes_skills/brief2edit.py` for the complete conversion script.

## Output Format
```json
{
  "video_title": "...",
  "detected_niche": "gacha_game",
  "bagian_dipertahankan": [
    {
      "timestamp": "00:00:01 - 00:10:16",
      "konten_id": 1,
      "jenis": "Raw Clip - Reaction",
      "judul": "...",
      "hook": "...",
      "vibe": "...",
      "alasan": ""
    }
  ]
}
```
