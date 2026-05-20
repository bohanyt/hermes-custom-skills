import json, re, sys

path = r"C:\Users\MSI Thin 15\Documents\hermes_live2video\raw_footages\GTA Anime - Neverness to Everness Indonesia\chunks\merged\production_brief.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Check format
if "potensi_konten" in data:
    # Already parsed
    parsed = data
elif "raw_response" in data:
    raw = data["raw_response"]
    try:
        parsed = json.loads(raw)
    except:
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        parsed = json.loads(match.group()) if match else None
else:
    parsed = None

if parsed is None:
    print("❌ Gagal parse")
    sys.exit(1)

potensi = parsed.get("potensi_konten", [])
print(f"Found {len(potensi)} potensi konten")

# Debug: print first potensi keys
if potensi:
    print("First potensi keys:", list(potensi[0].keys()))

edit_plan = {
    "video_title": parsed.get("analisis_keseluruhan", {}).get("topik_utama", "Unknown"),
    "detected_niche": parsed.get("analisis_keseluruhan", {}).get("detected_niche", "unknown"),
    "bagian_dipertahankan": []
}

for i, konten in enumerate(potensi):
    # Handle different field names
    start = konten.get("start_time", "")
    end = konten.get("end_time", "")
    
    # Try Waktu field (format: "00:00:01 → 00:10:16")
    waktu = konten.get("Waktu", "")
    if "→" in waktu:
        parts = waktu.split("→")
        start = parts[0].strip()
        end = parts[1].strip()
    elif " - " in waktu:
        parts = waktu.split(" - ")
        start = parts[0].strip()
        end = parts[1].strip()
    
    # Fallback: try extract from text
    if not start:
        ts_match = re.search(r'(\d{2}:\d{2}:\d{2})\s*[→-]\s*(\d{2}:\d{2}:\d{2})', str(konten))
        if ts_match:
            start = ts_match.group(1)
            end = ts_match.group(2)
    
    judul = konten.get("Judul", konten.get("judul_saran", ""))
    hook = konten.get("Hook", konten.get("hook", ""))
    jenis = konten.get("jenis", "Unknown")
    vibe = konten.get("vibe", "")
    alasan = konten.get("Alasan", konten.get("alasan", ""))
    
    edit_plan["bagian_dipertahankan"].append({
        "timestamp": f"{start} - {end}" if start else "00:00:00 - 00:00:00",
        "konten_id": i + 1,
        "jenis": jenis,
        "judul": judul,
        "hook": hook,
        "vibe": vibe,
        "alasan": alasan
    })

output_path = r"C:\Users\MSI Thin 15\Documents\hermes_live2video\raw_footages\GTA Anime - Neverness to Everness Indonesia\chunks\merged\edit_plan.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(edit_plan, f, ensure_ascii=False, indent=2)

print(f"✅ edit_plan.json saved")
print(f"   Total segments: {len(edit_plan['bagian_dipertahankan'])}")
for s in edit_plan["bagian_dipertahankan"]:
    print(f"   - [{s['konten_id']}] {s['jenis']}: {s['timestamp']}")
    print(f"     {s['judul'][:60]}")
