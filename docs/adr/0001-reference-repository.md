# ADR 0001: 参考仓库与新引擎边界

- 状态：阶段 0 已记录，远程参考 fork 与完整 Git 历史 clone 已验证
- 日期：2026-11-22
- 范围：Ren'Py 兼容性参考、Go 编译器基线、Rust 运行时基线

## 决策

Ren'Py 保持为独立的参考 fork 和兼容性 fixture 来源。新引擎仓库不复制 Ren'Py Python 包或运行时实现；Go 编译器和 Rust 运行时在本仓库内并列维护，阶段 0 只使用标准库。当前本地目录是新引擎候选仓库，远程 `origin` 已核验为 `https://github.com/yelusiku537/SuiYu-GameEditor`；远程默认分支为 `master`（另有仍停留在初始提交的 `main` 分支，不用于开发），阶段 0 实施分支为 `codex/phase0-complete`。

Ren’Py fork 已由 `yelusiku537` 建立并通过 GitHub API 核验为公开仓库，默认分支为 `master`。完整 clone 位于 `D:\my-project\renpy-reference-git`，保留 19,649 个提交和完整 blob；`origin` 指向 fork，`upstream` 指向官方仓库，`upstream` push URL 固定为不可用地址。项目外 `D:\my-project\renpy-reference` 的源码快照继续保留，供不需要 Git 历史的快速分析使用。

## 仓库地址与责任

| 仓库 | 地址 | 可见性 | 默认分支 | 责任 |
| --- | --- | --- | --- | --- |
| 新引擎工程 | `https://github.com/yelusiku537/SuiYu-GameEditor`（本地 origin 已核验） | public | `master`（远程默认分支；`main` 仅有初始提交，不用于开发；阶段 0 工作分支为 `codex/phase0-complete`） | Go 编译器、Rust 运行时、fixture、文档与 CI |
| Ren’Py 参考 fork | `https://github.com/yelusiku537/renpy`（官方上游 `https://github.com/renpy/renpy`） | public | `master` | 保存参考历史、兼容性对照材料和上游同步上下文 |

## 对照坐标

| 项目 | 值 | 证据状态 |
| --- | --- | --- |
| Ren'Py Windows SDK | 8.6.1；官方发布页 `https://www.renpy.org/release/8.6.1`；Windows SDK ZIP 复验 SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb` | 发布版本、归档指纹和 GitHub Actions run `44982689865` 的下载、校验、解压、lint、增强 GUI smoke 均已核验 |
| Ren'Py upstream tag | `8.6.1.26111705`；tag object `a2ded0b29fd1e0b61972469cfc558a910e717e3c`；peeled commit `de379eb4f85a4930244786c715e581a1cb3fd374` | `D:\my-project\renpy-reference-git` 本地 `git show` 已核验 |
| 完整参考提交 SHA | `de379eb4f85a4930244786c715e581a1cb3fd374` | 本地完整 clone `git show`、`git fsck --full` 已通过 |
| 本次 fixture | `compatibility-tests/fixtures/renpy/phase0` | 新引擎自编原创样例；本地 SDK lint 与增强 GUI smoke、CI run `44982689865` 的精确文本 widget/return/正常退出断言均已通过；人工像素观察未执行 |

## 只读上游同步步骤

在已经核验的参考 fork 根目录执行。`$RenpyDefaultBranch` 必须由远程引用确认：

```powershell
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
```

只有祖先检查退出码为 0 才能说明 fork 包含上游头；退出码为 1 记录分叉，其他非零值按 Git 错误处理。同步前比较差异，阶段 0 不执行远程推送。

## 内容边界

- Ren'Py Python 包结构只存在于参考 fork 的历史材料中，不作为新引擎实现复制。
- `compatibility-tests/fixtures/renpy/` 中的脚本是新仓库自编 fixture，独立记录来源和许可。
- Go 工具与 Rust 运行时通过明确命令或文件协议协作，阶段 0 不共享实现代码。
- MyGo Native UI、SDL3、wgpu 只登记版本和许可来源；在依赖实际引入前不得复制其代码或素材。

## 当前未决项

| 项目 | 当前记录 |
| --- | --- |
| Ren’Py fork 地址、可见性、默认分支 | `https://github.com/yelusiku537/renpy`，public，`master`；fork 头 `0be2c7103be5d537d9e6cad54ee44ce34c9422a` |
| 完整参考提交 SHA 与 fork Git 退出码 | `D:\my-project\renpy-reference-git`：`--is-shallow-repository=false`，`rev-list --count HEAD=19649`，`git show de379eb4f85a4930244786c715e581a1cb3fd374` 成功，`git fsck --full` 退出码 0；`merge-base --is-ancestor refs/remotes/upstream/master refs/remotes/origin/master` 退出码 0 |
| 参考提交许可核对 | GitHub API tree `67624ee443dd2dd03993d50e8e889459a528ad1e`；`sphinx/source/license.rst` blob `f4068def0d31d8d87cd9c7c9e665381b0cce1705`，记录 MIT/LGPL/依赖许可证；本仓库未复制其文件 |
| 新引擎许可证 | 阶段 0 自有代码采用 MIT，见根目录 `LICENSE` 与 `LICENSES/THIRD_PARTY.md` |
| Go module import path | `github.com/yelusiku537/SuiYu-GameEditor/compiler-go`，按本地 origin 暂定 |
| ADR 路径 | `docs/adr/0001-reference-repository.md` |
