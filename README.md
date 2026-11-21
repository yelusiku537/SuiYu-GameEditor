# SuiYu Game Editor

阶段 0 建立两个可独立运行的命令行基线程序，并保留一个独立 Ren'Py 对照 fixture。Go 工具位于 `compiler-go/`，Rust 运行时位于 `runtime-rust/`；Ren'Py 文件只用于兼容性对照，不是新引擎实现。

## 前置条件

- Windows 11 x64 或兼容的 Windows x64 环境
- PowerShell 7
- Go `1.27.4`
- Rust `1.100.0`，包含 `rustfmt`（`rust-toolchain.toml` 会固定工具链）
- Git、Rust MSVC linker 与 Windows SDK

安装入口见 [工具链台账](docs/development/toolchain.md)。阶段 0 不需要 MyGo、SDL3 或 wgpu 参与构建。

## 从干净环境执行

在原生 Windows PowerShell 7 中，从仓库根目录执行：

```powershell
pwsh -NoProfile -File ./scripts/phase0-check.ps1
```

脚本会把 Go/Cargo 缓存和构建目录放到仓库外的临时目录，不依赖本地缓存。单独运行时：

```powershell
Push-Location compiler-go
go test ./...
Pop-Location
cargo test --locked --manifest-path runtime-rust/Cargo.toml
```

CI 使用相同入口，配置见 `.github/workflows/phase0.yml`。失败时先确认工具版本与 PATH，再查看脚本输出的临时目录；Windows 原生环境缺少 Rust 或 linker 时，安装对应官方工具后重试。

## Ren'Py 对照 fixture

fixture 位于 `compatibility-tests/fixtures/renpy/phase0`，必须复制到项目外的一次性目录，并使用固定的官方 Ren'Py Windows SDK。lint、自动 GUI smoke、SDK 指纹及人工验收限制见 [阶段 0 验收记录](docs/development/phase0-verification.md)。参考 fork 为 `https://github.com/yelusiku537/renpy`；当前保留了源码快照，但完整历史克隆仍受网络限制，参考边界见 [ADR 0001](docs/adr/0001-reference-repository.md)。

## 协作

格式、测试、fixture、许可证和提交约定见 [CONTRIBUTING.md](CONTRIBUTING.md)。第三方来源见 [许可证台账](LICENSES/THIRD_PARTY.md)。
