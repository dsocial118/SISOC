param(
    [Parameter(Mandatory = $true)]
    [string]$Slug,
    [string]$Branch,
    [string]$Base = "origin/development",
    [string]$WorktreesRoot,
    [switch]$NoFetch,
    [switch]$Start,
    [switch]$ExposePorts
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "codex_common.ps1")

function ConvertTo-CodexSafeSlug {
    param(
        [string]$Value
    )

    $safe = $Value.Trim().ToLowerInvariant() -replace "[^a-z0-9._-]", "-"
    $safe = $safe.Trim("-")
    if ([string]::IsNullOrWhiteSpace($safe)) {
        throw "El slug no puede quedar vacio."
    }

    return $safe
}

function Get-CodexDefaultWorktreesRoot {
    param(
        [string]$RepoRoot
    )

    $repoParent = Split-Path $RepoRoot -Parent
    if ((Split-Path $repoParent -Leaf) -eq "worktrees") {
        return $repoParent
    }

    return Join-Path $repoParent "worktrees"
}

function Test-CodexGitRefExists {
    param(
        [string]$Ref
    )

    & git show-ref --verify --quiet $Ref
    return $LASTEXITCODE -eq 0
}

$repoRoot = Get-CodexRepoRoot
$safeSlug = ConvertTo-CodexSafeSlug -Value $Slug
if ([string]::IsNullOrWhiteSpace($Branch)) {
    $Branch = "codex/{0}" -f $safeSlug
}

if ([string]::IsNullOrWhiteSpace($WorktreesRoot)) {
    $WorktreesRoot = Get-CodexDefaultWorktreesRoot -RepoRoot $repoRoot
}

$worktreePath = Join-Path $WorktreesRoot $safeSlug
if (Test-Path -LiteralPath $worktreePath) {
    throw ("Ya existe el worktree: {0}" -f $worktreePath)
}

Push-Location $repoRoot
try {
    if (-not $NoFetch) {
        & git fetch origin --prune
    }

    if (Test-CodexGitRefExists -Ref ("refs/heads/{0}" -f $Branch)) {
        throw ("Ya existe la branch local: {0}" -f $Branch)
    }
    if (Test-CodexGitRefExists -Ref ("refs/remotes/origin/{0}" -f $Branch)) {
        throw ("Ya existe la branch remota: origin/{0}" -f $Branch)
    }

    New-Item -ItemType Directory -Force -Path $WorktreesRoot | Out-Null
    & git worktree add -b $Branch $worktreePath $Base
}
finally {
    Pop-Location
}

$bootstrapArgs = @("-NoStart")
if ($Start) {
    $bootstrapArgs = @()
}
if ($ExposePorts) {
    $bootstrapArgs += "-ExposePorts"
}

& powershell -ExecutionPolicy Bypass -File (Join-Path $worktreePath "scripts\ai\codex_bootstrap.ps1") @bootstrapArgs

Write-Host ("Worktree: {0}" -f $worktreePath)
Write-Host ("Branch: {0}" -f $Branch)
Write-Host ("Base: {0}" -f $Base)
