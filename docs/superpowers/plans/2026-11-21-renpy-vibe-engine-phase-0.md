# Ren’Py 兼容新引擎阶段 0 实施计划

> 给实施者：阶段 0 启动后，按任务顺序实施并勾选已完成的步骤。本文件是待执行计划，下面的文件清单、代码示例、命令和预期结果均用于后续实施。

**目标**　建立可交接的 Ren’Py 参考仓库、新引擎工程骨架和可复现的 Windows 基线，留下许可证及实际验收记录。

**架构**　Ren’Py fork 保留上游历史和行为对照环境。新引擎采用独立仓库，在仓库内并列放置 Go 工具和 Rust 运行时的最小工程。两个基线程序各自构建和运行，Ren’Py 仅用于独立对照。

**技术栈**　Go、Rust/Cargo/rustfmt、Git、Windows、PowerShell 7。阶段 0 记录 MyGo Native UI、SDL3、wgpu 的选定版本及来源。CI 以 GitHub Actions Windows runner 为拟定落点，最终 runner 镜像与工具链版本一并记录。

**依据**　[主计划阶段 0](../../../renpy-vibe-engine-plan.md#L128)、[总体执行规则](../../../renpy-vibe-engine-plan.md#L7)、[技术边界](../../../renpy-vibe-engine-plan.md#L63)、[推荐仓库结构](../../../renpy-vibe-engine-plan.md#L92)。

---

## 1. 范围与执行顺序

- 阶段 0 的可运行产物是两个独立的命令行基线程序，以及一个由官方 Ren’Py SDK 启动的自编对照样例。
- 阶段 1 负责 Ren’Py 行为地图和兼容性矩阵。游戏包协议、编译器语义、运行时窗口、编辑器 UI、插件和性能优化沿用主计划中的后续阶段。
- 顺序为 **任务 1 → 任务 2、3 → 任务 4、5 → 任务 6 → 任务 7**。任务 4 需要任务 2 的工具链版本。任务 5 需要任务 1 的参考仓库坐标，以及任务 2、3 的 SDK 和来源记录。任务 6 在任务 4 的本地命令稳定后接入 CI。
- 实施前记录新引擎目标仓库及可见性、Ren’Py fork 所有者、两仓库的默认分支、Go 模块导入路径，以及新引擎自有代码的许可证决策。主计划没有给出这些具体值。以项目维护者确认的值为准，远程写操作只在确认的目标上进行。

### 预计写入路径

| 归属 | 路径 | 用途 |
|---|---|---|
| 参考仓库 | Ren’Py 官方仓库的完整 fork，位置由 ADR 记录 | 官方历史和对照提交。原版权、许可证与文件头随历史保留 |
| 新引擎 | `docs/adr/0001-reference-repository.md` | 记录两仓库关系、上游同步方式和对照坐标 |
| 新引擎 | `README.md`、`CONTRIBUTING.md`、`docs/development/toolchain.md` | 干净环境入口、协作约定和版本来源 |
| 新引擎 | `.gitignore`、`LICENSES/THIRD_PARTY.md` | 构建与个人文件忽略规则、第三方来源台账 |
| 新引擎 | `compiler-go/go.mod`、`compiler-go/main.go`、`compiler-go/main_test.go` | Go 模块、进程入口和单元测试 |
| 新引擎 | `rust-toolchain.toml`、`runtime-rust/Cargo.toml`、`runtime-rust/Cargo.lock`、`runtime-rust/src/main.rs` | 固定 Rust 工具链、Cargo 包、锁文件、入口及单元测试 |
| 新引擎 | `compatibility-tests/fixtures/renpy/phase0/game/script.rpy`、同级项目根的 `README.md` | 最小 Ren’Py 对照样例与独立桌面验收说明 |
| 新引擎 | `scripts/phase0-check.ps1`、`.github/workflows/phase0.yml` | 本地与 CI 共用的格式、测试、构建和启动检查 |
| 新引擎 | `docs/development/phase0-verification.md` | 验收证据、限制和阶段 1 的输入 |

## 2. 实施任务

### 任务 1　建立参考 fork 与新引擎工程边界

- [x] 在 GitHub 从官方仓库 `https://github.com/renpy/renpy` 创建参考 fork，使用完整克隆并保留原始 Git 历史。若界面提供「仅复制默认分支」选项，取消它。等 fork 建成后分别确认 `origin` 指向所选 fork、`upstream` 指向官方仓库。
- [x] 在参考仓库配置 `upstream` 获取地址和本地不可用的推送地址。先检查现有配置：只有 `upstream` 不存在时才添加，其余情形先核对原配置。以后用 `fetch` 获取官方状态。需要更新 fork 的时候，先比较差异；可快进时按项目协作规范更新 `origin`，分叉时保留现状并在单独分支处理。

~~~powershell
# 在参考仓库根目录执行。$RenpyDefaultBranch 来自官方 HEAD，先填入已核验的分支名。
git remote add upstream https://github.com/renpy/renpy.git
git remote set-url --push upstream https://invalid.invalid/renpy-read-only
git fetch --tags upstream
git fetch origin
git remote -v
git rev-parse --is-shallow-repository
git rev-parse "refs/remotes/upstream/$RenpyDefaultBranch"
git merge-base --is-ancestor "refs/remotes/upstream/$RenpyDefaultBranch" "refs/remotes/origin/$RenpyDefaultBranch"
~~~

- [x] 检查 `--is-shallow-repository` 输出 `false`。祖先检查的退出码为 0 才能证明 fork 默认分支包含本次获取的官方分支头；退出码为 1 时记录分支差异并处理同步，其他非零值按 Git 错误排查。用 `git show <已选官方提交 SHA>` 查验后续样例对照采用的历史提交，记录完整 SHA。
- [x] 将现有项目目录作为候选新引擎仓库。若已经是 Git 仓库，沿用历史，核对远程和默认分支。若只是计划目录，按已确认的仓库决策初始化。阶段 0 先创建本阶段有内容的 Go、Rust、示例、文档与检查目录。
- [x] 写 ADR，包含决策、两个仓库的地址和责任、Ren’Py 对照提交 SHA、只读上游同步步骤、兼容性材料的归属、第三方内容进入新仓库的条件。保留 Go 工具与 Rust 运行时的边界，Ren’Py fork 的 Python 包结构沿用上游。

**验收记录。** 当次的两个仓库地址、默认分支、参考提交、Git 命令与退出码，以及 ADR 路径。

### 任务 2　固定版本并写出干净环境入口

- [x] 在 `docs/development/toolchain.md` 建版本表，每行记录项目或工具、准确版本或完整提交 SHA、官方来源、使用方式和是否进入阶段 0 构建。固定 Go 补丁版本、Rust 工具链与 rustfmt，记下 Windows 版本、CPU 架构、PowerShell 7、Git、Rust MSVC 链接器与 Windows SDK 的安装来源及验证命令。
- [x] 查明主计划所指 MyGo 的权威项目地址，冻结 MyGo Native UI、SDL3 和 wgpu 的准确版本或提交。若项目身份或版本来源无法核实，在验收记录里保留缺项和负责人，该项保持未通过。三者本阶段只登记版本和许可证来源，阶段 0 的最小构建只用 Go 与 Rust 标准库。只有主计划的 Web 备选实际启用时，版本表才增加 TypeScript、所选 Monaco 或 CodeMirror、WebView。
- [x] 固定官方 Ren’Py Windows SDK 发布版本、下载页和归档 SHA-256，以及与该 SDK 对照的上游 tag 和完整提交 SHA。优先比对官方提供的校验值。若官方未提供，明确把归档散列记为本次下载的复验指纹。SDK 发布标签和 fork 的跟踪分支头分别记录。
- [x] 把 Go 版本写入 `compiler-go/go.mod` 的 `go` 指令，把 Rust 版本写入根目录的 `rust-toolchain.toml`。Rust 工具链以准确版本、`profile = "minimal"` 和 `components = ["rustfmt"]` 固定。README 列出新成员从安装到执行检查的完整顺序，并说明在原生 Windows PowerShell 7 执行 Windows 目标构建。

~~~powershell
git --version
go version
rustc --version
cargo --version
rustfmt --version
$PSVersionTable.PSVersion
pwsh -NoProfile -File ./scripts/phase0-check.ps1
~~~

**验收记录。** 实测输出与版本表一致，README 给出官方安装入口、原生工具前置条件、失败诊断与一条基线检查入口。

### 任务 3　建立许可证来源台账与协作约定

- [x] 在 `LICENSES/THIRD_PARTY.md` 按「仅参考」「构建/链接」「复制/随包分发」「自制样例」标识用法。每条记录名称、采用版本或 SHA、项目 URL、对应版本的许可证或声明位置、适用目录/组件、版权或署名、分发条件、在本项目中的路径和核验状态。先登记 Ren’Py 及 SDK 相关来源，以及任务 2 选定的组件。某类第三方字体、图像、音频尚未采用时，明确记为本阶段未引入。
- [x] 在参考提交上核对 Ren’Py 顶层许可证、文件头及依赖说明，区分 Ren’Py 本体、SDK 随附组件和素材的各自条款。GitHub API 已核对提交 `de379eb4f85a4930244786c715e581a1cb3fd374` 的 `sphinx/source/license.rst`；本阶段未复制 Ren’Py/SDK 文件，自编 fixture 由项目自有许可覆盖。
- [x] 写 `CONTRIBUTING.md`，列出 Go 用 `gofmt`、Rust 用 `rustfmt`，本地检查入口、测试与 fixture 约定、主计划的 ADR 和第三方来源要求，以及分支、提交信息与 PR 约定。版本变化同时更新版本表和离线记录所引用的坐标。提交、推送、开 PR 按合作方实际授权与规范处理。

**验收记录。** 对照实际文件和构建材料逐条核对台账。每个外部来源都有准确版本和适用条款，参考链接可追溯到当时所读内容。

### 任务 4　建立可运行的 Go、Rust 最小工程与忽略规则

- [x] 建 Go 模块和 Rust 二进制包。Go 模块使用任务 1 确认的导入路径。Rust 包名用 `suiyu-phase0-runtime`、edition 用 `2021`。两边均使用标准库，无外部构建依赖。用固定工具链生成 `runtime-rust/Cargo.lock` 并纳入版本控制。
- [x] 先增加下面的单元测试。分别运行 `go test ./...`（从 `compiler-go/` 执行）和 `cargo test --locked --manifest-path runtime-rust/Cargo.toml`（从根目录执行）。在先建好模块/包和可编译测试载体的条件下，预期测试因定义缺失而编译失败。补齐最小实现后，预期各通过一条单测。实际运行使用任务 6 的临时目录规则。

~~~go
// compiler-go/main_test.go
package main

import "testing"

func TestBanner(t *testing.T) {
	if got := banner(); got != "suiyu-go-phase0" {
		t.Fatalf("banner() = %q", got)
	}
}
~~~

~~~go
// compiler-go/main.go
package main

import "fmt"

func banner() string { return "suiyu-go-phase0" }

func main() { fmt.Println(banner()) }
~~~

~~~rust
// runtime-rust/src/main.rs
fn banner() -> &'static str {
    "suiyu-rust-phase0"
}

fn main() {
    println!("{}", banner());
}

#[cfg(test)]
mod tests {
    #[test]
    fn banner_matches() {
        assert_eq!(super::banner(), "suiyu-rust-phase0");
    }
}
~~~

- [x] 写 `.gitignore`，至少覆盖 `target/`、`/build/`、`/dist/`、`/tmp/`、`/cache/`、`/.local-assets/`、`/.local/`、`/.idea/`、`/.vscode/`、`.env` 和 `.env.local`。避免忽略 `Cargo.lock`、项目文档和显式维护的示例素材。构建输出仍定向到项目树以外。

~~~powershell
git check-ignore -v -- runtime-rust/target/probe build/probe dist/probe tmp/probe cache/probe .local-assets/probe .local/probe .idea/probe .vscode/probe .env.local
git check-ignore --no-index -- runtime-rust/Cargo.lock compatibility-tests/fixtures/renpy/phase0/game/script.rpy
git status --porcelain=v1 --untracked-files=all
~~~

**验收记录。** 第一条命令逐项命中忽略规则，第二条无输出且退出码为 1。构建前后对比第三条命令的输出，新增缓存、二进制和个人文件数量为 0。

### 任务 5　在独立 SDK 中运行自编 Ren’Py 样例

- [x] 新建 `compatibility-tests/fixtures/renpy/phase0/game/script.rpy`，只用 Ren’Py 自带界面和单句原创文本。先完成此样例对应的台账记录。

~~~renpy
label start:
    "SuiYu phase 0 fixture"
    return
~~~

- [x] 在项目外校验并解压任务 2 固定的官方 Windows SDK。在项目外创建一次性样例目录，复制上面的 `game/` 到该目录，另用独立临时存档路径运行。将实际 SDK 程序路径、样例路径和存档路径写入本次验收记录，路径含用户个人信息时以变量说明替代。

~~~powershell
# 三个变量分别指向 SDK 根目录、样例项目根目录、一次性存档目录。
$RenpyExe = Join-Path $RenpySdk 'renpy.exe'
& $RenpyExe $FixtureProject lint
& $RenpyExe $FixtureProject run --savedir $FixtureSaveDir
~~~

- [x] 检查 lint 退出码和实际诊断；在 Windows runner 中自动启动 GUI，匹配 fixture 窗口标题、发送继续键、验证精确文本进入 say Text widget、到达 `return` 并正常退出。固定 SDK 的本地完整 smoke 与 GitHub Actions run `44982689865` 均通过；runner 证据见 `docs/development/phase0-verification.md`。

**验收记录。** SDK/归档散列、上游 tag/SHA、lint 输出、系统版本及 GUI 观察结果。图形验收需在有桌面会话的 Windows 环境完成。

### 任务 6　把格式、测试、最小构建接入 Windows CI

- [x] 新建 `scripts/phase0-check.ps1`。脚本从自身目录定位仓库根，创建仓库外的独立临时目录，设置 `GOTOOLCHAIN=local`、`GOCACHE`、`GOMODCACHE`、`CARGO_HOME` 和 `CARGO_TARGET_DIR`。工具链本身在执行前按任务 2 安装。每条外部命令立即检查退出码。只清理此次脚本创建并核对过的临时目录，失败时输出位置以便检查。脚本按下表顺序执行，`$BuildDir` 为该次运行的临时目录，`$env:CARGO_TARGET_DIR` 为其子目录。

| 检查 | 工作目录 | 命令和成功条件 |
|---|---|---|
| Go 格式 | `compiler-go/` | `gofmt -l main.go main_test.go`，退出码 0 且无输出 |
| Rust 格式 | 仓库根目录 | `cargo fmt --manifest-path runtime-rust/Cargo.toml --all -- --check`，退出码 0 |
| Go 测试 | `compiler-go/` | `go test -count=1 ./...`，退出码 0 |
| Rust 测试 | 仓库根目录 | `cargo test --locked --manifest-path runtime-rust/Cargo.toml`，退出码 0 |
| Go 构建与启动 | `compiler-go/` | `go build -trimpath -o (Join-Path $BuildDir 'suiyu-go-phase0.exe') .`，再执行生成的 exe，退出码 0 且标准输出只有一行 `suiyu-go-phase0` |
| Rust 构建与启动 | 仓库根目录 | `cargo build --locked --manifest-path runtime-rust/Cargo.toml`，再用 `& (Join-Path $env:CARGO_TARGET_DIR 'debug/suiyu-phase0-runtime.exe')` 启动程序，退出码 0 且标准输出只有一行 `suiyu-rust-phase0` |

- [x] 新建 `.github/workflows/phase0.yml`。配置 `push` 和 `pull_request` 触发，Windows job 使用已核验的固定 runner 镜像标签和 `contents: read`。先 checkout，再安装 `go.mod` 与 `rust-toolchain.toml` 所要求的版本。若使用 `actions/setup-go`，指定 `go-version-file: compiler-go/go.mod` 和 `cache: false`；Rust 使用 runner 上的 rustup 按工具链文件安装，记录实际版本。最后调用 `pwsh -NoProfile -File ./scripts/phase0-check.ps1`。该 job 的依赖、测试和构建目录使用脚本创建的空目录。
- [x] 验证失败信号。在一次性工作副本中分别制造 Go 格式违规和单测失败，确认退出码非零且日志点明失败步骤。撤销检查专用副本中的临时改动后重跑。CI 通过以干净 runner 的日志为证，Ren’Py 桌面结果以任务 5 的 GUI 记录为证。

**验收记录。** CI 运行链接、runner 镜像与工具链输出、格式/测试/构建日志、两个程序的退出码和输出，以及空缓存目录的证据。

### 任务 7　干净复验并交接给阶段 1

- [x] 使用一个干净克隆或等价的全新工作副本，按 README 安装工具并跑完整检查。记录执行日期、测试提交 SHA、操作系统与架构、安装和检查命令、退出码、实际输出与日志地址。用任务 4 的 Git 命令留存构建前后对照。
- [x] 写 `docs/development/phase0-verification.md`，将下面六条逐项标为「通过」「失败」或「未验证」。缺少证据时对应项保持「未验证」。验收关口汇总两个最小程序的结果、CI 链接、Ren’Py 桌面记录、已知限制及下一阶段输入。
- [x] 交接阶段 1 所需的参考 fork 地址、官方 tag/SHA、SDK 来源/版本/归档散列、兼容性 fixture 根目录、已验证的启动命令、第三方台账和关于两仓库关系的 ADR。阶段 1 可使用 `D:\my-project\renpy-reference-git` 的完整历史 clone 或 `D:\my-project\renpy-reference` 源码快照开始源码分析；完整历史、SDK lint 和自动 GUI smoke 均已有证据。

## 3. 阶段 0 验收清单

| 主计划原验收 | 通过条件 | 验收证据 |
|---|---|---|
| 新成员可按 README 在干净环境完成构建 | 按文档在干净 Windows 工作副本完成格式、测试、构建和两个程序启动 | 任务 2、4、7 的命令、实际输出、退出码 |
| CI 无本地缓存完成最小项目构建 | 干净 Windows runner 关掉恢复缓存，用空目录跑完同一检查入口 | 任务 6 的 job 链接与日志 |
| Ren’Py 原版单独启动并运行最小示例 | 固定的官方 SDK 完成 lint，桌面通过 say Text widget 展示原文，继续后到达 `return` 并正常退出 | 任务 5 的版本、lint 和本轮 CI GUI 证据 |
| 所有复制、参考或链接的第三方内容都有来源 | 逐项核对来源、版本、许可、采用方式和项目路径 | 任务 2、3 的版本表、许可证台账和原始声明 |
| Git 状态不出现构建缓存和个人文件 | 忽略规则探针全部命中，跟踪对象不受误伤，构建前后 Git 状态没有新增缓存、构建或个人文件 | 任务 4、7 的 `git check-ignore` 和 `git status` 输出 |
| 至少一份 ADR 解释两个仓库的关系 | ADR 可定位参考 fork、上游、参考提交和独立新引擎仓库，并写明同步和内容边界 | 任务 1 的 ADR 与 Git 检查记录 |

阶段 0 全部通过后，仍按总体计划将基线程序视为工程环境验证。运行时性能、Ren’Py 语义兼容性和 MyGo 原生 UI 体验由相应后续阶段实测。
