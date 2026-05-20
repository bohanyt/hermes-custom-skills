---
name: zoom-out
description: Tell the agent to zoom out and give broader context or a higher-level perspective on an unfamiliar section of code. Use when you're unfamiliar with a section of code, need to understand how it fits into the bigger picture, or says "zoom out" / "give me context" / "how does this fit".
disable-model-invocation: true
---

# Zoom Out

I don't know this area of code well. Go up a layer of abstraction. Give me a map of all the relevant modules and callers.

## What to Provide

1. **Module map** — What are the key modules/files in this area? How do they relate?
2. **Data flow** — Where does data enter? Where does it exit? What transforms happen?
3. **Callers** — Who calls this code? What do they expect?
4. **Dependencies** — What does this code depend on?
5. **Seams** — Where are the key interfaces/seams in this area?

## Format

Use a concise bullet-point or diagram format. Don't dump code — describe structure.

```
ModuleA (entry point)
  -> ModuleB (validates input)
  -> ModuleC (business logic)
    -> ModuleD (persistence)
  -> ModuleE (response formatting)
```
