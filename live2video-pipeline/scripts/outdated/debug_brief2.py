import json, re

path = r"C:\Users\MSI Thin 15\Documents\hermes_live2video\raw_footages\GTA Anime - Neverness to Everness Indonesia\chunks\merged\production_brief.json"

with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Top keys:", list(data.keys()))
raw = data.get("raw_response", "")
print("Type:", type(raw).__name__)
print("Len:", len(raw) if raw else 0)

if isinstance(raw, str) and len(raw) > 0:
    print("First 300 chars:")
    print(repr(raw[:300]))
    print()
    
    # Try parse
    try:
        parsed = json.loads(raw)
        print("Direct parse OK! Keys:", list(parsed.keys()))
    except Exception as e:
        print(f"Direct parse error: {e}")
        
        # Try find JSON object
        idx = raw.find('{')
        if idx >= 0:
            print(f"First '{{' at index {idx}")
            # Find matching closing brace
            depth = 0
            end_idx = -1
            for i in range(idx, len(raw)):
                if raw[i] == '{':
                    depth += 1
                elif raw[i] == '}':
                    depth -= 1
                    if depth == 0:
                        end_idx = i
                        break
            if end_idx >= 0:
                candidate = raw[idx:end_idx+1]
                print(f"JSON candidate length: {len(candidate)}")
                try:
                    parsed = json.loads(candidate)
                    print("Bracket-matched parse OK! Keys:", list(parsed.keys()))
                except Exception as e2:
                    print(f"Bracket-matched parse error: {e2}")
                    print("Candidate first 200:")
                    print(repr(candidate[:200]))
