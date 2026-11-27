# 回滚：记录与状态恢复

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

- 查询能力
  - `renpy/exports/rollbackexports.py:73 can_rollback`：依次检查 `config.rollback_enabled`、`store._rollback`、`renpy.game.context().rollback`，全部为真后才委托 `renpy.game.log.can_rollback()`（`:89`）。
  - `renpy/rollback.py:873 can_rollback`（`RollbackLog.can_rollback`）：`rollback_limit <= 0` 且未 force 时返回假；否则从 `self.log` 末尾向前数 `hard_checkpoint`，数够后要求该条目的 `rb.context.current` 用 `renpy.game.script.has_label` 能解析为 label（`:884–891`；`has_label` 见 `renpy/script.py:1171`）。
- 发起回滚
  - `renpy/exports/rollbackexports.py:181 rollback(force=False, checkpoints=1, defer=False, greedy=True, ...)`：`force` 为真时跳过三项开关检查；`:231–235` 清 `config.skipping`、`log.complete()`、`renpy.game.log.rollback(checkpoints, greedy=greedy, ..., force=True, abnormal=abnormal, ...)`。
  - fixture 的 `renpy.rollback(True)` 只给一个位置参数，落到 `force=True`；`checkpoints` 取默认 1，`greedy` 取默认真，`abnormal` 取默认真。
  - `renpy/rollback.py:894 rollback`（`RollbackLog.rollback`）：无可用回滚点时直接返回，否则 `:937` 抛 `RollbackException`。异常由 `renpy/execution.py:1095–1098` 在顶层 context 接住并调用 `RollbackException.perform_rollback`（`renpy/rollback.py:1212–1220`），转调 `rollback_core`。
- 实际回退
  - `renpy/rollback.py:939 rollback_core`：
    - `:940–941` 非读档时先 `complete(False)` 结算当前节点改动。
    - `:948–963` 从日志末尾弹出条目；`hard_checkpoint` 计为回滚点，数够且 `rb.context.current` 仍是 label 才停。
    - `:978–991` greedy 模式继续弹出，直到“恰好停在最近一个已完成 checkpoint 之后”。
    - `:1006–1007` 对每个被弹条目执行 `rb.rollback()`。
    - `:1034` `renpy.game.after_rollback = abnormal`。
    - `:1043` `renpy.exports.execute_default_statement(False)`（只补齐未被记录的默认值）。
    - `:1049–1050` 用 `renpy.game.context().rollback_copy()` 重建当前上下文。
  - `renpy/rollback.py:399 Rollback.rollback`：`:407–422` 逐个对象 `_rollback`；`:424–434` 把 `self.stores` 记录的旧键值写回 store；`:443` 回放 RNG；`:445` 调 `rollback_control()`。
  - `renpy/rollback.py:447 rollback_control`：`:453` `renpy.game.contexts = renpy.game.contexts[:-1] + [self.context]`——这就是**控制位置**的恢复。
  - `renpy/rollback.py:234 class Rollback`：`:273` 构造时即 `self.context = renpy.game.context().rollback_copy()`，保存了节点开始执行前的上下文浅拷贝；累计状态由 `:542 begin` / `:614 complete` 在每节点前后差分。
- checkpoint 的落点
  - `renpy/character.py:957 renpy.exports.checkpoint(True, hard=checkpoint)`：Say/TranslateSay 交互结束时落 checkpoint。
  - `renpy/rollback.py:736 checkpoint`：`:753` `self.current.checkpoint = True`，`:755–764` 维护 `hard_checkpoint` 与 `rollback_limit`。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-03-rollback/`
- `game/script.rpy`：
  - `default counter = 0`（13 行）。
  - `label start`（15 行）：16 行 `"A"` → 17 行 `$ counter += 1` → 18 行 `"B"` → 19 行 `$ counter += 1` → 20 行 `$ emit("at_b", counter=counter, can_rollback=renpy.can_rollback())` → 21 行 `"C"` → 22 行 `$ emit("at_c", counter=counter, can_rollback=renpy.can_rollback())` → 23 行 `$ renpy.rollback(True)` → 24 行 `$ emit("after_rollback", counter=counter)` → 25 行 `"D"` → 26 行 `$ emit("done", counter=counter)` → 27 行 `$ finish()` → 28 行 `return`。
  - `game/zz_evidence.rpy` 为 `harness/zz_evidence.rpy` 的逐字节副本。
- testcase：`rollback_restores`（39–49 行）。
- 证据：`docs/compatibility/evidence/03-rollback/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`，`testcases: rollback_restores`，`total_records: 26`，`record_kinds: {"at_b": 3, "at_c": 2, "label": 1, "stmt": 17, "test_after_rollback": 1, "test_at_b": 1, "test_done": 1}`）。

## 输入序列

`rollback_restores`（单进程，26 条记录）：

```text
$ arm()
run Jump("start")
advance until eval (store.counter == 2)
$ emit("test_at_b", counter=store.counter, can_rollback=renpy.can_rollback())
advance
$ emit("test_after_rollback", counter=store.counter)
advance
$ emit("test_done", counter=store.counter)
$ disarm()
exit
```

- 第一个 `advance until eval` 推进到 `counter == 2` 成立时的下一个交互，即停在 `"C"`（21 行）的交互上。
- 其后两次 `advance` 各自消耗一次 `"C"` 交互，把流程推进到 23 行 `renpy.rollback(True)`，触发一次回滚与重放。

## 预期 vs 实际观察

语义预期：`counter` 从默认 0 起，经 17、19 行两次 `+= 1` 变为 2；`at_b`/`at_c` 均读到 2；`renpy.rollback(True)` 把**已记录的 store 状态与控制位置**恢复到回滚点，而非清零或重置为新值，因此回滚后流程重放时各快照仍为 2；`can_rollback()` 在该流程可回滚时应为真。

实际（`docs/compatibility/evidence/03-rollback/actual.jsonl`，26 条记录），按轨迹顺序分三段。

### 段 1：首次正向执行（第 1–13 条）

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "label": "start", "line": 15, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "start"}
{"file": "game/script.rpy", "kind": "stmt", "line": 16, "node": "TranslateSay", "ret": 0, "what": "A", "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 17, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 18, "node": "TranslateSay", "ret": 0, "what": "B", "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 19, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 20, "node": "Python", "ret": 0, "what": null, "who": null}
{"can_rollback": true, "counter": 2, "kind": "at_b"}
{"file": "game/script.rpy", "kind": "stmt", "line": 21, "node": "TranslateSay", "ret": 0, "what": "C", "who": null}
{"can_rollback": true, "counter": 2, "kind": "test_at_b"}
{"file": "game/script.rpy", "kind": "stmt", "line": 22, "node": "Python", "ret": 0, "what": null, "who": null}
{"can_rollback": true, "counter": 2, "kind": "at_c"}
{"file": "game/script.rpy", "kind": "stmt", "line": 23, "node": "Python", "ret": 0, "what": null, "who": null}
```

- 1–7 条是 15–20 行的正常执行：`A`、第一次 `+=1`、`B`、第二次 `+=1`、`emit("at_b")`。
- 第 8 条 `at_b` 记录 `counter=2`、`can_rollback=true`，与两次自增后的值一致。
- 第 9 条是 21 行 `"C"` 的语句记录；testcase 的 `advance until eval (store.counter == 2)` 在此交互处判定成立并停下，第 10 条 `test_at_b` 由测试脚本在此时发出（`counter=2`、`can_rollback=true`）。
- 第 11–13 条是 22、23 行：`at_c`（`counter=2`、`can_rollback=true`）与 23 行的 `renpy.rollback(True)` 语句本身。

### 段 2：第一次回滚与重放（第 14–18 条）

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "line": 19, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 20, "node": "Python", "ret": 0, "what": null, "who": null}
{"can_rollback": true, "counter": 2, "kind": "at_b"}
{"file": "game/script.rpy", "kind": "stmt", "line": 21, "node": "TranslateSay", "ret": 0, "what": "C", "who": null}
{"counter": 2, "kind": "test_after_rollback"}
```

- 23 行回滚生效后，控制位置被恢复到回滚点：下一条语句记录直接是 19 行（`counter += 1`）而非 24 行。轨迹据此显示流程从 19 行重放：19 → 20 → （`at_b`，`counter=2`）→ 21 行 `"C"`。这与 `rollback_core` 先恢复回滚点的 store 状态、再用 `rollback_copy()` 复原控制位置（`renpy/rollback.py:1006–1007`、`:1049–1050`）的方向一致，因此重放 19 行的 `+=1` 后又落回 2，而不是累加出更大的值。
- 第 16 条是重放产生的第二个 `at_b`，`counter` 仍为 2、`can_rollback` 仍为真。
- 第 18 条 `test_after_rollback` 由 testcase 的第一次 `advance` 之后发出：该 `advance` 让段 1 的 `"C"` 交互通过，22、23 行随后执行，23 行触发回滚，流程重放到新的 `"C"` 交互才停下；测试随即取 `store.counter`，得 2。注意它**不是** fixture 24 行的 `after_rollback`——24 行从未执行，因此在 `actual.jsonl` 中不存在 `kind="after_rollback"` 记录。

### 段 3：重放再次命中回滚（第 19–26 条）

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "line": 22, "node": "Python", "ret": 0, "what": null, "who": null}
{"can_rollback": true, "counter": 2, "kind": "at_c"}
{"file": "game/script.rpy", "kind": "stmt", "line": 23, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 19, "node": "Python", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 20, "node": "Python", "ret": 0, "what": null, "who": null}
{"can_rollback": true, "counter": 2, "kind": "at_b"}
{"file": "game/script.rpy", "kind": "stmt", "line": 21, "node": "TranslateSay", "ret": 0, "what": "C", "who": null}
{"counter": 2, "kind": "test_done"}
```

- 第二次 `advance` 消耗段 2 末的新 `"C"`，流程再次执行 22 行（`at_c`，第 20 条，`counter=2`）与 23 行 `renpy.rollback(True)`（第 21 条），于是**再次**回滚到 19 行，重放 19 → 20 → `at_b`（第 24 条，`counter=2`）→ 21 行 `"C"`（第 25 条）。
- 第 26 条 `test_done` 由 testcase 的第二次 `advance` 之后发出，此时流程停在重放后的 `"C"` 交互，`counter=2`；随后 `disarm()` 与 `exit`，轨迹结束。
- 因此 24 行 `after_rollback`、25 行 `"D"`、26 行 `done`、27 行 `finish()`、28 行 `return` 在本轨迹中**从未出现**：每次重放到 23 行都被回滚打断，流程在 19–23 之间循环，直到 testcase 退出。

### 汇总读数

- `at_b` 出现 3 次（第 8、16、24 条），`at_c` 出现 2 次（第 12、20 条），`"C"` 的 `TranslateSay` 出现 3 次（第 9、17、25 条）。重复段即“回滚 → 从 19 行重放到 23 行 → 再次回滚”。
- 所有记录了 `can_rollback` 的条目（3 条 `at_b`、2 条 `at_c`、1 条 `test_at_b`）一律为 `true`；`test_after_rollback` 与 `test_done` 只记录 `counter`，未记录 `can_rollback`。
- 全部 17 条 `stmt` 的 `ret` 均为 0：本流程没有 `call`，回滚也不改变返回栈深度。
- `expected.jsonl`（人工语义断言，5 条）为：

```jsonl
{"can_rollback": true, "counter": 2, "kind": "at_b"}
{"counter": 2, "kind": "at_c"}
{"counter": 2, "kind": "at_b"}
{"counter": 2, "kind": "test_after_rollback"}
{"counter": 2, "kind": "test_done"}
```

`scripts/phase01-check.ps1:108–132` 只要求这些记录按顺序作为 `actual` 的有序子序列出现；第二条 `at_b` 未断言 `can_rollback`，因此只锁定 `counter=2`。

## 自动轨迹 vs 人工观察

- 全部结论来自 `actual.jsonl` 的 JSONL 轨迹，并与 `expected.jsonl` 的有序子序列断言比对。
- 人工观察：**无**。没有人工回滚、没有观察回滚动画/过渡、没有截图或像素审查。
- 复测条件：SDK SHA、对照提交、`script.rpy`、`zz_evidence.rpy`、testcase 或 `renpy.rollback` 调用参数任一变化，或 `scripts/phase01-check.ps1` 报告 `actual.jsonl` 不可复现 / 子序列不匹配时，须重跑 `rollback_restores` 并重新审定基线。

## 限制

1. **重复段是 fixture 与 testcase 交互的必然结果，轨迹不单独标注**：每次重放都会再次执行 23 行的 `renpy.rollback(True)`，因此循环往复。重放产生的 `at_b`/`at_c`/`"C"` 记录与首次执行共用同一 `kind`，没有“第 N 遍”或“replay”标记，只能靠出现顺序与条数区分；不能单看 `kind` 判断某条是首跑还是重放。
2. **流程未走完**：24 行 `after_rollback`、25 行 `"D"`、26 行 `done`、27 行 `finish()` 从未执行，`actual.jsonl` 中没有 `flow_complete`。本证据只覆盖“回滚把控制位置恢复到 19 行并重放”，不覆盖回滚后继续执行到 `"D"`/`done` 的后续路径。若要观察后续，需要把 `renpy.rollback` 放在不被重放命中的位置（例如只在首跑用标志位调用一次），但那会改变轨迹形状，属于新的取证设计。
3. **只有两次 `+=1` 之后的快照**：轨迹在 20 行 `emit("at_b")` 与 22 行 `emit("at_c")` 处取值，两处都在两次自增之后；自增之间的中间 store 值不在轨迹里，故不能用本证据断言回滚点处 `counter` 是 1 还是 2。可确定的是：回滚后重放得到的快照恒为 2，与“回滚恢复已记录的 store 状态而非清零”一致。
4. **`can_rollback` 只是布尔**：它只证明调用时返回真，不能从轨迹得出 `rollback_limit` 的具体数值，也不能区分是哪一项前置条件（`config.rollback_enabled` / `store._rollback` / `context().rollback` / 日志条目）使其为真。
5. **未覆盖**：`store._rollback`/`config.rollback_enabled` 关闭、`rollback_limit` 耗尽与 `rollback_block`、`checkpoints>1`、`greedy=False`、`defer=True`、带 `label`/`current_label` 的回滚、`fix_rollback`、`block_rollback`、`retain_after_load`、回滚与存档的交互、对象级 `_rollback`（`store.object` 之外的自定义类）、`config.ex_rollback_classes`、roll-forward（`forward`/`get_roll_forward`）、RNG 回放。
6. **未覆盖 GUI**：没有经过真实的历史记录/回滚菜单，回滚由 fixture 直接调用。
7. **`abnormal` 未被观测**：`renpy.rollback(True)` 走默认 `abnormal=True`，`rollback_core` 会置 `renpy.game.after_rollback` 并抑制过渡（`:1026`、`:1034`），但轨迹没有记录过渡或视觉状态，无法从 JSONL 验证该副作用。

## 目标兼容等级

**必须兼容（语义）** — 要求的语义是“回滚把已记录的 store 状态与控制位置恢复到回滚点”，而非逐条复刻本轨迹的重复段形状；现有剧本依赖回滚后变量回到 checkpoint 值、控制流从该点继续。证据：`docs/compatibility/evidence/03-rollback/actual.jsonl`、`expected.jsonl`、`run.log`（`total_records: 26`，`testcases: rollback_restores`）。