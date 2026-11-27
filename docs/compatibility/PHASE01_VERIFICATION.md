# 阶段 01 验收记录（Verification）

> 记录日期：2026-11-22（Asia/Shanghai）
> 对照坐标：Ren'Py `8.6.1.26111705` → commit `de379eb4f85a4930244786c715e581a1cb3fd374`
> 固定 SDK：`renpy-8.6.1-sdk`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`

本文件只记录**实跑结果**，不用计划代替证据。计划与节点定义见 `PHASE01_IMPLEMENTATION_PLAN_TREE.md`；行为等级与证据汇总见 `COMPATIBILITY_MATRIX.md`。

## 1. 环境

| 项目 | 值 |
| --- | --- |
| 引擎 | Ren'Py `8.6.1.26111705` |
| SDK | `renpy-8.6.1-sdk`（Windows ZIP SHA-256 `596c31be…0f0fdb`），本地解压于仓库外 `D:\temp\renpy-sdk-verified-20261122-root\renpy-8.6.1-sdk` |
| 对照源码 | `D:\my-project\renpy-reference-git`，提交 `de379eb4f85a4930244786c715e581a1cb3fd374` |
| 平台 / shell | Windows 11 x64；PowerShell 7（`pwsh -NoProfile`） |
| 证据通道 | Ren'Py 内置 `test` 命令 + `config.statement_callbacks`/`label_callback` 回调生成 JSONL；无人工点击 |
| Python（辅助脚本，不入库） | `C:\Users\yuki\AppData\Local\Programs\Python\Python311\python.exe` |

## 2. 执行命令与退出码

### 2.1 全量入口（实跑）

```powershell
pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk 'D:\temp\renpy-sdk-verified-20261122-root\renpy-8.6.1-sdk'
```

实跑输出（节选，2026-11-22）：

```text
==> Ren'Py SDK: D:\temp\renpy-sdk-verified-20261122-root\renpy-8.6.1-sdk\renpy.exe
    version: 8.6.1.26111705
==> Harness copies match (SHA-256 014B9F54ABC2DD1FC71D781AD00F7FDC0BCCEFCB9F8F4D5D4203416B0BFF77B0)
==> p01-01-startup
    OK (8 records)
==> p01-02-label
    OK (19 records)
...
==> p01-03-screen-atl-python
    OK (18 records)

Phase 01 checks passed (14 fixtures).
```

退出码 `0`。14 个 fixture 全部 `OK`，各 testcase 均为 `Status: PASSED`、进程退出码 `0`。该结果在本会话中重复多次稳定复现。

### 2.2 单 fixture 入口（README §7 模板）

`renpy.exe <project> lint --error-code` 后 `renpy.exe <project> test <testcase> --savedir <dir>`；`SUIYU_EVIDENCE` 指定轨迹输出路径。save/load 需按 `save_case` → `load_case` 顺序共用同一 `--savedir`。

### 2.3 退出码语义（实测）

| 情形 | 退出码 | 依据 |
| --- | --- | --- |
| testcase 通过 | 0 | `renpy/test/testexecution.py:quit_handler` |
| testcase failed | 1 | 同上 |
| testcase timeout | 1 | 同上 |
| lint 有问题（未定义图像/不可达语句等） | 1 | `lint --error-code` |
| lint 干净 | 0 | 同上 |

## 3. 逐 fixture 结果

| fixture | testcases | 记录数 | lint | 结果 |
| --- | --- | --- | --- | --- |
| `p01-01-startup` | `startup_reach` | 8 | 0 | OK |
| `p01-02-label` | `label_entry`, `label_from_start` | 19 | 0 | OK |
| `p01-02-jump` | `jump_forward`, `jump_skip` | 17 | 0 | OK |
| `p01-02-call-return` | `nested_call`, `call_empty` | 27 | 0 | OK |
| `p01-02-say` | `say_forms` | 11 | 0 | OK |
| `p01-02-menu` | `menu_choose_b`, `menu_nested` | 30 | 0 | OK |
| `p01-02-define` | `define_init` | 7 | 0 | OK |
| `p01-02-default` | `default_lifecycle` | 19 | 0 | OK |
| `p01-03-display` | `display_ops` | 28 | 0 | OK |
| `p01-03-audio` | `audio_lifecycle` | 19 | 0 | OK |
| `p01-03-transitions` | `transitions_apply` | 17 | 0 | OK |
| `p01-03-save-load` | `save_case`, `load_case` | 31 | 0 | OK |
| `p01-03-rollback` | `rollback_restores` | 26 | 0 | OK |
| `p01-03-screen-atl-python` | `screen_atl_python` | 18 | 0 | OK |

检查脚本执行的校验（`scripts/phase01-check.ps1`）：① 解析并校验 SDK 版本含 `8.6.1`；② 校验每个 fixture 的 `game/zz_evidence.rpy` 与 `harness/zz_evidence.rpy` SHA-256 逐字节一致；③ 每 fixture 复制 `game` 到仓库外临时项目并 `lint --error-code`；④ 每 testcase 以独立进程运行并要求退出码 `0` 且输出含 `Status: PASSED`；⑤ 非截图记录与实际基线 `actual.jsonl` **逐字节**一致（截图只比 `name`+`present`）；⑥ `expected.jsonl` 作为**有序子序列**在 `actual.jsonl` 中命中。

## 4. 证据路径

| 行为 | 证据目录 |
| --- | --- |
| B01 启动链 | [`evidence/01-startup/`](evidence/01-startup/)（含 `structural.json`） |
| B02 label | [`evidence/02-label/`](evidence/02-label/) |
| B03 jump | [`evidence/02-jump/`](evidence/02-jump/) |
| B04 call/return | [`evidence/02-call-return/`](evidence/02-call-return/) |
| B05 say | [`evidence/02-say/`](evidence/02-say/) |
| B06 menu | [`evidence/02-menu/`](evidence/02-menu/) |
| B07 define | [`evidence/02-define/`](evidence/02-define/) |
| B08 default | [`evidence/02-default/`](evidence/02-default/) |
| B09 display | [`evidence/03-display/`](evidence/03-display/) |
| B10 audio | [`evidence/03-audio/`](evidence/03-audio/) |
| B11 transitions | [`evidence/03-transitions/`](evidence/03-transitions/) |
| B12 save/load | [`evidence/03-save-load/`](evidence/03-save-load/) |
| B13 rollback | [`evidence/03-rollback/`](evidence/03-rollback/) |
| B14 screen/ATL/Python | [`evidence/03-screen-atl-python/`](evidence/03-screen-atl-python/) |

每个目录含 `actual.jsonl`、`expected.jsonl`、`run.log`；`01-startup` 另含 `structural.json`。

## 5. 自动轨迹 vs 人工观察（严格分开）

### 5.1 自动部分（已执行，可复现）

- 全部 14 个 fixture 的 `actual.jsonl`/`expected.jsonl`/`run.log` 由 `test` 命令 + 回调生成，非截图记录逐字节可复现。
- 自动截图生成于 5 处（`startup_at_start`、`say_plain_narration`、`menu_choice_shown`、`display_final_layer`、`transition_final`），仅以元数据（`name`/`present`/`bytes`/`sha256`）记录，PNG 不入库。
- 启动链的 boot/compile 阶段由 `structural.json`（`compile` 产物 + `run --json-dump` 源映射）补证。

### 5.2 人工部分（**未执行**）

**本阶段未进行任何人工 GUI / 像素 / 试听观察。** 具体未确认项：

- 主菜单呈现与“开始游戏”点击未观察（fixture 用 `run Jump("start")` 跳过主菜单）。
- 对白排版、字体、说者窗口、替换后文本的最终视觉呈现未确认（只记录节点原始文本）。
- 菜单按钮布局、层序遮挡、`zorder` 的实际绘制效果未确认。
- 音频未试听（只读 `get_playing` 的通道→文件名映射）。
- 转场视觉、动画时序未确认（仅有截图元数据）。
- HUD 文本 `HUD-VISIBLE` 是否真正渲染、ATL 动画是否可见未确认。

凡需上述视觉/听感判定，须另立人工观察或截图补证记录，不修改既有等级与基线。

## 6. 限制与复测条件

1. **证据基线与 SDK 强绑定**：SDK SHA、对照提交或 fixture/harness 变化时，须重跑全量入口并人工审定新基线；检查脚本会因逐字节不一致而失败，属预期保护。
2. **截图不做像素断言**：PNG 字节随 GPU/驱动变化，检查脚本只比 `name`+`present`；`bytes`/`sha256` 变化须记录，不计为回归。
3. **`structural.json` 不由检查脚本重生成**：`compile` 与 `run --json-dump` 需在带窗口会话手工执行；SDK 或提交变化时须手工重跑并替换。
4. **多 testcase 拼接无分隔**：B02/B03/B06/B12 的 `actual.jsonl` 是逐 testcase 输出拼接，拼接处无标记，判读须按 label 记录或重复段顺序，详见各行为文档“限制”。
5. **回滚轨迹形状**：B13 因每次重放到 `renpy.rollback` 再触发回滚，轨迹呈 19–23 行循环，`after_rollback`/`"D"`/`done` 不出现；要求的是“恢复已记录 store 状态与控制位置”的语义，不是复刻轨迹形状。
6. **B14 仅静态子集**：完整 screen/ATL/嵌入 Python 兼容性未判定，列阶段 8 待研究。

## 7. 交给下游阶段的决策清单

| 下游阶段 | 可引用的已定决策 | 依据 |
| --- | --- | --- |
| 阶段 2–5 | 启动链到 `start` 可达、编译产物位置、init 按 priority 执行 | B01、`01-startup/structural.json` |
| 阶段 3、7 | 图层状态模型：scene 清层写单项、show 按 tag 追加、同 tag 替换、hide 按 tag 移除、zorder 属性 | B09 |
| 阶段 4 | label/jump/call/return 的返回栈深度语义、菜单续行与嵌套落点、对白 who/what 原始文本 | B02–B06 |
| 阶段 4–5 | define init 求值、default start 前初始化 + 显式覆盖 + 读档默认值补齐 | B07、B08、B12 |
| 阶段 6 | 存档保存 store+回滚日志、读档跨进程恢复到 checkpoint、`after_load` 独立上下文、回滚恢复 store 与控制位置 | B12、B13 |
| 阶段 7 | 音频 API 级播放状态映射（允许时序不同）、转场语句执行与流程推进（允许视觉不同） | B10、B11 |
| 阶段 8 | screen 显隐、ATL 登记、嵌入 Python 执行的静态子集；完整行为待研究 | B14 |

**验收结论：** `scripts/phase01-check.ps1` 在固定 SDK 上实跑通过（退出码 0，14/14 fixture），每个核心行为均有冻结证据、可运行 fixture 与明确兼容等级；GUI 行为已分别记录自动轨迹与“人工未做”声明。CI 入口见 `.github/workflows/phase01.yml`。