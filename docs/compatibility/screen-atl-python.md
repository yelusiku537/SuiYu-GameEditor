# screen / ATL / 嵌入 Python 边界

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

以下路径均相对 SDK 根目录（`renpy-8.6.1-sdk/`）。

- `renpy/display/screen.py:1151` `get_screen(name, layer=None, tag_only=False)`：先按 tag、再按 screen 名向 `scene_lists()` 查询（`get_displayable_by_tag` / `get_displayable_by_name`）；未显示时返回 `None`。fixture 的 `renpy.get_screen("hud") is not None` 即走此函数。
- `renpy/display/screen.py:1291` `has_screen(name)`：只判断同名 screen 定义是否存在（经 `get_screen_variant`），不表示当前是否显示；本 fixture 未调用，列出以区分“定义存在”与“正在显示”。
- `renpy/display/screen.py:1327` `show_screen(_screen_name, *_args, **kwargs)`：`show screen` 语句的编程等价物。
- `renpy/display/screen.py:1505` `hide_screen(tag, layer=None, immediately=False)`：从场景列表移除屏幕，`immediately` 决定是否走 `on hide` 事件。
- `renpy/common/000statements.rpy:739` 注册 `"show screen"`，`:755` 注册 `"hide screen"`；对应执行体 `execute_show_screen`（同文件 `:656`）调用 `renpy.show_screen`，`execute_hide_screen`（同文件 `:700`）调用隐藏路径。两者在 AST 中都是 `UserStatement`。
- `renpy/ast.py:2179` `class UserStatement(Node)`：通用语句节点，`call("execute")` 分派到注册的语句实现；`show screen`/`hide screen` 因此只作为 `node=UserStatement` 出现在轨迹里。
- `renpy/ast.py:1376` `class Show(Node)`：`execute` 调 `show_imspec`（同文件 `:707`），把 at 表达式求值后经 `config.show` 登记到场景列表。
- `renpy/ast.py:1194` `class Python(Node)`：`execute` 调用 `renpy.python.py_exec_bytecode` 执行 `python:` 块；fixture 的 `local_sum = sum(range(5))` 即此节点。
- `renpy/display/scenelists.py:81` `class SceneLists`：`at_list` 为 `layer -> tag -> at 列表` 的映射；`add()` 在 `:402` 写入 `self.at_list[layer][key] = at_list`。fixture 读取 `scene_lists.at_list.get("master", {}).get("eileen")` 判断 ATL 是否登记。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-03-screen-atl-python/`
- `game/script.rpy`：`transform slide:`（第 1 行，`xalign 0.0` → `linear 0.1 xalign 1.0`）；`screen hud(): frame: text "HUD-VISIBLE" id "hudtext"`（17–19 行）；`image eileen = Solid("#aa88ff", xysize=(64, 64))`（21 行）；`label start:`（23 行）。
- `game/zz_evidence.rpy` 为 `harness/zz_evidence.rpy` 的逐字节副本。
- testcase：`screen_atl_python`（唯一用例）。
- 证据：`docs/compatibility/evidence/03-screen-atl-python/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`，`total_records: 18`）。

## 输入序列

```text
$ arm()
run Jump("start")
advance until screen "say"
advance
$ disarm()
exit
```

`start` 内的语句路径（行号与 `actual.jsonl` 一致）：

1. 第 23 行 `Label start`，随后第 24 行 `$ emit("screen_initial", ...)`。
2. 第 25 行 `show screen hud`（`UserStatement`）。
3. 第 26 行 `$ emit("screen_shown", ...)`。
4. 第 27 行 `show eileen at slide`（`Show`，ATL 随 at 列表登记）。
5. 第 28 行 `$ emit("atl_registered", ...)`。
6. 第 29–31 行 `python:` 块，计算 `local_sum = sum(range(5))` 并 `emit("embedded_python", local_sum=...)`。
7. 第 32 行 `hide screen hud`（`UserStatement`）。
8. 第 33 行 `$ emit("screen_hidden", ...)`。
9. 第 34 行 `"complex checked"`（`TranslateSay`）。
10. 第 35 行 `$ finish()` 产生 `flow_complete`；随后 `return`。

`testsuite global` 设置 `_test.timeout = 25.0`、`_test.transition_timeout = 0.05`、`_test.screenshot_directory = "shots"`、`_test.overwrite_screenshots = True`；本 testcase 未调用 `screenshot`/`shot`。

## 预期 vs 实际观察

语义预期（`expected.jsonl` 的有序子序列断言，共 6 条）：

```jsonl
{"kind": "screen_initial", "shown": false}
{"kind": "screen_shown", "shown": true}
{"in_at_list": true, "kind": "atl_registered"}
{"kind": "embedded_python", "local_sum": 10}
{"kind": "screen_hidden", "shown": false}
{"kind": "flow_complete"}
```

1. `hud` 初始未显示，`get_screen("hud")` 返回 `None`。
2. `show screen hud` 后 `get_screen("hud")` 返回非 `None`。
3. `show eileen at slide` 后，`master` 层 `eileen` 的 `at_list` 非空。
4. 嵌入 `python:` 块正常执行，`sum(range(5))` 为 10。
5. `hide screen hud` 后 `get_screen("hud")` 再次返回 `None`。
6. 流程到 `finish()` 结束一次完整 pass。

实际（`docs/compatibility/evidence/03-screen-atl-python/actual.jsonl`，全 18 条）：

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "label": "start", "line": 23, "node": "Label", "ret": 0, "what": null, "who": null}
{"abnormal": true, "kind": "label", "label": "start"}
{"file": "game/script.rpy", "kind": "stmt", "line": 24, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "screen_initial", "shown": false}
{"file": "game/script.rpy", "kind": "stmt", "line": 25, "node": "UserStatement", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 26, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "screen_shown", "shown": true}
{"file": "game/script.rpy", "kind": "stmt", "line": 27, "node": "Show", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 28, "node": "Python", "ret": 0, "what": null, "who": null}
{"in_at_list": true, "kind": "atl_registered"}
{"file": "game/script.rpy", "kind": "stmt", "line": 29, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "embedded_python", "local_sum": 10}
{"file": "game/script.rpy", "kind": "stmt", "line": 32, "node": "UserStatement", "ret": 0, "what": null, "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 33, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "screen_hidden", "shown": false}
{"file": "game/script.rpy", "kind": "stmt", "line": 34, "node": "TranslateSay", "ret": 0, "what": "complex checked", "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 35, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "flow_complete"}
```

要点：

- 记录顺序与 `script.rpy` 的语句顺序一一对应；每条自定义观察都紧跟在触发它的 `Python` 节点之后。
- `screen_initial`/`screen_shown`/`screen_hidden` 的 `shown` 分别对应 `get_screen("hud")` 的 `None`/非 `None`/`None`，说明屏幕显隐在本 fixture 中被 `show screen`/`hide screen` 正确切换。
- `atl_registered.in_at_list = true` 说明 `Show` 执行后 `eileen` 在 `master` 层登记了 at 列表；轨迹**不**说明该 ATL 的插值过程或视觉效果。
- `embedded_python.local_sum = 10` 是嵌入 Python 块真实执行的结果，而非静态解析产物。
- 11 条 `stmt` 构成为：`Label` 1、`Python` 6（24/26/28/29/33/35 行）、`UserStatement` 2（25/32 行）、`Show` 1（27 行）、`TranslateSay` 1（34 行）。

## 自动轨迹 vs 人工观察

- 本文全部结论来自 `actual.jsonl`、`expected.jsonl` 与 `run.log`；判定依据是 JSONL 中的布尔/数值字段与节点序列。
- **未进行任何人工或像素观察**。屏幕显隐只由 `renpy.get_screen(...) is not None` 的布尔值判定；`screen hud` 中的 `text "HUD-VISIBLE"` 是否真的渲染、字号、位置、层序均**未做视觉验证**。本 testcase 也没有生成截图。
- ATL 只验证了“已登记进 `scene_lists.at_list`”，`linear 0.1` 的时间插值、最终 `xalign`、动画是否可见，均未观察。

## 限制

1. **仅覆盖静态可识别子集**：一个可显示/隐藏的 screen、一个登记到图像的 ATL、一个正常执行的 `python:` 块。完整 screen 语言、任意 ATL 行为、任意嵌入 Python 均未声称兼容。
2. `show screen`/`hide screen` 在轨迹里只有 `node=UserStatement`，没有语句名；若需静态区分，必须解析节点 `line` 文本或调用 `renpy.statements`，本 fixture 未做。
3. `get_screen` 返回的是短期对象（上游文档明确不建议纳入存档或回滚）；本 fixture 只用其布尔存在性，未验证对象字段。
4. 未覆盖 `show screen` 带参数、`_transient`/`_layer`/`_zorder`、`call screen`、屏幕动作（`action`）、`screen` 参数传递与返回值。
5. 未覆盖 ATL 的运行时插值、时间推进、`on show`/`on hide`、参数化 transform、循环/事件块与暂停语义。
6. 嵌入 Python 只验证了一个纯计算块；未覆盖副作用（改 store、调用引擎 API、异常、`hide` 模式）、`init python` 与 `python early`。
7. 未覆盖回滚/存档中 screen、ATL、Python 状态的恢复（见 `rollback.md`、`save-load.md`）。
8. 无截图、无人工观察，故“显示成功”不等于“显示正确”。

### 待研究问题（阶段 8）

以下问题本阶段不回答，交由后续引擎阶段（阶段 8）以新的 fixture 和证据解决：

- 完整 screen 语言求值：`frame`/`vbox`/`text`/`textbutton`、条件与循环、`use`/`transclude`、样式与布局属性。
- ATL 运行时：插值函数、时间基准、`linear`/`ease`/`pause`、与交互/转场的时间关系，以及变换对可观察位置的影响。
- screen action 与回滚集成：`action` 的调用时机、`SensitiveIf`、`Return`/`Jump` 类动作对执行栈的影响、回滚时 screen 状态恢复。
- 任意嵌入 Python 的副作用：store 变更、引擎 API 调用、异常传播、`hide` 模式与作用域。
- `screen` 参数传递：调用方实参到屏作用域、`use ... id`、默认值与 `scope` 更新。
- transient screen：`_transient=True` 的显示/隐藏生命周期与交互结束后的清理。
- predictive screen evaluation：预测阶段是否会执行 screen 表达式/动作，其副作用边界。

## 目标兼容等级

**暂不支持（静态子集）** — 本 fixture 只界定可静态识别的稳定子集：screen 的显示/隐藏可由 `renpy.get_screen` 观察，ATL 登记可由 `scene_lists.at_list` 观察，`python:` 块按语句正常执行。完整 screen 语言、任意 ATL 运行时行为与任意嵌入 Python 均未验证，不足以判定兼容。证据：`docs/compatibility/evidence/03-screen-atl-python/actual.jsonl`、`expected.jsonl`、`run.log`。

### 复测条件

- SDK SHA-256、upstream tag 或对照提交任一变化。
- `game/script.rpy`、`zz_evidence.rpy` 或 testcase 被修改。
- `scripts/phase01-check.ps1` 报告 `actual.jsonl` 不可复现或 `expected.jsonl` 子序列不匹配。
- 阶段 8 扩展 screen/ATL/嵌入 Python 支持时，须新增 fixture 与证据，不得覆盖本记录。
- 若需确认视觉表现（HUD 文本、ATL 动画），须另行执行人工观察或截图并登记为新的补证记录。