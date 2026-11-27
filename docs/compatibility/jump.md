# jump 跳转

## 环境

- Ren'Py SDK：`renpy-8.6.1-sdk`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`
- upstream tag：`8.6.1.26111705`；对照提交：`de379eb4f85a4930244786c715e581a1cb3fd374`
- 平台：Windows 11 x64；PowerShell 7
- 全量命令：`pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>`
- 单 fixture 手工运行：见 `docs/compatibility/README.md` §7

## 上游代码路径与符号

- `renpy/ast.py:1969` `class Jump(Node)`。`Jump.chain`（`:1985`）显式 `self.next = None`，“不关心下一节点”。
- `Jump.execute`（`renpy/ast.py:1988`）：解析 `target`（`expression` 为真时用 `py_eval`）→ `renpy.game.script.lookup(target)`（`:1998`）→ `renpy.game.context().abnormal = True`（`:1999`）→ `next_node(rv)`（`:2001`）。**全程不调用 `Context.call`，不向 `return_stack` 压入任何东西**，因此 `ret` 保持 0。
- 对比 `renpy/ast.py:1662` `class Call` 的 `execute` 调 `renpy.game.context().call(label, return_site=self.next.name)`（`:1688`），会在 `Context.call`（`renpy/execution.py:750`）中修改 `return_stack`。这是 jump 与 call 的核心区别。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-02-jump/`
- `game/script.rpy`：`label start`（第 13 行）先 `"before jump"` 再 `jump destination`（第 15 行）；`label destination`（第 18 行）含 `"at destination"` + `$ finish()`；另一路径 `label skip_middle`（第 23 行）直接 `jump final_label`（第 24 行），跳过中间内容；`label final_label`（第 27 行）含 `"at final label"` + `$ finish()`。
- testcase：`jump_forward`、`jump_skip`。
- 证据：`docs/compatibility/evidence/02-jump/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`，共 17 条记录，含 `<file>` 等字段）。

## 输入序列

- `jump_forward`：`$ arm()` → `run Jump("start")` → `advance until screen "say"` → 2 次 `advance` → `$ disarm()` → `exit`。触发 `start` 内 `jump destination`。
- `jump_skip`：`$ arm()` → `run Jump("skip_middle")` → `advance until screen "say"` → 1 次 `advance` → `$ disarm()` → `exit`。触发 `skip_middle` 内 `jump final_label`。

## 预期 vs 实际观察

语义预期：`jump` 只改写下一节点；目标为非相邻 label 时轨迹中不出现中间节点；不改变栈深，故所有记录 `ret` 恒为 0。`expected.jsonl` 断言了 `before jump` → `label destination` → `at destination`，以及 `skip_middle` → `final_label` → `at final label` 的顺序。

实际（`docs/compatibility/evidence/02-jump/actual.jsonl`，节选）：

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "line": 15, "node": "Jump", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "label": "destination", "line": 18, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "destination"}
{"file": "game/script.rpy", "kind": "stmt", "line": 19, "node": "TranslateSay", "ret": 0, "what": "at destination", "who": null}
{"file": "game/script.rpy", "kind": "stmt", "label": "skip_middle", "line": 23, "node": "Label", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "label": "final_label", "line": 27, "node": "Label", "ret": 0, "what": null, "who": null}
```

- 两段（`jump_forward` → 首个 `flow_complete`，`jump_skip` → 第二个 `flow_complete`）记录按 testcase 顺序拼接为同一 `actual.jsonl`；每段末尾各有 `{"kind": "flow_complete"}`。
- `jump_skip` 段在 `skip_middle` 后**未出现** `skip_middle` 内第 25 行的 `return`，直接落到 `final_label`，符合 `Jump.chain` 置 `next=None` 的非顺序行为。
- 全部 11 条 `stmt` 记录 `ret` 均为 0，`jump` 没有压栈。

## 自动轨迹 vs 人工观察

- 本文结论全部来自 `actual.jsonl`；**未进行人工 GUI 观察或像素审查**，`abnormal=true` 的含义由上游 `execution.py:630-631` 与 `ast.py:1999` 推得，非人工确认。
- 复测条件：SDK SHA / 对照提交 / harness 变化，或检查脚本报告基线不可复现时重跑。

## 限制

- 只覆盖静态 `jump <label>`；`jump expression`（`Jump.expression` 为真）与相对 label（`.local`）未覆盖。
- `jump_skip` 只证明跳过了 `skip_middle` 块体，未验证“跨文件 / 跨模块”跳转与 `jump` 到不存在 label 的错误路径。
- 轨迹无法记录 `abnormal` 的消费方（如 window auto、rollback），仅记录置位与 label 回调观察值。

## 目标兼容等级

**必须兼容** — `jump` 改写控制流且不压 `return_stack` 是分支剧本的基础语义，必须逐条对齐（依据 `docs/compatibility/evidence/02-jump/actual.jsonl`）。