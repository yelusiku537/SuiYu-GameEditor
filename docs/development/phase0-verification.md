# 阶段 0 验收记录

> 记录日期：2026-11-21（Asia/Shanghai）
> 记录范围：`2026-11-21-renpy-vibe-engine-phase-0.md` 任务 1 至任务 7。
> 当前状态：工程骨架和自动化检查已落盘；本记录只把已有证据标为通过、失败或未验证，不把计划内容当作事实。

## 执行环境

本次记录在 `D:\my-project\SuiYu-GameEditor` 工作区生成。当前本地 Git 证据如下：

| 项目 | 实测结果 |
| --- | --- |
| 当前分支 | `codex/phase0-complete` |
| 当前提交 | `995ae1669a6bb7ea2f8f9430ba752443eebd8782 ci: make RenPy smoke quit deterministic` |
| 新引擎远程 | `origin=https://github.com/yelusiku537/SuiYu-GameEditor` |
| Ren'Py fork | `https://github.com/yelusiku537/renpy` 已创建，public，默认分支 `master`，API 核验头为 `0be2c7103be5d537d9e6cad54ee44ce34c9422a` |
| WSL Go | `go1.27.4 linux/amd64` |
| WSL Rust/Cargo | 未安装，`rustc: command not found` |
| Windows PowerShell | `7.6.6` |
| Windows Git | `2.54.0.windows.1` |
| Windows Go/Rust | 已在仓库外隔离工具目录配置 Go 1.27.4、Rust 1.100.0、Cargo 和 rustfmt；未修改系统 PATH |

Windows 目标构建必须在安装 Go、Rust MSVC 工具链和 Windows SDK 的环境中复验。WSL 中的 Go 版本只证明 WSL 工具可用，不替代 Windows runner 或原生 PowerShell 验收。

## 六项验收

| 主计划原验收 | 状态 | 证据与限制 |
| --- | --- | --- |
| 新成员可按 README 在干净环境完成构建 | 通过 | 使用仓库外隔离 Go/Rust 工具链运行 `pwsh -NoProfile -File ./scripts/phase0-check.ps1`；格式、单测、构建和启动全部通过。 |
| CI 无本地缓存完成最小项目构建 | 通过 | GitHub Actions run [44918120739](https://github.com/yelusiku537/SuiYu-GameEditor/actions/runs/44918120739) 在 Windows runner `windows-2025-vs2026` 上完成；`windows-baseline` 与 `renpy-fixture` 均成功，Go/Rust 基线和 Ren'Py SDK 下载、SHA-256、lint、自动 GUI smoke 均通过。 |
| Ren'Py 原版单独启动并运行最小示例 | 通过（自动 GUI smoke） | GitHub Actions run [44918120739](https://github.com/yelusiku537/SuiYu-GameEditor/actions/runs/44918120739) 使用固定 SDK URL 和 SHA-256 完成下载、解压、lint，并在 Windows runner 桌面会话中启动 fixture，匹配窗口标题、发送继续键、验证进程仍运行后正常关闭。该证据是自动 GUI smoke，不等同于人工桌面观察；人工观察仍未验证。 |
| 所有复制、参考或链接的第三方内容都有来源 | 通过 | Ren'Py 参考提交的许可页已通过 GitHub API 核对；许可证台账记录 MIT/LGPL/依赖说明及 SDK SHA-256。阶段 0 未复制 SDK、MyGo、SDL3、wgpu 或素材文件。 |
| Git 状态不出现构建缓存和个人文件 | 通过 | 构建输出和 Go/Cargo 缓存均写入仓库外临时目录；忽略探针逐项命中，构建后工作区只保留预期源码和文档变更。 |
| 至少一份 ADR 解释两个仓库的关系 | 通过（本地文档） | [ADR 0001](../adr/0001-reference-repository.md) 已说明参考 fork、新引擎边界、只读 upstream 同步步骤、材料归属和未决证据。fork 已创建；完整历史 clone 仍未完成。 |

## 当前可复验命令

以下命令是阶段 0 的预定入口；在 Windows PowerShell 7、依赖已安装且工作区干净时执行：

```powershell
pwsh -NoProfile -File ./scripts/phase0-check.ps1
```

当前已验证：Windows PowerShell 7.6.6 下使用仓库外 Go 1.27.4 和 Rust 1.100.0 运行 `pwsh -NoProfile -File ./scripts/phase0-check.ps1`，六个步骤全部通过；Go 输出 `suiyu-go-phase0`，Rust 输出 `suiyu-rust-phase0`。另在 WSL `compiler-go/` 执行 `go test -count=1 ./...` 通过，PowerShell 脚本解析和 `git diff --check` 通过。

失败信号探针也已验证：格式违规副本在 Go 格式步骤以退出码 1 停止并报告 `main.go`；单测失败副本在 Go 测试步骤以退出码 1 停止并报告 `TestBanner`。两个临时副本均已清理。

Ren'Py GUI 验收命令（需在项目外的临时目录和已核验 SDK 中执行）为：

```powershell
& $RenpyExe $FixtureProject lint
& $RenpyExe $FixtureProject run --savedir $FixtureSaveDir
```

GUI 观察必须记录标题界面、文本 `SuiYu phase 0 fixture`、继续后的 `return` 行为和正常退出。路径中的用户名或个人目录应使用变量代替。

## 未完成证据与责任

- Ren'Py 官方 fork：`yelusiku537/renpy` 已创建且 API 坐标已记录；仍需在网络可用时完成完整 clone，并记录 `git rev-parse --is-shallow-repository`、远程头和祖先检查退出码。
- Ren'Py SDK：版本、下载页、归档 SHA-256、对应 upstream tag 和完整提交 SHA 已登记；已实测官方 URL/校验文件可访问，但完整下载受网络吞吐限制，仍需要在可用网络或缓存环境完成实际下载、校验、lint 和 GUI 运行。
- Windows 工具链：Go、Rust 1.100.0、rustfmt、Git、PowerShell 7 已记录并通过脚本；`where.exe link/cl` 未单独定位，但 Rust MSVC 构建已通过。
- CI：成功运行 [44918120739](https://github.com/yelusiku537/SuiYu-GameEditor/actions/runs/44918120739) 已取得；此前格式违规、单测失败探针也已在隔离副本中得到非零退出码。
- GUI：自动 GUI smoke 已通过；仍没有人工桌面观察记录，因此不能把自动 smoke 描述为人工验收。

Ren'Py 许可补证：GitHub API 在提交 `de379eb4f85a4930244786c715e581a1cb3fd374` 的 tree `67624ee443dd2dd03993d50e8e889459a528ad1e` 中核对了 `sphinx/source/license.rst`（blob `f4068def0d31d8d87cd9c7c9e665381b0cce1705`）。该文件说明 Ren'Py 本体的 MIT 条款、LGPL 部分和依赖清单；本阶段没有复制 Ren'Py 或 SDK 文件，因此没有新增随包分发内容。

## 阶段 1 交接输入

阶段 1 可以从以下仓库内坐标开始工作：

- 参考说明：[ADR 0001](../adr/0001-reference-repository.md)
- 工具和外部来源：[toolchain.md](toolchain.md)
- 第三方来源台账：[THIRD_PARTY.md](../../LICENSES/THIRD_PARTY.md)
- Ren'Py fixture 根目录：`compatibility-tests/fixtures/renpy/phase0/`
- 自动检查入口：`scripts/phase0-check.ps1`
- 阶段 0 两个基线程序：`compiler-go/` 与 `runtime-rust/`

在参考 fork、SDK 和 CI 证据补齐前，阶段 1 只能把 fixture 当作源码级输入；不得据此推断 Ren'Py 语义兼容性、运行时窗口行为或性能结果。

## 后续更新规则

每次补证时更新本文件的日期、执行提交 SHA、实际命令、退出码和日志位置。状态只有在对应证据存在时才从“未验证”改为“通过”或“失败”；不要用计划、意图或局部源码检查替代实际运行证据。

## 2026-11-21 Ren'Py 参考 fork/API 快照补证

- GitHub API 核验：`https://github.com/yelusiku537/renpy` 为公开仓库，默认分支 `master`，该分支头为 `0be2c7103be5d537d9e6cad54ee44ce34c9422a`。
- 官方对照坐标：tag `8.6.1.26111705` 指向 `a2ded0b29fd1e0b61972469cfc558a910e717e3c`；提交 `de379eb4f85a4930244786c715e581a1cb3fd374` 可通过 GitHub API 取得，提交主题为 `android: On Android 16+, have the back button and gesture roll back rather than close the game.`。
- 完整克隆尝试：Windows Git Smart HTTP 经 `127.0.0.1:7810` 返回 HTTP 403；SSH over port 443 长时间停滞后终止。失败克隆的临时 pack 未被当作有效历史，已移出快照目录的 `.git-incomplete-clone` 以保留证据。
- 替代源码材料：`D:\my-project\renpy-reference` 通过 GitHub Git Blob API 保存 `master` 树的 1200 个源码/文档文件，并生成 `SOURCE_SNAPSHOT.md` 与 `TREE_MANIFEST.tsv`。这是源码快照，不等同于完整 Git clone；本地 `git show`、`--is-shallow-repository`、远程祖先检查保持未验证。

## 2026-11-21 干净副本复验

- 验证日期：2026-11-21（Asia/Shanghai）
- 等价干净副本：D:\temp\suiyu-phase0-clean（仓库外，已完成后可清理）
- 测试提交 SHA：934503b（`feat: establish Ren'Py phase 0 baseline`，干净副本由该提交重新克隆）
- 系统：Microsoft Windows 11 家庭版 中文版 10.0.26300 64 位
- Go：go version go1.27.4 windows/amd64
- Rust：rustc 1.100.0 (0ef1bc386 2026-11-09)
- Cargo：cargo 1.100.0 (3acc79c0c 2026-11-05)
- PowerShell：7.6.6
- 检查命令：pwsh -NoProfile -File ./scripts/phase0-check.ps1
- 退出码：0
- 结果：Go/Rust 格式、单测、构建和启动全部通过；输出分别为 suiyu-go-phase0 / suiyu-rust-phase0

## 2026-11-21 GitHub Actions 补证

- 提交：`995ae1669a6bb7ea2f8f9430ba752443eebd8782`
- 运行：[44918120739](https://github.com/yelusiku537/SuiYu-GameEditor/actions/runs/44918120739)
- runner：`windows-2025-vs2026`，镜像版本 `20261116.315.1`
- `windows-baseline`：通过；Go/Rust 格式、测试、构建和启动全部通过。
- `renpy-fixture`：通过；官方 Ren'Py 8.6.1 SDK 下载与 SHA-256 校验、fixture lint、自动 GUI smoke 全部通过。
- GUI smoke 关闭逻辑使用 CI 临时配置 `config.quit_action = renpy.quit`，用于绕过默认退出确认菜单；fixture 本身未修改。
