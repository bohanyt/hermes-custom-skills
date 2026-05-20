# M365 Copilot Pipeline — Session Reference

## Context

User has:
- **M365 Basic** license from office → access to Copilot (GPT-5.5 Think Deeper)
- **No enterprise API** → must use browser (Edge) to access Copilot
- **Local AI**: Gemma 4 e2b Q6 via LM Studio, 4.5GB VRAM (6GB total, RTX 3050)
- **Small context window** (4K-8K tokens) → can't process large files directly
- **Goal**: Automate the manual copy-paste workflow of sending chunks to Copilot and saving results

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  HERMES DESKTOP                          │
│                                                          │
│  ┌──────────┐    ┌───────────┐    ┌──────────────────┐  │
│  │ Hermes   │───▶│ Browser   │───▶│ Copilot M365     │  │
│  │ (Gemma   │    │ Tools     │    │ (GPT-5.5 Think   │  │
│  │  4 e2b)  │◀───│           │◀───│  Deeper)         │  │
│  └──────────┘    └───────────┘    └──────────────────┘  │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ File System                                       │   │
│  │ ├── chunks/ (50KB each)                          │   │
│  │ ├── results/ (timestamped responses)             │   │
│  │ └── wiki/ (knowledge base per project)           │   │
│  └──────────────────────────────────────────────────┘   │
│       │                                                  │
│       ▼                                                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │ LLM Wiki (Gemma 4 e2b Q6)                        │   │
│  │ → knowledge base per proyek/topik                 │   │
│  │ → output markdown                                 │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Data Flow

### Docx Pipeline
```
Docx (text + gambar)
  → Gemma: extract text + interpret gambar → markdown
  → Split per 50KB
  → Copilot: analisis per chunk (Think Deeper)
  → Save per timestamp (YYYYMMDD_HHMMSS.txt)
  → Optional: compress again via Copilot (<10KB)
  → Feed to LLM Wiki
  → Knowledge base per proyek/topik (markdown)
```

### Transkrip Rapat Pipeline (existing)
```
Livestream/Screenshot → PDF → OCR → TXT (500KB-3MB)
  → Chunk per 50KB
  → Copilot: ringkasan per chunk
  → TamperMonkey scrape → save (20-45KB, deduped)
  → LLM Wiki (source truth per video/rapat)
```

## Role Division

### Hermes (Gemma 4 e2b Q6) — "Project Manager"
- Read file paths
- Loop through chunks
- Send prompts to Copilot via browser
- Save responses to files
- Create timestamped folders
- Feed results to LLM Wiki
- **Does NOT read file contents** (context window too small)

### Copilot M365 (GPT-5.5 Think Deeper) — "Senior Analyst"
- Read 50KB+ file contents
- Analyze, summarize, synthesize
- Interpret images
- Complex reasoning
- **Does NOT access local files** (no API, browser-only)

## Key Decisions

### Why NOT CloakBrowser
- M365 Copilot enterprise has NO bot detection (no Cloudflare, no reCAPTCHA)
- It uses authorization-based access (session validity, device compliance)
- CloakBrowser's custom binary = red flag for IT security
- Zero value, high risk

### Why Playwright + Edge (not Chrome)
- Edge is corporate default on Windows
- M365 Copilot works best in Edge (native integration)
- Session auto-login with corporate account
- No additional install needed

### Why Hermes Desktop (not separate scripts)
- User wants everything in one UI
- No .bat files, no terminal, no separate Python scripts
- Chat-driven: type command, Hermes executes via browser tools
- File viewer built into Hermes Desktop

### Why TamperMonkey is replaceable
- Playwright's `inner_text()` and `browser_snapshot` can scrape any page content
- No need for separate browser extension
- More reliable (no extension update breaks)

## Context Window Mitigation

| Task | Needs large context? | Who handles |
|------|---------------------|-------------|
| Read file paths | No | Gemma ✅ |
| Loop chunks | No | Gemma ✅ |
| Send prompt to Copilot | No | Gemma ✅ |
| Save response to file | No | Gemma ✅ |
| Feed to LLM Wiki | No | Gemma ✅ |
| **Read 50KB file** | **Yes** | **Copilot ✅** |
| **Analyze long document** | **Yes** | **Copilot ✅** |
| **Interpret images** | **Yes** | **Copilot ✅** |

## Folder Structure

```
copilot-pipeline/
├── input/              # Raw files (docx, txt, pdf)
├── markdown/           # After docx → markdown
├── chunks/             # Split per 50KB
│   ├── chunk_001.txt
│   └── ...
├── results/            # Copilot responses (timestamped)
│   ├── 20260515_143022.txt
│   └── ...
├── wiki/               # LLM Wiki — knowledge base
│   ├── proyek-a/
│   │   ├── overview.md
│   │   ├── keputusan.md
│   │   └── action-items.md
│   └── proyek-b/
├── copilot-session/    # Browser session (auto-generated)
└── pipeline.log
```

## M365 Copilot UI Selectors (need inspection)

These need to be determined by inspecting the actual Copilot UI:
- Model selector dropdown
- Textarea input
- File upload button/input
- Response area
- Send button

## Rate Limiting Guidelines
- 30-60 second delays between requests
- Sequential processing (no parallel)
- On 429: wait 60s and retry
- Don't run concurrent sessions on same account

## Next Steps (as of 2026-05-15)
1. Confirm Hermes Desktop installed + Gemma 4 e2b Q6 configured
2. Inspect Copilot M365 UI for selectors
3. Determine default prompt template
4. Setup folder structure
5. Test run with single chunk
6. Scale to full pipeline
