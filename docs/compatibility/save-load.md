# 存档与读档：跨进程状态恢复

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

- 存档
  - `renpy/loadsave.py:214 save`：`:256` `renpy.game.log.freeze(None)` 取 roots（当前 store 根），`:263` 把 `(roots, renpy.game.log)` 一起 dump 进存档，`:308` `location.save(slotname, sr)` 落盘，`:310–311` 重新扫描 slot 并清缓存。
- 槽位存在性
  - `renpy/loadsave.py:693 can_load`：取 `get_cache(filename)` 的 mtime，非零即存在（`:702–707`）。不读取存档内容。
- 读档
  - `renpy/loadsave.py:710 load`：`:718` 读存档、`:730` `call_in_new_context("_before_load")`、`:732` `loads(log_data)` 还原 `(roots, log)`、`:734` `log.unfreeze(roots, label="_after_load")`。docstring 明言成功时不返回，因此其后语句不可达。
- 解冻与回滚
  - `renpy/rollback.py:1083 unfreeze`：先 `can_rollback(0, True)` 确认日志可用，再在 `:1098` 抛 `UnfreezeException`；由 `renpy/execution.py:1103–1105` 在顶层 context 接住并调用 `UnfreezeException.perform_unfreeze`（`renpy/rollback.py:1186–1187`）。
  - `renpy/rollback.py:1100 unfreeze_core`：`:1119–1135` 把存档 roots 逐个写回 store（带 `.` 的归到子 store），`:1142` 调 `rollback_core(0, label=label, greedy=greedy, on_load=True)`。
  - `renpy/rollback.py:939 rollback_core`：`:958` 在 `on_load` 时把任意 `rb.checkpoint` 计入回滚点，`:978–991` greedy 模式继续退到“上一 checkpoint 之后”，`:1006–1007` 对每个被弹出的条目执行 `rb.rollback()`（`renpy/rollback.py:399`，`:424–434` 逐项恢复 store 键值），`:1019–1023` 记录 `come_from` 并在到达该节点时调用 `_after_load`，`:1043` 调 `renpy.exports.execute_default_statement(False)`，`:1049–1050` 用 `context.rollback_copy()` 重建当前上下文。
  - `renpy/execution.py:589 Context.come_from` 与 `:618–621`：到达 `come_from_name` 时执行 `self.call(come_from_label, return_site=node.name)`，因此 `after_load` 以“被 call”的方式进入，返回栈深度为 1。
- 默认值补齐
  - `renpy/exports/statementexports.py:362 execute_default_statement(start=False)` 遍历 `default_statements`；`renpy/ast.py:2618 Default.execute_default` 在 `:2649` 以 `if start or (self.varname not in d.ever_been_changed)` 决定是否写入，因此读档只补齐**未被存档记录**的变量，已有记录不覆盖。
  - `save` 的 roots 只含 `ever_been_changed` 的变量（`renpy/rollback.py:664 get_roots`，`:674–679`）。
- `_after_load` 与自动读档
  - `renpy/common/00start.rpy:106 label _after_load`：`:143–144` `if renpy.has_label("after_load"): jump expression "after_load"`，即用户 `after_load` 在独立上下文中执行。
  - `renpy/common/00start.rpy:241–243`：仅当 `RENPY_AUTO_LOAD` 或 `config.auto_load` 设置且 `can_load` 为真时才自动 `renpy.load`。本 fixture 两者均未设置，`start` 不会自动读档。
- checkpoint 的产生
  - `renpy/character.py:957 renpy.exports.checkpoint(True, hard=checkpoint)` 在 Say/TranslateSay 交互结束时落 checkpoint；`renpy/rollback.py:736 checkpoint` 标记 `checkpoint`/`hard_checkpoint` 并调整 `rollback_limit`。`renpy/execution.py:662` `log.begin`、`:741` `log.complete` 与 `renpy/rollback.py:542/614` 负责每个节点前后的状态差分。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-03-save-load/`
- `game/script.rpy`：
  - `default points = 0`（24 行）、`default stage = "init"`（25 行）、`default resumed = False`（26 行）。
  - `label start`（28 行）：29 行 `"checkpoint line"` → 30 行 `$ points = 3` → 31 行 `$ stage = "pre-save"` → 32 行 `$ renpy.save("slot_a")` → 33 行 `$ emit("save_done", ...)` → 34 行 `"after save line"` → 35 行 `$ points = 99` → 36 行 `$ stage = "mutated"` → 37 行 `$ emit("post_save_mutation", ...)` → 38 行 `"finish line"` → 39 行 `$ finish()` → 40 行 `return`。
  - `label after_load`（42 行）：45 行 `$ emit("after_load_hook", ...)` → 46 行 `$ resumed = True` → 47 行 `return`。
  - `label loader_main`（49 行）：50 行 `$ emit("loader_before", ...)` → 51 行 `$ renpy.load("slot_a")` → 52 行 `$ emit("loader_after", note="unreachable on success")` → 53 行 `return`。
  - `game/zz_evidence.rpy` 为 `harness/zz_evidence.rpy` 的逐字节副本。
- testcase：`save_case`（64–68 行）、`load_case`（70–74 行）。
- 证据：`docs/compatibility/evidence/03-save-load/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`，`testcases: save_case, load_case`，`total_records: 31`，`record_kinds: {"after_load_hook": 1, "label": 3, "loader_before": 1, "post_save_mutation": 1, "save_done": 2, "stmt": 23}`）。
- 两个 testcase 由 `scripts/phase01-check.ps1` 的循环分别以**独立进程**调用，共用同一个 `--savedir`；其单 case 轨迹文件按 `$Plan` 顺序拼接成一份 `actual.jsonl`（`scripts/phase01-check.ps1:173–194`）。因此 `actual.jsonl` 第 1–14 行属于 `save_case`，第 15–31 行属于 `load_case`，两者之间没有分隔标记。

## 输入序列

`save_case`（进程 1）：

```text
$ arm()
run Jump("start")
advance until eval (store.stage == "mutated")
exit
```

`load_case`（进程 2，复用同一 `--savedir`）：

```text
$ arm()
run Jump("loader_main")
advance until eval store.resumed
exit
```

手工复验必须按 `save_case` → `load_case` 的顺序执行（先后关系决定 `slot_a` 是否存在）：

```powershell
& renpy.exe $Project test save_case --savedir $SaveDir
& renpy.exe $Project test load_case  --savedir $SaveDir
```

## 预期 vs 实际观察

语义预期：

1. `renpy.save("slot_a")` 把当时 store（`points=3`、`stage="pre-save"`）连同 rollback log 写入槽位，`can_load` 立即为真。
2. 存档后把 `points` 改成 99 不影响已写入的存档。
3. 新进程里 `renpy.load("slot_a")` 先还原存档状态，再回滚到存档的 checkpoint；引擎在独立上下文执行用户 `after_load`，然后恢复存档流程继续执行。
4. `start` 自身没有任何自动读档逻辑；只有 `loader_main` 显式调用 `renpy.load`。

实际（`docs/compatibility/evidence/03-save-load/actual.jsonl`，31 条记录）。

### `save_case` 段（第 1–14 条）

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "label": "start", "line": 28, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "start"}
{"file": "game/script.rpy", "kind": "stmt", "line": 29, "node": "TranslateSay", "ret": 0, "what": "checkpoint line", "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 30, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 31, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 32, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 33, "node": "Python", "ret": 0, "what": null, "who": null}
{"can_load": true, "kind": "save_done", "points": 3, "stage": "pre-save"}
{"file": "game/script.rpy", "kind": "stmt", "line": 34, "node": "TranslateSay", "ret": 0, "what": "after save line", "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 35, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 36, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 37, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "post_save_mutation", "points": 99, "stage": "mutated"}
{"file": "game/script.rpy", "kind": "stmt", "line": 38, "node": "TranslateSay", "ret": 0, "what": "finish line", "who": null}
```

- 进入 `start` 后依次执行 29–33 行；`save_done` 的 `can_load=True` 证明槽位在 `renpy.save` 之后立刻可见（`loadsave.py:693` 只看 mtime），`points=3`、`stage="pre-save"` 是存档时刻的 store 值。
- 存档后继续执行 35–37 行，`post_save_mutation` 记录 `points=99`、`stage="mutated"`。这证明“存档之后的变更”发生在存档完成之后；轨迹本身不包含它被写入 `slot_a` 的任何记录。
- 轨迹止于 38 行 `"finish line"`：`save_case` 的条件 `store.stage == "mutated"` 已满足，testcase 随即 `exit`，39 行 `$ finish()` 未执行，因此本 fixture 的两段轨迹都**没有** `flow_complete`。

### `load_case` 段（第 15–31 条）

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "label": "loader_main", "line": 49, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "loader_main"}
{"file": "game/script.rpy", "kind": "stmt", "line": 50, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "loader_before", "points": 0, "stage": "init"}
{"file": "game/script.rpy", "kind": "stmt", "line": 51, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "label": "after_load", "line": 42, "node": "Label", "ret": 1, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "after_load"}
{"file": "game/script.rpy", "kind": "stmt", "line": 45, "node": "Python", "ret": 1, "what": null, "who": null}
{"kind": "after_load_hook", "points": 0, "stage": "init"}
{"file": "game/script.rpy", "kind": "stmt", "line": 46, "node": "Python", "ret": 1, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 47, "node": "Return", "ret": 1, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 30, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 31, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 32, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 33, "node": "Python", "ret": 0, "what": null, "who": null}
{"can_load": true, "kind": "save_done", "points": 3, "stage": "pre-save"}
{"file": "game/script.rpy", "kind": "stmt", "line": 34, "node": "TranslateSay", "ret": 0, "what": "after save line", "who": null}
```

- 新进程从 `loader_main` 进入，50 行先取 store：`loader_before` 为 `points=0`、`stage="init"`，即默认值。录制区域内没有任何 `start` 的语句记录，store 也未出现 `start` 30 行之后的赋值（`3/"pre-save"` 或 `99/"mutated"`），与该进程内 `start` 的 Python 在录制区域内未执行一致。`start` 本身不含任何读档语句；自动读档仅由 `config.auto_load`/`RENPY_AUTO_LOAD` 触发（`00start.rpy:241–243`），本 fixture 均未设置，因此 `start` 不会自动读档。
- 51 行调用 `renpy.load("slot_a")` 后，**没有** `loader_after` 记录：`load` 成功时不返回（`loadsave.py:710` docstring），52 行不可达。随后出现 `after_load` 的 Label 记录，`ret` 为 1：引擎在控制点到达 `come_from_name` 时用 `Context.call` 进入 `_after_load`（`execution.py:618–621`），压入一个返回点；`_after_load` 在 `00start.rpy:143–144` 以 `jump expression "after_load"` 进入 fixture 的 `after_load`（42 行），该 jump 不改变返回栈，故 Label 记录仍为 `ret: 1`；47 行 `Return` 弹出后，后续记录回到 `ret: 0`。轨迹中的 `after_load` 是 fixture 自己的 label；`_after_load` 的语句在 `common/` 下，被 harness 的 `file.startswith("game/")` 过滤（`zz_evidence.rpy:126–127`），其 `_` 前缀也会被 label 回调跳过（`zz_evidence.rpy:142–145`）。
- `after_load_hook` 读到 `points=0`、`stage="init"`，即与 `default` 的初始值相同，**不是**存档里的 `3/"pre-save"`。按观测顺序，hook 在恢复流程重放 30–33 行之前执行；存档值要等重放 30–31 行才重新落到 store（第 130 条的第二次 `save_done` 即为重放后 `points=3`）。上游路径给出的解释是：`unfreeze_core` 先把 roots 写回 store（`rollback.py:1119–1135`），随后 `rollback_core(0, ..., on_load=True)` 在 greedy 模式下回退到最近一个已完成 checkpoint 之后（`rollback.py:948–991`），被弹出条目的 `rb.rollback()` 逐项写回各节点开始前的 store 值（`rollback.py:1006–1007`、`:424–434`）。本 fixture 最近的 checkpoint 是 29 行 `"checkpoint line"` 的交互（由 `renpy/character.py:957` 落下），其记录的 store 尚未执行 30–31 行的赋值，因此 hook 读到 `0/"init"`；该成因由上游代码与轨迹的 `0→3` 先后共同支撑，轨迹本身直接给出的是“hook 时 store 为 `0/"init"`”这一事实。
- `after_load` 返回后，控制点落在存档的 checkpoint 处：轨迹紧接着重放 30、31、32、33 行，然后第二次出现 `save_done`（`points=3`、`stage="pre-save"`、`can_load=True`），再到 34 行 `"after save line"`。**第二个 `save_done` 是恢复流程重放同一段语句的产物，不是测试重新发起的一次独立存档**；其 `points=3` 来自重放 30–31 行后落到 store 的存档值（32 行的 `renpy.save` 也作为被重放语句再次执行，再次写入 `slot_a`）。轨迹在 34 行的交互处结束，因为 `load_case` 的条件 `store.resumed` 已满足，testcase `exit`。
- `after_load_hook` 的 `0` 与重放后的 `3` 并不矛盾：前者是回滚完成、恢复流程尚未重放到 30 行时的读值，后者是重放到 33 行 emit 时的读值。两者在轨迹中的先后即证据。
- 存档之后写成的 `99/"mutated"` 在 `load_case` 段完全没有出现：`after_load_hook` 读 `0/"init"`，重放 33 行 emit 时读 `3/"pre-save"`。这说明读档恢复的是存档时刻（`points=3`、`stage="pre-save"`）的状态，而不是进程 1 的最终 store。

`expected.jsonl`（人工语义断言，7 条）为：

```jsonl
{"can_load": true, "kind": "save_done", "points": 3, "stage": "pre-save"}
{"kind": "post_save_mutation", "points": 99, "stage": "mutated"}
{"kind": "label", "label": "loader_main"}
{"kind": "loader_before", "stage": "init"}
{"kind": "label", "label": "after_load"}
{"kind": "after_load_hook", "points": 0, "stage": "init"}
{"kind": "save_done", "points": 3, "stage": "pre-save"}
```

`scripts/phase01-check.ps1:108–132` 只要求 `expected` 的每条记录按顺序出现在 `actual` 中，且 `expected` 列出的字段逐一相等（`Test-ValueMatch`，`:84–106`：对象只递归匹配 expected 拥有的属性，`:98–103`）；actual 上没有对应键或值不等时才失败，actual 多出的字段（如 `loader_before` 的 `points`、`save_done` 的 `can_load` 之外的多余键）不算失败。因此 `loader_before` 只断言 `stage="init"`，第二个 `save_done` 只断言 `points=3`、`stage="pre-save"`，用来固定“重放确实回到存档值”。

## 自动轨迹 vs 人工观察

- 全部结论来自 `actual.jsonl` 的 JSONL 轨迹，并与 `expected.jsonl` 的有序子序列断言比对。
- 人工观察：**无**。没有人工打开存档/读档界面、没有核对读档后的 UI、没有像素或截图审查。
- 复测条件：SDK SHA、对照提交、三个 `default`、`script.rpy`、`zz_evidence.rpy` 或任一 testcase 变化，或 `scripts/phase01-check.ps1` 报告 `actual.jsonl` 不可复现 / 子序列不匹配时，必须按 `save_case` → `load_case` 顺序、共用同一 `--savedir` 重跑并重新审定基线。

## 限制

1. **两段轨迹拼接无分隔**：`actual.jsonl` 由检查脚本按 `save_case`、`load_case` 两个独立进程的输出顺序拼接（`phase01-check.ps1:173–194`）；第 14/15 条之间没有标记，只能按 `loader_main` 的 Label 记录判断第二段开始。
2. **第二个 `save_done` 不能被读成独立存档操作**：它是恢复流程重放 30–33 行的结果，且 32 行的 `renpy.save("slot_a")` 也属于被重放语句。轨迹无法区分“同一条语句被重放”与“测试主动再存档一次”；本用例要观察的是恢复后的状态值，不是第二次存档行为。
3. **没有 `flow_complete`**：两个 testcase 都在 `advance until eval` 命中后 `exit`，`start` 的 39 行 `$ finish()` 与 `load_case` 的 52 行 `loader_after` 都未执行。因此“完整走到流程末尾”不在本证据范围内。
4. **`after_load_hook` 只给一个瞬间值**：轨迹只证明该 hook 读到 `0/"init"`，并随后在重放到 33 行时读到 `3/"pre-save"`；解冻/回滚的逐条中间值不在轨迹中。`0` 的具体成因（roots 写回后被回滚条目覆盖）由上游 `unfreeze_core`/`rollback_core` 路径与 `0→3` 的先后共同支撑，不是逐帧观测，也没有记录 `rb.checkpoint` 判定停在哪一条日志条目。
5. **`loader_before` 的默认值成因不可辨**：录制从 `arm()` 之后开始，`arm()` 会截断轨迹文件（`zz_evidence.rpy:52–57`），因此轨迹只能证明“录制开始后 store 为默认值”，不能证明新进程启动到 `arm()` 为止发生过什么。`load_case` 的条件是 `store.resumed`（`after_load` 中置位），与 `save_case` 的 `store.stage` 相互独立，两段之间的 store 状态没有交集。
6. **未覆盖**：自动存档、`config.auto_load`/`RENPY_AUTO_LOAD`、除 `slot_a` 外的槽位与翻页、`extra_info`/`extra_json`、存档截图、`can_load` 对空槽位返回假、签名校验（`savetoken`）、`_before_load`、`config.retain_after_load`、读档失败（`load_failed_label`）、同一进程内多次 save/load、回滚过程中存档。
7. **未覆盖 GUI**：没有经过真实的存档/读档菜单按钮，`renpy.save`/`renpy.load` 均由 fixture 直接调用。

## 目标兼容等级

**必须兼容** — 存档要保存当时的 store 与回滚日志，读档要在新进程恢复该状态并回到 checkpoint，`after_load` 要在独立上下文执行后继续原流程；现有剧本与存档依赖该语义才能跨进程继续。证据：`docs/compatibility/evidence/03-save-load/actual.jsonl`、`expected.jsonl`、`run.log`（`total_records: 31`，`testcases: save_case, load_case`）。