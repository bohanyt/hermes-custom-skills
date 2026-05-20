# archive-skills.ps1
# Archive default skills yang tidak relevan untuk menghemat token
# Usage: .\archive-skills.ps1 [-WhatIf]

param(
    [switch]$WhatIf
)

$ErrorActionPreference = "Stop"

Write-Host "=== Hermes Skills - Archive Irrelevant Defaults ===" -ForegroundColor Cyan
Write-Host ""

$SkillsDir = "$env:LOCALAPPDATA\hermes\skills"
$ArchiveDir = "$SkillsDir\.archive"

# Create archive directory
if (-not (Test-Path $ArchiveDir)) {
    New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null
}

# Skills to archive (26 total)
$ArchiveList = @(
    # Apple/Mac (5)
    "apple-notes"
    "apple-reminders"
    "findmy"
    "imessage"
    "macos-computer-use"
    # Gaming (2)
    "minecraft-modpack-server"
    "pokemon-player"
    # Music/Audio (3)
    "heartmula"
    "songsee"
    "songwriting-and-ai-music"
    # ML Research (4)
    "dspy"
    "llama-cpp"
    "obliteratus"
    "weights-and-biases"
    # Red Teaming (1)
    "godmode"
    # Misc (8)
    "airtable"
    "blogwatcher"
    "dogfood"
    "linear"
    "nano-pdf"
    "notion"
    "polymarket"
    "research-paper-writing"
    "touchdesigner-mcp"
    # Social/Web (3)
    "xurl"
    "popular-web-designs"
    "pretext"
)

$Archived = 0
$NotFound = 0

foreach ($skill in $ArchiveList) {
    # Find the skill directory
    $skillDir = Get-ChildItem -Path $SkillsDir -Directory -Recurse -Filter $skill -ErrorAction SilentlyContinue | 
                Where-Object { $_.Name -eq $skill -and $_.Parent.FullName -ne $ArchiveDir } |
                Select-Object -First 1
    
    if ($skillDir) {
        $dest = Join-Path $ArchiveDir $skill
        
        if ($WhatIf) {
            Write-Host "  WOULD ARCHIVE: $($skillDir.FullName) -> $dest" -ForegroundColor DarkYellow
        } else {
            # Move to archive
            if (Test-Path $dest) {
                Remove-Item $dest -Recurse -Force
            }
            Move-Item $skillDir.FullName $dest -Force
            Write-Host "  ARCHIVED: $skill" -ForegroundColor Green
        }
        $Archived++
    } else {
        Write-Host "  NOT FOUND: $skill" -ForegroundColor DarkGray
        $NotFound++
    }
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Archived:   $Archived" -ForegroundColor Green
Write-Host "Not found:  $NotFound" -ForegroundColor DarkGray
Write-Host ""

if ($WhatIf) {
    Write-Host "This was a dry run. Run without -WhatIf to actually archive." -ForegroundColor Yellow
} else {
    Write-Host "Archived skills are in: $ArchiveDir" -ForegroundColor Cyan
    Write-Host "To restore: move them back to $SkillsDir" -ForegroundColor Cyan
}
