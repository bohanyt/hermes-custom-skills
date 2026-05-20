"""
TOPIC DETECTOR v3: Batch processing untuk chunk banyak
Split chunks jadi batch, detect topics per batch, merge hasilnya.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

BATCH_SIZE = 12  # chunks per LLM call

PROMPT_SYSTEM = """Kamu adalah "Topic Detector" untuk livestream gaming/entertainment.

Tugasmu: baca chunk summary dan kelompokkan yang topiknya SAMA.

ATURAN:
1. Baca summary tiap chunk secara BERURUTAN
2. Kelompokkan chunk berdekatan yang membahas TOPIK YANG SAMA
3. Label topik harus SPESIFIK dan DESKRIPTIF
   - BAGUS: "First Reaction ZZZ Grafik Bikin Kaget", "Boss Battle Chicken Jacket"
   - JANGAN: "Gameplay", "Review", "Momen Lucu"
4. video_type pilih dari: [Raw Clip - Reaction, YouTube Shorts, Storytime - Gaming, Video Essay - Analysis, Tutorial - Guide, Lore & Story Retelling, Rank Up / Progress, Rage / Funny Moments, Storytime - Horror, Raw Clip - Highlight, Raw Clip - Funny, Tutorial - Build With Me, Video Essay - Opinion, Storytime - Vibecoding, Raw Clip - Reaction]
5. JANGAN terlalu agresif merge — lebih baik banyak topik kecil
6. Minimal durasi per topik: 60 detik, maksimal: 600 detik

OUTPUT FORMAT (JSON array):
[
  {
    "topic_id": "topic_001",
    "label": "Label spesifik",
    "chunks": ["chunk_001", "chunk_002"],
    "start_time": "00:00:01",
    "end_time": "00:05:30",
    "duration_sec": 329,
    "summary": "Ringkasan 1-2 kalimat",
    "video_type": "Raw Clip - Reaction",
    "engagement_score": 8,
    "reasoning": "Kenapa score ini"
  }
]

PENTING: Output HARUS JSON valid, tanpa markdown. engagement_score 1-10."""

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

def detect_topics_batch(summaries: list, batch_start: int, batch_end: int) -> list:
    """Detect topics untuk batch chunks."""
    batch = summaries[batch_start:batch_end]
    
    chunks_text = ""
    for s in batch:
        chunk_id = s.get("chunk_id", s.get("id", "unknown"))
        start = s.get("start_time", s.get("start", "00:00:00"))
        end = s.get("end_time", s.get("end", "00:00:00"))
        duration = s.get("duration_sec", 0)
        summary = s.get("summary", s.get("text", ""))
        chunks_text += f"[{chunk_id}] {start} → {end} ({duration}s): {summary}\n\n"
    
    # Add context from previous batch (last 2 chunks)
    if batch_start > 0:
        prev = summaries[max(0, batch_start-2):batch_start]
        chunks_text = "**Previous context:**\n" + "\n".join(
            f"[{s.get('chunk_id', '?')}]: {s.get('summary', '')[:100]}"
            for s in prev
        ) + "\n\n**Current batch:**\n" + chunks_text
    
    user_msg = PROMPT_USER.replace("[[chunks_summary]]", chunks_text)
    
    messages = [
        {"role": "system", "content": PROMPT_SYSTEM},
        {"role": "user", "content": user_msg}
    ]
    
    for attempt in range(3):
        try:
            response = call_llm("secondary", messages, max_tokens=4000, temperature=0.3)
            
            if not response or not response.strip():
                print(f"    ⚠️  Empty response (attempt {attempt+1})")
                continue
            
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            if response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            response_clean = response_clean.strip()
            
            topics = json.loads(response_clean)
            return topics
        except json.JSONDecodeError as e:
            print(f"    ⚠️  JSON parse error (attempt {attempt+1}): {e}")
            print(f"    Raw: {response[:200]}")
            continue
        except Exception as e:
            print(f"    ⚠️  Error (attempt {attempt+1}): {e}")
            continue
    
    return []

def merge_topics(all_topics: list) -> list:
    """Merge topics dari semua batch, fix overlap."""
    if not all_topics:
        return []
    
    # Sort by start_time
    all_topics.sort(key=lambda t: t.get("start_time", "00:00:00"))
    
    # Re-number
    for i, t in enumerate(all_topics):
        t["topic_id"] = f"topic_{i+1:03d}"
    
    return all_topics

def main():
    if len(sys.argv) < 2:
        print("Usage: python topic_detector_v3.py <all_summaries.json>")
        sys.exit(1)
    
    summaries_path = sys.argv[1]
    summaries = load_summaries(summaries_path)
    
    print("=" * 60)
    print("TOPIC DETECTOR v3 — Batch Processing")
    print("=" * 60)
    print(f"  📊 Total chunks: {len(summaries)}")
    print(f"  📦 Batch size: {BATCH_SIZE}")
    print(f"  🔢 Batches: {(len(summaries) + BATCH_SIZE - 1) // BATCH_SIZE}")
    
    all_topics = []
    num_batches = (len(summaries) + BATCH_SIZE - 1) // BATCH_SIZE
    
    for i in range(num_batches):
        start = i * BATCH_SIZE
        end = min(start + BATCH_SIZE, len(summaries))
        print(f"\n  🔬 Batch {i+1}/{num_batches} (chunks {start+1}-{end})")
        
        batch_topics = detect_topics_batch(summaries, start, end)
        
        if batch_topics:
            print(f"    ✅ {len(batch_topics)} topics detected")
            all_topics.extend(batch_topics)
        else:
            print(f"    ⚠️  No topics in this batch")
    
    # Merge
    merged = merge_topics(all_topics)
    
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
