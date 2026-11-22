# 阶段 00 · 仓库、许可证和开发环境基线

当前状态为已验收。任务细节、样例与命令仍以[原实施计划](../2026-11-21-renpy-vibe-engine-phase-0.md)为历史依据，实际结果见[验收记录](../../../development/phase0-verification.md)。

## 范围和输入

以官方 Ren'Py fork 和固定 Windows SDK 作为参考，用 Go、Rust 标准库建立各自能构建、测试和启动的程序。引擎项目与参考仓库的职责由 [ADR 0001](../../../adr/0001-reference-repository.md)约定。阶段 1 从该 ADR、工具链台账、许可台账和原版 fixture 开始。

## 任务与交付

### P00-01 参考 fork 与项目边界

保留完整历史，核对 fork 的 `origin`、官方只读 `upstream` 和固定对照提交。交付 ADR，记录浅克隆检查、历史完整性和两仓库的同步及材料归属。

### P00-02 工具链与许可证台账

固定 Go、Rust、Windows runner 和 Ren'Py SDK，记录来源、哈希和安装说明。在 `LICENSES/THIRD_PARTY.md` 标出仅供参考、参与链接、随包分发、自制 fixture 的材料。MyGo、SDL3、wgpu 的实际接入留给消费它们的阶段。交付 `docs/development/toolchain.md` 和贡献指南。

### P00-03 Go、Rust 和 Ren'Py 基线

在 `compiler-go/` 与 `runtime-rust/` 各交付独立的最小入口和单元测试。`compatibility-tests/fixtures/renpy/phase0/` 放置自编脚本，使用固定 SDK 的隔离副本运行 lint 和 GUI smoke。工具链需先就绪，SDK 与 fixture 还依赖参考坐标。

### P00-04 本地检查、CI 和验收归档

将上述入口接入 `scripts/phase0-check.ps1` 和 Windows CI，验证格式、单测、构建、启动。归档成功 run，加上格式违规及单测失败的非零退出证据，并记录还有哪些场景需要在后续阶段复测。

## 验收与交接

在 Windows PowerShell 7 执行 `pwsh -NoProfile -File ./scripts/phase0-check.ps1`。Go 和 Rust 分别打印 `suiyu-go-phase0` 和 `suiyu-rust-phase0`。固定 SDK 的自动 GUI smoke 断言对白、脚本返回、窗口关闭和退出码。人工像素观察仍未记录，阶段 1 按特性独立采集语义证据。
