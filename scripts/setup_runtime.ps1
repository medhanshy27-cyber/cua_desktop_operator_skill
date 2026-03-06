param(
  [string]$Python = "python",
  [switch]$SkipDeps,
  [switch]$InstallToCodex,
  [string]$InstallDir = "",
  [string]$CodexSkillDir = "$env:USERPROFILE\.codex\skills\cua_desktop_operator_skill"
)

function Resolve-DesktopOperatorRoot {
  param([string]$StartDir)

  if ($env:DESKTOP_OPERATOR_ROOT) {
    $envRoot = $env:DESKTOP_OPERATOR_ROOT
    if ((Test-Path (Join-Path $envRoot "desktop_operator_core")) -and (Test-Path (Join-Path $envRoot "desktop_operator_mcp"))) {
      return (Resolve-Path $envRoot).Path
    }
  }

  $cursor = (Resolve-Path $StartDir).Path
  for ($i = 0; $i -lt 8; $i++) {
    if ((Test-Path (Join-Path $cursor "desktop_operator_core")) -and (Test-Path (Join-Path $cursor "desktop_operator_mcp"))) {
      return $cursor
    }
    $parent = Split-Path -Parent $cursor
    if (-not $parent -or $parent -eq $cursor) {
      break
    }
    $cursor = $parent
  }

  throw "Could not locate desktop operator project root."
}

$skillRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$projectRoot = Resolve-DesktopOperatorRoot -StartDir $skillRoot

if (-not $SkipDeps) {
  & $Python -m pip install -r (Join-Path $projectRoot "desktop_operator_mcp\requirements.txt")
  if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
  }
}

$resolvedInstallDir = ""
if ($InstallDir) {
  $resolvedInstallDir = $InstallDir
} elseif ($InstallToCodex) {
  $resolvedInstallDir = $CodexSkillDir
}

if ($resolvedInstallDir) {
  New-Item -ItemType Directory -Force -Path $resolvedInstallDir | Out-Null
  $dirCopies = @(
    @{ Source = (Join-Path $skillRoot "agents"); Destination = (Join-Path $resolvedInstallDir "agents") },
    @{ Source = (Join-Path $skillRoot "references"); Destination = (Join-Path $resolvedInstallDir "references") },
    @{ Source = (Join-Path $skillRoot "scripts"); Destination = (Join-Path $resolvedInstallDir "scripts") },
    @{ Source = (Join-Path $projectRoot "desktop_operator_core"); Destination = (Join-Path $resolvedInstallDir "desktop_operator_core") },
    @{ Source = (Join-Path $projectRoot "desktop_operator_mcp"); Destination = (Join-Path $resolvedInstallDir "desktop_operator_mcp") }
  )

  Copy-Item -Force (Join-Path $skillRoot "SKILL.md") (Join-Path $resolvedInstallDir "SKILL.md")
  foreach ($copy in $dirCopies) {
    if (Test-Path $copy.Destination) {
      Remove-Item -Recurse -Force $copy.Destination
    }
    New-Item -ItemType Directory -Force -Path $copy.Destination | Out-Null
    Copy-Item -Recurse -Force (Join-Path $copy.Source "*") $copy.Destination
  }
}

Write-Host "desktop operator root: $projectRoot"
Write-Host "skill root: $skillRoot"
if ($resolvedInstallDir) {
  Write-Host "installed to: $resolvedInstallDir"
}
