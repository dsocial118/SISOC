param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "bootstrap",
        "doctor",
        "up",
        "shell",
        "test",
        "smoke",
        "black-check",
        "black-format",
        "djlint-check",
        "djlint-format",
        "pylint",
        "manage"
    )]
    [string]$Action,
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Args
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "codex_common.ps1")

$repoRoot = Get-CodexRepoRoot

function Invoke-DjangoCommand {
    param(
        [string[]]$CommandArgs,
        [switch]$RequiresMysql,
        [switch]$Interactive
    )

    $bootstrapArgs = @("-NoStart")
    & (Join-Path $PSScriptRoot "codex_bootstrap.ps1") @bootstrapArgs

    if ($RequiresMysql) {
        Invoke-CodexCompose -RepoRoot $repoRoot -Arguments @("up", "-d", "mysql")
        Wait-CodexServiceHealthy -RepoRoot $repoRoot -Service "mysql"
    }

    $composeArgs = @("run", "--rm")
    if (-not $Interactive) {
        $composeArgs += "-T"
    }
    $composeArgs += @("django")
    $composeArgs += $CommandArgs

    Invoke-CodexCompose -RepoRoot $repoRoot -Arguments $composeArgs
}

switch ($Action) {
    "bootstrap" {
        $bootstrapParams = @()
        if ($Args -contains "-NoStart" -or $Args -contains "--no-start") {
            $bootstrapParams += "-NoStart"
        }
        if ($Args -contains "-StartDjango" -or $Args -contains "--start-django") {
            $bootstrapParams += "-StartDjango"
        }
        & (Join-Path $PSScriptRoot "codex_bootstrap.ps1") @bootstrapParams
        break
    }
    "doctor" {
        & (Join-Path $PSScriptRoot "codex_doctor.ps1")
        break
    }
    "up" {
        & (Join-Path $PSScriptRoot "codex_bootstrap.ps1")
        break
    }
    "shell" {
        Invoke-DjangoCommand -CommandArgs @("bash") -RequiresMysql -Interactive
        break
    }
    "test" {
        $targetArgs = if ($Args) { $Args } else { @("-n", "auto") }
        Invoke-DjangoCommand -CommandArgs (@("pytest") + $targetArgs)
        break
    }
    "smoke" {
        Invoke-DjangoCommand -CommandArgs @("pytest", "-m", "smoke")
        break
    }
    "black-check" {
        $targetArgs = if ($Args) { $Args } else { @(".", "--config", "pyproject.toml") }
        Invoke-DjangoCommand -CommandArgs (@("black", "--check") + $targetArgs)
        break
    }
    "black-format" {
        $targetArgs = if ($Args) { $Args } else { @(".", "--config", "pyproject.toml") }
        Invoke-DjangoCommand -CommandArgs (@("black") + $targetArgs)
        break
    }
    "djlint-check" {
        $targetArgs = if ($Args) { $Args } else { @(".", "--configuration=.djlintrc") }
        Invoke-DjangoCommand -CommandArgs (@("djlint") + $targetArgs + @("--check"))
        break
    }
    "djlint-format" {
        $targetArgs = if ($Args) { $Args } else { @(".", "--configuration=.djlintrc") }
        Invoke-DjangoCommand -CommandArgs (@("djlint") + $targetArgs + @("--reformat"))
        break
    }
    "pylint" {
        if (-not $Args) {
            throw "pylint requiere al menos una ruta de archivo."
        }
        Invoke-DjangoCommand -CommandArgs (@("pylint") + $Args + @("--rcfile=.pylintrc"))
        break
    }
    "manage" {
        if (-not $Args) {
            throw "manage requiere argumentos para manage.py."
        }
        $requiresMysqlCommands = @(
            "makemigrations",
            "migrate",
            "showmigrations",
            "dbshell",
            "createsuperuser",
            "loaddata",
            "dumpdata"
        )
        $requiresMysql = $requiresMysqlCommands -contains $Args[0]
        Invoke-DjangoCommand -CommandArgs (@("python", "manage.py") + $Args) -RequiresMysql:$requiresMysql
        break
    }
}
