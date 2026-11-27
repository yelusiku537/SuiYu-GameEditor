# label 定义与进入

## 环境

- Ren'Py SDK：`renpy-8.6.1-sdk`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`
- upstream tag：`8.6.1.26111705`；对照提交：`de379eb4f85a4930244786c715e581a1cb3fd374`
- 平台：Windows 11 x64；PowerShell 7
- 全量命令：`pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>`
- 单 fixture 手工运行：见 `docs/compatibility/README.md` §7（`renpy.exe <project> test <testcase> --savedir <dir>`）

## 上游代码路径与符号

- `renpy/ast.py:1135` `class Label(Node)`。`Label.execute`（`renpy/ast.py:1174`）顺序为：`next_node(self.next)` → `mark_seen()` → `renpy.easy.run_callbacks(renpy.config.label_callback, self.name, ...)`（`renpy/ast.py:1187`）。即 Label 只负责把执行指针移入块首，不改变调用栈。
- `renpy/config.py:390-391` 定义 `label_callback` 与旧名 `label_callbacks`。
- `renpy/execution.py:157` `class Context`。执行循环在 `renpy/execution.py:630` 取 `self.last_abnormal = self.abnormal`，紧接 `:631` 重置 `self.abnormal = False`；因此 label 回调收到的是“上一节点是否经跳转/调用到达”的标记。
- `renpy/ast.py:1999`（Jump）与 `renpy/ast.py:1690`（Call）都把 `renpy.game.context().abnormal = True`，所以经 `jump`/`call`/测试 `run Jump(...)` 到达的 label，在轨迹里 `abnormal` 为 `true`。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-02-label/`
- `game/script.rpy` 定义 `label start`（第 13 行）、`first_label`（第 17 行）、`second_label`（第 22 行）；`game/zz_evidence.rpy` 为 `harness/zz_evidence.rpy` 的逐字节副本。
- testcase：`label_entry`、`label_from_start`。
- 证据：`docs/compatibility/evidence/02-label/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`，共 19 条记录）。

## 输入序列

- 公共前置：`$ arm()` 开始录制；`run Jump("<label>")` 从主菜单直接进入目标 label；`advance until screen "say"` 消解首行竞态。
- `label_entry`：`run Jump("first_label")` → `advance until screen "say"` → 1 次 `advance` → `$ disarm()` → `exit`。该用例在 `second_label` 的对白处被 disarm 截断，未到 `$ finish()`，因此本身不产生 `flow_complete`。
- `label_from_start`：`run Jump("start")` → `advance until screen "say"` → 2 次 `advance` → `$ disarm()` → `exit`。经 `start` → `jump first_label` → `jump second_label` → `$ finish()`，产生本文件唯一的 `flow_complete`。

## 预期 vs 实际观察

语义预期（`expected.jsonl` 断言）：进入任一 label 产生一条 `kind=stmt`/`node=Label` 记录（额外带 `label` 名）和一条 `kind=label` 记录；Label 执行后继续块内首语句；label 不触碰 `return_stack`，故所有记录 `ret` 恒为 0。

实际（`docs/compatibility/evidence/02-label/actual.jsonl`，节选）：

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "label": "first_label", "line": 17, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "first_label"}
{"file": "game/script.rpy", "kind": "stmt", "line": 18, "node": "TranslateSay", "ret": 0, "what": "in first label", "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 19, "node": "Jump", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "label": "second_label", "line": 22, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "second_label"}
```

- `label_from_start` 段额外显示 `Label start`（`line 13`）→ `Jump`（`line 14`）→ 再次进入 `first_label`（`line 17`）→ `second_label`（`line 22`）→ `Python`（`line 24`）→ `{"kind": "flow_complete"}`。
- 全部 5 条 `kind=label` 记录的 `abnormal` 均为 `true`；所有 `stmt` 记录 `ret` 均为 0。与 `expected.jsonl` 的有序子序列断言一致。

## 自动轨迹 vs 人工观察

- 本文结论全部来自 `actual.jsonl` 的 JSONL 轨迹，并与 `expected.jsonl` 的语义断言比对；**未进行任何人工 GUI 观察或像素审查**。
- 复测条件：SDK SHA、对照提交、`zz_evidence.rpy` 任一变化，或 `scripts/phase01-check.ps1` 报告“不可复现 / 子序列不匹配”时，须重跑 `p01-02-label` 两个 testcase 后重新审定基线。

## 限制

- 只观测非 `_` 前缀 label（harness `_ev_on_label` 过滤）；`_` 开头的系统 label 与 `label ... hide`、参数化 label 未覆盖。
- `abnormal` 只记录布尔，不能从轨迹区分是经 `jump` 还是 `call` 到达。
- `label_entry` 因 disarm 截断在 `second_label` 对白处，其后路径仅由 `label_from_start` 覆盖，两条用例路径不完全等价。
- 未验证 label 块的 fall-through 边界之外的控制流（如块内 `return` 结束整个流程时与主菜单再入的交互），该部分由 `call-return.md` 与启动链文档覆盖。

## 目标兼容等级

**必须兼容** — label 进入与 `ret` 不变是剧本跳转的基础语义，新引擎必须逐条复现（依据 `docs/compatibility/evidence/02-label/actual.jsonl`）。