# Windows Process Management & Multi-Session Pitfalls

## Killing Hermes ACP Processes (Keep CLI Alive)

When AionUI hangs with spinner/animation still visible, kill only ACP processes:

```powershell
# Identify: ACP processes have CommandLine matching 'acp', CLI has 'chat --yolo'
Get-CimInstance Win32_Process -Filter "Name='hermes.exe'" |
  Select-Object ProcessId, ParentProcessId, CommandLine

# Kill only ACP (write .ps1 to avoid bash escaping issues with spaces in path)
# File: kill_hermes_acp.ps1
Get-CimInstance Win32_Process -Filter "Name='hermes.exe'" |
  Where-Object { $_.CommandLine -match 'acp' } |
  ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
```

Running PowerShell inline via bash breaks on paths with spaces (`C:\Users\MSI Thin 15`). Always write `.ps1` file first, then `powershell -File script.ps1`.

## Multi-Session Rate Limit Hang

**Symptom**: 3 sessions (1 CLI + 2 AionUI) on same API key → spinner/hang on AionUI.

**Cause**: OpenRouter rate limits concurrent requests per API key. AionUI spawn multiple ACP processes.

**Fix**: Close idle sessions. Run one session at a time when possible.

**Kill order**:
1. Kill AionUI app (Task Manager or `taskkill /IM AionUi.exe /F`)
2. Kill ACP processes (see above)
3. Keep `hermes chat --yolo` (terminal session) alive

## AionUI vs Terminal Tradeoffs

| Feature | Terminal (CLI) | AionUI |
|---------|---------------|--------|
| Image upload | ❌ No | ✅ Yes (drag & drop) |
| Model switching | `/model` command | ✅ Click to switch |
| Vision support | Depends on model | ✅ Easier with GUI |
| Multi-session | Manual terminal windows | ✅ Built-in |
| Rate limit risk | Low (single session) | High (multiple ACP) |
| Resource usage | Low | High (Electron + agents) |
| Scripting/automation | ✅ Easy | ❌ Harder |

**Recommendation**: Use terminal for scripting/automation pipelines (like live2video). Use AionUI for interactive tasks requiring image uploads or model switching on the fly.

## Vision Model Support

`openrouter/owl-alpha` does **not** support image input. For vision, use:

| Model | Vision? | Cost | Context |
|-------|---------|------|---------|
| `nvidia/nemotron-nano-12b-v2-vl:free` | ✅ Image + Video | Free | 128K |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | ✅ Multi-modal | Free | 256K |

Config: set `auxiliary.vision.model` explicitly. Auto-detect may not pick vision-capable model.

## OpenRouter Multi-Model Setup

Single API key (`sk-or-v1-...`) works for all models. Different scripts use different models via `config_api.py` profiles:

```yaml
# config.yaml
model:
  default: openrouter/owl-alpha  # primary
```

```python
# In script
from config_api import call_llm
response = call_llm("summarizer", messages)  # uses SUMMARIZER_MODEL from .env
```

Free tier models have rate limits (~1 req/3s). Add delay + retry:
```python
time.sleep(3)  # between requests
# Retry with exponential backoff on 429
```

## YouTube API vs yt-dlp for Market Research

When building `market_scraper.py`, views accuracy matters:

| Approach | Views Accuracy | Filter by Date | Min Views Filter | Cost |
|----------|---------------|----------------|------------------|------|
| yt-dlp | ⚠️ Cached/delayed | ✅ `--dateafter` | ❌ Post-filter only | Free |
| YouTube Data API v3 | ✅ Real-time | ✅ `publishedAfter` | ✅ Native | 10K units/day free |

**Recommendation**: Use YouTube Data API v3 for market_scraper (accurate views, date filters, min views). Falls back to yt-dlp when `YOUTUBE_API_KEY` not set.

To enable: set `YOUTUBE_API_KEY` in `.env` (get key from https://console.cloud.google.com → YouTube Data API v3).

**API quota**: 10,000 units/day free. Search = 100 units, video stats = 1 unit, comments = 1 unit, channel stats = 1 unit.

## Content Type Detection (Niche Matching)

The orchestrator uses `content_types.json` to detect the content niche and select appropriate video types. This is keyword-based matching against video title, channel, and chunk summaries.

**Key pattern**: Each niche has `keywords[]` for detection and `content_types[]` with `cocok_untuk`, `hook_pattern`, `durasi_ideal`, `editing_style`.

**Extending**: Add new niches to `content_types.json` following the existing format. No code changes needed — the orchestrator reads it dynamically.

## AionUI Process Management

AionUI spawns multiple `hermes acp` processes. When killing:
1. Kill AionUI app: `taskkill /IM AionUi.exe /F`
2. Kill ACP processes: filter by CommandLine matching 'acp', keep 'chat --yolo'
3. AionUI may auto-spawn new ACP processes — kill the app first, then the processes
