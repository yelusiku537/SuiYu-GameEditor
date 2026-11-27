# 变量初始化：`define` 与 `default`

## 环境

| 项目 | 值 |
| --- | --- |
| Ren'Py SDK | `renpy-8.6.1-sdk`（Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`） |
| upstream tag | `8.6.1.26111705` |
| 对照提交 | `de379eb4f85a4930244786c715e581a1cb3fd374` |
| 平台 / shell | Windows 11 x64；PowerShell 7 |
| 全量入口 | `pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>` |
| 单 fixture 入口 | `renpy.exe <project> test <testcase> --savedir <dir>`，模板见 `docs/compatibility/README.md` §7 |

## 上游代码路径与符号

路径相对 SDK 根目录。

- `define`
  - `renpy/parser.py:935 define_statement`：解析 `define name = expr`，默认 `create_init` 为真，在 975 行包装成 `ast.Init(loc, [rv], priority + l.init_offset)`。
  - `renpy/ast.py:2480 class Define`；`execute`（2517 行）登记 `define_statements` 并调用 `set()`；`set()`（2541 行）用 `renpy.python.py_eval_bytecode` 求值后写入 store。即表达式在 init 阶段求值一次。
  - `renpy/main.py:483–488`：按优先级遍历 `game.script.initcode` 并 `node.execute_init()`，发生在跳转 `_start` 之前。
- `default`
  - `renpy/parser.py:983 default_statement`：同样在 1010 行把声明包装成 `ast.Init`，因此声明的登记也发生在 init。
  - `renpy/ast.py:2578 class Default`；`execute`（2596 行）把节点加入 `default_statements`；真正的赋值在 `execute_default(start)`（2618 行）。
  - `renpy/exports/statementexports.py:362 execute_default_statement(start=False)` 遍历 `default_statements`；`renpy/common/00start.rpy:209 label _start` 在 215 行调用 `renpy.execute_default_statement(True)`，早于 312 行的 `renpy.jump("start")`。
  - `Default.execute_default` 通过 `_defaults_set` 防重复（2636–2639 行）；`start` 为真时重复给出默认值在 developer 模式会抛异常。
- 读档路径（本证据未执行，仅登记上游坐标）
  - `renpy/loadsave.py:710 load` → 734 行 `log.unfreeze(roots, label="_after_load")`。
  - `renpy/rollback.py:1083 unfreeze` / `1100 unfreeze_core`：先恢复存档 roots，再 `rollback_core(..., on_load=True)`（1142 行）；`rollback_core` 在 1043 行调用 `renpy.exports.execute_default_statement(False)`。即读档恢复到 checkpoint 处的存档状态，默认值只补齐尚未被记录的变量。

## fixture

两套 fixture，同任务号 P01-02。

- `compatibility-tests/fixtures/renpy/phase01/p01-02-define/`
  - `game/script.rpy:13–16`：`define greeting = "hello"`、`define config_value = 42`、`define computed = 6 * 7`、`define char = Character("DefinedChar")`。
  - `label start` 在 19–23 行 `$ emit("define_values", greeting=greeting, config_value=config_value, computed=computed, char_name=char.name)`，24 行 `"define checked"`。
  - testcase：`define_init`。
- `compatibility-tests/fixtures/renpy/phase01/p01-02-default/`
  - `game/script.rpy:13–16`：`default points = 0`、`default named = "unset"`、`default listed = []`，以及 `default allow_mutation = False`（默认关闭，使启动时自动进入 `start` 的 ambient pass 只读默认值、不改写它们）。
  - `label start`：19 行 `$ emit("default_initial", ...)`；20 行 `if allow_mutation:`；21–28 行在被 testcase 打开开关后才执行改写——`points = 5`、`named = "changed"`、`listed.append("x")`、`$ emit("default_mutated", ...)`、`$ renpy.save("default_slot")`、`points = 99`、`named = "after-save"`、`$ emit("default_after_save", ...)`；29 行 `"checkpoint line"`；30 行 `$ finish()`。
  - testcase：`default_lifecycle`（`run.log` 写明 `testcases: default_lifecycle`），在 `arm()` 后设置 `$ store.allow_mutation = True` 再 `run Jump("start")`。fixture 另定义 `label mutation` 与 `label after_load` 及 `testcase default_after_load`，但不在本证据运行范围内。

## 输入序列

`define_init`：

```text
$ arm()
run Jump("start")
advance until screen "say"
advance
$ disarm()
exit
```

`default_lifecycle`：

```text
$ arm()
$ store.allow_mutation = True
run Jump("start")
advance until screen "say"
$ emit("test_barrier", points=store.points)
advance
$ disarm()
exit
```

## 预期 vs 实际观察

### `define`

语义预期：`define` 的表达式在 init 阶段求值并写入 store；进入 `start` 时值已就绪，`6 * 7` 应得到 42。

实际（`docs/compatibility/evidence/02-define/actual.jsonl`，`run.log` 记 `total_records: 7`、`lint_exit: 0`）：

```json
{"file": "game/script.rpy", "kind": "stmt", "label": "start", "line": 18, "node": "Label", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 19, "node": "Python", "ret": 0, "what": null, "who": null}
{"char_name": "DefinedChar", "computed": 42, "config_value": 42, "greeting": "hello", "kind": "define_values"}
{"file": "game/script.rpy", "kind": "stmt", "line": 24, "node": "TranslateSay", "ret": 0, "what": "define checked", "who": null}
{"kind": "flow_complete"}
```

`define_values` 同时给出四个值：`greeting="hello"`、`config_value=42`、`computed=42`（`6 * 7` 已求值，不是字符串）、`char_name="DefinedChar"`（`Character.name` 可读）。init 本身不在轨迹里（`arm()` 之后才开始录），但值在 `start` 首条 Python 即可见，符合“init 阶段完成求值与赋值”。

### `default`

语义预期：`default` 声明在首次进入游戏时把变量初始化为声明的表达式（`0`、`"unset"`、`[]`），随后 `start` 才读它们；同一 pass 内的显式赋值覆盖默认值，并随存档保存。

实际（`docs/compatibility/evidence/02-default/actual.jsonl`，`run.log` 记 `total_records: 19`、`lint_exit: 0`）：

```json
{"kind": "default_initial", "listed": [], "named": "unset", "points": 0}
{"kind": "default_mutated", "listed": ["x"], "named": "changed", "points": 5}
{"kind": "default_after_save", "named": "after-save", "points": 99}
{"kind": "test_barrier", "points": 99}
{"file": "game/script.rpy", "kind": "stmt", "line": 29, "node": "TranslateSay", "ret": 0, "what": "checkpoint line", "who": null}
{"kind": "flow_complete"}
```

`expected.jsonl`（人工语义断言）为：

```json
{"kind": "default_initial", "listed": [], "named": "unset", "points": 0}
{"kind": "default_mutated", "listed": ["x"], "named": "changed", "points": 5}
{"kind": "default_after_save", "named": "after-save", "points": 99}
{"kind": "test_barrier", "points": 99}
{"kind": "flow_complete"}
```

读数：

- `default_initial` 是干净首启值 `points=0`、`named="unset"`、`listed=[]`：`allow_mutation` 默认为 `False`，启动时自动进入 `start` 的 ambient pass 只读默认值，不会改写 store；testcase 在 `arm()` 后打开 `allow_mutation` 再重跑 `start`，被录制的 pass 因此仍从干净默认值开始。
- `default_mutated` 证明显式赋值覆盖默认值：`points 0→5`、`named "unset"→"changed"`、`listed []→["x"]`。
- `default_after_save` 在 25 行存档之后、29 行交互 checkpoint 之前取值，为 `points=99`、`named="after-save"`；随后 `test_barrier` 在 checkpoint 处复核 `store.points` 仍为 99，说明 checkpoint 前的 Python 改写已生效。
- 本轨迹**没有执行读档**：`default_after_save` 是存档之后继续改写的结果，不是 load 回放；`_after_load` label 未出现。读档“从 checkpoint 恢复并补齐默认值”的语义只能从上游路径（`loadsave.py:710/734`、`rollback.py:1043/1142`）确认，见“限制”。

## 自动轨迹 vs 人工观察

- 全部结论来自 JSONL：`define_values` 的四个值、`default_initial`/`default_mutated`/`default_after_save`、`test_barrier`、语句行号。
- 人工观察：**无**。没有人工打开游戏核对变量面板或存档界面；也未逐字段核对 `Character.name` 的显示效果。
- 复测条件：更换 SDK/提交、修改两个 `script.rpy`、`zz_evidence.rpy` 或 testcase 后，用 README §7 单 fixture 命令或 `phase01-check.ps1` 重跑。`allow_mutation` 守卫一旦被移除，`default_initial` 会退回污染值并导致 `expected.jsonl` 的数值断言失败，届时必须重新处理取证手法而不是放宽断言。

## 限制

1. **ambient pass 与测试 pass 的隔离靠 `allow_mutation` 开关**：Ren'Py 启动时会在 testcase 之前自动进入一次 `label start`（`00start.rpy:310–312` 的 `renpy.jump("start")`）。若 `start` 无条件改写默认变量，录制时 store 已被污染（`arm()` 只截断**文件**，不清空 store，见 `zz_evidence.rpy:52–57`）。本 fixture 用默认关闭的 `allow_mutation` 让 ambient pass 只读、测试 pass 才改写，从而得到干净首启值。这是 fixture 的取证手法，不代表 Ren'Py 对“同一进程二次进入 start”有任何自动重置语义。
2. `02-define` 与 `02-default` 都未记录 init 语句本身（录制在 `arm()` 后才开启），所以“init 早于 start”由值可见性与上游 `main.py:483` / `00start.rpy:215` 共同支撑，不是轨迹直接观测。
3. `02-default` 未运行读档：fixture 中的 `mutation`、`after_load` 与 `testcase default_after_load` 不在 `run.log` 的 `testcases` 里。跨进程存档/读档语义由 `03-save-load` 单独覆盖，不在本文证据内。
4. 未覆盖：`define` 的 `+=`/`|=`/索引赋值、`store.` 命名空间、`default` 重复赋值抛错（developer 模式）、特殊命名空间 `default`。
5. `char_name` 来自 `Character.name`，未验证 `Character` 的其他属性或显示层行为。

## 目标兼容等级

**必须兼容**：`define` 于 init 求值、`default` 于 start 前初始化并由显式赋值覆盖，均以 `define_values` 与 `default_mutated`/`default_after_save` 的可执行断言稳定复现，现有剧本依赖该语义才能在启动时拿到正确值。证据：`docs/compatibility/evidence/02-define/actual.jsonl`、`docs/compatibility/evidence/02-default/actual.jsonl`、各自 `expected.jsonl` 与 `run.log`。