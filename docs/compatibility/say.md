# say 对白

## 环境

- Ren'Py SDK：`renpy-8.6.1-sdk`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`
- upstream tag：`8.6.1.26111705`；对照提交：`de379eb4f85a4930244786c715e581a1cb3fd374`
- 平台：Windows 11 x64；PowerShell 7
- 全量命令：`pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>`
- 单 fixture 手工运行：见 `docs/compatibility/README.md` §7

## 上游代码路径与符号

- `renpy/ast.py:876` `class Say(Node)`，字段 `who: str | None`、`what: str`。`Say.__init__`（`:893`）对 `who` 走 `who_fast` 判定，`what` 原样存入 `self.what`。
- `renpy/ast.py:973` `Say.execute`：`next_node(self.next)` → `eval_who(self.who, self.who_fast)` → 经 `renpy.exports.say(who, what, ...)`（`:1022`）显示。`what` 在节点内保持**未替换的原始文本**；替换发生在显示层。
- `renpy/ast.py:2916` `class TranslateSay(Say)`。`TranslateSay.execute`（`:2970`）先查翻译，未命中才 `Say.execute(self)`（`:2995`）。编译期所有 say 语句均被包成 `TranslateSay`，故轨迹里的 `node` 为 `TranslateSay` 而非 `Say`。
- 显示实现位于 `renpy/character.py`：`Character.__call__`（`renpy/character.py:1494`）→ `do_display`（`:1240`）→ `display_say`（`:566`）。变量替换由 `renpy/substitutions.py:339` `substitute(s, ...)` 完成，作用于显示文本而非节点 `what`。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-02-say/`
- `game/script.rpy`：`define e = Character("Eileen")`（第 13 行）、`default name_var = "Variable Name"`（第 14 行）；`label start`（第 16 行）依次 6 种 say 形态（第 17–22 行）后 `$ finish()`。
- testcase：`say_forms`。
- 证据：`docs/compatibility/evidence/02-say/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`，共 11 条记录；`screenshots: say_plain_narration`）。

## 输入序列

- `$ arm()` → `run Jump("start")` → `advance until screen "say"`（停在第 1 条对白）→ `screenshot "say_plain_narration"` → `$ shot("say_plain_narration")` → 连续 6 次 `advance` → `$ disarm()` → `exit`。
- 截图只取第一条“plain narration”所在帧；后续 5 条对白只记录 `stmt`，不截图。

## 预期 vs 实际观察

语义预期：每种 say 形态产生一条 `TranslateSay` 记录；`what` 为节点内的原始文本（替换前的 `[name_var]` 亦然）；`who` 反映说话者，旁白为 `null`，显式旁白为 `"narrator"`，`e` 角色为 `"e"`；`ret` 恒为 0。

实际（`docs/compatibility/evidence/02-say/actual.jsonl`，节选，保留真实文本）：

```jsonl
{"file": "game/script.rpy", "kind": "stmt", "line": 17, "node": "TranslateSay", "ret": 0, "what": "plain narration", "who": null}
{"bytes": 4908, "kind": "screenshot", "name": "say_plain_narration", "present": true, "sha256": "fa3598eeff7a975086f83e4385e947b62a65ff3091836e5bc432c412439f58ef"}
{"file": "game/script.rpy", "kind": "stmt", "line": 18, "node": "TranslateSay", "ret": 0, "what": "character line", "who": "e"}
{"file": "game/script.rpy", "kind": "stmt", "line": 20, "node": "TranslateSay", "ret": 0, "what": "narrator explicit", "who": "narrator"}
{"file": "game/script.rpy", "kind": "stmt", "line": 21, "node": "TranslateSay", "ret": 0, "what": "substitution [name_var]", "who": "e"}
{"kind": "flow_complete"}
```

- 六种形态的实际 `what` 依次为：`"plain narration"`、`"character line"`（`who=e`）、`"line with quoted text"`、`"narrator explicit"`（`who=narrator`）、`"substitution [name_var]"`（`who=e`，**替换前的原始文本**）、`"two words"`；`line` 为 17–22，`ret` 全为 0。
- 截图记录 `present: true`、`bytes: 4908`、`sha256: fa3598…f58ef`；PNG 本体不入库，仅元数据。
- `expected.jsonl` 断言了上述 6 条 `TranslateSay` 与截图记录的有序子序列，全部命中。

## 自动轨迹 vs 人工观察

- 本文结论全部来自 `actual.jsonl` 与截图元数据；**未进行人工 GUI 观察或像素审查**。截图只证明“生成了 PNG 且字节非空/有哈希”，未评估文字排版、字体、说话者名字框等视觉呈现。
- 复测条件：SDK SHA / 对照提交 / harness 变化时重跑；截图字节随 GPU/驱动变化，检查脚本仅比对 `name`+`present`，故像素差异不视为回归，但 `bytes`/`sha256` 变化须记录。

## 限制

- 只覆盖 6 种基础形态；未覆盖 `nointeract`、`extend`、`with`、形象属性（`e happy`）、多行字符串与转义序列（`\n`、`\"`、`{w}` 等文本标签）。
- `what` 记录的是节点原始文本，`substitution [name_var]` 证明替换未回写节点；但**未验证**最终显示文本确实替换为 `Variable Name`（显示层结果属像素/GUI 范畴）。
- 截图只取旁白帧，角色名显示、`who` 渲染、说者窗口布局均未经人工确认。
- 未验证翻译命中路径（`TranslateSay.lookup` 非空时跳转翻译节点）。

## 目标兼容等级

**必须兼容** — say 的 `who`/`what` 记录形状与原始文本保留是剧本对白复用的基础语义，必须逐条对齐（依据 `docs/compatibility/evidence/02-say/actual.jsonl` 与 `say_plain_narration` 截图元数据）。