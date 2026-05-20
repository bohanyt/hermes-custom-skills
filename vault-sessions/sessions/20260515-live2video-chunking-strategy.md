---
title: Live2Video Pipeline — Chunking Strategy & HTML Guide Review
date: 2026-05-15
sessions: [session_20260515_050241_238bd6, session_20260515_052451_439848]
platform: tui
model: openrouter/owl-alpha
total_messages: ~572 (combined)
tags: [live2video, pipeline, chunking, html-guide, review]
---

# Live2Video Pipeline — Chunking Strategy & HTML Guide Review

**Date:** 2026-05-15 | **Platform:** TUI | **Combined messages:** ~572

## What Happened

User reviewed the HTML pipeline guide and noticed the output was just video chunks without narration. Discussed chunking strategy — chunks were too large (10 min, 35 min, 1 hr 45 min). Decided to implement proper chunking with smaller, fixed-duration segments.

## Key Topics

### Pipeline Output Review
- HTML guide output was just video chunks without narration
- Need to integrate narrative scripts with video chunks
- HTML guide needs improvement for better documentation

### Chunking Strategy
- **Problem:** Chunks were too large (10 min, 35 min, 1 hr 45 min)
- **Solution:** Implement fixed-duration chunking (2.5 min target)
- **Smart cut points:** Cut at silence gaps (>1.5s) near target boundary
- **Fallback:** Closest segment to target time if no silence gap

### Narration Integration
- Each chunk needs a narrative script
- 5C storytelling framework (Character, Context, Conflict, Climax, Closure)
- Scripts should be conversational Indonesian

## Related

- [[live2video-pipeline]] — Full pipeline architecture
- [[live2video-detailed]] — Detailed technical knowledge
- [[20260516-17-live2video-pipeline-v1.2]] — Next day development
