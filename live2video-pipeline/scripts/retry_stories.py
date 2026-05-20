"""Retry failed stories"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from storyteller_v4 import create_story, load_trend_research

topics_path = r"C:\Users\MSI Thin 15\Documents\hermes_live2video\testing\v1.2_tes1\work\chunks\topics.json"
stories_path = r"C:\Users\MSI Thin 15\Documents\hermes_live2video\testing\v1.2_tes1\work\chunks\stories.json"
trend_path = r"C:\Users\MSI Thin 15\Documents\hermes_live2video\testing\v1.2_tes1\work\chunks\trend_research.json"

with open(topics_path, "r", encoding="utf-8") as f:
    topics = json.load(f)
with open(stories_path, "r", encoding="utf-8") as f:
    stories = json.load(f)
trend = load_trend_research(trend_path)

# Find failed stories
failed = [s for s in stories if s.get("status") != "ok"]
print(f"Failed stories: {len(failed)}")

for i, story in enumerate(failed):
    topic_id = story.get("topic_id", "")
    topic = next((t for t in topics if t.get("topic_id") == topic_id), None)
    if not topic:
        continue
    
    print(f"\n[{i+1}/{len(failed)}] Retrying {topic.get('label', '')}...")
    
    vt = topic.get("video_type", "")
    type_trend = trend.get(vt, {})
    
    new_story = create_story(topic, type_trend)
    
    # Replace in stories list
    for j, s in enumerate(stories):
        if s.get("topic_id") == topic_id:
            stories[j] = new_story
            break
    
    if new_story.get("status") == "ok":
        print(f"  ✅ {new_story.get('title', '')[:50]}")
    else:
        print(f"  ❌ {new_story.get('status')}")

# Save
with open(stories_path, "w", encoding="utf-8") as f:
    json.dump(stories, f, ensure_ascii=False, indent=2)

ok = sum(1 for s in stories if s.get("status") == "ok")
print(f"\n✅ Total: {ok}/{len(stories)} stories OK")
