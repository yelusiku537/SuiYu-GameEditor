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
normally. The official SDK archive was verified on 2026-11-22 with SHA-256
`596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`.
Local fixture lint and GUI smoke passed. GitHub Actions installs a test-only
say screen that renders `text what id "what"`; when that screen appears, the
smoke reads `renpy.get_widget("say", "what").text` and requires an exact match.
It also records the fixture's `return`, requests a normal window close, and
requires process exit code 0. This stronger CI smoke remains unverified until
the workflow on this revision passes; its run is recorded in
`docs/development/phase0-verification.md`.
