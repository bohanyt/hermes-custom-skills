# Prompt Engineering Pattern: Escaping Curly Braces

## Problem
Python's `str.format()` interprets ALL `{...}` as placeholders, including JSON examples in prompt strings:

```python
PROMPT = """Output format:
{
  "key": "value"
}"""

# This BREAKS:
messages = [{"role": "system", "content": PROMPT.format(guide=guide)}]
# KeyError: 'key'
```

## Solution: `[[placeholder]]` + `.replace()` Pattern

### Step 1: Use `[[double_braces]]` for placeholders in prompt strings

```python
PROMPT_SYSTEM = """CONTENT TYPES:
[[content_types_guide]]

OUTPUT FORMAT:
{
  "key": "value"
}"""

PROMPT_USER = """Data:
[[data]]

Process this."""
```

### Step 2: Use `.replace()` instead of `.format()`

```python
messages = [
    {"role": "system", "content": PROMPT_SYSTEM.replace("[[content_types_guide]]", guide)},
    {"role": "user", "content": PROMPT_USER.replace("[[data]]", data_text)}
]
```

## Affected Files (all fixed)

| File | Placeholders |
|------|-------------|
| orchestrator.py | `[[content_types_guide]]` |
| chunk_merger.py | `[[max_duration]]`, `[[chunks_summary]]` |
| data_miner.py | `[[brief]]`, `[[chunks_text]]` |
| storyteller.py | `[[brief]]`, `[[data_mining]]`, `[[trend]]` |
| retention_architect.py | `[[story_brief]]`, `[[chunks_info]]` |
| chunk_summarizer.py | `[[chunk_text]]` |
| topic_detector.py | `[[content_types_guide]]`, `[[total_chunks]]`, `[[total_duration]]`, `[[chunks_summary]]` |
| storyteller_v2.py | `[[label]]`, `[[video_type]]`, `[[summary]]`, `[[trend_insights]]` |
| trend_researcher_v2.py | (none yet — add if needed) |

## Checklist When Adding New Prompt Strings

1. Use `[[placeholder_name]]` for any dynamic value
2. Use `.replace()` to substitute values
3. Never use `.format()` on prompt strings containing JSON examples
4. Test with sample data to verify no KeyError
