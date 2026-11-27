# 阶段 01 兼容性行为文档写作约定

> 记录日期：2026-11-22（Asia/Shanghai）
> 适用范围：`docs/compatibility/` 下阶段 01 全部行为文档。
> 事实源：本目录 `PHASE01_IMPLEMENTATION_PLAN_TREE.md` §0 的实测结论。

本文件规定行为文档必须写什么、证据必须放哪里、轨迹必须长什么样、复验必须怎么执行。不符合本约定的文档视为未完成。

## 1. 固定对照坐标

| 项目 | 值 |
| --- | --- |
| Ren'Py SDK | `8.6.1`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb` |
| Ren'Py upstream tag | `8.6.1.26111705` |
| 对照提交 | `de379eb4f85a4930244786c715e581a1cb3fd374` |
| 平台 | Windows 11 x64；PowerShell 7 |

任一坐标变化都必须新增补证记录，不得覆盖旧记录。

## 2. 每份行为文档的必备字段

每份 `<feature>.md` 必须包含以下七个小节，标题保持一致：

1. **环境**：SDK 指纹、对照提交、平台、命令入口。
2. **上游代码路径与符号**：Ren'Py 源码路径 + 符号名，指到文件与函数/类，例如
   `renpy/execution.py:Context.call`。结论必须能顺着这行找到实现。
3. **fixture**：fixture 目录相对路径、testcase 名、运行命令。
4. **输入序列**：testcase 中触发的操作序列（`advance`、`click`、`run`、`screenshot`）。
5. **预期 vs 实际观察**：预期写明语义，实际给出 `evidence/<id>/actual.jsonl` 中的关键记录与截图清单。
6. **限制**：不可复现、未覆盖、依赖 GUI 人工观察的部分，逐条列出。
7. **目标兼容等级**：`必须兼容` / `允许不同` / `暂不支持`，并给出一句理由。

另需一节 **自动轨迹 vs 人工观察**，明确哪些结论来自 JSONL/截图，哪些尚未人工确认。

## 3. 事件记录格式（JSONL）

轨迹文件为 JSON Lines：每行一个 JSON 对象，键排序，UTF-8。记录种类：

| `kind` | 字段 | 含义 |
| --- | --- | --- |
| `stmt` | `node`,`file`,`line`,`who`,`what`,`ret`（`Label` 另有 `label`） | 执行到某语句节点。`ret` 为 `len(return_stack)` |
| `label` | `label`,`abnormal` | 进入某非 `_` 前缀 label |
| `value` / `marker` / 自定义 | 任意 | fixture 主动记录的状态快照 |
| `screenshot` | `name`,`present`,`bytes`,`sha256` | 截图元数据，PNG 本体不进仓库 |

约束：

- `file` 只允许 `game/` 下且非 `zz_evidence.rpy` 的文件，Ren'Py 自带 `common/` 轨迹一律排除。
- 记录顺序必须可复现；同一 fixture 连续 3 次运行 `actual.jsonl` 需逐字节一致。
- `actual.jsonl` 是**冻结基线**：首次人工审定后提交；后续变化先看 `expected.jsonl` 是否命中，再看是否属预期内的 Ren'Py 变更。
- `expected.jsonl` 是**人工撰写的语义预期**，只列关键记录，语句形状与 `actual.jsonl` 相同。检查脚本要求 `expected` 中每条记录按顺序出现在 `actual` 中（子序列匹配），因此它既是可读规格，也是可执行断言。

## 4. fixture 目录规范

```text
compatibility-tests/fixtures/renpy/phase01/<fixture-id>/
└── game/
    ├── script.rpy        # 纯剧情脚本，含必需的最小 say/choice 屏
    └── zz_evidence.rpy   # 与 harness/zz_evidence.rpy 逐字节一致
```

规则：

- `<fixture-id>` 形如 `p01-02-call-return`，全小写、短横线分隔，前缀为任务号。
- `zz_evidence.rpy` 必须是 `harness/zz_evidence.rpy` 的逐字节副本（检查脚本强制校验），以保证 fixture 自包含、单独可跑。
- 需要图像时用 `image x = Solid("#rrggbb", xysize=(w,h))` 内联定义，不引入二进制素材。
- 需要音频时使用仓库内小体积 OGG，并在文档登记来源为“ffmpeg 生成的定长正弦波，自编素材”。
- 需要自定义 `say`/`choice` 屏时写在 `script.rpy` 内，保持最小、稳定。

## 5. testcase 写法契约（实测结论）

```renpy
testsuite global:
    setup:
        $ _test.timeout = 20.0
        $ _test.screenshot_directory = "shots"
        $ _test.overwrite_screenshots = True
    teardown:
        exit

testcase <name>:
    $ arm()                      # 开始录制，清空 previous
    run Jump("start")            # 从 start 进入，跳过主菜单
    advance until screen "say"   # 稳健等待，避免首行竞态
    screenshot "<name>"
    $ shot("<name>")             # 截图元数据
    ...
    $ disarm()                   # 停止录制，排除 teardown 噪声
    exit                         # 用例结束，通过时进程退出码 0
```

必须遵守的实测约束：

- **`exit` 必须紧跟 `click`，中间不得插 `advance`**，否则用例挂起直到 timeout。
- **`advance until eval <flag>` 需要下一次交互才生效**。纯 Python 赋值后若没有后续交互，会触发 `Possible infinite loop`。要么在 flag 置位后继续推进到下一个 `say`，要么改用 `advance until screen "say"`。
- `_test.overwrite_screenshots = True` 必须为真，否则第二次运行会尝试与旧 PNG 做像素比较而非覆盖。
- harness 的 `import renpy` 只能出现在函数体内。

## 6. 产物隔离位置

- SDK 本体与解压目录：仓库外临时目录，由环境变量 `SUIYU_RENPY_SDK` 或 `-RenpySdk` 指定。
- 运行期一次性项目副本、`--savedir`、截图 PNG、临时日志：全部写入仓库外临时目录，由检查脚本创建并清理。
- 仓库内只保留：fixture 源码、`evidence/<id>/actual.jsonl`、`expected.jsonl`、`run.log`。截图元数据（name/present/bytes/sha256）内嵌于 `actual.jsonl`，不单独提交清单文件，也不提交 PNG 本体。

## 7. 复验命令

单 fixture 手工复验（Windows PowerShell 7，路径用变量）：

```powershell
$RenpySdk   = $env:SUIYU_RENPY_SDK
$Fixture    = '<repo>/compatibility-tests/fixtures/renpy/phase01/<fixture-id>'
$Work       = Join-Path $env:TEMP ('p01-' + [guid]::NewGuid().ToString('N'))
$Project    = Join-Path $Work 'project'
$SaveDir    = Join-Path $Work 'saves'
$Evidence   = Join-Path $Work 'actual.jsonl'
New-Item -ItemType Directory -Path $Project -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $Fixture 'game') -Destination $Project -Recurse
$env:SUIYU_EVIDENCE = $Evidence
& (Join-Path $RenpySdk 'renpy.exe') $Project lint --error-code
& (Join-Path $RenpySdk 'renpy.exe') $Project test <testcase> --savedir $SaveDir
Compare-Object (Get-Content $Evidence) (Get-Content '<repo>/docs/compatibility/evidence/<id>/actual.jsonl')
Remove-Item -LiteralPath $Work -Recurse -Force
```

全量复验：

```powershell
pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk $env:SUIYU_RENPY_SDK
```

## 8. 兼容等级判定

| 等级 | 判定标准 |
| --- | --- |
| 必须兼容 | 语义可被自动轨迹稳定复现，且新引擎必须与 Ren'Py 一致才能运行现有剧本 |
| 允许不同 | 语义可复现，但表现层（时序、视觉细节、实现手段）不要求逐字节相同 |
| 暂不支持 | 边界复杂（screen 语言、ATL、嵌入 Python 全量），阶段 01 只界定可静态识别的子集并列出待研究问题 |

等级必须链接证据文件；无证据不得写等级。

## 9. 分歧与复测

若同一行为在不同运行或机器上出现差异，必须在文档 **限制** 与 **复测条件** 中记录：

- 差异现象、出现条件；
- 判定为“允许不同”还是“需复测”；
- 复测所需环境与命令。

不得用“已修复”代替复测记录。