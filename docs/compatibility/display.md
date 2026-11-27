# scene / show / hide：clear、replace 与 zorder 图层状态

## 环境

- Ren'Py SDK：`renpy-8.6.1-sdk`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`
- upstream tag：`8.6.1.26111705`；对照提交：`de379eb4f85a4930244786c715e581a1cb3fd374`
- 平台：Windows 11 x64；PowerShell 7
- 全量命令：`pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>`
- 单 fixture 手工运行：见 `docs/compatibility/README.md` §7；本 fixture 的 testcase 为 `display_ops`
- 证据：`docs/compatibility/evidence/03-display/` 下的 [actual.jsonl](evidence/03-display/actual.jsonl)、[expected.jsonl](evidence/03-display/expected.jsonl)、[run.log](evidence/03-display/run.log)

## 上游代码路径与符号

- `renpy/ast.py:1376` `class Show`；`Show.execute` 位于 `renpy/ast.py:1396`。
- `renpy/ast.py:1488` `class Scene`；`Scene.execute` 位于 `renpy/ast.py:1516`。
- `renpy/ast.py:1548` `class Hide`；`Hide.execute` 位于 `renpy/ast.py:1590`。
- `renpy/exports/displayexports.py:382` `show`；`:544` `hide`；`:576` `scene`。
- `renpy/display/scenelists.py:44` `class SceneListEntry`；`:81` `class SceneLists`。`SceneLists` 持有 `layers` / `at_list` 字段，`SceneListEntry` 持有 `tag` / `zorder` / `name` 字段。

可观测的图层状态取自 `renpy.game.context().scene_lists.layers["master"]`：fixture 的 `layer_state()` 遍历该列表，逐项读取 `d.tag`、`list(d.name)`、`d.zorder`。因此本文断言的是 **master 层的条目集合、tag、图像名与 zorder 属性**。`zorder` 是可观测的排序属性，不是像素结果或绘制顺序的断言。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-03-display/`
- `game/script.rpy`：
  - 第 1-5 行以内联 `Solid` 定义 `bg room`、`bg hall`、`alice neutral`、`alice happy`、`bob`。
  - 第 19-22 行 `init python` 定义 `layer_state()`：

    ```renpy
    def layer_state():
        sl = renpy.game.context().scene_lists.layers["master"]
        return [{"tag": d.tag, "name": list(d.name), "zorder": d.zorder} for d in sl]
    ```

  - 第 24-41 行 `label start` 依次执行 `scene bg room` → `show alice neutral` → `show bob` → `show alice happy` → `hide alice` → `scene bg hall` → `show bob at truecenter zorder 5` → `"display checked"` → `$ finish()`，每个操作后调用 `emit()` 记录一次图层快照。
  - 第 52-61 行 `testcase display_ops`。
- `game/zz_evidence.rpy` 为 `harness/zz_evidence.rpy` 的逐字节副本。
- 证据：[actual.jsonl](evidence/03-display/actual.jsonl)（28 条记录）、[expected.jsonl](evidence/03-display/expected.jsonl)、[run.log](evidence/03-display/run.log)（`lint_exit: 0`，`total_records: 28`，`screenshots: display_final_layer`）。

## 输入序列

- 测试入口：`$ arm()` → `run Jump("start")` → `advance until screen "say"`。
- `label start` 内的语句序列（即被观测的显示操作序列）：
  1. `scene bg room`
  2. `show alice neutral`
  3. `show bob`
  4. `show alice happy`（同 tag、不同图像）
  5. `hide alice`
  6. `scene bg hall`
  7. `show bob at truecenter zorder 5`
  8. `"display checked"`（`TranslateSay`）
- 测试序列：`screenshot "display_final_layer"` → `$ shot("display_final_layer")` → `$ emit("test_pause")` → `advance` → `$ disarm()` → `exit`。
- 对白推进后执行 `$ finish()`，产生 `flow_complete`。

## 预期 vs 实际观察

语义预期（[expected.jsonl](evidence/03-display/expected.jsonl) 按有序子序列断言）：

- `scene` 清空 master 层，然后只写入场景图像这一项。
- `show` 以 tag 为键向 master 层追加条目；未指定时 `zorder` 为 0。
- 同 tag 的 `show`（图像不同）替换该 tag 的条目，列表位置保持。
- `hide` 按 tag 移除条目。
- `show ... zorder 5` 把 `zorder` 记录到对应条目上。

实际（[actual.jsonl](evidence/03-display/actual.jsonl)，全部 7 条图层快照）：

```jsonl
{"kind": "layer_initial", "state": [{"name": ["bg", "hall"], "tag": "bg", "zorder": 0}, {"name": ["bob"], "tag": "bob", "zorder": 5}]}
{"kind": "layer_after_scene", "state": [{"name": ["bg", "room"], "tag": "bg", "zorder": 0}]}
{"kind": "layer_after_shows", "state": [{"name": ["bg", "room"], "tag": "bg", "zorder": 0}, {"name": ["alice", "neutral"], "tag": "alice", "zorder": 0}, {"name": ["bob"], "tag": "bob", "zorder": 0}]}
{"kind": "layer_after_replace", "state": [{"name": ["bg", "room"], "tag": "bg", "zorder": 0}, {"name": ["alice", "happy"], "tag": "alice", "zorder": 0}, {"name": ["bob"], "tag": "bob", "zorder": 0}]}
{"kind": "layer_after_hide", "state": [{"name": ["bg", "room"], "tag": "bg", "zorder": 0}, {"name": ["bob"], "tag": "bob", "zorder": 0}]}
{"kind": "layer_after_clear", "state": [{"name": ["bg", "hall"], "tag": "bg", "zorder": 0}]}
{"kind": "layer_after_zorder", "state": [{"name": ["bg", "hall"], "tag": "bg", "zorder": 0}, {"name": ["bob"], "tag": "bob", "zorder": 5}]}
```

逐次转换：

- `scene bg room`（第 26 行）后：master 层由 `[{bg,hall,z0},{bob,z5}]` 变为仅 `[{bg,room,z0}]`，原有的 bg 与 bob 都被清除，再写入新的场景条目。
- `show alice neutral`（第 28 行）+ `show bob`（第 29 行）后：在 bg 之后按调用顺序追加 `alice` 与 `bob`，两者默认 `zorder` 为 0，得到 `[{bg,room,z0},{alice,neutral,z0},{bob,z0}]`。
- `show alice happy`（第 31 行）后：`alice` 条目的 `name` 由 `["alice","neutral"]` 变为 `["alice","happy"]`，位置仍在 bg 与 bob 之间；bg、bob 不变，条目总数不变（替换而非追加）。
- `hide alice`（第 33 行）后：按 tag 移除 alice，剩余 `[{bg,room,z0},{bob,z0}]`。
- `scene bg hall`（第 35 行）后：master 层清空后仅写入 `[{bg,hall,z0}]`，bob 消失。
- `show bob at truecenter zorder 5`（第 37 行）后：bob 重新作为新条目追加，`zorder` 为 5；bg 仍为 0。`at truecenter` 不进入 `layer_state()` 的观测字段，本文不对其位置作断言。

其余记录：

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "line": 39, "node": "TranslateSay", "ret": 0, "what": "display checked", "who": null}
{"bytes": 7749, "kind": "screenshot", "name": "display_final_layer", "present": true, "sha256": "fe6a10be0630840552d0e5090c60bd111c507e9044aad0bb509373ddfdb96e61"}
{"kind": "test_pause"}
{"file": "game/script.rpy", "kind": "stmt", "line": 40, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "flow_complete"}
```

`expected.jsonl` 不包含 `layer_initial`，从 `layer_after_scene` 开始断言；其记录按顺序出现在 `actual.jsonl` 中，匹配通过。`run.log` 记录 `stmt: 17`、7 类图层快照各 1 条（`layer_initial` + 6 条 `layer_after_*`）、`screenshot: 1`、`test_pause: 1`、`label: 1`、`flow_complete: 1`，与 28 条总数一致。

## 自动轨迹 vs 人工观察

- 本文全部结论来自 `actual.jsonl` 的 JSONL 轨迹、`expected.jsonl` 的语义断言与 `run.log` 的运行摘要；**未进行任何人工 GUI 观察或像素审查**。
- 截图仅有元数据：`display_final_layer` 的 `present: true`、`bytes: 7749`、`sha256: fe6a10be...e61`；PNG 本体不入仓库，未做像素比对，不能据此断言最终画面的颜色、布局或遮挡关系。
- 复测条件：SDK SHA-256、upstream tag/对照提交、`zz_evidence.rpy`（`emit`/`shot`/`arm` 时序）、fixture 的 scene/show/hide 序列任一变化，或 `scripts/phase01-check.ps1` 报告 `actual.jsonl` 不可复现 / `expected.jsonl` 子序列不匹配时，须重跑 `p01-03-display` 的 `display_ops`（lint 后执行 `renpy.exe <project> test display_ops --savedir <dir>`），再按新的 `actual.jsonl` 重新审定基线。

## 限制

- `layer_initial` 是已知取证 artifact：环境启动阶段（ambient boot pass）在 `arm()` 之前已经执行过一次 `start`，其结束态 `[{bg,hall,z0},{bob,z5}]` 残留在 master 层。本文不把 `layer_initial` 当作语义断言，`expected.jsonl` 也从 `layer_after_scene` 开始；有意义的是 6 条 `layer_after_*` 快照。
- `zorder` 只是可观测的排序属性，**不构成绘制顺序 / 像素结果断言**；本文没有验证 zorder 是否改变实际遮挡、合成顺序或屏幕像素。
- 只读取 `layers["master"]`；`screens`、`overlay`、`transient`、`top-level` 等其他层，以及 layer 的显示/隐藏本身，均未覆盖。
- 只观测 `tag` / `name` / `zorder`；`at_list`、ATL、transform 参数、位置（`truecenter`）、alpha、动画时间与 transition 状态都不在快照中。`show bob at truecenter` 只验证了 `zorder: 5`。
- 未覆盖 `scene`/`show`/`hide` 的 transition 形式、同语句多 tag 的 `hide`、`show` 的 `as` 重命名、`behind`/`onlayer` 等参数，也未覆盖 rollback、save/load 后图层状态的恢复。
- `expected.jsonl` 是有序子序列断言，不是全量逐字节相等断言；`actual.jsonl` 中的 stmt / label 记录只用于定位执行路径，不构成显示语义断言。
- 截图 `display_final_layer` 只登记元数据；fixture 图像均为 `Solid` 色块，即使有 PNG 也不能替代人工像素审查。本次**未进行人工像素观察**。
- 启动预热执行 `start` 的行为依赖 harness 与 `_test` setup（`timeout`、`transition_timeout`、`screenshot_directory`、`overwrite_screenshots`）；若这些前置改变，`layer_initial` 乃至首条快照的时序需要重新取证。

## 目标兼容等级

**必须兼容** — scene 清层后写入单项、show 按 tag 追加、同 tag 替换、hide 按 tag 移除、show 设置 zorder 是现有剧本显示状态的基础语义，新引擎必须逐条复现；依据 [actual.jsonl](evidence/03-display/actual.jsonl) 与 [expected.jsonl](evidence/03-display/expected.jsonl) 的有序断言。