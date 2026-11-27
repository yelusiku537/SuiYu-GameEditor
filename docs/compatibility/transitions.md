# 转场（`with`）可观察结果

## 环境

| 项目 | 值 |
| --- | --- |
| Ren'Py SDK | `renpy-8.6.1-sdk`（Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`） |
| upstream tag | `8.6.1.26111705` |
| 对照提交 | `de379eb4f85a4930244786c715e581a1cb3fd374` |
| 平台 / shell | Windows 11 x64；PowerShell 7 |
| 全量入口 | `pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>` |
| 单 fixture 入口 | `renpy.exe <project> test <testcase> --savedir <dir>`，模板见 `docs/compatibility/README.md` §7 |

本条对应计划表 B11，目标等级预先登记为“允许不同（视觉细节）”。

## 上游代码路径与符号

路径相对 SDK 根目录（`renpy-8.6.1-sdk/`）。

- 语句节点：`renpy/ast.py:1609 class With(Node)`，字段 `expr: str | None`、`paired: str | None`。`With.execute`（`renpy/ast.py:1630`）顺序为：
  1. `next_node(self.next)`（先把执行指针移走）；
  2. `statement_name("with")`——这一步触发 `config.statement_callbacks`（`renpy/ast.py:546`），也就是证据轨迹里的 `stmt` 记录来源；
  3. `expr` 非空时 `py_eval` 出过渡对象，否则 `trans = None`；
  4. `paired` 非空时 `py_eval` 出配对表达式，否则 `paired = None`；
  5. `renpy.exports.with_statement(trans, paired=paired)`。
- 转场执行：`renpy/exports/statementexports.py:210 with_statement(trans, always=False, paired=None, clear=True)`。init 阶段调用会抛异常；`config.skipping` 或用户关闭转场（`renpy.game.preferences.transitions` 为假且 `always` 为假）时把 `trans` 置 `None`；dict 形式按 layer 拆分后逐个 `renpy.exports.transition`，其余情况交给 `renpy.game.interface.do_with(trans, paired, clear=clear)`。
- 实际渲染：`renpy/display/core.py:1497 do_with(self, trans, paired, clear=False)`。`trans` 为空（或 `suppress_transition`）时只走 `with_none()` 抓取“旧画面”并立即返回；否则 `set_transition(trans)` 后进入一次带 `trans_pause=True` 的 `interact`，即转场是一次独立交互，结束后才继续下一条语句。
- 解析降级：
  - 独立 `with dissolve` 由 `renpy/parser.py:891 with_statement` 解析，直接返回单个 `ast.With(loc, expr)`。
  - `scene ... with <expr>` 由 `renpy/parser.py:785 scene_statement` 解析：先构造 `ast.Scene(loc, imspec, imspec[4])`，再在 `:798` 调用 `parse_with(l, stmt)`。
  - `renpy/parser.py:194 parse_with` 在有 `with` 子句时返回 `[ast.With(loc, None, expr), node, ast.With(loc, expr)]`：**一个前导 With（`expr=None`、`paired=<expr>`）、原语句节点、一个后置 With（`expr=<expr>`、`paired=None`）**。这就是 `scene bg hall with fade` 编译成三节点的来源。
- `renpy/ast.py:1488 class Scene`，`Scene.execute`（`:1516`）先 `next_node(self.next)` 再 `statement_name("scene")`，随后 `renpy.exports.scene(...)` 与 `show_imspec(...)`，所以裸露的 `scene` 只产生一条 `Scene` 记录。
- 测试框架的转场等待：`renpy/test/testsettings.py:74 transition_timeout`（默认 5.0 秒，本 fixture 设为 0.05）；`renpy/test/testast.py:821` 在 `trans_pause`/`ongoing_transition` 持续超过该值时把 `renpy.game.less_updates` 置真，即**强制结束转场并等下一帧**。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-03-transitions/`
- `game/script.rpy`：
  - `:1 image bg room = Solid("#102030", xysize=(320, 180))`、`:2 image bg hall = Solid("#203040", xysize=(320, 180))`。两张背景均为内联纯色，符合 README §4“不引入二进制素材”。
  - `:16 label start:` → `:17 scene bg room` → `:18 $ emit("transition_before", marker="room_shown")` → `:19 with dissolve` → `:20 $ emit("transition_after_dissolve", marker="dissolved_in")` → `:21 scene bg hall with fade` → `:22 $ emit("transition_after_fade", marker="hall_faded")` → `:23 "transition checked"` → `:24 $ finish()` → `:25 return`。
  - `:27 testsuite global:` 设 `_test.timeout = 25.0`、`_test.transition_timeout = 0.05`、`_test.screenshot_directory = "shots"`、`_test.overwrite_screenshots = True`。
- `game/zz_evidence.rpy` 为 `compatibility-tests/fixtures/renpy/phase01/harness/zz_evidence.rpy` 的逐字节副本。
- testcase：`transitions_apply`。
- 证据：`docs/compatibility/evidence/03-transitions/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`、`testcases: transitions_apply`、`total_records: 17`、`screenshots: transition_final`）。

## 输入序列

```text
$ arm()
run Jump("start")
advance until screen "say"
screenshot "transition_final"
$ shot("transition_final")
advance
$ disarm()
exit
```

`advance until screen "say"` 一等到底：它要等到所有转场与语句都走完、停在 `"transition checked"` 的 say 屏，才截图。因此截图取的是**转场结束后的稳定终帧**，不是过渡中的任何一帧。

## 预期 vs 实际观察

语义预期（`expected.jsonl` 的断言，共 5 条）：

1. `scene bg room` 执行后再触发 `transition_before`（`room_shown`），证明裸 `scene` 是独立节点、且在两语句之间确实落到下一语句。
2. `with dissolve` 执行后触发 `transition_after_dissolve`（`dissolved_in`），证明独立 With 语句执行完毕并继续到下一条语句。
3. `scene bg hall with fade` 之后触发 `transition_after_fade`（`hall_faded`），证明带 `with` 的 scene 降级出的多个节点全部执行完、流程继续。
4. 生成截图 `transition_final`，`present: true`。
5. `flow_complete`。

实际（`docs/compatibility/evidence/03-transitions/actual.jsonl`，完整序列，行号为 `game/script.rpy`）：

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "label": "start", "line": 16, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "start"}
{"file": "game/script.rpy", "kind": "stmt", "line": 17, "node": "Scene", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 18, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "transition_before", "marker": "room_shown"}
{"file": "game/script.rpy", "kind": "stmt", "line": 19, "node": "With", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 20, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "transition_after_dissolve", "marker": "dissolved_in"}
{"file": "game/script.rpy", "kind": "stmt", "line": 21, "node": "With", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 21, "node": "Scene", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 21, "node": "With", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 22, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "transition_after_fade", "marker": "hall_faded"}
{"file": "game/script.rpy", "kind": "stmt", "line": 23, "node": "TranslateSay", "ret": 0, "what": "transition checked", "who": null}
{"bytes": 7453, "kind": "screenshot", "name": "transition_final", "present": true, "sha256": "0b7c5f19a3cba34ee8bafb3fb6fc0ac954b13ad1e73082dacca0c27f745514e4"}
{"file": "game/script.rpy", "kind": "stmt", "line": 24, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "flow_complete"}
```

要点：

- `:17` 的裸 `scene bg room` 只产生一条 `Scene`，没有伴随 `With`，与 `scene_statement` 在没有 `with` 子句时直接返回 `ast.Scene` 一致。
- `:19` 的独立 `with dissolve` 只有**一条** `With`；`with_statement`（`renpy/parser.py:891`）返回的就是单个 `ast.With(loc, expr)`。
- `:21` 的 `scene bg hall with fade` 产生**三条同属第 21 行的记录，顺序固定为 `With` → `Scene` → `With`**。这正是 `parse_with`（`renpy/parser.py:194`）返回的 `[With(expr=None, paired="fade"), Scene, With(expr="fade")]`：前导 With 以 `trans=None`/`paired="fade"` 先执行（`With.execute` 走 `with_statement(None, paired=...)`，先按 `do_with` 的 `with_none()` 分支抓旧帧），随后 Scene 换背景，最后后置 With 才真正跑 `fade` 转场。轨迹顺序与这条降级规则互相印证。
- 三个 marker（`room_shown` → `dissolved_in` → `hall_faded`）严格夹在对应语句前后，说明每种写法都执行完毕并把控制权交给下一条语句；所有 `stmt` 记录 `ret` 均为 0，转场没有改变调用栈。
- 截图记录 `present: true`、`bytes: 7453`、`sha256: 0b7c5f…4514e4`；PNG 本体不入仓库。检查脚本对 `screenshot` 记录只比对 `kind`+`name`+`present`（`scripts/phase01-check.ps1` 的截图归一化逻辑），字节数/哈希变化不算回归。
- `run.log` 的 `record_kinds` 计数与 17 条记录一致：`stmt` 11、`label` 1、三个 marker 各 1、`screenshot` 1、`flow_complete` 1。

## 自动轨迹 vs 人工观察

- 本文结论全部来自 `actual.jsonl` 的节点序列与 `expected.jsonl` 的子序列比对，另有 `actual.jsonl` 中的截图元数据；**未进行人工 GUI / 像素观察，也未对 PNG 做任何视觉审查**，没有确认 dissolve 是否淡入、fade 是否淡出、颜色是否由 `#102030` 变为 `#203040`，也没有逐帧观察过渡过程。
- 复测条件：SDK SHA、对照提交、`game/script.rpy`、`zz_evidence.rpy` 任一变化，或 `scripts/phase01-check.ps1` 报告基线不可复现/子序列不匹配时，按 README §7 重跑 `transitions_apply` 并重新审定基线。若要提出“视觉一致”结论，必须另做人工截图对照并新增补证记录，不得引用本文等级。

## 限制

1. **无像素断言**：截图只留元数据，PNG 不入仓库。`bytes`/`sha256` 会随 GPU、驱动、字体与窗口尺寸变化，故不作为一致性依据；本文不声称终帧画面与 Ren'Py GUI 模板一致。
2. **无时序断言**：fixture 把 `_test.transition_timeout` 设为 `0.05`。按 `renpy/test/testast.py:821`，转场持续超过 0.05 秒时测试框架会强制结束它（置 `less_updates`）。因此 dissolve/fade 在本次运行中**可能被提前截断**，`dissolve` 与 `fade` 的实际时长、缓动曲线、以及“是否完整播放”均未验证。
3. 截图只在 `"transition checked"` 的 say 屏上取一帧，属于稳定终帧；过渡中间帧、转场是否真的渲染、是否被 `config.skipping` 或用户关闭转场设置短路（`with_statement` 中 `trans = None` 分支）均无证据区分。
4. 未覆盖：`with` 带参数表达式（`with Dissolve(0.4)`、`with Pause(1.0)`）、`with None`、`show ... with` / `hide ... with`（同一 `parse_with` 路径，但未单独断言）、dict 形式按 layer 的转场、`config.with_callback`、`always=True`、CDS（`renpy.with_statement` 的 `:doc: se_with` 自定义语句入口）以及 ATL 内嵌转场。
5. 三节点降级顺序由 `actual.jsonl` 观察 + `parse_with` 源码推得，未直接反编译 `.rpyc` 或导出 AST；若上游改写 `parse_with` 的返回形状，本条的行序断言需重审。
6. `ret` 恒为 0 只能说明转场不压 `return_stack`，不能说明 `interact` 期间的回滚、自动存档、`window auto` 等副作用；这些由 rollback / save-load 文档覆盖。

## 目标兼容等级

**允许不同（视觉细节）** — 新引擎必须保证“`with` 语句被执行、并且控制流继续到下一条语句”这一可观察语义（三种写法各自的语句节点与 marker 顺序一致），但 dissolve/fade 的像素结果、持续时长与缓动细节允许不同；本文不提出任何像素或时序等价要求。依据：`docs/compatibility/evidence/03-transitions/actual.jsonl`、`expected.jsonl`、`run.log`。