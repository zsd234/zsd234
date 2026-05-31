param(
  [Parameter(Mandatory = $true)]
  [string]$TemplatePptx,

  [string]$SourceDocument,

  [string]$ContentJson,

  [string]$Workspace,

  [ValidateSet("classroom", "executive", "minimal")]
  [string]$AnimationMode = "classroom",

  [ValidateSet("classroom", "report")]
  [string]$DeliveryMode = "classroom"
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SkillDir = Join-Path $RepoRoot "skills\ppt-template-deck-builder"
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
  throw "Python was not found on PATH."
}

if (-not (Test-Path $TemplatePptx)) {
  throw "Template PPTX not found: $TemplatePptx"
}

if (-not $Workspace) {
  $Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
  $Workspace = Join-Path $RepoRoot "outputs\run-$Stamp"
}
New-Item -ItemType Directory -Force $Workspace | Out-Null

$ModelJson = Join-Path $Workspace "template_model.json"
$SemanticsJson = Join-Path $Workspace "template_semantics.json"
$OutlineJson = Join-Path $Workspace "content_outline.json"
$PlanJson = Join-Path $Workspace "final_slide_plan.json"
$AnimationJson = Join-Path $Workspace "animation_plan.json"
$QaJson = Join-Path $Workspace "qa_report.json"

& $Python.Source (Join-Path $SkillDir "scripts\extract_template_model.py") $TemplatePptx --out $ModelJson --pretty
& $Python.Source (Join-Path $SkillDir "scripts\classify_template_semantics.py") $ModelJson --out $SemanticsJson --pretty

if ($SourceDocument) {
  if (-not (Test-Path $SourceDocument)) {
    throw "Source document not found: $SourceDocument"
  }
  & $Python.Source (Join-Path $SkillDir "scripts\extract_document_logic.py") $SourceDocument --out $OutlineJson --pretty
  $ContentInput = $OutlineJson
} elseif ($ContentJson) {
  if (-not (Test-Path $ContentJson)) {
    throw "Content JSON not found: $ContentJson"
  }
  $ContentInput = $ContentJson
} else {
  $ContentInput = Join-Path $RepoRoot "examples\content.example.json"
}

& $Python.Source (Join-Path $SkillDir "scripts\build_deck_plan.py") $ContentInput $SemanticsJson --out $PlanJson --pretty
& $Python.Source (Join-Path $SkillDir "scripts\build_animation_plan.py") $PlanJson --mode $AnimationMode --out $AnimationJson --pretty
& $Python.Source (Join-Path $SkillDir "scripts\qa_deck_plan.py") $PlanJson --animation-plan $AnimationJson --delivery-mode $DeliveryMode --out $QaJson --pretty

Write-Host "Done. Artifacts written to:"
Write-Host (Resolve-Path $Workspace)
