# Default Skills — Archive vs Keep vs Pin
# Generated: 2026-05-20
# Based on: user setup (Windows, no Mac, no Minecraft, no Spotify, etc.)

## Legend
- 🗑️ ARCHIVE = nggak perlu, bisa dihapus dari skills folder
- ✅ KEEP = useful, keep as on-demand skill
- 📌 PIN = harusnya always on (inject ke system prompt)

---

## 🗑️ ARCHIVE CANDIDATES (32 skills)

### Apple/Mac only (5) — kamu pake Windows
| Skill | Reason |
|-------|--------|
| apple-notes | Mac only |
| apple-reminders | Mac only |
| findmy | Mac only |
| imessage | Mac only |
| macos-computer-use | Mac only |

### Gaming (2) — kamu nggak main game
| Skill | Reason |
|-------|--------|
| minecraft-modpack-server | Minecraft server setup |
| pokemon-player | Pokemon emulator |

### Social Media / Web (3) — nggak relevan
| Skill | Reason |
|-------|--------|
| xurl | Twitter/X URL shortener |
| popular-web-designs | Web design reference |
| pretext | Browser demos |

### Music / Audio (4) — nggak bikin musik
| Skill | Reason |
|-------|--------|
| audiocraft-audio-generation | Music generation |
| heartmula | Song generation |
| songsee | Audio spectrograms |
| songwriting-and-ai-music | Songwriting |

### ML / AI Research (8) — nggak lagi riset ML
| Skill | Reason |
|-------|--------|
| dspy | ML research framework |
| evaluating-llms-harmness | LLM evaluation |
| llama-cpp | Local LLM inference (kamu pake API) |
| obliteratus | LLM inference |
| segment-anything-model | Image segmentation |
| serving-llms-vllm | LLM serving |
| weights-and-biases | ML experiment tracking |

### Red Teaming (1) — nggak perlu
| Skill | Reason |
|-------|--------|
| godmode | Jailbreak LLMs |

### Misc (9) — nggak relevan dengan workflow kamu
| Skill | Reason |
|-------|--------|
| airtable | Airtable API (kamu pake custom vault) |
| blogwatcher | RSS monitoring |
| dogfood | Exploratory QA |
| linear | Linear issue tracker |
| nano-pdf | PDF editing |
| notion | Notion API (kamu pake custom vault) |
| polymarket | Prediction markets |
| research-paper-writing | Academic writing |
| touchdesigner-mcp | Visual programming |

---

## ✅ KEEP — On-Demand (28 skills)

### Development (10)
| Skill | Why Keep |
|-------|----------|
| claude-code | Claude Code delegation |
| codex | Codex delegation |
| opencode | OpenCode delegation |
| codebase-inspection | Codebase analysis |
| debugging-hermes-tui-commands | Debug Hermes itself |
| github-auth | GitHub auth setup |
| github-code-review | PR review |
| github-issues | Issue management |
| github-pr-workflow | PR lifecycle |
| github-repo-management | Repo management |

### Software Engineering (7)
| Skill | Why Keep |
|-------|----------|
| hermes-agent | Hermes self-config |
| hermes-agent-skill-authoring | Write skills |
| kanban-codex-lane | Kanban + Codex |
| kanban-orchestrator | Kanban orchestration |
| kanban-worker | Kanban worker |
| node-inspect-debugger | Node.js debugging |
| python-debugpy | Python debugging |

### Planning & Review (5)
| Skill | Why Keep |
|-------|----------|
| plan | Plan mode |
| requesting-code-review | Pre-commit review |
| spike | Throwaway experiments |
| subagent-driven-development | Subagent patterns |
| systematic-debugging | Debugging methodology |
| test-driven-development | TDD |
| writing-plans | Implementation plans |

### Content & Media (4)
| Skill | Why Keep |
|-------|----------|
| gif-search | GIF search |
| youtube-content | YouTube transcripts |
| yuanbao | Yuanbao groups |

### Research (3)
| Skill | Why Keep |
|-------|----------|
| arxiv | Paper search |
| llm-wiki | LLM knowledge base |
| maps | Geocoding/routes |

### Productivity (3)
| Skill | Why Keep |
|-------|----------|
| google-workspace | Gmail/Calendar/Drive |
| himalaya | Email CLI |
| ocr-and-documents | OCR |

### DevOps (2)
| Skill | Why Keep |
|-------|----------|
| webhook-subscriptions | Webhook events |
| native-mcp | MCP client |

### Creative (4)
| Skill | Why Keep |
|-------|----------|
| architecture-diagram | SVG diagrams |
| excalidraw | Hand-drawn diagrams |
| manim-video | Math animations |
| p5js | Creative coding |

### Other (2)
| Skill | Why Keep |
|-------|----------|
| comfyui | Image generation |
| huggingface-hub | HF model hub |

---

## 📌 PIN CANDIDATES (5 skills)

Ini yang harusnya always on tanpa disebut:

| Skill | Why Pin |
|-------|---------|
| **hermes-agent** | Self-config, harusnya always available |
| **hermes-agent-skill-authoring** | Biar bisa write/modify skills on-the-fly |
| **writing-plans** | Biar selalu plan dulu sebelum eksekusi |
| **requesting-code-review** | Biar selalu review sebelum commit |
| **systematic-debugging** | Biar selalu debug terstruktur |

---

## SUMMARY

| Action | Count | Skills |
|--------|-------|--------|
| 🗑️ ARCHIVE | 32 | Apple, gaming, social, music, ML research, red teaming, misc |
| ✅ KEEP | 28 | Dev, SWE, planning, content, research, productivity, devops, creative |
| 📌 PIN | 5 | hermes-agent, skill-authoring, writing-plans, code-review, debugging |

---

## HOW TO ARCHIVE

Option 1: Delete from skills folder (Hermes will re-install on update)
Option 2: Move to archive folder (safer, bisa di-restore)

```bash
# Create archive folder
mkdir -p ~/AppData/Local/hermes/skills/.archive

# Move archived skills (example)
mv ~/AppData/Local/hermes/skills/apple/ ~/AppData/Local/hermes/skills/.archive/
mv ~/AppData/Local/hermes/skills/gaming/ ~/AppData/Local/hermes/skills/.archive/
# ... etc
```

Option 3: Unpin + ignore (skills tetap ada tapi nggak di-load)

Note: Hermes mungkin re-install archived skills pada update berikutnya.
Untuk permanent removal, perlu edit `.bundled_manifest` atau update Hermes config.
