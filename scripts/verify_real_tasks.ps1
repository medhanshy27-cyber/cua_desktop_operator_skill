[CmdletBinding(PositionalBinding = $false)]
param(
  [string]$Python = "python",
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$RemainingArgs
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

if ($Python.StartsWith("--")) {
  $RemainingArgs = @($Python) + $RemainingArgs
  $Python = "python"
}

if ($env:PYTHONPATH) {
  $env:PYTHONPATH = "$projectRoot;$env:PYTHONPATH"
} else {
  $env:PYTHONPATH = $projectRoot
}

& $Python (Join-Path $PSScriptRoot "verify_real_tasks.py") @RemainingArgs
