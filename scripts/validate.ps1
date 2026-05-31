$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SkillDir = Join-Path $RepoRoot "skills\ppt-template-deck-builder"

if (-not (Test-Path $SkillDir)) {
  throw "Missing skill directory: $SkillDir"
}

$Required = @(
  "SKILL.md",
  "agents\openai.yaml",
  "scripts\extract_template_model.py",
  "scripts\classify_template_semantics.py",
  "scripts\build_deck_plan.py",
  "scripts\extract_document_logic.py",
  "scripts\build_animation_plan.py",
  "scripts\qa_deck_plan.py",
  "scripts\qa_pptx_package.py",
  "scripts\qa_accessibility_structure.py"
)

foreach ($Rel in $Required) {
  $Path = Join-Path $SkillDir $Rel
  if (-not (Test-Path $Path)) {
    throw "Missing required file: $Rel"
  }
}

$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
  throw "Python was not found on PATH."
}

$CheckScript = @'
from pathlib import Path
import re
import sys

skill = Path(sys.argv[1])
text = (skill / "SKILL.md").read_text(encoding="utf-8")
if not text.startswith("---\n"):
    raise SystemExit("SKILL.md is missing YAML frontmatter")
parts = text.split("---\n", 2)
if len(parts) < 3:
    raise SystemExit("SKILL.md frontmatter is not closed")
front = parts[1]
fields = {}
for line in front.splitlines():
    if ":" in line:
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip()
if fields.get("name") != "ppt-template-deck-builder":
    raise SystemExit("Invalid skill name")
if not fields.get("description"):
    raise SystemExit("Missing skill description")
print("frontmatter ok")
'@

$Temp = New-TemporaryFile
try {
  Set-Content -LiteralPath $Temp -Value $CheckScript -Encoding UTF8
  & $Python.Source $Temp $SkillDir
} finally {
  Remove-Item -LiteralPath $Temp -Force
}

$PyFiles = Get-ChildItem -Path (Join-Path $SkillDir "scripts") -Filter "*.py" -File
& $Python.Source -m py_compile @($PyFiles | ForEach-Object { $_.FullName })

Write-Host "Repository validation passed."
