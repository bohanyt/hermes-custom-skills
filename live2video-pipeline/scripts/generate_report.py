"""
REPORT GENERATOR: Generate HTML report dari semua JSON output
"""
import json
import sys
from pathlib import Path

def generate_report(base_dir: str):
    base = Path(base_dir)
    
    # Load all data
    topics = []
    stories = []
    clips = []
    metadata = {}
    
    topics_file = base / "topics.json"
    stories_file = base / "stories.json"
    render_log_file = base.parent / "final_cuts" / "topics" / "render_log.json"
    metadata_file = base.parent / "metadata.json"
    
    if topics_file.exists():
        with open(topics_file, "r", encoding="utf-8") as f:
            topics = json.load(f)
    
    if stories_file.exists():
        with open(stories_file, "r", encoding="utf-8") as f:
            stories = json.load(f)
    
    if render_log_file.exists():
        with open(render_log_file, "r", encoding="utf-8") as f:
            clips_data = json.load(f)
            clips = clips_data.get("clips", [])
    
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    
    # Build topics HTML
    topics_html = ""
    for t in topics:
        score = t.get("engagement_score", 5)
        score_class = "score-high" if score >= 7 else "score-mid" if score >= 4 else "score-low"
        video_type = t.get("video_type", "Unknown")
        type_class = "raw-clip" if "Reaction" in video_type or "Highlight" in video_type or "Funny" in video_type else "shorts" if "Shorts" in video_type else "storytime" if "Storytime" in video_type or "Story" in video_type else "tutorial" if "Tutorial" in video_type or "Guide" in video_type else "essay" if "Essay" in video_type else "raw-clip"
        
        dur = t.get("duration_sec", 0)
        mins = dur // 60
        secs = dur % 60
        
        # Find matching story
        story = next((s for s in stories if s.get("topic_id") == t.get("topic_id")), None)
        
        topics_html += f"""
<div class="topic-card">
  <span class="topic-label">{t.get('topic_id', '?')}</span>
  <span class="topic-type {type_class}">{video_type}</span>
  <span class="topic-score {score_class}">Score: {score}/10</span>
  <div class="topic-title">{t.get('label', 'Unknown')}</div>
  <div class="topic-meta">⏱️ {t.get('start_time', '?')} → {t.get('end_time', '?')} ({mins}m{secs}s) | 📦 {', '.join(t.get('chunks', []))}</div>
  <div class="topic-summary">{t.get('summary', '')}</div>
  {"<div class='hook'><strong>Hook:</strong> " + story.get('hook', '') + "</div>" if story and story.get('hook') else ""}
  {"<div class='topic-summary'><strong>Title:</strong> " + story.get('title', '') + "</div>" if story and story.get('title') else ""}
</div>"""
    
    # Build clips HTML
    clips_html = ""
    for c in clips:
        dur_min = c.get("duration_sec", 0) // 60
        dur_sec = c.get("duration_sec", 0) % 60
        score = c.get("engagement_score", 5)
        score_class = "score-high" if score >= 7 else "score-mid" if score >= 4 else "score-low"
        
        clips_html += f"""
<div class="topic-card">
  <span class="topic-label">{c.get('label', '?')}</span>
  <span class="topic-score {score_class}">Score: {score}/10</span>
  <div class="topic-title">{c.get('topic_label', 'Unknown')}</div>
  <div class="topic-meta">📄 {c.get('file', '')} ({c.get('size_mb', 0)} MB) | ⏱️ {c.get('start', '')} → {c.get('end', '')} ({dur_min}m{dur_sec}s)</div>
  <div class="topic-meta">🏷️ {c.get('video_type', 'Unknown')}</div>
</div>"""
    
    # Build stories HTML
    stories_html = ""
    for s in stories:
        if s.get("status") != "ok":
            continue
        
        narasi = s.get("narasi", {})
        full_script = s.get("full_script", "")
        cta = s.get("cta", "")
        
        stories_html += f"""
<div class="topic-card">
  <div class="topic-title">{s.get('title', 'Unknown')}</div>
  <div class="topic-meta">📌 {s.get('topic_id', '')} | 🏷️ {s.get('video_type', '')}</div>
  
  <div class="hook"><strong>Hook:</strong> {s.get('hook', '')}</div>
  
  <h3>5C Storytelling</h3>
  <div class="card">
    <p><strong>Character:</strong> {narasi.get('character', '')}</p>
    <p><strong>Context:</strong> {narasi.get('context', '')}</p>
    <p><strong>Conflict:</strong> {narasi.get('conflict', '')}</p>
    <p><strong>Climax:</strong> {narasi.get('climax', '')}</p>
    <p><strong>Closure:</strong> {narasi.get('closure', '')}</p>
  </div>
  
  <h3>Full Script</h3>
  <div class="script">{full_script}</div>
  
  <div class="quote"><strong>CTA:</strong> {cta}</div>
  <div class="topic-meta"><strong>Thumbnail:</strong> {s.get('thumbnail_text', '')}</div>
</div>"""
    
    # Load template
    template_path = Path(__file__).parent / "report_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # Fill template
    html = template.replace("[[video_title]]", metadata.get("title", "Unknown"))
    html = html.replace("[[channel]]", metadata.get("channel", "Unknown"))
    html = html.replace("[[duration]]", metadata.get("duration", "Unknown"))
    html = html.replace("[[processed_at]]", metadata.get("processed_at", "Unknown"))
    html = html.replace("[[niche]]", metadata.get("detected_niche", "Unknown"))
    html = html.replace("[[total_chunks]]", str(len(topics)))
    html = html.replace("[[total_topics]]", str(len(topics)))
    html = html.replace("[[total_clips]]", str(len(clips)))
    html = html.replace("[[total_quotes]]", str(len([q for s in stories for q in s.get("quotes", [])])))
    html = html.replace("[[total_stories]]", str(len([s for s in stories if s.get("status") == "ok"])))
    html = html.replace("[[topics_html]]", topics_html)
    html = html.replace("[[clips_html]]", clips_html)
    html = html.replace("[[stories_html]]", stories_html)
    
    # Save
    output_path = base.parent / "final_cuts" / "topics" / "report.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ Report saved: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_report.py <chunks_merged_dir>")
        sys.exit(1)
    generate_report(sys.argv[1])
