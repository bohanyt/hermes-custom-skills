# Free Multi-Modal Models on OpenRouter (2026-05-14)

Free models that support image/video input, sorted by latency (low to high).

## Vision + Video Understanding

| Model | Context | Input | Notes |
|-------|---------|-------|-------|
| `nvidia/nemotron-nano-12b-v2-vl:free` | 128K | Text + Multi-Image + Video | Designed for video understanding + document intelligence. Hybrid Transformer-Mamba. Efficient Video Sampling (EVS) for long videos. |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256K | Text + Image + Audio + Video | Full multi-modal. "Omni" = all modalities. |

## Text-Only Free Models (for reference)

| Model | Context | Notes |
|-------|---------|-------|
| `nvidia/nemotron-3-nano-30b-a3b:free` | 256K | Text only |
| `deepseek/deepseek-v4-flash:free` | 256K | Text only. Good for summarization. |
| `openrouter/owl-alpha` | 1.05M | Text only. Primary orchestrator model. |

## API Key Note

One OpenRouter API key (`sk-or-v1-...`) works for ALL models on OpenRouter. No need for separate keys per model.

## Config Example

```yaml
# config.yaml
model:
  default: openrouter/owl-alpha
  provider: openrouter
  base_url: https://openrouter.ai/api/v1
  api_key: sk-or-v1-xxxxxxxx

# .env
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxx
SUMMARIZER_API_KEY=sk-or-v1-xxxxxxxx  # same key, different model
```

Switch models mid-session in CLI:
```
/model nvidia/nemotron-nano-12b-v2-vl:free
```
