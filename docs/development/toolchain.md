# 阶段 0 工具链与版本台账

本表只记录阶段 0 实际需要的工具。版本、提交、来源或安装事实无法从当前工作区核验时保留为 未验证，并注明负责人和补证动作。

## 构建工具

| 项目/工具 | 准确版本或完整 SHA | 官方来源 | 使用方式 | 进入阶段 0 构建 | 验证命令/状态 |
| --- | --- | --- | --- | --- | --- |
| Go | 未验证（补证后写入 compiler-go/go.mod） | 未验证 | Go 标准库 CLI 与测试 | 是 | go version; go env GOVERSION；当前未验证 |
| Rust toolchain | 未验证（补证后写入 rust-toolchain.toml） | 未验证 | Rust 标准库 CLI 与测试 | 是 | rustc --version --verbose；当前未验证 |
| rustfmt | 未验证 | 随 Rust toolchain | cargo fmt --check | 是 | rustfmt --version；当前未验证 |
| Cargo | 未验证 | 随 Rust toolchain | cargo test, cargo build | 是 | cargo --version；当前未验证 |
| Windows | 未验证 | Microsoft | 原生 Windows 目标构建环境 | 是 | Get-ComputerInfo；当前未验证 |
| CPU 架构 | 未验证 | 主机事实 | 选择 Windows 构建目标 | 是 | Get-CimInstance Win32_OperatingSystem；当前未验证 |
| PowerShell 7 | 未验证 | Microsoft | 执行 scripts/phase0-check.ps1 | 是 | $PSVersionTable.PSVersion；当前未验证 |
| Git | 未验证 | Git SCM | 版本、远程、worktree 和 ignore 证据 | 是 | git --version; git status --short；当前未验证 |
| Rust MSVC linker | 未验证 | Visual Studio / Windows SDK | Windows MSVC 目标链接 | 是 | rustc -vV; where.exe link; where.exe cl；当前未验证 |
| Windows SDK | 未验证 | Microsoft | Windows 头文件和链接库 | 是 | 注册表 Installed Roots；当前未验证 |

## 参考与兼容性材料

| 项目/工具 | 准确版本或完整 SHA | 官方来源 | 使用方式 | 进入阶段 0 构建 | 验证命令/状态 |
| --- | --- | --- | --- | --- | --- |
| Ren'Py Windows SDK | 未验证 | 未验证 | 只作为兼容性 fixture 的参考运行环境 | 否 | 官方下载页、归档 SHA-256、SDK 自报版本；当前未验证 |
| Ren'Py upstream tag | 未验证 | https://github.com/renpy/renpy（候选上游，待核验） | 与 SDK 对照提交关联 | 否 | git show <已核验完整 SHA>；当前未验证 |
| Ren'Py fork owner/URL/default branch | 未验证 | 未验证 | 只读上游同步和历史保留 | 否 | git remote -v; git branch --show-current；当前未验证 |
| MyGo Native UI | 未验证 | 未验证 | 仅登记候选依赖，不进入阶段 0 构建 | 否 | 由负责人提供权威项目地址、版本和许可证；未验证 |
| SDL3 | 未验证 | 未验证 | 仅登记候选依赖，不进入阶段 0 构建 | 否 | 由负责人提供权威版本/提交和许可证；未验证 |
| wgpu | 未验证 | 未验证 | 仅登记候选依赖，不进入阶段 0 构建 | 否 | 由负责人提供权威版本/提交和许可证；未验证 |
| TypeScript / Monaco / CodeMirror / WebView | 不适用 | 不适用 | Web 备选未启用 | 否 | 不添加版本记录，直到 Web 方案实际启用 |

## 版本写入规则

1. Go 版本确认后写入 compiler-go/go.mod 的 go 指令，并在本表保留完整版本来源。
2. Rust 版本确认后同时更新 rust-toolchain.toml 和本表；文件必须保留 profile = minimal 与 components = rustfmt。
3. MyGo Native UI、SDL3、wgpu 的身份或版本不能核验时，验收状态保持 未验证，不允许用猜测的坐标替代。
4. Windows 构建、SDK、链接器和 PowerShell 证据必须来自实际主机命令；计划文本不是安装证据。
