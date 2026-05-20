---
title: Skipped Sessions Log
updated: 2026-05-17
---

# Skipped Sessions Log

Sessions yang dihapus dari `sessions/detail/` karena tidak memiliki konten meaningful.

## Criteria
- 1-2 messages only (connection test, greeting)
- Exact clone of another session (same first 200 chars)
- No unique information not already captured in other summaries

## Skipped Sessions

### Connection Tests (1-2 messages)
- `20260514_063452_115cdd` — "hermes chat --allow-shell" test
- `20260514_070254_21d13e` — connection test
- `20260516_063910_c474aa` — "tes lagi nyala ga?"
- `20260516_064210_b2b441` — "tes lai"
- `20260516_064249_5e3017` — "tes chat 2"
- `20260516_064646_c8e8e9` — "yaudah nanti dulu"
- `20260516_065241_9c4da2` — "gabisa resume session di hermes desktop?"
- `aacd39a9-0e7c-4b33-bf19-e263a051c34c` — "hi" (ACP session, 1 msg)
- `acbd3767-db94-4ad0-b8d6-7955710d0877` — 1 msg
- `945c4182-7dae-4c4b-870f-b1f1802da77b` — 1 msg
- `9a302170-40c6-495c-b9e1-d5fadbea04f5` — 1 msg
- `faf613c3-10b5-42d9-862d-5a1a154a3ca7` — 1 msg
- `f989184f-9733-48c2-b500-981ca027265d` — 1 msg
- `257a78ce-d763-413d-8626-875ba55785b4` — 1 msg
- `41074997-b756-47e7-b8c1-40a4d2b9006b` — 1 msg
- `bg_050241_abfc47` — 2 messages, WhatsApp setup (covered in 20260515-whatsapp-setup.md)

### Clones (same content as another session)
- 66 sessions identified as clones by `detect_clones.py`
- All clones have same first 200 chars of user messages as their original
- Originals are preserved in `sessions/detail/`
- See `_meta/_processing_state.json` for full list

## Preserved Sessions

Total preserved in `sessions/detail/`: ~23 unique sessions
- All have 5+ messages
- All contain unique information
- Covered by 10 topic summaries in `sessions/`
