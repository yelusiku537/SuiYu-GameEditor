# 阶段 01 实施计划树

> 生成日期：2026-11-22（Asia/Shanghai）
> 需求基线：`docs/superpowers/plans/phase-01/README.md` 与阶段 01 精准执行提示词
> 对照坐标：Ren'Py `8.6.1.26111705` → commit `de379eb4f85a4930244786c715e581a1cb3fd374`
> 固定 SDK：`renpy-8.6.1-sdk`，Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`

本文件是阶段 01 的计划事实源。每个节点记录目标、依赖、输入、产出路径、验收标准、风险、负责阶段与复测条件。计划树节点编号 `N01-xx` 与任务编号 `P01-0x` 对应。

## 0. 证据通道决策（已实测）

阶段 01 的“实际观察”不依赖人工点击，使用 Ren'Py 内置 `test` 命令 + 回调钩子生成确定性轨迹。以下事实已在本地固定 SDK 上实测确认，构成本计划的技术前提：

| 事实 | 实测结果 | 依据 |
| --- | --- | --- |
| 自动化入口 | `renpy.exe <project> test <testcase> --savedir <dir>` 无需人工输入即可运行到结束 | `renpy/test/testcli.py` `test_command` |
| 语句观测 | `config.statement_callbacks` 回调可取得当前节点 `type().__name__`、`filename`、`linenumber`、`what`、`who`、`name`、`len(context.return_stack)` | `renpy/ast.py` `statement_name`、`renpy/execution.py` `Context` |
| label 观测 | `config.label_callback(label, abnormal)` 记录非 `_` 前缀 label | `renpy/execution.py` |
| 轨迹确定性 | 同一 fixture 连续 5 次运行，JSONL 逐字节一致 | 本地实测，见 §3 N01-05 |
| 退出码 | 用例通过 → `0`；`failed` → `1`；`timeout` → `1` | `renpy/test/testexecution.py` `quit_handler` |
| 退出稳定写法 | `click <text>` 之后紧跟 `exit`（中间不得有 `advance`），否则用例挂起超时 | 本地实测 |
| 阻塞等待 | `advance until eval <flag>` 需要下一次交互才生效；纯 Python 赋值后无交互会“Possible infinite loop” | 本地实测 |
| 截图 | `screenshot "<name>"` 在 `_test.screenshot_directory` 下生成 PNG；同机两次运行 SHA-256 一致 | `renpy/test/testast.py` `Screenshot` |
| 源码地图 | `run --json-dump <file>` 输出 `location.label` 等 label→源文件行映射 | `renpy/arguments.py` |
| 编译产物 | `compile` 生成 `game/*.rpyc` 与 `game/cache/*.rpyb` | 本地实测 |
| 关键陷阱 | `init python` 顶层 `import renpy` 会遮蔽 Ren'Py 懒加载代理，导致 `renpy.music` 缺失；必须在函数内 `import renpy` | 本地实测 |
| lint | 有 lint 问题（如未定义图像）时 `lint --error-code` 返回 `1`；无问题时返回 `0` | 本地实测 |

### 证据通道的两个隔离面

1. **自动轨迹**：`test` 命令 + JSONL。可重复、逐字节可比。
2. **自动截图 + 人工观察**：`screenshot` 语句生成 PNG（只提交清单与哈希），人工像素观察标为未执行并写复测条件。

## 1. 目录与命名约定

```text
docs/compatibility/
├── README.md                      # 写作约定（P01-01）
├── PHASE01_IMPLEMENTATION_PLAN_TREE.md   # 本文件
├── COMPATIBILITY_MATRIX.md        # P01-04 汇总矩阵
├── startup-chain.md               # P01-01
├── label.md / jump.md / call-return.md / say.md / menu.md / variables.md   # P01-02
├── display.md / audio.md / transitions.md / save-load.md / rollback.md     # P01-03
├── screen-atl-python.md           # P01-03 复杂特性边界
└── evidence/
    └── <fixture-id>/
        ├── actual.jsonl           # 提交的实际轨迹（确定性）
        ├── expected.jsonl         # 提交的预期轨迹（人工审定的基线）
        ├── run.log                # 提交的运行摘要（exit code + Status 行）
        └── screenshots.manifest.json  # 截图清单：名称、相对路径、字节数、SHA-256

compatibility-tests/fixtures/renpy/phase01/
├── README.md
├── harness/
│   └── zz_evidence.rpy            # 规范 harness 副本（唯一事实源）
└── <fixture-id>/
    └── game/
        ├── script.rpy             # 纯剧情脚本（不含 harness）
        ├── zz_evidence.rpy        # 与 harness/zz_evidence.rpy 逐字节一致（自包含）
        └── options.rpy            # 必要时仅设 config.developer 等最小项
```

命名规则：

- fixture 目录：`p01-<任务号>-<行为>`，全小写、短横线分隔，如 `p01-02-call-return`。
- testcase 名：与行为同名，如 `call_return`。
- 证据目录与 fixture 目录同名（去掉 `p01-` 前缀），如 `evidence/call-return/`。
- 截图名：`<行为>_<状态>`，如 `display_after_shows`。

## 2. 目标行为清单（≥10 个核心行为）

| 编号 | 行为 | 兼容等级目标 | fixture | 文档 |
| --- | --- | --- | --- | --- |
| B01 | 启动链（boot → 编译 → main menu → start） | 必须兼容 | `p01-01-startup` | `startup-chain.md` |
| B02 | `label` 定义与进入 | 必须兼容 | `p01-02-label` | `label.md` |
| B03 | `jump` 跳转 | 必须兼容 | `p01-02-jump` | `jump.md` |
| B04 | `call` / `return` 调用返回位置、嵌套 | 必须兼容 | `p01-02-call-return` | `call-return.md` |
| B05 | `say` 对白（who/what、多行、转义） | 必须兼容 | `p01-02-say` | `say.md` |
| B06 | `menu` 菜单及其继续位置、嵌套 | 必须兼容 | `p01-02-menu` | `menu.md` |
| B07 | `define` 常量与初始化时序 | 必须兼容 | `p01-02-define` | `variables.md` |
| B08 | `default` 初始化与读档默认值 | 必须兼容 | `p01-02-default` | `variables.md` |
| B09 | `scene` / `show` / `hide` 清空、替换、层序 | 必须兼容 | `p01-03-display` | `display.md` |
| B10 | 音频播放/停止可观察状态 | 允许不同（时序） | `p01-03-audio` | `audio.md` |
| B11 | 转场可观察结果 | 允许不同（视觉细节） | `p01-03-transitions` | `transitions.md` |
| B12 | 存档/读档跨进程状态 | 必须兼容 | `p01-03-save-load` | `save-load.md` |
| B13 | 回滚记录与状态恢复 | 必须兼容（语义） | `p01-03-rollback` | `rollback.md` |
| B14 | screen / ATL / 嵌入 Python 边界 | 暂不支持（静态子集） | `p01-03-screen-atl-python` | `screen-atl-python.md` |

14 个行为，超过“至少 10 个核心行为”要求。其中 B10/B11 目标等级为“允许不同”，需在文档中写明差异边界与复测条件。

## 3. 计划树节点

### N01-01 写作约定与证据规范

| 字段 | 内容 |
| --- | --- |
| 目标 | 定义 `docs/compatibility/` 的写作约定：证据字段、fixture 目录规范、事件记录格式、复验命令、产物隔离位置 |
| 依赖 | 无 |
| 输入 | 本文件 §0/§1 的实测事实 |
| 产出 | `docs/compatibility/README.md` |
| 验收 | 文档包含 7 个必备字段（环境、上游路径+符号、fixture、输入序列、预期 vs 实际、限制、兼容等级）的逐项说明，并给出可复制的复验命令模板 |
| 风险 | 约定与 phase0-verification.md 风格不一致 → 发布前对齐 |
| 负责阶段 | 阶段 1（P01-01） |
| 复测条件 | fixture 结构或 harness 字段变化时 |

### N01-02 共享证据 harness

| 字段 | 内容 |
| --- | --- |
| 目标 | 提供 `zz_evidence.rpy`：arm/disarm、JSONL 输出、语句与 label 回调、截图清单写入 |
| 依赖 | 无 |
| 输入 | §0 实测事实；`SUIYU_EVIDENCE` 环境变量指定输出路径 |
| 产出 | `compatibility-tests/fixtures/renpy/phase01/harness/zz_evidence.rpy` |
| 验收 | 单测式验证：同一 fixture 连跑 3 次，`actual.jsonl` 逐字节一致；`init python` 内不出现顶层 `import renpy` |
| 风险 | 回调在预测阶段重复触发 → 已实测可接受且确定；不裁剪以保证可比 |
| 负责阶段 | 阶段 1 |
| 复测条件 | Ren'Py 升级或回调 API 变化 |

### N01-03 启动链 fixture 与文档

| 字段 | 内容 |
| --- | --- |
| 目标 | 跟踪 boot → `.rpy` 编译 → init → main menu → `label start`；记录编译产物与 `--json-dump` 源映射 |
| 依赖 | N01-02 |
| 输入 | 最小 `script.rpy`、`compile` 命令、`run --json-dump` |
| 产出 | fixture `p01-01-startup`；`startup-chain.md`；`evidence/startup/` |
| 验收 | 文档记录 boot 路径符号（`renpy/bootstrap.py`、`renpy/main.py`、`renpy/script.py`）、源码路径与行号；实际轨迹到达 `start` |
| 风险 | `--json-dump` 需要以 `run` 启动并有窗口 → CI 已有 GUI 能力 |
| 负责阶段 | 阶段 1（P01-01），交阶段 2–5 |
| 复测条件 | 启动顺序或编译产物位置变化 |

### N01-04 控制流 fixtures（label/jump/call/return）

| 字段 | 内容 |
| --- | --- |
| 目标 | 四类跳转各自的入口、返回位置、嵌套调用轨迹 |
| 依赖 | N01-02 |
| 输入 | 4 个独立 fixture |
| 产出 | fixture `p01-02-label`、`p01-02-jump`、`p01-02-call-return`；`label.md`、`jump.md`、`call-return.md`；对应 `evidence/` |
| 验收 | 每行为：独立 fixture、输入序列、预期观察、实际观察、证据路径、限制、兼容等级；call/return 需展示 `return_stack` 深度变化 |
| 风险 | 无 |
| 负责阶段 | 阶段 1（P01-02），交阶段 4 |
| 复测条件 | 调用栈语义变化 |

### N01-05 对白、菜单、变量 fixtures

| 字段 | 内容 |
| --- | --- |
| 目标 | `say`（who/what/多行/转义）、`menu`（继续位置/嵌套）、`define`、`default`（含读档默认值） |
| 依赖 | N01-02、N01-03（读档默认值需要？不，默认值用 test 内 save/load） |
| 输入 | 4 个独立 fixture |
| 产出 | fixture `p01-02-say`、`p01-02-menu`、`p01-02-define`、`p01-02-default`；`say.md`、`menu.md`、`variables.md`；对应 `evidence/` |
| 验收 | menu 需记录“选择后继续位置”；default 需记录首次初始化与读档后取值 |
| 风险 | menu 交互需 `click` + `exit` 紧邻写法 → §0 已固化 |
| 负责阶段 | 阶段 1（P01-02），交阶段 4–5 |
| 复测条件 | 菜单续行或默认值初始化时机变化 |

### N01-06 演出 fixtures（scene/show/hide）

| 字段 | 内容 |
| --- | --- |
| 目标 | 清空、同标签替换、层序（zorder）、hide 后的列表状态 |
| 依赖 | N01-02 |
| 输入 | 1 个 fixture，多段断言 |
| 产出 | fixture `p01-03-display`；`display.md`；`evidence/display/` + 截图清单 |
| 验收 | 记录 `scene_lists.layers["master"]` 的 `(tag, name, zorder)` 快照三态：show 后、hide 后、scene 后 |
| 风险 | zorder 与绘制顺序关联需在文档中说明为“可观察顺序”，不做像素判定 |
| 负责阶段 | 阶段 1（P01-03），交阶段 3、7 |
| 复测条件 | 图层模型变化 |

### N01-07 音频与转场 fixtures

| 字段 | 内容 |
| --- | --- |
| 目标 | 音频 `play`/`stop` 的 `get_playing` 可观察状态；转场后状态可观察 |
| 依赖 | N01-02 |
| 输入 | 1 个 fixture，含生成的短 OGG（仓库内自带，ffmpeg 生成后提交；体积受控） |
| 产出 | fixture `p01-03-audio`、`p01-03-transitions`；`audio.md`、`transitions.md`；`evidence/` |
| 验收 | 记录播放前 `null`、播放后路径、停止后状态；转场不判定像素，仅记录语句执行与截图清单 |
| 风险 | 音频后端在 CI 无声卡 → 只断言 API 层状态，不断言听感 |
| 负责阶段 | 阶段 1（P01-03），交阶段 7 |
| 复测条件 | 音频 API 或转场执行路径变化 |

### N01-08 存档/读档与回滚 fixtures

| 字段 | 内容 |
| --- | --- |
| 目标 | 存档后跨进程读档恢复状态；读档后 `after_load` 钩子与默认值；回滚恢复状态 |
| 依赖 | N01-02 |
| 输入 | 2 个 fixture；save/load 需两次进程调用 |
| 产出 | fixture `p01-03-save-load`、`p01-03-rollback`；`save-load.md`、`rollback.md`；`evidence/` |
| 验收 | save/load：进程 1 存档 + 变更，进程 2 读档恢复；rollback：`can_rollback` 与状态值前后对比 |
| 风险 | 读档需要先有交互 checkpoint → §0 已固化；跨进程用同一 `--savedir` |
| 负责阶段 | 阶段 1（P01-03），交阶段 6 |
| 复测条件 | 存档格式或回滚模型变化 |

### N01-09 screen / ATL / Python 边界 sample

| 字段 | 内容 |
| --- | --- |
| 目标 | 用小样例界定 screen 显隐、ATL 变换登记、嵌入 Python 的边界；列为“暂不支持（静态子集）” |
| 依赖 | N01-02 |
| 输入 | 1 个 fixture |
| 产出 | fixture `p01-03-screen-atl-python`；`screen-atl-python.md`；`evidence/` |
| 验收 | 记录 `renpy.get_screen` 显隐、`scene_lists.at_list` 是否登记 ATL、嵌入 Python 语句节点；明确列出待研究问题 |
| 风险 | 静态可识别子集边界主观 → 以实测可观察项为准 |
| 负责阶段 | 阶段 1（P01-03），交阶段 8 |
| 复测条件 | 后续阶段扩展 screen/ATL 支持时 |

### N01-10 检查脚本 `scripts/phase01-check.ps1`

| 字段 | 内容 |
| --- | --- |
| 目标 | 固定 SDK fixture 检查入口：定位 SDK、校验 SHA-256、隔离目录、逐 fixture lint + test + 证据比对 |
| 依赖 | N01-02..N01-09 |
| 输入 | `-RenpySdk <path>` 或 `SUIYU_RENPY_SDK` / `RENPY_SDK`；缺省时按约定路径探测 |
| 产出 | `scripts/phase01-check.ps1` |
| 验收 | 可从仓库根调用；缓存与产物写仓库外临时目录；全部 fixture 通过则退出码 0；任一失败退出码非 0 并打印失败 fixture 与临时目录 |
| 风险 | CI 无 SDK 时需下载 → workflow 负责下载与验签，脚本只消费已存在的 SDK |
| 负责阶段 | 阶段 1 验收 |
| 复测条件 | fixture 增删或证据格式变化 |

### N01-11 CI workflow

| 字段 | 内容 |
| --- | --- |
| 目标 | `windows-2025` runner 上安装固定 SDK 并运行 `phase01-check.ps1` |
| 依赖 | N01-10 |
| 输入 | 官方 SDK URL + SHA-256 |
| 产出 | `.github/workflows/phase01.yml` |
| 验收 | job 成功；失败时打印证据差异 |
| 风险 | GUI 会话依赖 → 沿用 phase0 已验证的 windows-2025 桌面能力 |
| 负责阶段 | 阶段 1 验收 |
| 复测条件 | runner 镜像或 SDK 变化 |

### N01-12 兼容性矩阵

| 字段 | 内容 |
| --- | --- |
| 目标 | `COMPATIBILITY_MATRIX.md` 按功能标注三级等级，链接源证据、fixture、负责阶段；保留分歧观察与复测条件 |
| 依赖 | N01-03..N01-09 |
| 输入 | 各行为文档的“兼容等级”与证据路径 |
| 产出 | `docs/compatibility/COMPATIBILITY_MATRIX.md` |
| 验收 | 每个 B01..B14 行都有等级、证据链接、fixture 链接、负责阶段；阶段 4 与阶段 8 可引用同一语义决策 |
| 风险 | 等级无依据 → 必须链接真实证据文件 |
| 负责阶段 | 阶段 1（P01-04），交阶段 4、8 |
| 复测条件 | 任一行为等级改变 |

### N01-13 验收交接记录

| 字段 | 内容 |
| --- | --- |
| 目标 | 汇总环境、命令、退出码、限制；分别标注自动轨迹与人工观察 |
| 依赖 | N01-10、N01-11、N01-12 |
| 输入 | 实际运行输出 |
| 产出 | `docs/compatibility/PHASE01_VERIFICATION.md` |
| 验收 | 含 SDK 指纹、实际命令、退出码、证据路径、人工观察未执行声明；交给阶段 2–5 与阶段 8 的决策清单 |
| 风险 | 用计划代替证据 → 只记录实跑结果 |
| 负责阶段 | 阶段 1 验收 |
| 复测条件 | 每次补证 |

## 4. 依赖图

```text
N01-01 ─┐
N01-02 ─┴─> N01-03 ─┐
             N01-04 ─┤
             N01-05 ─┼─> N01-10 ─> N01-11 ─┐
             N01-06 ─┤                    ├─> N01-13
             N01-07 ─┤                    │
             N01-08 ─┤   N01-12 <──────────┘
             N01-09 ─┘
```

N01-03..N01-09 之间相互独立，可并行。

## 5. 风险与回滚

| 风险 | 缓解 | 回滚/复测 |
| --- | --- | --- |
| `test` 命令在某些机器挂起 | 每个 fixture 设 `_test.timeout` 且脚本有硬超时 | 记录挂起 fixture，降级为“人工观察”并在证据中标注 |
| 截图在 CI 与本地不一致 | 只提交清单+哈希，不做 CI 像素断言 | 若需像素对比，改为人工观察 |
| 回调轨迹含预测期重复 | 接受并写入基线，用逐字节比对保证稳定 | Ren'Py 变更导致差异时重采基线并记录原因 |
| `init python` 顶层 `import renpy` 陷阱 | harness 内函数级 `import renpy` | harness 单测覆盖 |
| 证据文件过期 | 检查脚本重跑并与提交基线比对 | 差异即失败，需人工确认后重采 |

## 6. 验收总表（可追溯）

| 验收项 | 节点 | 判定方式 |
| --- | --- | --- |
| 写作约定覆盖 7 字段 | N01-01 | 文档检查 |
| ≥10 核心行为各具证据/ fixture/等级 | N01-03..N01-09 | 矩阵 + 证据文件存在性 |
| `scripts/phase01-check.ps1` 可运行 | N01-10 | 实际执行退出码 |
| 证据可复现 | N01-02 | 3 次逐字节一致 + 检查脚本比对 |
| GUI 观察方法分别记录 | N01-06/N01-07 | 文档“自动轨迹/人工观察”两节 |
| 阶段 2–5、8 交接输入 | N01-12/N01-13 | 矩阵链接 + 交接清单 |