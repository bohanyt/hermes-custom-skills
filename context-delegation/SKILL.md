---
name: context-delegation
description: SOP untuk handle context window overload — kalau data terlalu besar untuk satu model, delegate ke API lain atau split processing.
---

# Context Delegation SOP

## Masalah
Kalau context window udah besar (misal >100k tokens), model jadi:
- Lambat
- Malas baca semua data
- Output quality turun
- Bisa skip penting parts

## Solusi: Delegate ke API Lain

### Kapan Delegate
- Context window >50% capacity
- Data yang perlu dibuat >20 items
- Task yang repetitive (klasifikasi, summarization)
- Model utama sedang sibuk

### Cara Delegate

#### Opsi 1: Split Batch
- Bagi data jadi batch kecil (5-10 items per batch)
- Proses setiap batch secara terpisah
- Gabung hasilnya

#### Opsi 2: Gunakan Model Lain via API
- Untuk task repetitif, pakai model yang lebih kecil/cepat
- Contoh: klasifikasi topik → pakai model ringan
- Contoh: summarization → pakai model khusus

#### Opsi 3: Subagent via delegate_task
- Spawn subagent untuk handle bagian besar
- Setiap subagent handle subset data
- Parent agent gabung hasilnya

## Implementasi

### Untuk Orchestrator (Topic Analysis)
```
Jika chunks > 20:
  Split jadi batch of 5 chunks
  Untuk setiap batch:
    Baca summaries
    Klasifikasi: storytime-worthy atau tidak
  Gabung hasil klasifikasi
```

### Untuk Storyteller (Script Writing)
```
Jika script outline > 1000 words:
  Split per act
  Generate script per act
  Gabung jadi full script
```

## Model Fallback
- Primary: owl-alpha (current)
- Fallback 1: openrouter/anthropic/claude-sonnet-4
- Fallback 2: openrouter/google/gemini-2.0-flash
- Untuk task ringan: openrouter/meta-llama/llama-3.1-8b

## Catatan
- Jangan malas baca — kalau data penting, baca semua
- Kalau memang overload, delegate jangan dipaksakan
- Quality > speed untuk analisis penting
