[CmdletBinding()]
param(
    [string]$RenpySdk = $env:SUIYU_RENPY_SDK,
    [string]$SdkArchiveSha256 = '596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb',
    [switch]$KeepWork
)

$ErrorActionPreference = 'Stop'
$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$FixtureRoot = Join-Path $RepoRoot 'compatibility-tests/fixtures/renpy/phase01'
$EvidenceRoot = Join-Path $RepoRoot 'docs/compatibility/evidence'
$HarnessPath = Join-Path $FixtureRoot 'harness/zz_evidence.rpy'

# Fixture id -> testcases (order matters: cross-process save/load shares a savedir).
$Plan = [ordered]@{
    'p01-01-startup'           = @('startup_reach')
    'p01-02-label'             = @('label_entry', 'label_from_start')
    'p01-02-jump'              = @('jump_forward', 'jump_skip')
    'p01-02-call-return'       = @('nested_call', 'call_empty')
    'p01-02-say'               = @('say_forms')
    'p01-02-menu'              = @('menu_choose_b', 'menu_nested')
    'p01-02-define'            = @('define_init')
    'p01-02-default'           = @('default_lifecycle')
    'p01-03-display'           = @('display_ops')
    'p01-03-audio'             = @('audio_lifecycle')
    'p01-03-transitions'       = @('transitions_apply')
    'p01-03-save-load'         = @('save_case', 'load_case')
    'p01-03-rollback'          = @('rollback_restores')
    'p01-03-screen-atl-python' = @('screen_atl_python')
}

function Resolve-RenpyExe {
    param([string]$Sdk)
    if ($Sdk) {
        $exe = Join-Path $Sdk 'renpy.exe'
        if (-not (Test-Path -LiteralPath $exe)) {
            throw "SUIYU_RENPY_SDK is set but does not contain renpy.exe: $Sdk"
        }
        return $exe
    }
    foreach ($candidate in @(
            'D:\temp\renpy-sdk-verified-20261122-root\renpy-8.6.1-sdk',
            (Join-Path $env:TEMP 'renpy-sdk'))) {
        $exe = Join-Path $candidate 'renpy.exe'
        if (Test-Path -LiteralPath $exe) { return $exe }
    }
    throw 'Ren''Py SDK not found. Set -RenpySdk or $env:SUIYU_RENPY_SDK to the verified renpy-8.6.1-sdk directory.'
}

function Assert-HarnessCopies {
    $source = Get-Content -LiteralPath $HarnessPath -Raw
    $sourceHash = (Get-FileHash -LiteralPath $HarnessPath -Algorithm SHA256).Hash
    foreach ($fixture in $Plan.Keys) {
        $copy = Join-Path $FixtureRoot $fixture 'game/zz_evidence.rpy'
        if (-not (Test-Path -LiteralPath $copy)) {
            throw "Fixture '$fixture' is missing game/zz_evidence.rpy"
        }
        $copyHash = (Get-FileHash -LiteralPath $copy -Algorithm SHA256).Hash
        if ($copyHash -ne $sourceHash) {
            throw "Fixture '$fixture' zz_evidence.rpy differs from harness/zz_evidence.rpy"
        }
    }
    return $sourceHash
}

function Invoke-Renpy {
    param(
        [Parameter(Mandatory)] [string]$RenpyExe,
        [Parameter(Mandatory)] [string]$Project,
        [Parameter(Mandatory)] [string[]]$Arguments,
        [string]$LogDirectory
    )
    $stdout = Join-Path $LogDirectory ('stdout-' + [guid]::NewGuid().ToString('N') + '.txt')
    $stderr = Join-Path $LogDirectory ('stderr-' + [guid]::NewGuid().ToString('N') + '.txt')
    $process = Start-Process -FilePath $RenpyExe -ArgumentList (@($Project) + $Arguments) `
        -Wait -PassThru -NoNewWindow -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $text = ''
    if (Test-Path -LiteralPath $stdout) { $text += (Get-Content -LiteralPath $stdout -Raw) }
    if (Test-Path -LiteralPath $stderr) { $text += (Get-Content -LiteralPath $stderr -Raw) }
    return [pscustomobject]@{ Exit = $process.ExitCode; Output = $text }
}

function Test-ValueMatch {
    param($Expected, $Actual)
    if ($null -eq $Expected) { return ($null -eq $Actual) }
    if ($Expected -is [string]) { return ($Expected -eq [string]$Actual) }
    if ($Expected -is [System.Collections.IEnumerable] -and $Expected -isnot [string]) {
        # Arrays match positionally; object elements allow partial keys so a
        # hand-written assertion can name only the fields it cares about.
        $exp = @($Expected)
        $act = @($Actual)
        if ($exp.Count -ne $act.Count) { return $false }
        for ($k = 0; $k -lt $exp.Count; $k++) {
            if (-not (Test-ValueMatch -Expected $exp[$k] -Actual $act[$k])) { return $false }
        }
        return $true
    }
    if ($Expected -is [System.Management.Automation.PSCustomObject]) {
        foreach ($prop in $Expected.PSObject.Properties) {
            if (-not $Actual.PSObject.Properties[$prop.Name]) { return $false }
            if (-not (Test-ValueMatch -Expected $prop.Value -Actual $Actual.($prop.Name))) { return $false }
        }
        return $true
    }
    return ($Expected -eq $Actual)
}

function Test-Subsequence {
    param([object[]]$Actual, [object[]]$Expected)
    $i = 0
    foreach ($want in $Expected) {
        $matched = $false
        while ($i -lt $Actual.Count) {
            $have = $Actual[$i]
            $i++
            $kindOk = (-not $want.PSObject.Properties['kind']) -or ($have.kind -eq $want.kind)
            if (-not $kindOk) { continue }
            $ok = $true
            foreach ($prop in $want.PSObject.Properties) {
                if ($prop.Name -eq 'kind') { continue }
                if (-not $have.PSObject.Properties[$prop.Name]) { $ok = $false; break }
                if (-not (Test-ValueMatch -Expected $prop.Value -Actual $have.($prop.Name))) { $ok = $false; break }
            }
            if ($ok) { $matched = $true; break }
        }
        if (-not $matched) {
            Write-Host "    unmatched expected record: $($want | ConvertTo-Json -Compress -Depth 10)"
            return $false
        }
    }
    return $true
}

$RenpyExe = Resolve-RenpyExe -Sdk $RenpySdk
Write-Host "==> Ren'Py SDK: $RenpyExe"
$version = (& $RenpyExe --version 2>&1 | Select-Object -First 1)
Write-Host "    version: $version"
if ($version -notmatch '8\.6\.1') {
    throw "Expected Ren'Py 8.6.1 SDK, got: $version"
}

$harnessHash = Assert-HarnessCopies
Write-Host "==> Harness copies match (SHA-256 $harnessHash)"

$workRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('suiyu-phase01-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $workRoot -Force | Out-Null
$tempCreated = $true
$failures = New-Object System.Collections.Generic.List[string]

try {
    foreach ($fixture in $Plan.Keys) {
        $evId = $fixture -replace '^p01-', ''
        $fixtureDir = Join-Path $FixtureRoot $fixture
        $evDir = Join-Path $EvidenceRoot $evId
        $project = Join-Path $workRoot ($fixture + '-project')
        $saveDir = Join-Path $workRoot ($fixture + '-saves')
        $actualPath = Join-Path $workRoot ($fixture + '-actual.jsonl')
        New-Item -ItemType Directory -Path $project -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $fixtureDir 'game') -Destination $project -Recurse

        Write-Host "==> $fixture"

        $lint = Invoke-Renpy -RenpyExe $RenpyExe -Project $project -Arguments @('lint', '--error-code') -LogDirectory $workRoot
        if ($lint.Exit -ne 0) {
            $failures.Add("$fixture lint failed (exit $($lint.Exit))")
            Write-Host $lint.Output
            continue
        }

        if (Test-Path -LiteralPath $actualPath) { Remove-Item -LiteralPath $actualPath -Force }
        $env:SUIYU_EVIDENCE = $actualPath
        $caseOk = $true
        foreach ($case in $Plan[$fixture]) {
            $caseEvidence = Join-Path $workRoot ($fixture + '-' + $case + '.jsonl')
            $env:SUIYU_EVIDENCE = $caseEvidence
            $result = Invoke-Renpy -RenpyExe $RenpyExe -Project $project -Arguments @('test', $case, '--savedir', $saveDir) -LogDirectory $workRoot
            $status = 'UNKNOWN'
            foreach ($line in ($result.Output -split "`n")) {
                if ($line -match 'Status:\s*(\S+)') { $status = $Matches[1] }
            }
            if ($result.Exit -ne 0 -or $status -ne 'PASSED') {
                $failures.Add("$fixture/$case failed (exit $($result.Exit), status $status)")
                Write-Host $result.Output
                $caseOk = $false
                continue
            }
            if (Test-Path -LiteralPath $caseEvidence) {
                $content = (@(Get-Content -LiteralPath $caseEvidence) -join "`n")
                if (-not [string]::IsNullOrWhiteSpace($content)) {
                    $normalized = $content.TrimEnd("`n")
                    $existing = ''
                    if (Test-Path -LiteralPath $actualPath) { $existing = ((@(Get-Content -LiteralPath $actualPath)) -join "`n") }
                    $combined = if ([string]::IsNullOrWhiteSpace($existing)) { $normalized } else { $existing.TrimEnd("`n") + "`n" + $normalized }
                    [System.IO.File]::WriteAllText($actualPath, $combined + "`n", (New-Object System.Text.UTF8Encoding($false)))
                }
            }
        }
        Remove-Item Env:SUIYU_EVIDENCE -ErrorAction SilentlyContinue
        if (-not $caseOk) { continue }

        $committedActual = Join-Path $evDir 'actual.jsonl'
        $committedExpected = Join-Path $evDir 'expected.jsonl'
        if (-not (Test-Path -LiteralPath $committedActual)) {
            $failures.Add("$fixture missing committed actual.jsonl")
            continue
        }
        if (-not (Test-Path -LiteralPath $committedExpected)) {
            $failures.Add("$fixture missing committed expected.jsonl")
            continue
        }

        # Reproducibility: every non-screenshot record must be byte-identical. PNG
# bytes vary with GPU/driver, so screenshot records are compared on identity
# (name + present) only, while still requiring the expected set to mention them.
        $reproducedLines = @(@(Get-Content -LiteralPath $actualPath) |
            Where-Object { $_.Trim() } |
            ForEach-Object {
                $r = $_ | ConvertFrom-Json
                if ($r.kind -eq 'screenshot') {
                    "{`"kind`":`"screenshot`",`"name`":`"$($r.name)`",`"present`":$($r.present.ToString().ToLower())}"
                } else { $_ }
            })
        $baselineLines = @(@(Get-Content -LiteralPath $committedActual) |
            Where-Object { $_.Trim() } |
            ForEach-Object {
                $r = $_ | ConvertFrom-Json
                if ($r.kind -eq 'screenshot') {
                    "{`"kind`":`"screenshot`",`"name`":`"$($r.name)`",`"present`":$($r.present.ToString().ToLower())}"
                } else { $_ }
            })
        if (($reproducedLines -join "`n") -ne ($baselineLines -join "`n")) {
            $failures.Add("$fixture actual.jsonl is not reproducible vs committed baseline (excluding screenshot bytes)")
            continue
        }

        $actualRecords = @(Get-Content -LiteralPath $committedActual | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
        $expectedRecords = @(Get-Content -LiteralPath $committedExpected | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json })
        if (-not (Test-Subsequence -Actual $actualRecords -Expected $expectedRecords)) {
            $failures.Add("$fixture expected.jsonl does not match actual.jsonl as an ordered subsequence")
            continue
        }

        Write-Host "    OK ($($actualRecords.Count) records)"
    }
}
finally {
    if ($tempCreated -and (Test-Path -LiteralPath $workRoot)) {
        if ($KeepWork) {
            Write-Warning "Temporary work directory retained: $workRoot"
        } else {
            Remove-Item -LiteralPath $workRoot -Recurse -Force
        }
    }
    Remove-Item Env:SUIYU_EVIDENCE -ErrorAction SilentlyContinue
}

if ($failures.Count -gt 0) {
    Write-Host ''
    Write-Host "Phase 01 checks FAILED:"
    foreach ($f in $failures) { Write-Host "  - $f" }
    exit 1
}

Write-Host ''
Write-Host "Phase 01 checks passed ($($Plan.Count) fixtures)."