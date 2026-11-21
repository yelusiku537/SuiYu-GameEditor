# ADR 0001: 参考仓库与新引擎边界

- 状态：阶段 0 已记录，远程参考 fork 已建立；完整 Git 历史克隆受网络限制未完成
- 日期：2026-11-21
- 范围：Ren'Py 兼容性参考、Go 编译器基线、Rust 运行时基线

## 决策

Ren'Py 保持为独立的参考 fork 和兼容性 fixture 来源。新引擎仓库不复制 Ren'Py Python 包或运行时实现；Go 编译器和 Rust 运行时在本仓库内并列维护，阶段 0 只使用标准库。当前本地目录是新引擎候选仓库，远程 `origin` 已核验为 `https://github.com/yelusiku537/SuiYu-GameEditor`，分支为 `main`，当前 HEAD 为 `a470600`（`chore: initialize repository`）。

Ren’Py fork 已由 `yelusiku537` 建立并通过 GitHub API 核验为公开仓库，默认分支为 `master`。Git Smart HTTP 经本机加速器返回 403，SSH over port 443 在完成克隆前长时间停滞，因此本次没有把不完整的 pack 当作完整 clone。项目外 `D:\my-project\renpy-reference` 保留了 `master` 树的 1200 个源码/文档文件 API 快照及 `TREE_MANIFEST.tsv`；该目录仅供阶段 1 源码分析，不能替代带历史的参考仓库。

## 仓库地址与责任

| 仓库 | 地址 | 可见性 | 默认分支 | 责任 |
| --- | --- | --- | --- | --- |
| 新引擎工程 | `https://github.com/yelusiku537/SuiYu-GameEditor`（本地 origin 已核验） | 未验证 | `main`（本地当前分支） | Go 编译器、Rust 运行时、fixture、文档与 CI |
| Ren’Py 参考 fork | `https://github.com/yelusiku537/renpy`（官方上游 `https://github.com/renpy/renpy`） | public | `master` | 保存参考历史、兼容性对照材料和上游同步上下文 |

## 对照坐标

| 项目 | 值 | 证据状态 |
| --- | --- | --- |
| Ren'Py Windows SDK | 8.6.1；官方发布页 `https://www.renpy.org/release/8.6.1`；Windows SDK ZIP 复验 SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb` | 发布版本与归档指纹已登记；本机未下载复验 |
| Ren'Py upstream tag | `8.6.1.26111705` | 官方远程材料已取得；未执行本地 `git show` |
| 完整参考提交 SHA | `de379eb4f85a4930244786c715e581a1cb3fd374` | GitHub API 已核验该提交存在；本地完整 clone 尚未完成，未执行本地 `git show` |
| 本次 fixture | `compatibility-tests/fixtures/renpy/phase0` | 新引擎自编原创样例，待独立 SDK GUI 验收 |

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
| 完整参考提交 SHA 与 fork Git 退出码 | API 已核验 `de379eb4f85a4930244786c715e581a1cb3fd374`；本地 clone 因 403/停滞未完成，`--is-shallow-repository` 等本地历史检查未验证 |
| 参考提交许可核对 | GitHub API tree `67624ee443dd2dd03993d50e8e889459a528ad1e`；`sphinx/source/license.rst` blob `f4068def0d31d8d87cd9c7c9e665381b0cce1705`，记录 MIT/LGPL/依赖许可证；本仓库未复制其文件 |
| 新引擎许可证 | 阶段 0 自有代码采用 MIT，见根目录 `LICENSE` 与 `LICENSES/THIRD_PARTY.md` |
| Go module import path | `github.com/yelusiku537/SuiYu-GameEditor/compiler-go`，按本地 origin 暂定 |
| ADR 路径 | `docs/adr/0001-reference-repository.md` |
