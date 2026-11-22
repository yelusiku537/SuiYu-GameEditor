# 第三方来源台账

核验日期：2026-11-22。阶段 0 当前没有复制第三方源代码、字体、图像或音频；Go/Rust 基线只使用标准库。

| 用法 | 名称与版本/SHA | 项目 URL | 许可证/声明位置 | 适用路径 | 版权/分发条件 | 核验状态 |
| --- | --- | --- | --- | --- | --- | --- |
| 仅参考 | Ren'Py 8.6.1；tag `8.6.1.26111705`; `de379eb4f85a4930244786c715e581a1cb3fd374` | `https://github.com/renpy/renpy`, `https://www.renpy.org/release/8.6.1` | `sphinx/source/license.rst`（MIT、LGPL 与依赖清单）；README 贡献许可说明 | 参考 fork、独立 SDK fixture | 只读参考；不得把 SDK 内容当作新引擎代码分发 | 完整历史 clone、GitHub API 和源码快照均已核验 |
| 仅参考 | Ren'Py Windows SDK 8.6.1；ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb` | `https://www.renpy.org/release/8.6.1` | SDK 随附许可文件，以实际归档为准 | 项目外一次性验收目录 | 不复制入仓库；按 SDK 条款使用 | 官方发布页、`checksums.txt`、本地归档下载/lint/增强 GUI smoke 与旧 CI 下载/lint/GUI smoke 已核验；新 CI 增强断言待验证 |
| 仅参考 | MyGo Native UI `v0.10.0`; `ebde9399baf2734b3361856a53f4036859973d1d` | `https://github.com/egoist/mygo` | MIT，官方仓库许可证 | 仅版本台账 | 阶段 0 不引入 | 官方版本与许可证已核验 |
| 仅参考 | SDL3 `release-3.4.20`; `f00dc919ca35b9756316e86c4777392de442f9b2` | `https://github.com/libsdl-org/SDL` | SDL 许可文件 | 仅版本台账 | 阶段 0 不引入 | 官方 release 坐标已核验 |
| 仅参考 | wgpu `v30.0.2`; `89f8a2be4a536503ed97451320cda16414044e31` | `https://github.com/gfx-rs/wgpu` | wgpu 仓库许可/NOTICE | 仅版本台账 | 阶段 0 不引入 | 官方 release 坐标已核验 |
| 自制样例 | `SuiYu phase 0 fixture` | 本仓库 `compatibility-tests/fixtures/renpy/phase0` | 项目自有 MIT 许可决策；无外部素材 | Ren'Py `script.rpy` | 可随本仓库分发 | 已确认原创单句文本 |
| 复制/随包分发 | 第三方字体、图像、音频 | 不适用 | 不适用 | 不适用 | 本阶段未引入 | 未采用 |

任何实际复制的文件必须保留原版权、许可证、NOTICE 或文件头，并补充原始路径和永久链接。来源或分发条件有疑问时，暂停纳入仓库或构建产物。
