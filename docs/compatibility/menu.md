# `menu` 菜单与继续位置

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

- `renpy/parser.py:688 menu_statement`：把 `menu:` 解析成 `ast.Menu`。
- `renpy/ast.py:1781 class Menu`；`execute`（同文件 1829 行起）收集可选项并调用 `renpy.exports.menu`；`chain`（1815 行）上的注释写明 “Blocks of statements in a choice continue after the menu.”，并让每个选项块经 `chain_block(block, next)` 结束到 `self.next`。
- 选择结果落点：`execute` 中 `next_node(self.items[choice][2][0])` 进入所选块，`else: next_node(self.next)` 落到菜单之后的语句（1887–1890 行）。
- `renpy/exports/menuexports.py:43 menu`：过滤 `set`/条件并调用 `renpy.store.menu`。
- `renpy/exports/menuexports.py:202 display_menu`：默认 `screen="choice"`（214 行）；屏幕存在时 `show_screen(screen, items=..., _transient=True, ...)`（386 行）。
- 参考模板 `screen choice(items)` 位于 `gui/game/screens.rpy:207`；本 fixture 用自带的同名最小屏覆盖它（`game/script.rpy:8`），因此不依赖 GUI 模板。
- `renpy/defaultstore.py:373 menu = renpy.exports.display_menu`：剧本里无参数 `menu` 的最终实现。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-02-menu/`
- `game/script.rpy`：`default choice_log = []`（13 行）；`label start` 中先有菜单（16 行，选项 A 17–20 / 选项 B 21–24），菜单后 `$ emit("after_first_menu", ...)`（25 行）与 `"after first menu"`（26 行）；随后是嵌套菜单 `outer`（27–29 行）内含 `inner one`（30–33 行），最后 `$ emit("after_nested_menu", ...)`（34 行）与 `"after nested menu"`（35 行）。
- testcase：`menu_choose_b`（选 Option B）与 `menu_nested`（先 Option A，再 outer → inner one）。
- 截图：`menu_choice_shown`。

## 输入序列

`menu_choose_b`：

```text
$ arm()
run Jump("start")
advance until screen "choice"
screenshot "menu_choice_shown"
$ shot("menu_choice_shown")
click "Option B" always
advance until screen "say"
advance
exit
```

`menu_nested`：

```text
$ arm()
run Jump("start")
advance until screen "choice"
click "Option A" always
advance until screen "say"
advance until screen "choice"
click "outer" always
advance until screen "choice"
click "inner one" always
advance until screen "say"
advance
exit
```

## 预期 vs 实际观察

语义预期：

1. 进入 `menu` 节点后等待 `choice` 屏交互；选中某项才执行该选项块。
2. 选项块执行完落到菜单之后的语句，不重新进入菜单。
3. 嵌套菜单：外层选项块内再次进入 `menu`，内层选择结果落到内层菜单之后的语句。

实际（`docs/compatibility/evidence/02-menu/actual.jsonl`，按 testcase 顺序拼接；`run.log` 记录 `total_records: 30`，`lint_exit: 0`）：

```json
{"file": "game/script.rpy", "kind": "stmt", "line": 16, "node": "Menu", "ret": 0, "what": null, "who": null}
{"bytes": 7127, "kind": "screenshot", "name": "menu_choice_shown", "present": true, "sha256": "007b5d5262184817d405329b858f22e02754ea46b997b99058b70f21d111857f"}
{"file": "game/script.rpy", "kind": "stmt", "line": 23, "node": "Python", "ret": 0, "what": null, "who": null}
{"kind": "choice_taken", "which": "B"}
{"file": "game/script.rpy", "kind": "stmt", "line": 24, "node": "TranslateSay", "ret": 0, "what": "chose B", "who": null}
{"kind": "after_first_menu", "log": ["B"]}
{"file": "game/script.rpy", "kind": "stmt", "line": 26, "node": "TranslateSay", "ret": 0, "what": "after first menu", "who": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 29, "node": "Menu", "ret": 0, "what": null, "who": null}
{"kind": "nested_choice_taken", "log": ["A", "inner-one"]}
{"kind": "after_nested_menu", "log": ["A", "inner-one"]}
```

要点：

- 选 B 的实际记录顺序是 `Menu`(16) → `Python`(22，追加日志) → `Python`(23，`emit`) → `choice_taken`(which=B) → `TranslateSay`(24，“chose B”) → `Python`(25) → `after_first_menu`(log=["B"]) → `TranslateSay`(26，“after first menu”)。自定义记录 `choice_taken` 紧跟在产生它的 `Python`(23) 之后。
- 继续位置是所选块之后的 `after first menu`（26 行），同一 pass 内没有再出现 16 行的 `Menu`，与 `Menu.chain` 的注释和 `next_node(self.next)` 路径一致。
- `menu_nested` 的 pass 记录为 `Menu`(27，outer) → `Menu`(29，inner) → `Python`(31) → `Python`(32) → `nested_choice_taken`(log=["A","inner-one"]) → `TranslateSay`(33，“inner one chosen”) → `Python`(34) → `after_nested_menu`(log=["A","inner-one"]) → `TranslateSay`(35，“after nested menu”)。
- 该 pass 的第一条 16 行 `Menu` 与第二次 `Label start` 属于 **第二个 testcase 的新进程**（检查脚本对每个 testcase 单独启动 `renpy.exe`，每个用例前 `arm()` 清空文件），不是同一 pass 内菜单重跑。因此 `choice_log` 从空开始，`log` 只含 `["A"]` / `["A","inner-one"]`。
- 截图记录 `present: true`，字节数 7127 与 `sha256` 见上；PNG 本体不入仓库。

## 自动轨迹 vs 人工观察

- 全部结论来自 JSONL：语句节点序列、行号、自定义 `choice_taken`/`after_first_menu`/`nested_choice_taken`/`after_nested_menu` 记录。
- 人工观察：**无**。未对 `menu_choice_shown` 的 PNG 做像素级检查，菜单的实际排版、字号、按钮位置均未人工确认；只能确认截图生成成功及其元数据。
- 复测条件：更换 SDK/提交、修改 `game/script.rpy`、`zz_evidence.rpy` 或 testcase 后，用 README §7 单 fixture 命令或 `phase01-check.ps1` 重跑；若需确认视觉表现，须人工打开截图并与 GUI 模板对照，结果另立补证记录。

## 限制

1. `actual.jsonl` 是两个 testcase 的拼接文件，两段之间没有显式分隔记录；判断段边界要看第二次 `Label start`（12–13 行记录）。
2. 未覆盖：菜单条件项（`if` 后置条件）、`menu (set=...)`、`nvl` 菜单、菜单参数与禁用项；这些只在上游路径中确认存在，未在本 fixture 断言。
3. 未覆盖回滚/重放下的菜单行为；`choice_screen_chosen`/`MenuEntry` 的可选字段不在轨迹里。
4. `say` 节点以 `TranslateSay` 出现（翻译包装后的节点类型），不代表原始 `Say` 类名；`who` 为 `null` 因为 fixture 用的是旁白式引号行。
5. 截图只保留元数据，无法据 JSONL 判断菜单视觉布局是否与 Ren'Py GUI 模板一致。

## 目标兼容等级

**必须兼容**：选择结果、所选块执行顺序、菜单后继续语句和嵌套菜单落点都由 `actual.jsonl` 稳定复现，且现有剧本依赖这些语义才能运行；新引擎行为必须一致。证据：`docs/compatibility/evidence/02-menu/actual.jsonl`、`expected.jsonl`、`run.log`。