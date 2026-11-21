# Ren'Py phase 0 fixture

This directory is a self-authored compatibility fixture. It contains only the
single `game/script.rpy` file and does not copy Ren'Py source, SDK files, or
third-party assets into the SuiYu repository.

## Expected behavior

The script starts at `label start`, displays the exact line
`SuiYu phase 0 fixture`, and then returns to the caller. The fixture has no
custom screens, images, audio, fonts, or persistent data.

## SDK verification

Run this fixture from a disposable directory outside the repository with a
fixed official Windows SDK. Set these variables in PowerShell 7:

```powershell
$RenpySdk = 'C:\path\to\renpy-8.6.1-sdk'
$FixtureProject = 'C:\path\to\phase0-fixture'
$FixtureSaveDir = 'C:\path\to\phase0-save'
$RenpyExe = Join-Path $RenpySdk 'renpy.exe'
& $RenpyExe $FixtureProject lint
& $RenpyExe $FixtureProject run --savedir $FixtureSaveDir
```

Copy only this fixture's `game` directory into `$FixtureProject` before
running the commands. Record the SDK archive URL, SHA-256, SDK-reported
version, command exit codes, and the disposable paths in
`docs/development/phase0-verification.md`; replace user-specific path
segments with variables in committed records.

## Desktop acceptance

With a Windows desktop session, launch the same project with the fixed SDK.
Confirm that the title screen starts, the exact fixture text is visible, the
next/continue action reaches the end of the script, and the window closes
normally. The repository currently contains no SDK archive or desktop run
evidence, so this acceptance remains **未验证** until a maintainer records
the actual run.
