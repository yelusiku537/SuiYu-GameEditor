# ADR 0001: 参考仓库与新引擎边界

- 状态：阶段 0 草案，外部坐标尚未核验
- 日期：2026-11-21
- 范围：Ren'Py 兼容性参考、Go 编译器基线、Rust 运行时基线

## 决策

阶段 0 将 Ren'Py 保持为参考 fork 与兼容性 fixture 的来源，不把 Ren'Py Python 包或其运行时复制成新引擎的实现。新引擎工程在当前项目中先承载最小 Go 编译器命令、Rust 运行时命令、兼容性 fixture、文档和检查脚本；Go 与 Rust 基线只使用各自标准库。

外部仓库的身份、可见性、默认分支和提交坐标必须由实际 Git 配置或官方发布材料核验后才能写入。本 ADR 对缺失证据使用 未验证，不推断 URL、分支、提交 SHA 或许可证。

## 仓库地址与责任

| 仓库 | 地址 | 可见性 | 默认分支 | 责任 |
| --- | --- | --- | --- | --- |
| 新引擎工程 | 未验证 | 未验证 | 未验证 | Go 编译器、Rust 运行时、fixture、文档与 CI 检查 |
| Ren'Py 参考 fork | 未验证（官方上游候选：https://github.com/renpy/renpy，尚未由本地 fork 证据确认） | 未验证 | 未验证 | 仅保存参考历史、兼容性对照材料和上游同步上下文 |

本地候选工程目录为当前项目；是否对应已经存在的远程新引擎仓库仍需核验。Ren'Py fork 的 owner、实际地址和默认分支不能从计划文本推断。

## 对照提交

| 项目 | 值 | 证据状态 |
| --- | --- | --- |
| Ren'Py SDK 发布版本 | 未验证 | 未取得官方发布记录 |
| 上游 tag | 未验证 | 未取得对应 SDK/tag 记录 |
| 完整参考提交 SHA | 未验证 | 尚未对实际完整 clone 执行 git show |
| 本次对照样例来源 | 未验证 | 等待参考 fork 和 SDK 坐标核验 |

## 只读上游同步步骤

以下命令只在已经核验的参考 fork 根目录执行；其中 $RenpyDefaultBranch 必须先由官方 HEAD 或远程引用确认，不能手填猜测值：

~~~powershell
git remote -v
git rev-parse --is-shallow-repository
if (-not (git remote | Select-String '^upstream$')) {
    git remote add upstream https://github.com/renpy/renpy.git
}
git remote set-url --push upstream https://invalid.invalid/renpy-read-only
git fetch --tags upstream
git fetch origin
git rev-parse "refs/remotes/upstream/$RenpyDefaultBranch"
git merge-base --is-ancestor "refs/remotes/upstream/$RenpyDefaultBranch" "refs/remotes/origin/$RenpyDefaultBranch"
~~~

upstream 的获取地址指向官方仓库，推送地址是故意不可用的只读保护地址。只有祖先检查退出码为 0 时，才可说明 fork 默认分支包含当前上游头；退出码为 1 要记录分叉，其他非零值按 Git 错误处理。同步前先比较差异；可快进时按项目协作规范更新 origin，发生分叉则在独立分支保留处理过程。阶段 0 不执行远程推送。

## 兼容性材料归属

- Ren'Py 的 Python 包结构沿用上游目录结构，仅作为参考 fork 的历史材料；不得在新引擎仓库中无条件复制。
- compatibility-tests/fixtures/renpy/ 中的最小脚本是新仓库的测试 fixture，必须以独立来源记录和第三方条款为依据。
- Go 工具负责编译器/CLI 基线；Rust 运行时负责运行时 CLI 基线；二者通过明确的命令或文件协议协作，阶段 0 不共享实现代码。
- SDL3、wgpu、MyGo Native UI 或其他第三方内容只有在许可证、版本、来源、归属和实际使用范围已经核验并登记后，才能进入新仓库。
- 阶段 0 的 Go 与 Rust 基线不引入第三方依赖。

## 未决项与验收记录

| 项目 | 当前记录 |
| --- | --- |
| 两个仓库地址、可见性、默认分支 | 未验证 |
| 参考提交 SHA | 未验证 |
| Git 命令与退出码 | 未验证（参考 fork 尚未在本地核验） |
| Go module import path | 未验证（阶段 0 使用本地模块占位，正式路径待仓库决策） |
| 新引擎许可证决策 | 未验证 |
| ADR 路径 | docs/adr/0001-reference-repository.md |

## 变更条件

在补齐上表证据前，不得把本 ADR 中的 未验证 项替换成推测值；补证时应同时记录来源、核验命令、退出码和核验日期。
