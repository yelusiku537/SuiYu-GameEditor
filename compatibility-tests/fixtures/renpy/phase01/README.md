# Ren'Py phase 01 fixtures

每个子目录是一个自包含 fixture，用于把 Ren'Py 的可观察行为固化成可复验证据。fixture 只含自编脚本、内联 `Solid(...)` 图像与最小的 `say`/`choice` 屏，不复制 Ren'Py 源码、SDK 文件或第三方素材。

## 结构

```text
phase01/
├── harness/zz_evidence.rpy     # 唯一事实源：证据录制钩子
└── <fixture-id>/game/
    ├── script.rpy              # 纯剧情 + 最小屏
    └── zz_evidence.rpy         # harness 的逐字节副本
```

`zz_evidence.rpy` 必须是 `harness/zz_evidence.rpy` 的逐字节副本；检查脚本会校验，以保证任何 fixture 单独拿出来都能跑出证据。

## 单个 fixture 复验

在 Windows PowerShell 7 中，用固定 SDK（`SUIYU_RENPY_SDK` 指向已核验的 `renpy-8.6.1-sdk`）：

```powershell
$Work = Join-Path $env:TEMP ('p01-' + [guid]::NewGuid().ToString('N'))
$Project = Join-Path $Work 'project'
New-Item -ItemType Directory -Path $Project -Force | Out-Null
Copy-Item -LiteralPath './compatibility-tests/fixtures/renpy/phase01/<fixture-id>/game' -Destination $Project -Recurse
$env:SUIYU_EVIDENCE = Join-Path $Work 'actual.jsonl'
& (Join-Path $env:SUIYU_RENPY_SDK 'renpy.exe') $Project lint --error-code
& (Join-Path $env:SUIYU_RENPY_SDK 'renpy.exe') $Project test <testcase> --savedir (Join-Path $Work 'saves')
```

## 全量复验

```powershell
pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk $env:SUIYU_RENPY_SDK
```

写作约定、证据格式与 testcase 约束见 [docs/compatibility/README.md](../../../docs/compatibility/README.md)。