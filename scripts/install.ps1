param(
  [string]$SkillHome
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SourceSkill = Join-Path $RepoRoot "skills\ppt-template-deck-builder"

if (-not (Test-Path $SourceSkill)) {
  throw "Skill folder not found: $SourceSkill"
}

if (-not $SkillHome) {
  if ($env:CODEX_HOME) {
    $SkillHome = Join-Path $env:CODEX_HOME "skills"
  } else {
    $SkillHome = Join-Path $HOME ".codex\skills"
  }
}

New-Item -ItemType Directory -Force $SkillHome | Out-Null

$TargetSkill = Join-Path $SkillHome "ppt-template-deck-builder"
$ResolvedSkillHome = [IO.Path]::GetFullPath($SkillHome)
$ResolvedTarget = [IO.Path]::GetFullPath($TargetSkill)

if (-not $ResolvedTarget.StartsWith($ResolvedSkillHome, [StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to install outside SkillHome: $ResolvedTarget"
}

if (Test-Path $TargetSkill) {
  Remove-Item -LiteralPath $TargetSkill -Recurse -Force
}

Copy-Item -LiteralPath $SourceSkill -Destination $TargetSkill -Recurse

Write-Host "Installed ppt-template-deck-builder to:"
Write-Host $TargetSkill
