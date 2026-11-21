# Contributing

## 本地检查

提交前在 Windows PowerShell 7 执行 `pwsh -NoProfile -File ./scripts/phase0-check.ps1`。Go 文件使用 `gofmt`，Rust 文件使用 `rustfmt`；fixture 只放在 `compatibility-tests/fixtures/`，不得把 SDK 内容复制进仓库。

## 变更边界

- 维护 Go 编译器和 Rust 运行时的独立边界，不引入阶段 0 不需要的依赖。
- 新增外部代码、素材或链接依赖前，先在 `LICENSES/THIRD_PARTY.md` 登记版本、来源、许可、版权和路径。
- Ren'Py 行为对照、上游坐标和同步规则遵循 `docs/adr/0001-reference-repository.md`。
- 工具链变化同时更新 `docs/development/toolchain.md` 和验收记录。

## 分支与提交

使用描述性分支名和清晰的命令式提交标题。提交前保持格式检查、单元测试和最小构建通过；PR 说明应列出测试命令、未验证项和第三方来源变化。阶段 0 的远程 fork、推送和 PR 创建需要维护者明确授权。
