# call / return 调用与返回

## 环境

- Ren'Py SDK：`renpy-8.6.1-sdk`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`
- upstream tag：`8.6.1.26111705`；对照提交：`de379eb4f85a4930244786c715e581a1cb3fd374`
- 平台：Windows 11 x64；PowerShell 7
- 全量命令：`pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>`
- 单 fixture 手工运行：见 `docs/compatibility/README.md` §7

## 上游代码路径与符号

- `renpy/ast.py:1662` `class Call(Node)`。`Call.execute`（`:1678`）调 `renpy.game.context().call(label, return_site=self.next.name)`（`:1688`）→ `next_node(rv)` → `renpy.game.context().abnormal = True`（`:1690`）。
- `renpy/execution.py:750` `Context.call`：先 `self.call_location_stack.append(self.current)`（`:761`），再 `self.return_stack.append(return_site)`（`:763`），随后 `self.current = label`（`:766`）并返回 `renpy.game.script.lookup(label)`。**先压栈、再跳转**。
- `renpy/ast.py:1738` `class Return(Node)`。`Return.execute`（`:1752`）设置 `store._return` 后调用 `next_node(renpy.game.context().lookup_return(pop=True))`（`:1769`），再 `pop_dynamic()`。
- `renpy/execution.py:790` `Context.lookup_return(pop=True)`：从 `return_stack` 取返回点，`pop` 为真时同时弹出 `return_stack` / `call_location_stack` 等（`:828` 起）。
- `renpy/execution.py:774` `Context.pop_call` 为“无条件弹栈”的辅助函数（无栈时在 developer 模式抛异常）。
- `renpy/parser.py:776`（`call_statement`）在解析 `call <label>` 时追加一个 `ast.Pass(loc)` 作为紧邻节点。返回点 `return_site` 取 `self.next.name`，即该 `Pass` 节点；因此返回后轨迹先出现调用行位置的 `Pass`，再执行下一语句。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-02-call-return/`
- `game/script.rpy`：`label start`（第 13 行）`"outer before"` → `call sub_one`（第 15 行）→ `"outer after"` → `$ finish()`；`label sub_one`（第 20 行）`"in sub one"` → `call sub_two`（第 22 行）→ `"back in sub one"` → `return`；`label sub_two`（第 26 行）`"in sub two"` → `return`；另有 `label returns_immediately`（第 30 行）`call empty_sub` → `"after empty call"`，与 `label empty_sub`（第 36 行）仅 `return`。
- testcase：`nested_call`、`call_empty`。
- 证据：`docs/compatibility/evidence/02-call-return/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`，共 27 条记录）。

## 输入序列

- `nested_call`：`$ arm()` → `run Jump("start")` → `advance until screen "say"` → 4 次 `advance` → `$ disarm()` → `exit`。走 `start` → `call sub_one` → `call sub_two` → 两级返回 → `outer after` → `$ finish()`。
- `call_empty`：`$ arm()` → `run Jump("returns_immediately")` → `advance until screen "say"` → 1 次 `advance` → `$ disarm()` → `exit`。走 `call empty_sub`（立即 `return`）→ `"after empty call"` → `$ finish()`。

## 预期 vs 实际观察

语义预期：`Call` 记录 `ret` 为压栈前深度；进入被调 label 后 `ret` 递增 1；`Return` 记录弹出前的深度；返回点先出现调用行位置的 `Pass`，再执行调用之后的语句。`expected.jsonl` 断言 `ret` 序列 0→1→2→1→0。

实际（`docs/compatibility/evidence/02-call-return/actual.jsonl`，节选）：

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "line": 15, "node": "Call", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "label": "sub_one", "line": 20, "node": "Label", "ret": 1, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "label": "sub_two", "line": 26, "node": "Label", "ret": 2, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 28, "node": "Return", "ret": 2, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 22, "node": "Pass", "ret": 1, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 23, "node": "TranslateSay", "ret": 1, "what": "back in sub one", "who": null}
```

- `sub_two` 的 `Return`（`ret: 2`）之后，紧接 `line 22` 的 `Pass`（`ret: 1`，即 `sub_one` 内 `call sub_two` 所在行），随后才是 `"back in sub one"`——证实返回到 **call 之后的语句**，且返回点即解析器合成的 `Pass` 节点。
- `call_empty` 段：`Call`（`line 31`，`ret: 0`）→ `empty_sub` `Label`（`line 36`，`ret: 1`）→ `Return`（`line 37`，`ret: 1`）→ `Pass`（`line 31`，`ret: 0`）→ `TranslateSay "after empty call"`（`line 32`，`ret: 0`）→ `Python`（`line 33`）→ `flow_complete`。
- 全 21 条 `stmt` 的 `ret` 在 0/1/2 间按调用深度变化，与预期一致。

## 自动轨迹 vs 人工观察

- 本文结论全部来自 `actual.jsonl`；**未进行人工 GUI 观察或像素审查**。`ret` 由 harness 取 `len(context.return_stack)`，属自动轨迹而非人工确认。
- 复测条件：SDK SHA / 对照提交 / harness 变化，或检查脚本报告基线不可复现 / 子序列不匹配时重跑。

## 限制

- 未覆盖 `call ... from <label>`（显式返回点）、`call expression`、带参数的 `call`（`_args`/`_kwargs`）与命名参数。
- 用 `ret` 观测栈深，无法从轨迹区分 `call_location_stack` 与 `return_stack` 的成对变体，也看不到 `dynamic_stack`。
- 未覆盖 `return` 带表达式（`store._return`）、多层异常恢复路径（`lookup_return` 的 `return_not_found_label` 分支）。
- `call_empty` 只验证单层即时返回，深层嵌套返回仅由 `nested_call` 覆盖两层。

## 目标兼容等级

**必须兼容** — `call`/`return` 的栈深增减与“返回点=调用后语句”语义是现有剧本复用的关键，必须逐条对齐（依据 `docs/compatibility/evidence/02-call-return/actual.jsonl`）。