# 项目进度与协作看板

> 用途：公开、不含个人信息的项目进度与规范索引。具体证据、命令和限制以链接的源文档为准；本文件只做汇总，不替代验收记录。
>
> 最近更新：2026-11-22（Asia/Shanghai）

## 当前阶段

| 阶段 | 名称 | 状态 | 主要证据 |
| --- | --- | --- | --- |
| **00（P0）** | 仓库、许可证和开发环境基线 | **已完成** | [验收记录](development/phase0-verification.md) · [阶段计划](superpowers/plans/phase-00/README.md) |
| 01 | Ren'Py 源码分析与行为地图 | 未开始 | [阶段计划](superpowers/plans/phase-01/README.md) |
| 02–14 | 游戏包格式、运行时、脚本语言、编辑器、效果与生态 | 未开始 | [阶段计划索引](superpowers/plans/README.md) |

路线图与可认领任务统一在 [Issue #1「路线图 TODO 合集 · 阶段 01–14」](https://github.com/yelusiku537/SuiYu-GameEditor/issues/1) 追踪。阶段 00 不在该合集内，其完成状态以本文件和验收记录为准。

## 阶段 00 完成结论

阶段 00 的六项验收均有记录，详见[阶段 0 验收记录](development/phase0-verification.md)：

- Go 与 Rust 两个独立命令行基线可在干净 Windows 环境按 README 构建、测试并启动。
- 同一检查入口 `scripts/phase0-check.ps1` 在无本地缓存的 GitHub Actions Windows runner 上通过。
- 固定官方 Ren'Py SDK 完成 lint、归档 SHA-256 校验和自动 GUI smoke（精确文本、`return`、正常退出），**未做人工像素观察**。
- 第三方材料、工具链与参考仓库坐标均已登记来源和许可。
- `git status` 不出现构建缓存或个人文件；至少一份 ADR 说明了参考仓库和新引擎仓库的关系。

由此，阶段 00 的状态提升为「已完成」。该结论只代表工程环境与对照基线可用，不代表运行时性能、Ren'Py 语义兼容性或 MyGo 原生 UI 体验已达成。

## 规范与限制

- **状态变更只认运行证据。** 任何阶段/任务只有在对应命令、退出码或 CI/桌面记录存在时才能标为「通过」；计划、意图或局部源码检查不能替代实际运行。详见[验收记录·后续更新规则](development/phase0-verification.md#后续更新规则)。
- **认领与验收流程。** 在 Issue #1 评论 `认领 P01-01` 并注明未就绪依赖；PR 引用 Issue 与任务编号，附交付路径、命令、退出码/证据和已知限制。详见[阶段计划索引·认领与验收](superpowers/plans/README.md)。
- **技术边界。** Go 负责编辑器、编译器、转换器与打包；Rust 负责游戏运行时；两者通过项目文件、游戏包或低频调试协议通信，不做每帧跨语言调用。详见[总计划](https://github.com/yelusiku537/SuiYu-GameEditor/blob/master/renpy-vibe-engine-plan.md)。
- **第三方与许可证。** 新增外部代码、素材或链接依赖前，先在[第三方来源台账](../LICENSES/THIRD_PARTY.md)登记版本、来源、许可、版权和路径。
- **构建产物隔离。** 构建输出、Go/Cargo 缓存和测试临时目录放在仓库树之外，不提交到 Git。本地入口为 `pwsh -NoProfile -File ./scripts/phase0-check.ps1`。
- **工具链固定。** Go、Rust/rustfmt、SDK、runner 镜像及外部组件版本以[工具链台账](development/toolchain.md)为准；版本变化需同步更新该台账与验收记录。
- **参考仓库只读。** Ren'Py 参考 fork 仅用于源码研究与行为对照，`upstream` 为只读同步，同步细节见 [ADR 0001](adr/0001-reference-repository.md)。

## 已知未决项

- Ren'Py GUI 验收仅覆盖自动 smoke，人工像素观察仍待后续阶段按特性补充（不影响阶段 00 完成判定）。
- Rust MSVC linker / Windows SDK 的具体来源尚未单独定位，阶段 00 Rust 构建实际通过，来源待补，见[工具链台账](development/toolchain.md)。
- 阶段 01 及以后的功能、性能与兼容性结论尚未产生，不得对外宣称已达成。

## 隐私与数据边界

本文件及仓库内的公开文档只记录版本、提交 SHA、命令、退出码、CI/运行链接和可复现证据，不写入用户名、个人目录路径、令牌或其它可识别个人身份的信息。涉及本地机器路径的原始记录以变量或省略形式呈现。