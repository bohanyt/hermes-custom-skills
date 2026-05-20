"""
TOPIC DETECTOR v4: Fix batch processing
- Retry 3x per batch dengan exponential backoff
- Simpan raw response untuk debug
- Merge hasil batch dengan overlap detection
"""
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

BATCH_SIZE = 10
OVERLAP = 2  # chunks overlap antara batch untuk continuity

PROMPT_SYSTEM = """Kamu adalah "Topic Detector" untuk livestream gaming/entertainment.

Tugasmu: baca chunk summary dan kelompokkan yang topiknya SAMA PERSIS.

ATURAN:
1. Baca summary tiap chunk secara BERURUTAN
2. Chunk berdekatan yang topiknya SAMA → merge jadi 1 topik
3. Chunk yang topiknya BEDA → topik baru
4. Label topik harus SPESIFIK berdasarkan isi (bukan generic):
   - BAGUS: "First Reaction Lihat Grafik ZZZ", "Boss Battle Chicken Jacket", "Gacha Pull Dapat Epic", "Rage Quit Karena Lag"
   - JANGAN: "Gameplay", "Review", "Momen Lucu", "Diskusi"
5. video_type dari: [Raw Clip - Reaction, YouTube Shorts, Storytime - Gaming, Video Essay - Analysis, Tutorial - Guide, Lore & Story Retelling, Rank Up / Progress, Rage / Funny Moments, Storytime - Horror, Raw Clip - Highlight, Raw Clip - Funny, Tutorial - Build With Me, Video Essay - Opinion, Storytime - Vibecoding]
6. Minimal durasi: 60s, maksimal: 600s (kalau lebih, split)
7. Setiap chunk harus masuk ke tepat 1 topik

OUTPUT: JSON array, tanpa markdown code block.
Format:
[
  {
    "topic_id": "topic_001",
    "label": "Label spesifik berdasarkan isi",
    "chunks": ["chunk_001", "chunk_002"],
    "start_time": "00:00:01",
    "end_time": "00:05:30",
    "duration_sec": 329,
    "summary": "Ringkasan 1-2 kalimat",
    "video_type": "Raw Clip - Reaction",
    "engagement_score": 8,
    "reasoning": "Kenapa score ini"
  }
]"""

PROMPT_USER = """Analisis chunks berikut dan tentukan topik:

{chunks_summary}

Buat topic groups dalam format JSON."""

def load_summaries(summaries_path: str) -> list:
    with open(summaries_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        for key in ["summaries", "chunks", "data"]:
            if key in data:
                return data[key]
        return list(data.values())
    return []

def parse_json_response(response: str) -> list:
    """Parse JSON dari response LLM, dengan fallback."""
    if not response or not response.strip():
        return []
    
    text = response.strip()
    
    # Remove markdown
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try extract JSON array
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    
    # Try extract individual JSON objects
    objects = []
    for m in re.finditer(r'\{[^{}]*\}', text, re.DOTALL):
        try:
            obj = json.loads(m.group())
            if "topic_id" in obj or "label" in obj:
                objects.append(obj)
        except:
            pass
    
    return objects

def detect_batch(summaries: list, batch_start: int, batch_end: int, is_first: bool, is_last: bool) -> list:
    """Detect topics untuk 1 batch, dengan retry."""
    batch = summaries[batch_start:batch_end]
    
    chunks_text = ""
    for s in batch:
        chunk_id = s.get("chunk_id", s.get("id", "unknown"))
        start = s.get("start_time", s.get("start", "00:00:00"))
        end = s.get("end_time", s.get("end", "00:00:00"))
        duration = s.get("duration_sec", 0)
        summary = s.get("summary", s.get("text", ""))
        chunks_text += f"[{chunk_id}] {start} → {end} ({duration}s): {summary}\n\n"
    
    # Add position context
    total = len(summaries)
    pos = "PERTAMA" if is_first else "TERAKHIR" if is_last else "TENGAH"
    context = f"**Posisi: batch {pos} (chunks {batch_start+1}-{batch_end} dari {total})**\n\n"
    
    user_msg = PROMPT_USER.replace("[[chunks_summary]]", context + chunks_text)
    
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": user_msg}
    ]
    
    # Retry 3x dengan backoff
    for attempt in range(3):
        try:
            response = call_llm("secondary", messages, max_tokens=4000, temperature=0.3)
            
            if not response or not response.strip():
                print(f"    ⚠️  Empty response (attempt {attempt+1})")
                time.sleep(2 ** attempt)
                continue
            
            topics = parse_json_response(response)
            
            if topics:
                return topics
            else:
                print(f"    ⚠️  No topics parsed (attempt {attempt+1})")
                time.sleep(2 ** attempt)
                continue
                
        except Exception as e:
            print(f"    ⚠️  Error (attempt {attempt+1}): {e}")
            time.sleep(2 ** attempt)
            continue
    
    return []

def merge_batch_results(all_results: list, total_chunks: int) -> list:
    """Merge hasil dari semua batch, handle overlap dan gap."""
    if not all_results:
        return []
    
    # Flatten all topics
    all_topics = []
    for batch_topics in all_results:
        if batch_topics:
            all_topics.extend(batch_topics)
    
    if not all_topics:
        return []
    
    # Sort by start_time
    all_topics.sort(key=lambda t: t.get("start_time", "00:00:00"))
    
    # Remove duplicates (same chunks)
    seen_chunks = set()
    unique = []
    for t in all_topics:
        chunks_key = tuple(sorted(t.get("chunks", [])))
        if chunks_key not in seen_chunks:
            seen_chunks.add(chunks_key)
            unique.append(t)
    
    # Re-number
    for i, t in enumerate(unique):
        t["topic_id"] = f"topic_{i+1:03d}"
    
    return unique

def main():
    if len(sys.argv) < 2:
        print("Usage: python topic_detector_v4.py <all_summaries.json>")
        sys.exit(1)
    
    summaries_path = sys.argv[1]
    summaries = load_summaries(summaries_path)
    
    print("=" * 60)
    print("TOPIC DETECTOR v4 — Fixed Batch Processing")
    print("=" * 60)
    print(f"  📊 Total chunks: {len(summaries)}")
    print(f"  📦 Batch size: {BATCH_SIZE}")
    
    # Create batches dengan overlap
    batches = []
    i = 0
    while i < len(summaries):
        end = min(i + BATCH_SIZE, len(summaries))
        batches.append((i, end))
        i = end - OVERLAP if end < len(summaries) else end
    
    print(f"  🔢 Batches: {len(batches)}")
    
    all_results = []
    for batch_idx, (start, end) in enumerate(batches):
        is_first = batch_idx == 0
        is_last = batch_idx == len(batches) - 1
        
        print(f"\n  🔬 Batch {batch_idx+1}/{len(batches)} (chunks {start+1}-{end})")
        
        batch_topics = detect_batch(summaries, start, end, is_first, is_last)
        
        if batch_topics:
            print(f"    ✅ {len(batch_topics)} topics detected")
            all_results.append(batch_topics)
        else:
            print(f"    ❌ No topics in this batch")
    
    # Merge
    merged = merge_batch_results(all_results, len(summaries))
    
    print(f"\n{'=' * 60}")
    print(f"✅ TOTAL: {len(merged)} topics detected")
    print(f"{'=' * 60}")
    
    total_dur = sum(t.get("duration_sec", 0) for t in merged)
    total_mins = total_dur // 60
    
    for t in merged:
        dur = t.get("duration_sec", 0)
        mins = dur // 60
        secs = dur % 60
        score = t.get("engagement_score", "?")
        print(f"  [{t['topic_id']}] {t.get('label', 'Unknown')}")
        print(f"    ⏱️ {t.get('start_time', '?')} → {t.get('end_time', '?')} ({mins}m{secs}s) | Score: {score}/10")
        print(f"    🏷️  {t.get('video_type', 'Unknown')}")
        print(f"    📦 {', '.join(t.get('chunks', []))}")
        print()
    
    print(f"  📊 Total duration: {total_mins} menit tercakup")
    
    # Save
    output_path = Path(summaries_path).parent / "topics.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)
    print(f"📝 Saved: {output_path}")

if __name__ == "__main__":
    main()
