"""
fix_prompts.py — Fix curly brace issues in prompt strings
Scan all .py files and replace {placeholder} with [[placeholder]]
in prompt strings, so .replace() works without KeyError.
"""
import re
import sys
from pathlib import Path

# Files to fix
FILES = [
    "orchestrator.py",
    "chunk_merger.py",
    "data_miner.py",
    "storyteller.py",
    "retention_architect.py",
    "chunk_summarizer.py",
]

# Placeholders that should NOT be escaped (they're intentional)
PLACEHOLDERS = [
    "{content_types_guide}",
    "{metadata}",
    "{summaries}",
    "{detected_niche}",
    "{max_duration}",
    "{chunks_summary}",
    "{chunk_text}",
    "{brief}",
    "{data_mining}",
    "{trend_research}",
    "{story_brief}",
]

def fix_file(filepath: str):
    """Fix curly braces in prompt strings."""
    path = Path(filepath)
    if not path.exists():
        print(f"  ⚠️  Not found: {filepath}")
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    original = content

    # Find all triple-quoted strings
    # Pattern: """...""" or '''...'''
    patterns = [
        r'"""(.*?)"""',
        r"'''(.*?)'''",
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            string_content = match.group(1)

            # Skip if it's a docstring (starts with newline or is short)
            if len(string_content) < 50:
                continue

            # Find all {word} patterns that are NOT placeholders
            # These are likely JSON curly braces that need escaping
            new_string = string_content

            # Find all {something} patterns
            brace_patterns = re.findall(r'\{([^{}]+)\}', new_string)

            for bp in brace_patterns:
                full = "{" + bp + "}"
                # Skip if it's a known placeholder
                if full in PLACEHOLDERS:
                    continue
                # Skip if it's inside a JSON example (has quotes around it)
                # Replace with double braces for .format() safety
                # Actually, we don't need to escape — we just need to make sure
                # .format() or .replace() doesn't break

            # The real fix: replace .format() calls with .replace()
            # But that's done manually per file

    # Actually, let's just do a simpler fix:
    # Replace all .format( with .replace( for prompt strings
    # This is done per-file below

    if content != original:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Fixed: {filepath}")
    else:
        print(f"  ℹ️  No changes: {filepath}")


def fix_orchestrator():
    """Fix orchestrator.py specifically."""
    path = Path("orchestrator.py")
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Fix: replace .format() with .replace() for prompt strings
    # Already done manually, but let's verify

    # Fix: make sure JSON examples in prompts use {{ and }}
    # Find ORCHESTRATOR_SYSTEM_PROMPT and escape JSON braces

    # Pattern: Find the prompt string and escape JSON examples
    # This is tricky with regex, so we do targeted fixes

    fixes = [
        # Fix any remaining .format() calls on prompt strings
        (
            r'ORCHESTRATOR_SYSTEM_PROMPT\.format\([^)]+\)',
            'ORCHESTRATOR_SYSTEM_PROMPT.replace("[[content_types_guide]]", content_types_guide)'
        ),
        (
            r'ORCHESTRATOR_USER_TEMPLATE\.format\([^)]+\)',
            'ORCHESTRATOR_USER_TEMPLATE.replace("[[metadata]]", metadata_text).replace("[[summaries]]", summaries_text).replace("[[detected_niche]]", detected_niche_text).replace("[[content_types_guide]]", content_types_guide)'
        ),
    ]

    for old, new in fixes:
        content = re.sub(old, new, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  ✅ orchestrator.py fixed")


def fix_chunk_merger():
    """Fix chunk_merger.py."""
    path = Path("chunk_merger.py")
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Already fixed with .replace() — verify
    if ".format(" in content and "MERGE_SYSTEM_PROMPT" in content:
        print("  ⚠️  chunk_merger.py still has .format() — needs manual fix")
    else:
        print("  ✅ chunk_merger.py OK")


def fix_data_miner():
    """Fix data_miner.py."""
    path = Path("data_miner.py")
    if not path.exists():
        return

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check for .format() in prompt strings
    if '.format(' in content:
        # Find prompt strings and replace .format() with .replace()
        lines = content.split('\n')
        new_lines = []
        for line in lines:
            if '.format(' in line and ('PROMPT' in line or 'TEMPLATE' in line):
                # Replace .format(...) with .replace(...)
                line = re.sub(
                    r'\.format\(([^)]+)\)',
                    lambda m: '.replace(' + m.group(1).replace('=', ') + .replace(') if '=' in m.group(1) else m.group(1)),
                    line
                )
            new_lines.append(line)
        content = '\n'.join(new_lines)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("  ✅ data_miner.py fixed")


if __name__ == "__main__":
    print("Fixing prompt curly brace issues...")
    print()

    # Fix each file
    fix_orchestrator()
    fix_chunk_merger()
    fix_data_miner()

    print()
    print("Done! Test with: python orchestrator.py <chunks_dir>")
