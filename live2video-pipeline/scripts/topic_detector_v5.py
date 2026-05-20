"""
TOPIC DETECTOR v5: Rule-based + LLM fallback
1. Group chunks berdasarkan keyword overlap (rule-based)
2. LLM hanya untuk label + video_type + score
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from config_api import call_llm

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

def extract_keywords(text: str) -> set:
    """Extract keywords dari text."""
    # Remove common words
    stopwords = {"dan", "atau", "yang", "di", "ke", "dari", "ini", "itu", "dengan", "untuk", "pada", "juga", "sudah", "belum", "bisa", "akan", "sedang", "saja", "karena", "tetapi", "namun", "saya", "kita", "mereka", "dia", "aku", "kamu", "gue", "lu", "nya", "ya", "ga", "nggak", "tidak", "ada", "tidak", "sangat", "banget", "sekali", "lagi", "masih", "sudah", "baru", "lama", "banyak", "sedikit", "besar", "kecil", "baik", "buruk", "bagus", "jelek", "mantap", "keren", "gila", "wow", "wah", "hai", "halo", "hi", "yo", "oke", "ok", "thanks", "makasih", "sorry", "maaf"}
    
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    keywords = {w for w in words if w not in stopwords and len(w) > 3}
    return keywords

def compute_similarity(summary1: str, summary2: str) -> float:
    """Compute similarity antara 2 summaries."""
    kw1 = extract_keywords(summary1)
    kw2 = extract_keywords(summary2)
    
    if not kw1 or not kw2:
        return 0.0
    
    intersection = kw1 & kw2
    union = kw1 | kw2
    
    return len(intersection) / len(union)

def group_chunks_by_topic(summaries: list, similarity_threshold: float = 0.15) -> list:
    """Group chunks berdasarkan similarity."""
    if not summaries:
        return []
    
    groups = []
    current_group = [summaries[0]]
    
    for i in range(1, len(summaries)):
        prev_summary = current_group[-1].get("summary", "")
        curr_summary = summaries[i].get("summary", "")
        
        similarity = compute_similarity(prev_summary, curr_summary)
        
        # Also check time gap
        prev_end = current_group[-1].get("end_time", "00:00:00")
        curr_start = summaries[i].get("start_time", "00:00:00")
        
        # Parse timestamps
        def ts_to_sec(ts):
            parts = ts.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            return 0
        
        time_gap = ts_to_sec(curr_start) - ts_to_sec(prev_end)
        
        # Merge if similar OR time gap < 30s
        if similarity >= similarity_threshold or time_gap < 30:
            current_group.append(summaries[i])
        else:
            groups.append(current_group)
            current_group = [summaries[i]]
    
    groups.append(current_group)
    return groups

def label_topic_with_llm(group: list) -> dict:
    """Pakai LLM untuk label, video_type, score."""
    chunks_text = ""
    for s in group:
        chunk_id = s.get("chunk_id", "?")
        start = s.get("start_time", "?")
        end = s.get("end_time", "?")
        summary = s.get("summary", "")
        chunks_text += f"[{chunk_id}] {start} → {end}: {summary}\n\n"
    
    first = group[0]
    last = group[-1]
    
    prompt = f"""Berikan label, video_type, dan engagement_score untuk grup chunk berikut:

{chunks_text}

Output JSON:
{{
  "label": "Label spesifik berdasarkan isi (contoh: 'First Reaction Lihat Grafik ZZZ', 'Boss Battle Chicken Jacket')",
  "video_type": "Pilih dari: Raw Clip - Reaction, YouTube Shorts, Storytime - Gaming, Video Essay - Analysis, Tutorial - Guide, Lore & Story Retelling, Rank Up / Progress, Rage / Funny Moments, Storytime - Horror, Raw Clip - Highlight, Raw Clip - Funny, Tutorial - Build With Me, Video Essay - Opinion, Storytime - Vibecoding",
  "engagement_score": 1-10,
  "summary": "Ringkasan 1-2 kalimat"
}}

Hanya output JSON, tanpa teks lain."""
    
    messages = [
        {"role": "system", "content": "Kamu adalah Topic Labeler. Output HARUS JSON valid."},
        {"role": "user", "content": prompt}
    ]
    
    for attempt in range(3):
        try:
            response = call_llm("secondary", messages, max_tokens=1000, temperature=0.3)
            
            if not response or not response.strip():
                continue
            
            text = response.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
            
            result = json.loads(text)
            
            return {
                "label": result.get("label", f"Topic {first.get('chunk_id', '?')}"),
                "video_type": result.get("video_type", "Raw Clip - Reaction"),
                "engagement_score": result.get("engagement_score", 5),
                "summary": result.get("summary", " ".join(s.get("summary", "")[:100] for s in group)),
            }
        except Exception as e:
            continue
    
    # Fallback
    return {
        "label": f"Topic {first.get('chunk_id', '?')}",
        "video_type": "Raw Clip - Reaction",
        "engagement_score": 5,
        "summary": " ".join(s.get("summary", "")[:100] for s in group),
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python topic_detector_v5.py <all_summaries.json>")
        sys.exit(1)
    
    summaries_path = sys.argv[1]
    summaries = load_summaries(summaries_path)
    
    print("=" * 60)
    print("TOPIC DETECTOR v5 — Rule-based + LLM Label")
    print("=" * 60)
    print(f"  📊 Total chunks: {len(summaries)}")
    
    # Step 1: Group chunks by similarity
    print(f"\n  🔬 Grouping chunks by similarity...")
    groups = group_chunks_by_topic(summaries)
    print(f"  ✅ {len(groups)} groups formed")
    
    # Step 2: Label each group with LLM
    print(f"\n  🏷️  Labeling groups with LLM...")
    topics = []
    
    for i, group in enumerate(groups):
        first = group[0]
        last = group[-1]
        
        start = first.get("start_time", "00:00:00")
        end = last.get("end_time", "00:00:00")
        
        # Parse timestamps for duration
        def ts_to_sec(ts):
            parts = ts.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
            return 0
        
        duration = ts_to_sec(end) - ts_to_sec(start)
        
        # Skip if too short (< 30s)
        if duration < 30:
            continue
        
        # Split if too long (> 300s = 5 menit)
        if duration > 300:
            # Split into chunks of ~250s each
            sub_groups = []
            current = []
            current_dur = 0
            for s in group:
                s_dur = s.get("duration_sec", 150)
                current.append(s)
                current_dur += s_dur
                if current_dur >= 250:
                    sub_groups.append(current)
                    current = []
                    current_dur = 0
            if current:
                sub_groups.append(current)
        else:
            sub_groups = [group]
        
        for sg in sub_groups:
            if not sg:
                continue
            
            sg_first = sg[0]
            sg_last = sg[-1]
            sg_start = sg_first.get("start_time", "00:00:00")
            sg_end = sg_last.get("end_time", "00:00:00")
            sg_duration = ts_to_sec(sg_end) - ts_to_sec(sg_start)
            
            if sg_duration < 30:
                continue
            
            print(f"    [{i+1}/{len(groups)}] Labeling {sg_first.get('chunk_id', '?')} - {sg_last.get('chunk_id', '?')} ({sg_duration}s)...")
            
            label = label_topic_with_llm(sg)
            
            topic = {
                "topic_id": f"topic_{len(topics)+1:03d}",
                "label": label["label"],
                "chunks": [s.get("chunk_id", "?") for s in sg],
                "start_time": sg_start,
                "end_time": sg_end,
                "duration_sec": int(sg_duration),
                "summary": label["summary"],
                "video_type": label["video_type"],
                "engagement_score": label["engagement_score"],
            }
            topics.append(topic)
            print(f"      ✅ {label['label'][:50]}")
    
    print(f"\n{'=' * 60}")
    print(f"✅ TOTAL: {len(topics)} topics detected")
    print(f"{'=' * 60}")
    
    total_dur = sum(t.get("duration_sec", 0) for t in topics)
    total_mins = total_dur // 60
    
    for t in topics:
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
        json.dump(topics, f, ensure_ascii=False, indent=2)
    print(f"📝 Saved: {output_path}")

if __name__ == "__main__":
    main()
