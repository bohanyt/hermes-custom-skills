# Topic Detection Approaches — Evolution

## v3: Pure LLM Batch Processing (DEPRECATED)
- Split 44 chunks into batches of 12
- LLM reads all chunks in batch and groups them
- **Problem:** LLM context window limits coverage. Many batches fail silently. Only 5-8 topics detected.

## v4: Batch Processing + Retry (DEPRECATED)
- Same as v3 but with 3x retry + exponential backoff
- **Problem:** Still relies on LLM for both grouping AND labeling. Inconsistent results.

## v5: Rule-Based Grouping + LLM Labeling (CURRENT)
- **Step 1:** Compute keyword similarity (Jaccard) between adjacent chunks
- **Step 2:** Group chunks with similarity >= 0.15 OR time gap < 30s
- **Step 3:** Split groups > 300s into sub-groups of ~250s each
- **Step 4:** Call LLM per group for: label, video_type, engagement_score
- **Result:** 22 topics from 44 chunks, 116 min covered
- **Advantage:** LLM only does labeling (fast, reliable), grouping is deterministic

### Keyword Similarity Algorithm
```python
def compute_similarity(summary1, summary2):
    kw1 = extract_keywords(summary1)  # remove stopwords, len > 3
    kw2 = extract_keywords(summary2)
    return len(kw1 & kw2) / len(kw1 | kw2)  # Jaccard
```

### Thresholds
- Similarity >= 0.15 → same topic
- Time gap < 30s → same topic (even if keywords differ)
- Max group duration: 300s (5 min)
- Min group duration: 30s
