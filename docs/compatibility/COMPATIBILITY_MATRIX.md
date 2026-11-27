# 阶段 01 兼容性矩阵

> 记录日期：2026-11-22（Asia/Shanghai）
> 对照坐标：Ren'Py `8.6.1.26111705` → commit `de379eb4f85a4930244786c715e581a1cb3fd374`
> 固定 SDK：`renpy-8.6.1-sdk`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`

本文件汇总 B01..B14 共 14 个核心行为的兼容等级、证据、fixture、负责阶段与差异/复测条件。等级定义见 `README.md` §8；每条等级都必须链接真实证据文件，无证据不得写等级。

## 1. 等级总览

| 编号 | 行为 | 目标等级 | 证据 | fixture | 负责阶段 | 详情 |
| --- | --- | --- | --- | --- | --- | --- |
| B01 | 启动链（boot → 编译 → init → main menu → start） | 必须兼容 | [`01-startup`](evidence/01-startup/) | `p01-01-startup` | 阶段 1；交阶段 2–5 | [startup-chain.md](startup-chain.md) |
| B02 | `label` 定义与进入 | 必须兼容 | [`02-label`](evidence/02-label/) | `p01-02-label` | 阶段 1；交阶段 4 | [label.md](label.md) |
| B03 | `jump` 跳转 | 必须兼容 | [`02-jump`](evidence/02-jump/) | `p01-02-jump` | 阶段 1；交阶段 4 | [jump.md](jump.md) |
| B04 | `call` / `return` 调用返回位置、嵌套 | 必须兼容 | [`02-call-return`](evidence/02-call-return/) | `p01-02-call-return` | 阶段 1；交阶段 4 | [call-return.md](call-return.md) |
| B05 | `say` 对白的 who/what 与原始文本保留（多行/转义未断言） | 必须兼容 | [`02-say`](evidence/02-say/) | `p01-02-say` | 阶段 1；交阶段 4–5 | [say.md](say.md) |
| B06 | `menu` 菜单及继续位置、嵌套 | 必须兼容 | [`02-menu`](evidence/02-menu/) | `p01-02-menu` | 阶段 1；交阶段 4–5 | [menu.md](menu.md) |
| B07 | `define` 常量与初始化时序 | 必须兼容 | [`02-define`](evidence/02-define/) | `p01-02-define` | 阶段 1；交阶段 4–5 | [variables.md](variables.md) |
| B08 | `default` 初始化与读档默认值 | 必须兼容 | [`02-default`](evidence/02-default/) | `p01-02-default` | 阶段 1；交阶段 4–5 | [variables.md](variables.md) |
| B09 | `scene` / `show` / `hide` 清空、替换、层序 | 必须兼容 | [`03-display`](evidence/03-display/) | `p01-03-display` | 阶段 1；交阶段 3、7 | [display.md](display.md) |
| B10 | 音频播放/停止可观察状态 | 允许不同（时序） | [`03-audio`](evidence/03-audio/) | `p01-03-audio` | 阶段 1；交阶段 7 | [audio.md](audio.md) |
| B11 | 转场可观察结果 | 允许不同（视觉细节） | [`03-transitions`](evidence/03-transitions/) | `p01-03-transitions` | 阶段 1；交阶段 7 | [transitions.md](transitions.md) |
| B12 | 存档/读档跨进程状态 | 必须兼容 | [`03-save-load`](evidence/03-save-load/) | `p01-03-save-load` | 阶段 1；交阶段 6 | [save-load.md](save-load.md) |
| B13 | 回滚记录与状态恢复 | 必须兼容（语义） | [`03-rollback`](evidence/03-rollback/) | `p01-03-rollback` | 阶段 1；交阶段 6 | [rollback.md](rollback.md) |
| B14 | screen / ATL / 嵌入 Python 边界 | 暂不支持（静态子集） | [`03-screen-atl-python`](evidence/03-screen-atl-python/) | `p01-03-screen-atl-python` | 阶段 1；交阶段 8 | [screen-atl-python.md](screen-atl-python.md) |

统计：必须兼容 11 条（B01–B09、B12、B13），允许不同 2 条（B10、B11），暂不支持 1 条（B14）。共 14 条，满足“≥10 核心行为”。

## 2. 证据文件构成

每个 `evidence/<id>/` 目录包含：

- `actual.jsonl`：冻结的实际轨迹基线，非截图记录逐字节可复现（检查脚本强制比对）。
- `expected.jsonl`：人工语义预期，作为有序子序列被检查脚本断言。
- `run.log`：SDK 指纹、对照提交、引擎版本、`lint_exit`、testcases、记录条数与种类、截图清单。
- `01-startup` 额外含 `structural.json`：`compile` 产物与 `run --json-dump` 源映射（游戏内轨迹看不到的 boot/compile 阶段）。

截图仅以**元数据**形式进入 `actual.jsonl`（`name`/`present`/`bytes`/`sha256`），PNG 本体不入仓库；检查脚本对截图只比对 `name`+`present`。全量复验命令：`pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>`。

## 3. 差异与复测条件（按等级）

### 必须兼容（B01–B09、B12、B13）

语义须逐条复现。差异只在 SDK/提交/fixture/harness 变化时出现，届时重跑检查脚本并人工审定新基线；不得用“已修复”代替复测记录。各条的具体复测面见对应文档“限制/复测条件”小节。

- B08 备注：干净首启值依赖 fixture 的 `allow_mutation` 守卫隔离 ambient pass 与测试 pass；守卫移除会导致 `default_initial` 退回污染值并使数值断言失败，届时须重新处理取证手法而非放宽断言。
- B12/B13 备注：`actual.jsonl` 是多 testcase 拼接（B12 为两进程、B13 为单进程重放）；拼接处无分隔标记，须按 label 记录或重复段顺序判读，详见各文档“限制”。

### 允许不同（B10 音频时序、B11 转场视觉）

- B10：只要求“在指定通道上播放/停止哪个文件”的可观察映射一致；淡入淡出时序、解码启动时机、真实音频输出允许不同。证据只读 `renpy.music.get_playing`，不做试听/波形断言。
- B11：只要求转场语句按序执行且流程推进到后续语句；像素、时序、视觉细节不做逐字节等价断言。仅截图元数据，无像素审查。

### 暂不支持（B14 screen/ATL/嵌入 Python）

仅界定可静态识别的稳定子集：screen 显隐（`renpy.get_screen`）、ATL 登记（`scene_lists.at_list`）、`python:` 块正常执行。完整 screen 语言、任意 ATL 运行时、任意嵌入 Python 的边界列为阶段 8 待研究问题（见 `screen-atl-python.md`）。

## 4. 人工观察状态

**全部 14 条均未进行人工 GUI / 像素 / 试听观察。** 证据来自自动轨迹（JSONL）与自动截图元数据；GUI 类行为（B01 主菜单、B05 对白排版、B09 画面、B10 听感、B11 转场视觉、B14 HUD 渲染）一律在各自文档“自动轨迹 vs 人工观察”小节标注“未人工确认”，并给出人工补证条件。凡需像素/听感判定，须另立补证记录，不修改本矩阵既有等级。

## 5. 下游阶段引用面

- 阶段 3、7：B09 图层状态模型（`scene`/`show`/`hide`/`zorder` 的条目集合语义）。
- 阶段 4：B02–B04 控制流（`label`/`jump`/`call`/`return` 与返回栈深度），B05/B06 对白（who/what 与原始文本）与菜单续行。
- 阶段 4–5：B07/B08 初始化时序（`define` init 求值、`default` start 前初始化与显式覆盖），B12 读档默认值补齐。
- 阶段 6：B12 存档/读档跨进程恢复，B13 回滚状态与控制位置恢复。
- 阶段 8：B14 screen/ATL/嵌入 Python 静态子集与待研究清单。

矩阵中任一等级或证据变动都必须同步更新本文件与对应行为文档，并重跑 `scripts/phase01-check.ps1`。复测条件：任一行为等级改变、证据重采、或 Ren'Py SDK/对照提交变更。