---
title: Hermes Desktop + LM Studio Setup & Testing
sessions: [20260516_074620_6f1cf8, 20260516_074919_24fdcc, 20260516_080203_0958bc, 20260516_080250_e7f174, 20260516_080313_1376c7, 20260516_080545_e7cc36, 20260516_081500_eecdbc, 20260516_083253_a5839f, 20260516_083819_19338c, 20260516_091547_868e7a, 20260516_095404_fc824f, 20260516_095700_878c38, 20260516_101951_0729e5, 20260516_104440_e27c9b]
date: 2026-05-16
platform: tui
model: openrouter/owl-alpha
total_messages: ~1800 (combined)
tags: [hermes-desktop, lm-studio, local-ai, setup, testing]
---

# Hermes Desktop + LM Studio Setup & Testing

**Date:** 2026-05-16 | **Platform:** TUI | **Combined messages:** ~1800

## What Happened

Full-day setup and testing of Hermes Desktop + LM Studio on laptop kantor (RTX 3050 6GB). Multiple TUI sessions covering installation, configuration, model loading, and integration testing.

## Laptop Kantor Specs

- GPU: RTX 3050 6GB VRAM
- Model: Gemma 4 e2b Q6 (4.5GB)
- Hermes Desktop: v0.4.3

## LM Studio Configuration

- **Context length**: 64000 (override for Hermes Desktop)
- **GPU offload**: 35 layers (fits in 6GB VRAM)
- **Model**: Gemma 4 e2b Q6 (~4.5GB)
- **Endpoint**: `http://localhost:1234/v1/chat/completions`

## Hermes Desktop Config

```yaml
model:
  name: google/gemma-4-e2b
  context_length: 64000
  base_url: http://localhost:1234/v1
```

## Setup Steps

1. Install LM Studio
2. Download Gemma 4 e2b Q6 model
3. Set context length to 64K in LM Studio
4. Set GPU offload to 35 layers
5. Start LM Studio server
6. Configure Hermes Desktop to use LM Studio endpoint
7. Override context_length in config.yaml

## Common Issues

| Issue | Solution |
|-------|----------|
| 400 Bad Request | Use `/v1/chat/completions` not `/chat/completions` |
| Context window error | Override `context_length: 64000` in config.yaml |
| GPU OOM | Reduce GPU offload layers |
| Model too large | Use Q4 or Q5 quantization |
| Hermes Desktop requires 64K+ context | Override model metadata in config.yaml |

## Key Decisions

- **Context window override**: Gemma 4 e2b has 8K context by default, but Hermes Desktop requires 64K minimum. Override in config.yaml.
- **5 API keys**: Set up for OpenRouter fallback
- **OneDrive sync**: Planned for cross-device access

## Related

- [[hermes-desktop-setup]] — Full setup guide
- [[lm-studio-integration]] — Integration details
- [[context-window-override]] — Context window override decision
- [[vision-model-selection]] — Nemotron Nano 12B VL for vision
- [[hermes-web-ui]] — Web UI dashboard (discovered session 20260517_233528_84bcf2)
- [[cloudflare-tunnel]] — Remote access via tunnel (session 20260518_061437_f2e056d3)

## Detail Files

14 condensed session files in `sessions/detail/` (see index for full list)
