---
title: 4-Agent Arsitektur v2 -- Kiro x Hermes x Gemma x Copilot
sessions: [20260519-kiro-4agent-architecture]
date: 2026-05-19
platform: cli
model: owl-alpha
total_messages: 45
tags: [kiro, gemma-4, copilot-m365, multi-agent, security, architecture]
---

# 4-Agent Arsitektur v2 -- Kiro x Hermes x Gemma x Copilot

**Date:** 2026-05-19 | **Platform:** CLI | **Messages:** ~45

## What Happened

Mendesain arsitektur 4-agent yang menggabungkan Kiro CLI (Claude Opus 4.7), Hermes Agent (Owl Alpha), Gemma 4 e2b Q6 (LM Studio), dan Copilot M365 (GPT-5.5) dengan prinsip security-first.

Arsitektur awal (v1) hanya 2 agent: Hermes (executor) + Kiro (judger). v2 menambahkan:
- Gemma 4 e2b sebagai "Data Gateway" -- satu-satunya yang boleh baca data kantor
- Copilot M365 sebagai "Tutor" -- fallback reasoning untuk Gemma 4 via Playwright + cookie inject ke Edge

## Key Security Principle

Data kantor (Excel, PDF, Email, DB) hanya boleh diakses oleh AI lokal di laptop kantor: Gemma 4 dan Copilot. Hermes dan Kiro TIDAK PERNAH boleh sentuh data kantor. Gemma 4 extract/summarize data ke TXT non-sensitive, hanya hasil olahan yang boleh keluar zona kantor.

## Key Learnings

- Kiro role: spec generation (EARS notation) + audit ONLY, never implement code
- Gemma 4 role: data gateway, extract/summarize data kantor ke TXT, fallback ke Copilot via Playwright
- Copilot role: "tutor" untuk Gemma 4 saat context overflow atau reasoning berat
- Hermes role: executor utama, baca TXT + spec, implement code + tests, kirim ke Kiro
- Security boundary: air-gapped zone (kantor) vs safe zone (personal/cloud)
- Credit optimization: 4-agent sinergi bisa ~500+ features vs Kiro saja ~75 features (2000 credits)
- Data funneling: Kiro design spec untuk normalisasi data macam-macam jadi TXT terstruktur
- Sanitization rules: no PII, no raw financials, no internal system names, max 5000 chars per TXT

## Files Generated

- `Downloads/arsitektur-v2.html` -- Visual architecture diagram (42KB)
- `Downloads/kiro-judger-setup.txt` -- Kiro skills + steering + prompt (22KB)
- `Downloads/kiro-kantor-setup-guide.txt` -- Setup guide untuk laptop kantor (pending)

## Related

- [[copilot-m365-pipeline]] -- Playwright automation untuk Copilot
- [[hermes-desktop-setup]] -- LM Studio + Gemma 4 setup
- [[playwright-m365-automation]] -- Playwright browser automation
- [[kiro-judger]] -- NEW: Kiro sebagai judger/auditor
- [[multi-agent-architecture]] -- NEW: 4-agent security-first architecture
