import json, sys

path = r"C:\Users\MSI Thin 15\Documents\hermes_live2video\raw_footages\GTA Anime - Neverness to Everness Indonesia\chunks\merged\production_brief.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Top keys:", list(data.keys()))
raw = data.get("raw_response", "")
print("Type:", type(raw).__name__)
print("Len:", len(raw))
print("First 100:", repr(raw[:100]))

# Try parse raw_response
if isinstance(raw, str):
    try:
        parsed = json.loads(raw)
        print("Parsed OK! Keys:", list(parsed.keys()))
        if "potensi_konten" in parsed:
            print("potensi_konten count:", len(parsed["potensi_konten"]))
    except Exception as e:
        print("Parse error:", e)
        # Try unescape
        try:
            unescaped = raw.encode().decode("unicode_escape")
            parsed = json.loads(unescaped)
            print("Unescaped OK! Keys:", list(parsed.keys()))
        except Exception as e2:
            print("Unescape error:", e2)
