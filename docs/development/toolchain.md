# 阶段 0 工具链与版本台账

核验日期：2026-11-21（Asia/Shanghai）。阶段 0 的 Go/Rust 基线只使用标准库；MyGo Native UI、SDL3 和 wgpu 仅登记，不进入构建。

## 构建工具

| 项目/工具 | 准确版本或完整 SHA | 官方来源 | 使用方式 | 进入阶段 0 构建 | 验证命令/状态 |
| --- | --- | --- | --- | --- | --- |
| Go | `go1.27.4` | `https://go.dev/dl/` | Go 标准库 CLI 与测试 | 是 | Windows `go version go1.27.4 windows/amd64`；使用仓库外隔离工具目录 |
| Rust toolchain | `1.100.0` | `https://www.rust-lang.org/tools/install` | Rust 标准库 CLI 与测试 | 是 | Windows `rustc 1.100.0 (0ef1bc386 2026-11-09)`；rustup 使用官方 USTC 镜像完成安装 |
| rustfmt | `1.11.0-stable (0ef1bc3860 2026-11-09)` | Rust toolchain | `cargo fmt --check` | 是 | Windows `rustfmt --version` 已核验 |
| Cargo | `1.100.0 (3acc79c0c 2026-11-05)` | Rust toolchain | `cargo test`, `cargo build` | 是 | Windows `cargo --version` 已核验 |
| Windows | Windows 11 Home，版本 `10.0.26300` | Microsoft | 原生 Windows 目标构建环境 | 是 | `Get-CimInstance Win32_OperatingSystem` 已核验 |
| CPU 架构 | x64 | 主机事实 | Windows x64 目标 | 是 | `Win32_OperatingSystem.OSArchitecture` 已核验 |
| PowerShell 7 | `7.6.6` | `https://github.com/PowerShell/PowerShell` | 执行 `scripts/phase0-check.ps1` | 是 | `$PSVersionTable.PSVersion` 已核验 |
| Git | Windows `2.54.0.windows.1`；WSL `2.53.0` | `https://git-scm.com/download/win` | 版本、远程与 ignore 证据 | 是 | `git --version` 已核验 |
| Rust MSVC linker / Windows SDK | 未单独定位 | Visual Studio / Microsoft | Rust Windows MSVC 链接 | 是 | `where.exe link`、`where.exe cl` 未找到；阶段 0 Rust MSVC 构建实际通过，具体 linker 来源待补 |

## 参考与兼容性材料

| 项目/工具 | 准确版本或完整 SHA | 官方来源 | 使用方式 | 进入阶段 0 构建 | 验证命令/状态 |
| --- | --- | --- | --- | --- | --- |
| Ren'Py Windows SDK | `8.6.1`；Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb` | `https://www.renpy.org/release/8.6.1` | 独立 fixture lint/运行 | 否 | 官方发布页与 `checksums.txt` 已访问；完整 `163957166` 字节归档下载受当前网络吞吐限制，未完成解压、lint 和 GUI 验收 |
| Ren'Py upstream tag | `8.6.1.26111705`; `de379eb4f85a4930244786c715e581a1cb3fd374` | `https://github.com/renpy/renpy` | 与 SDK 对照提交关联 | 否 | 官方远程材料已核验；本地未 clone |
| Ren'Py fork | `https://github.com/yelusiku537/renpy`; public; default `master`; head `0be2c7103be5d537d9e6cad54ee44ce34c9422a` | 参考 fork | 只读上游同步和历史保留 | 否 | GitHub API 已核验；完整历史 clone 受代理限制未完成 |
| MyGo Native UI | `v0.10.0`; `ebde9399baf2734b3361856a53f4036859973d1d` | `https://github.com/egoist/mygo`, `https://mygo.run` | 仅登记候选依赖 | 否 | 官方仓库与 MIT 许可证已核验 |
| SDL3 | `release-3.4.20`; `f00dc919ca35b9756316e86c4777392de442f9b2` | `https://github.com/libsdl-org/SDL` | 仅登记候选依赖 | 否 | 官方 release 坐标已核验 |
| wgpu | `v30.0.2`; `89f8a2be4a536503ed97451320cda16414044e31` | `https://github.com/gfx-rs/wgpu` | 仅登记候选依赖 | 否 | 官方 release 坐标已核验 |
| TypeScript / Monaco / CodeMirror / WebView | 不适用 | 不适用 | Web 备选未启用 | 否 | 不加入版本记录 |

## 版本写入规则

1. Go 版本必须与 `compiler-go/go.mod` 的 `go` 指令一致。
2. Rust 版本必须同时存在于 `rust-toolchain.toml`，并固定 `profile = "minimal"` 与 `components = ["rustfmt"]`。
3. 外部依赖未实际引入前只登记来源，不放入阶段 0 构建。
4. Windows 原生工具缺失时，验收记录必须标为未验证，不能用 WSL 版本替代 Windows 证据。
