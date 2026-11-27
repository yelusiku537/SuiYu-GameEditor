# 启动链：boot → 编译 → init → main menu → `start`

## 环境

| 项目 | 值 |
| --- | --- |
| Ren'Py SDK | `renpy-8.6.1-sdk`（Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`） |
| upstream tag | `8.6.1.26111705` |
| 对照提交 | `de379eb4f85a4930244786c715e581a1cb3fd374` |
| 平台 / shell | Windows 11 x64；PowerShell 7 |
| 全量入口 | `pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>` |
| 单 fixture 入口 | `renpy.exe <project> test startup_reach --savedir <dir>`，模板见 `docs/compatibility/README.md` §7 |
| 结构证据入口 | `renpy.exe <project> compile`；`renpy.exe <project> run --json-dump <file>` |
| 证据目录 | [`evidence/01-startup/`](evidence/01-startup/)（`actual.jsonl`、`expected.jsonl`、`run.log`、`structural.json`） |

`run.log` 记录的引擎版本为 `8.6.1.26111705`，`lint_exit: 0`；`structural.json` 的 `engine_sdk` 为 `renpy-8.6.1-sdk`，但其 `engine_version_reported` 为 `null`（仅未填写，见“限制”）。

## 上游代码路径与符号

路径均相对 SDK 根目录（`renpy-8.6.1-sdk/`）。启动链按执行顺序如下。

| 阶段 | 上游坐标 | 语义 |
| --- | --- | --- |
| boot | `renpy/bootstrap.py:359 bootstrap`；同文件 `:554` 调用 `renpy.main.main()` | 进程入口完成参数解析、basedir 解析后进入主函数 |
| 主函数 | `renpy/main.py:311 main` | 加载脚本、init、建立界面、进入运行循环 |
| 编译 / 加载 | `renpy/script.py:420 Script.load_script`，由 `renpy/main.py:409` 调用 | 读取或编译 `game/*.rpy`，生成 `game/*.rpyc` 与 `game/cache/*.rpyb` |
| init 排序 | `renpy/script.py:458 initcode.sort(key=lambda i: i[0])`；`:718–719` 收集 `(priority, node)` | 所有 `Init` 节点按 priority 升序排列 |
| init 执行 | `renpy/main.py:483–488` 遍历 `game.script.initcode` 调 `node.execute_init()` | init 在脚本正式启动前执行；`renpy/ast.py:1095 class Init` |
| 进入起点 | `renpy/main.py:111–116`：`has_label("_start")` 为真则 `goto_label("_start")` | 存在 `_start` 时以 `_start` 而非 `start` 为真正起点 |
| `_start` | `renpy/common/00start.rpy:209 label _start` | 系统启动 label |
| default | `renpy/common/00start.rpy:215 renpy.execute_default_statement(True)` | 在跳到 `start` 之前执行默认值初始化 |
| 主菜单 | `renpy/common/00start.rpy:298 label _invoke_main_menu`；`:305 call_in_new_context("_main_menu")`；`:316 label _main_menu` | 进入独立上下文的 `_main_menu` |
| 跳到 start | `renpy/common/00start.rpy:312 renpy.jump("start")` | 主菜单返回后进入剧本 `start` |
| 源码地图 | `renpy/arguments.py:169 --json-dump`；`renpy/dump.py:63 dump`，由 `renpy/main.py:537` 调用 | `run --json-dump` 写出 `location.label/define/screen` 映射 |
| 编译命令 | `renpy/arguments.py:316`（`compile` 分支）与 `:329 register_command("compile", compile)` | 单独执行编译并落盘产物 |

priority 的来源：`renpy/parser.py:1152 init_statement` 把 `init [N] python:` 解析为 priority `N`（缺省 0）的 `Init`；`:934 define_statement` 与 `:983 default_statement` 在 `create_init` 时包成 `ast.Init(loc, [rv], priority + l.init_offset)`（缺省 0）。因此 `define`/`default` 与 `init python:` 同处 priority 0，`init 100 python:` 为 priority 100。

注意：`main.py:111–116` 的 `goto_label("_start")` 发生在 `run()` 之内（`main.py:57`），即每个 pass 都会从 `_start` 重新走一次 default 与主菜单分支，这也是 harness `finish()` 注释所说的“脚本 return 后 Ren'Py 会再次进入 `label start`”的上游原因。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-01-startup/`
- `game/script.rpy`：
  - 第 9 行定义最小 `screen say(who, what)`（`window`+`vbox`+`text id "who"/"what"`），不依赖 GUI 模板。
  - 第 18 行 `define startup_marker = "defined"`；第 19 行 `define startup_order = []`（同 priority 0，文件序在前）。
  - 第 21–22 行 `init python:` 中 `startup_order.append("init_default")`（priority 0）。
  - 第 24–25 行 `init 100 python:` 中 `startup_order.append("init_100")`（priority 100）。
  - 第 27–34 行 `label start:`：28 行 `$ emit("startup_state", marker=..., order=..., has_start=renpy.has_label("start"))`；32 行 `"startup chain reached start"`；33 行 `$ finish()`；34 行 `return`。
- `game/zz_evidence.rpy` 为 `harness/zz_evidence.rpy` 的逐字节副本（检查脚本 `Assert-HarnessCopies` 强制校验）。
- testcase：`startup_reach`（`run.log` 记 `testcases: startup_reach`）。
- 证据：[`actual.jsonl`](evidence/01-startup/actual.jsonl)、[`expected.jsonl`](evidence/01-startup/expected.jsonl)、[`run.log`](evidence/01-startup/run.log)、[`structural.json`](evidence/01-startup/structural.json)。

## 输入序列

`startup_reach`：

```text
$ arm()
run Jump("start")
advance until screen "say"
screenshot "startup_at_start"
$ shot("startup_at_start")
advance
exit
```

`arm()` 之后才开始写 JSONL（`zz_evidence.rpy:52–57` 截断文件并置 `armed=True`），因此轨迹起点是 `start`，看不到 boot/compile/init。`run Jump("start")` 是 README §5 约定的“从 start 进入、跳过主菜单”写法。结构面另跑两条命令取得编译产物与源映射：

```text
renpy.exe <project> compile
renpy.exe <project> run --json-dump <file>
```

## 预期 vs 实际观察

### 语义预期（`expected.jsonl` 有序子序列断言）

1. 到达非 `_` 前缀的 `start` 时产生 `kind=label`/`label=start`。
2. `start` 首条 Python 读到的是 init 已完成后的状态：`startup_marker` 已定义、`startup_order` 已按 priority 升序含两项、`renpy.has_label("start")` 为真。
3. 执行到 32 行 say 节点，其文本为 `startup chain reached start`。
4. 流程以 `flow_complete` 结束。

### 游戏内轨迹（`actual.jsonl`，8 条记录，全文）

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "label": "start", "line": 27, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "start"}
{"file": "game/script.rpy", "kind": "stmt", "line": 28, "node": "Python", "ret": 0, "what": null, "who": null}
{"has_start": true, "kind": "startup_state", "marker": "defined", "order": ["init_default", "init_100"]}
{"file": "game/script.rpy", "kind": "stmt", "line": 32, "node": "TranslateSay", "ret": 0, "what": "startup chain reached start", "who": null}
{"bytes": 6108, "kind": "screenshot", "name": "startup_at_start", "present": true, "sha256": "72eddca63a884efaa725030bb36c3cd4fdd82ab56d115c1b9a7521838746249e"}
{"file": "game/script.rpy", "kind": "stmt", "line": 33, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "flow_complete"}
```

读数：

- `Label start`（27 行）与 `label start` 的 `abnormal: true` 同时出现：`run Jump("start")` 经 Jump 进入 label，Jump 置 `context.abnormal`（`renpy/ast.py:1999`），与 `label.md` 的基线一致。
- `startup_state` 是 28 行 `emit` 的快照：`has_start: true` 证明 `start` 标签在正式运行前已注册（编译/加载阶段完成）；`marker: "defined"` 证明 priority 0 的 `define` 已执行；`order: ["init_default", "init_100"]` 证明 priority 0 的 `init python` 先于 priority 100 执行，且 `define startup_order = []` 在同 priority 中先于 append 发生（否则列表会被清空）。这三点共同支撑“init 已全部完成于 `start` 之前”。
- `TranslateSay`（32 行）文本与预期一致；`who: null` 是旁白式引号行。33 行 `Python` 是 `finish()`，它写出 `flow_complete` 后关闭录制（`zz_evidence.rpy:63–72`），所以 `return`（34 行）与之后的重入不在轨迹中。
- 截图记录 `present: true`、`bytes: 6108`、`sha256: 72eddca6…8746249e`；PNG 本体不入仓库。

### 结构面：游戏内看不到的 boot/compile

[`structural.json`](evidence/01-startup/structural.json) 记录编译与源映射，补足录制开始前的阶段：

```json
{
  "compile": {
    "cache_rpyb": ["bytecode-312.rpyb", "py3analysis.rpyb", "screens.rpyb"],
    "exit": 0,
    "rpyc": ["script.rpyc", "zz_evidence.rpyc"]
  },
  "source_map": {
    "define": {"startup_marker": ["game/script.rpy", 18], "startup_order": ["game/script.rpy", 19]},
    "label": {"start": ["game/script.rpy", 27]},
    "screen": {"say": ["game/script.rpy", 9]},
    "transform": {}
  }
}
```

- `compile.exit: 0` 且同时出现 `script.rpyc`、`zz_evidence.rpyc`：两个 `.rpy` 都已编译为 `.rpyc`，即 `Script.load_script` 的产物成立。
- `cache_rpyb` 三项与上游文件名对应：`bytecode-312.rpyb` 是 `renpy/python.py:822` 的 `cache/bytecode-{major}{minor}.rpyb`（Python 3.12 → `312`），`py3analysis.rpyb` 是 `renpy/pyanalysis.py:945`，`screens.rpyb` 是 `renpy/sl2/slast.py:2781`。它们证明 init 前的字节码/分析/屏幕缓存阶段已执行。
- `source_map` 由 `run --json-dump` 按 `renpy/dump.py:125–140` 遍历 `renpy.game.script.namemap` 生成：`label start → game/script.rpy:27`、`define startup_marker → :18`、`startup_order → :19`、`screen say → :9`，与 fixture 行号逐条吻合；`transform` 为空是因为 fixture 未定义 transform。

### 串起来的启动链

| 阶段 | 观测方式 | 结论 |
| --- | --- | --- |
| boot → 主函数 | 仅上游路径（`bootstrap.py:359/554`、`main.py:311`） | 进程进入 `main()`；未被游戏内轨迹捕获 |
| 编译 `.rpy → .rpyc` + `cache/*.rpyb` | `structural.json` 的 `compile` 段 | `compile.exit 0` 且产物齐全 |
| init 按 priority 执行 | `startup_state.order` + `structural.json.source_map` | priority 0 先于 100；`define`/`init` 均在 `start` 前完成 |
| 进入 `_start` → default → main menu → `jump start` | 上游路径（`00start.rpy:209/215/298/305/312`）；游戏内仅有 `start` 之后 | `_start` 被 harness 的 `_` 前缀过滤排除（`zz_evidence.rpy:142–145`），轨迹从 `start` 起；夹具用 `run Jump("start")` 跳过主菜单 |
| `start` 执行 | `actual.jsonl` | `Label start`(27) → `Python`(28) → `startup_state` → `TranslateSay`(32) → `Python`(33) → `flow_complete` |

关键结论：**游戏内轨迹从 `start` 开始，录制在 `arm()` 之后才开启；boot/compile/init 本身没有任何 `stmt` 记录。** 录制前的阶段由两条独立证据支撑：`structural.json` 的编译产物与 `--json-dump` 源映射，以及游戏内 `startup_state` 显示的 init priority 顺序与已注册的 `start`。三者互相印证，但没有一条轨迹直接记录 `_start`、default 或主菜单。

## 自动轨迹 vs 人工观察

- 全部行为结论来自两份自动证据：`actual.jsonl`（游戏内 JSONL）与 `structural.json`（编译产物 + 源映射）；`expected.jsonl` 提供可执行的有序子序列断言，`run.log` 记录 `total_records: 8`、`record_kinds: {"flow_complete":1,"label":1,"screenshot":1,"startup_state":1,"stmt":4}`。
- **未进行任何人工 GUI 观察或像素审查。** `startup_at_start` 只留有元数据（`name`/`bytes`/`sha256`），PNG 未入仓库，因此无法确认 32 行文本的实际字体、排版与位置，也无法确认窗口是否真的显示了该画面。
- 主菜单的实际呈现与“开始游戏”点击均未观察；夹具用 `run Jump("start")` 直接进入 `start`。
- 复测条件：SDK SHA、对照提交、fixture、`zz_evidence.rpy` 或 `scripts/phase01-check.ps1` 任一变化时，重跑 `pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>` 并重新审定基线；`structural.json` 不在该脚本的比对范围内（见“限制”第 3 条），需另跑 `compile` 与 `run --json-dump` 复核。

## 限制

1. **主菜单未观测。** 夹具按 README §5 用 `run Jump("start")` 跳过主菜单；`_invoke_main_menu`、`_main_menu` 的呈现、用户点击与 `00start.rpy:312` 的 `jump("start")` 回跳都不在轨迹中。主菜单语义仅有上游路径支撑。复测条件：新增一个不跳过主菜单的用例（或人工 GUI 记录）后另立补证，不修改本记录。
2. **boot/compile/init 不在游戏内轨迹。** 录制从 `arm()` 开始，`_start` 又被 `_` 前缀过滤，故这些阶段只能由 `structural.json` 与 `startup_state` 间接证明。init 顺序只在 fixture 的两个 priority（0、100）上验证，其他 priority、`init offset` 与多文件间的同优先级顺序未覆盖。
3. **`structural.json` 不由 `phase01-check.ps1` 重新生成。** 该脚本只做 harness 哈希校验、`lint`、`test`、非截图记录逐字节可复现比对与 `expected` 子序列比对（`scripts/phase01-check.ps1:163–241`）；`compile` 与 `run --json-dump` 需在带窗口的会话手工执行。因此全量复验不会自动发现 `structural.json` 过期，且其 `engine_version_reported` 为 `null`。复测条件：SDK 或提交变化时手工重跑这两条命令并替换该文件。
4. **截图仅元数据。** `startup_at_start` 的 6108 字节与 `sha256` 只能证明截图已生成且内容稳定，无法据此判断视觉效果；未做人工像素审查。
5. **未覆盖的启动分支：** `splashscreen`、`config.early_start_store`/`_start_store`、`_gl_test`、`warp`、`RENPY_AUTO_LOAD`/`config.auto_load`、`RENPY_SKIP_MAIN_MENU`、`before_main_menu` 与 `_library_main_menu` 均只在上游路径确认存在，未在本 fixture 断言。
6. **未覆盖的启动依赖：** style 构建（`renpy/main.py:403–404`）、persistent 加载（`renpy/main.py:466`）与 save 目录初始化等发生在 `start` 之前的副作用，未以证据断言；本文只界定“编译产物存在、init 顺序正确、`start` 可达”这一可自动复现的子集。
7. `TranslateSay` 是翻译包装后的节点名，不代表原始 `Say` 类；`who: null` 因 fixture 使用旁白式引号行。

## 目标兼容等级

**必须兼容** — 编译产物（`.rpyc` + `cache/*.rpyb`）、init 按 priority 升序执行、`start` 在 init 完成后可达并由 `run Jump` 稳定进入，均由自动证据复现且现有剧本依赖这些语义才能启动；新引擎必须与 Ren'Py 一致。依据：[`evidence/01-startup/actual.jsonl`](evidence/01-startup/actual.jsonl)、[`expected.jsonl`](evidence/01-startup/expected.jsonl)、[`run.log`](evidence/01-startup/run.log)、[`structural.json`](evidence/01-startup/structural.json)。