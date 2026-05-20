# 5C Storytelling Framework for Live2Video

## v1.3 Update: 5C Applies to ENTIRE Video, Not Per-Clip

**CRITICAL ARCHITECTURAL CHANGE (2026-05-18):**

In v1.2, 5C was applied per topic/clip (22 topics → 22 separate 5C scripts). This produced repetitive, shallow scripts. The correct approach:

**One livestream → ONE 10-15 min video → ONE 5C arc spanning the entire video.**

Topics become scenes within the arc, not standalone videos. Each act pulls clips from different parts of the livestream:

| Act | Role | Source Topics | Duration |
|-----|------|---------------|----------|
| Context | Setup, first reactions | Early stream (topics 1-3) | 0-2 min |
| Character | World-building, lore, discovery | Early-middle stream (topics 4-8) | 2-4.5 min |
| Conflict | Boss battles, struggles | Middle stream (topics 9-14) | 4.5-7 min |
| Choice | Exploration, decisions | Middle-late stream (topics 15-18) | 7-10 min |
| Consequence | Rewards, resolution | Late stream (topics 19-22) | 10-12 min |

Write ONE continuous `full_script` (500-800 words, conversational Indonesian) that flows naturally across all acts. The script should feel like one YouTuber narration, not separate mini-scripts.

## Overview
Every narrative script produced by `storyteller_v2.py` must follow the 5C framework. This is NOT optional — it's the core output format the user expects.

## The 5C's

### 1. Character
- **Who** is the protagonist? (usually the streamer)
- **What** do they feel? (excitement, frustration, surprise, fear)
- **Why** should the viewer care about them?

Example: "Bohan, streamer yang udah lama gak main game anime, akhirnya coba ZZZ — dan langsung speechless."

### 2. Context
- **What** is happening? (the situation/setup)
- **Why** is this interesting/relevant now?
- **Where** does this fit in the stream?

Example: "Ini pertama kali Bohan main Zenless Zone Zero, game baru dari HoYoverse yang lagi rame banget."

### 3. Conflict
- **What** problem/challenge do they face?
- **What** is at stake?
- **Why** is this tense or uncertain?

Example: "Grafiknya terlalu bagus sampai dia gak bisa fokus main. Terus ada boss yang bikin dia mati-matian."

### 4. Climax
- **What** is the peak moment?
- **What** makes viewers say "WOW"?
- **What** is the most memorable/emotional moment?

Example: "Pas bossnya ngeluarin animasi domain expansion ala JJK, Bohan langsung teriak 'GILA!'"

### 5. Closure
- **What** is the conclusion/lesson?
- **What** happens next?
- **What** should the viewer take away?

Example: "Setelah 2 jam main, Bohan bilang ini game terbaik yang pernah dia coba tahun ini."

## Output Format

The `full_script` field must be:
- **Conversational** — like a YouTuber talking to camera, NOT formal writing
- **Natural flow** — the 5C sections should blend together, NOT feel like a checklist
- **150-300 words** total
- **Indonesian** — casual Indonesian with occasional English gaming terms
- **NO editing notes** — no sound effects, zoom instructions, transition notes, or thumbnail tips

## Video Type → 5C Mapping

| Video Type | Character Focus | Conflict Focus | Climax Focus |
|------------|----------------|----------------|--------------|
| Raw Clip - Reaction | Streamer's emotional state | Surprise/shock moment | Peak reaction |
| Raw Clip - Highlight | Player skill | Difficult challenge | Epic play |
| Raw Clip - Funny | Streamer's personality | Fail/mistake | Funniest moment |
| YouTube Shorts | Quick intro | Hook in 3 seconds | Punchline/moment |
| Storytime - Gaming | Personal experience | Journey/struggle | Key realization |
| Tutorial - Build With Me | Player's goal | Build challenge | Final result |
| Video Essay - Opinion | Author's perspective | Debate/argument | Strongest point |
