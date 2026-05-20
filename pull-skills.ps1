# pull-skills.ps1
# Tarik custom skills dari GitHub dan pasang ke Hermes
# Usage: .\pull-skills.ps1 [-RepoUrl <url>] [-Branch <branch>]

param(
    [string]$RepoUrl = "https://github.com/vincentiusbohan/hermes-custom-skills.git",
    [string]$Branch = "main",
    [string]$TempDir = "$env:TEMP\hermes-skills-pull"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Hermes Custom Skills - Pull from GitHub ===" -ForegroundColor Cyan
Write-Host ""

# Check if git is available
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: git not found. Install git first." -ForegroundColor Red
    exit 1
}

# Clone or pull
if (Test-Path $TempDir) {
    Write-Host "Updating existing clone..." -ForegroundColor Yellow
    Set-Location $TempDir
    git pull origin $Branch
} else {
    Write-Host "Cloning from GitHub..." -ForegroundColor Yellow
    git clone --branch $Branch $RepoUrl $TempDir
    Set-Location $TempDir
}

Write-Host ""
Write-Host "=== Installing skills ===" -ForegroundColor Cyan

$SkillsDir = "$env:LOCALAPPDATA\hermes\skills"
$HomeSkillsDir = "$env:USERPROFILE\.hermes\skills"
$DocsDir = "$env:USERPROFILE\Documents"

# Ensure directories exist
New-Item -ItemType Directory -Force -Path $SkillsDir | Out-Null
New-Item -ItemType Directory -Force -Path $HomeSkillsDir | Out-Null

# Custom skills to install (from export folder)
$CustomSkills = @(
    @{ Name = "content-pipeline-builder";    Dest = "$SkillsDir\content-pipeline-builder" },
    @{ Name = "hermes-multi-session";        Dest = "$SkillsDir\hermes-multi-session" },
    @{ Name = "hermes-python-pipeline";      Dest = "$SkillsDir\hermes-python-pipeline" },
    @{ Name = "hermes-save-session";         Dest = "$SkillsDir\hermes-save-session" },
    @{ Name = "hermes-fix-session-index";    Dest = "$SkillsDir\hermes-fix-session-index" },
    @{ Name = "vault-query";                 Dest = "$HomeSkillsDir\vault-query" },
    @{ Name = "vault-update";                Dest = "$HomeSkillsDir\vault-update" },
    @{ Name = "vault-session-capture";       Dest = "$SkillsDir\devops\vault-session-capture" },
    @{ Name = "vault-management";            Dest = "$SkillsDir\devops\vault-management" },
    @{ Name = "storytime-pipeline";          Dest = "$SkillsDir\devops\storytime-pipeline" },
    @{ Name = "live2video-pipeline";         Dest = "$SkillsDir\mlops\live2video-pipeline" },
    @{ Name = "context-delegation";          Dest = "$SkillsDir\devops\context-delegation" },
    @{ Name = "caveman";                     Dest = "$SkillsDir\productivity\caveman" },
    @{ Name = "grill-me";                    Dest = "$SkillsDir\software-development\grill-me" },
    @{ Name = "handoff";                     Dest = "$SkillsDir\productivity\handoff" },
    @{ Name = "improve-codebase-architecture"; Dest = "$SkillsDir\software-development\improve-codebase-architecture" },
    @{ Name = "zoom-out";                    Dest = "$SkillsDir\software-development\zoom-out" },
    @{ Name = "browser-automation-enterprise"; Dest = "$SkillsDir\software-development\browser-automation-enterprise" }
)

$Installed = 0
$Skipped = 0

foreach ($skill in $CustomSkills) {
    $src = Join-Path $TempDir $skill.Name
    if (Test-Path $src) {
        # Create parent directory if needed
        $parent = Split-Path $skill.Dest -Parent
        if (-not (Test-Path $parent)) {
            New-Item -ItemType Directory -Force -Path $parent | Out-Null
        }
        # Copy (overwrite if exists)
        Copy-Item -Path $src -Destination $skill.Dest -Recurse -Force
        Write-Host "  OK: $($skill.Name)" -ForegroundColor Green
        $Installed++
    } else {
        Write-Host "  SKIP: $($skill.Name) (not found in repo)" -ForegroundColor Yellow
        $Skipped++
    }
}

# Install hermes-tools
$ToolsSrc = Join-Path $TempDir "hermes-tools"
$ToolsDest = "$DocsDir\hermes-tools"
if (Test-Path $ToolsSrc) {
    Copy-Item -Path $ToolsSrc -Destination $ToolsDest -Recurse -Force
    Write-Host "  OK: hermes-tools" -ForegroundColor Green
    $Installed++
} else {
    Write-Host "  SKIP: hermes-tools (not found in repo)" -ForegroundColor Yellow
    $Skipped++
}

# Install pipeline scripts
$PipelineSrc = Join-Path $TempDir "live2video-pipeline\scripts"
$PipelineDest = "$DocsDir\hermes_live2video\hermes_skills"
if (Test-Path $PipelineSrc) {
    New-Item -ItemType Directory -Force -Path $PipelineDest | Out-Null
    Copy-Item -Path $PipelineSrc\* -Destination $PipelineDest -Recurse -Force
    Write-Host "  OK: live2video-pipeline scripts" -ForegroundColor Green
    $Installed++
} else {
    Write-Host "  SKIP: live2video-pipeline scripts (not found in repo)" -ForegroundColor Yellow
    $Skipped++
}

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host "Installed: $Installed" -ForegroundColor Green
Write-Host "Skipped:   $Skipped" -ForegroundColor Yellow
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run archive-skills.ps1 to remove irrelevant default skills"
Write-Host "  2. Pin skills: hermes skills pin vault-query"
Write-Host "                 hermes skills pin writing-plans"
Write-Host "                 hermes skills pin systematic-debugging"
