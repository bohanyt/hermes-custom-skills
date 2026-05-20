# Folder Cleanup & Organization Standard

## Standard Structure

After pipeline completes, each test folder should look like:

```
testing/v{version}_tes{N}/
├── final_cuts/topics/     ← ALL output: mp4 clips, render_log.json, report.html, progress_report.html
└── work/                  ← Intermediate files only: chunks/, metadata.json
    ├── chunks/
    │   ├── chunks.json
    │   ├── all_summaries.json
    │   ├── merged/
    │   ├── topics.json
    │   ├── trend_research.json
    │   ├── stories.json
    │   └── story_log.txt
    └── metadata.json
```

## Common Issue: Duplicate `work/final_cuts/`

**Cause:** `technician.py --mode topics` outputs to `work/final_cuts/topics/` by default.

**Fix:** After render completes, move contents up and delete duplicate:
```powershell
Move-Item "testing/v{version}/work/final_cuts/topics/*" "testing/v{version}/final_cuts/topics/"
Remove-Item -Recurse "testing/v{version}/work/final_cuts"
```

## raw_footages/ Hygiene

`raw_footages/` should ONLY contain source files (video.mp4, .srt, metadata.json).
NEVER leave intermediate outputs (chunks/, final_cuts/) in raw_footages/.
