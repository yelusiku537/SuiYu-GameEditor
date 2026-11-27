# 音频播放 / 停止的可观察状态

## 环境

| 项目 | 值 |
| --- | --- |
| Ren'Py SDK | `renpy-8.6.1-sdk`（Windows ZIP SHA-256 `596c31be88b351de64166276708278a70f24e833be7181e7c37b8c106a0f0fdb`） |
| upstream tag | `8.6.1.26111705` |
| 对照提交 | `de379eb4f85a4930244786c715e581a1cb3fd374` |
| 平台 / shell | Windows 11 x64；PowerShell 7 |
| 全量入口 | `pwsh -NoProfile -File ./scripts/phase01-check.ps1 -RenpySdk <sdk>` |
| 单 fixture 入口 | `renpy.exe <project> test <testcase> --savedir <dir>`，模板见 `docs/compatibility/README.md` §7 |

本条对应计划表 B10，目标等级预先登记为“允许不同（时序）”。

## 上游代码路径与符号

路径相对 SDK 根目录（`renpy-8.6.1-sdk/`）。

- 剧本语句入口：`renpy/common/000statements.rpy` 注册四个用户语句——`play music`（`:177`）、`stop music`（`:285`）、`play sound`（`:332`）、`stop sound`（`:376`）。`play music` 的 `execute_play_music`（`:123`）调用 `renpy.music.play(...)`；`stop music` 的 `execute_stop_music`（`:276`）调用 `renpy.music.stop(...)`；`play sound`（`:306`）与 `stop sound`（`:365`）分别调用 `renpy.sound.play` / `renpy.sound.stop`，而 `renpy/audio/sound.py` 的实现只是把同名调用转给 `renpy.audio.music`（`sound.py:34 play`、`:61 stop`、`:81 get_playing`）。
- 用户语句经 `renpy/ast.py:2179 class UserStatement` 执行；`UserStatement.execute`（`:2297`）先 `next_node(self.get_next())` 再 `statement_name(name)`，最后 `self.call("execute")`，这解释了轨迹里 `play`/`stop` 行记录为 `node: UserStatement`。
- `renpy/audio/music.py:36 play`：参数归一化后，取/建通道，`fadeout is None` 时改用 `config.fadeout_audio`，先 `c.dequeue()` 与 `c.fadeout(fadeout)`，再 `c.enqueue(filenames, loop=..., fadein=...)`，并把 `last_filenames` 写进通道上下文。即“播放”是向通道入队 + 启动淡入，而不是同步解开整段音频。
- `renpy/audio/music.py:287 stop`：`c.fadeout(fadeout)` 后把 `ctx.last_filenames` 置空、`c.last_filenames` 置空；`stop` 本身只改变通道状态，不等淡出结束。
- `renpy/audio/music.py:459 get_playing`：转调 `renpy.audio.audio.get_channel(channel).get_playing()`；实现在 `renpy/audio/audio.py:839`——优先取 `renpysound.playing_name`，取不到再退到 `self.queue[0].filename`，最后退到 `self.loop[0]`；`pcm_ok` 为假时直接返回 `None`。
- 音频子系统初始化在 `renpy/audio/audio.py:1125 init`：`renpysound.init` 失败时写日志并改用 `SDL_AUDIODRIVER=dummy` 重试，成功后 `pcm_ok = True`。因此 CI/无独显无声卡环境下仍然能读到 API 级状态，但并没有真实回放。

## fixture

- 目录：`compatibility-tests/fixtures/renpy/phase01/p01-03-audio/`
- `game/audio/tone.ogg`：4518 字节，SHA-256 `d620787f1db5ed137152d4bb734747ca3fa8a5a58d3eba5efcfe9fd2369877c9`。来源登记为**自编素材**：由 ffmpeg 生成的定长 440 Hz 正弦波 OGG（符合 `docs/compatibility/README.md` §4 对音频素材的要求）。
- `game/script.rpy`：
  - `:13 init python:` 定义 `audio_state()`，返回 `{"music": renpy.music.get_playing("music"), "sound": renpy.music.get_playing("sound")}`。
  - `:20 label start:` → `:21 $ emit("audio_initial", ...)` → `:22 play music "audio/tone.ogg" fadein 0.1` → `:23 $ emit("audio_playing", ...)` → `:24 play sound "audio/tone.ogg"` → `:25 $ emit("audio_sound_playing", ...)` → `:26 stop sound` → `:27 $ emit("audio_sound_stopped", ...)` → `:28 stop music` → `:29 $ emit("audio_music_stopped", ...)` → `:30 "audio checked"` → `:31 $ finish()`。
  - `:36 testsuite global:` 设 `_test.timeout = 25.0`、`_test.transition_timeout = 0.05`、`_test.screenshot_directory = "shots"`、`_test.overwrite_screenshots = True`。
- testcase：`audio_lifecycle`（输入序列见下）。
- `game/zz_evidence.rpy` 为 `compatibility-tests/fixtures/renpy/phase01/harness/zz_evidence.rpy` 的逐字节副本。
- 证据：`docs/compatibility/evidence/03-audio/actual.jsonl`、`expected.jsonl`、`run.log`（`lint_exit: 0`，`testcases: audio_lifecycle`，`total_records: 19`）。

## 输入序列

```text
$ arm()
run Jump("start")
advance until screen "say"
advance
$ disarm()
exit
```

`arm()` 清空并开始录制；`run Jump("start")` 跳过主菜单；`advance until screen "say"` 消解首行竞态；一次 `advance` 越过 `"audio checked"` 后 `disarm()`，随后 `exit`。

## 预期 vs 实际观察

语义预期（`expected.jsonl` 的断言，共 6 条）：

1. 初始无音乐、无音效：`audio_initial {music: null, sound: null}`。
2. `play music` 后 music 通道报告该文件名，sound 仍为 `null`。
3. `play sound` 后两通道同时报告该文件名。
4. `stop sound` 后只剩 music。
5. `stop music` 后两通道均为 `null`。
6. 流程走完并 `flow_complete`。

实际（`docs/compatibility/evidence/03-audio/actual.jsonl`，关键记录，行号为 `game/script.rpy`）：

```jsonl
{"kind": "audio_initial", "music": null, "sound": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 22, "node": "UserStatement", "ret": 0, "what": null, "who": null}
{"kind": "audio_playing", "music": "audio/tone.ogg", "sound": null}
{"kind": "audio_sound_playing", "music": "audio/tone.ogg", "sound": "audio/tone.ogg"}
{"kind": "audio_sound_stopped", "music": "audio/tone.ogg", "sound": null}
{"kind": "audio_music_stopped", "music": null, "sound": null}
{"file": "game/script.rpy", "kind": "stmt", "line": 30, "node": "TranslateSay", "ret": 0, "what": "audio checked", "who": null}
{"kind": "flow_complete"}
```

要点：

- 四条 `play`/`stop` 语句在轨迹里各产生一条 `node: UserStatement`（行 22/24/26/28），其后的 `$ emit(...)` 是 `node: Python`（行 23/25/27/29）；`audio_*` 记录紧跟在各自的 `Python` 记录之后，说明状态快照读的是该语句执行完的瞬间。
- `audio_state()` 只读 `renpy.music.get_playing("music")` / `("sound")`，因此断言的**只有“哪个通道报告哪个文件名”**，不包含音量、是否真实出声、淡入曲线。
- `run.log` 的 `record_kinds` 为 `{"audio_initial": 1, "audio_music_stopped": 1, "audio_playing": 1, "audio_sound_playing": 1, "audio_sound_stopped": 1, "flow_complete": 1, "label": 1, "stmt": 12}`，合计 19 条；`expected.jsonl` 作为有序子序列全部命中。
- 读到 `"audio/tone.ogg"` 而不是 `null`，同时说明本次运行的音频子系统已初始化（`pcm_ok` 为真，可能走了 `SDL_AUDIODRIVER=dummy` 回退）。若 `pcm_ok` 为假，`get_playing` 会恒返回 `None`，本条断言将无法成立。
- 实际记录的值来自 `get_playing` 在 `playing_name` 缺失时的 `queue[0].filename` / `loop[0]` 回退（`renpy/audio/audio.py:839`），也就是入队即可读到，不要求解码已经开始。这正是本条把时序列为“允许不同”的直接依据。

## 自动轨迹 vs 人工观察

- 本文结论全部来自 `actual.jsonl` 与 `expected.jsonl` 的子序列比对；**未进行人工试听**，没有确认 440 Hz 正弦波是否真正被听到、淡入 0.1 秒是否符合预期，也没有检查系统音量或设备输出。
- 复测条件：SDK SHA、对照提交、`game/script.rpy`、`zz_evidence.rpy` 或 `tone.ogg` 任一变化，或 `scripts/phase01-check.ps1` 报告基线不可复现/子序列不匹配时，按 README §7 重跑 `audio_lifecycle` 并重新审定基线。若运行环境变为 `pcm_ok = False`（例如强制 `RENPY_DISABLE_SOUND`），报 `null` 属环境差异而非语义回归，须另立补证记录。

## 限制

1. 只断言 API 级可观察状态（通道 → 文件名），**没有可听性验证**：无波形分析、无录音回采、无音量测量。CI/无头环境本就无声卡，回放是否发生不可从证据判断。
2. `fadein 0.1` 与 `stop` 的默认淡出（`config.fadeout_audio`）没有被计时断言；`stop` 后立刻读到 `null` 只说明 API 已不报告该文件，不代表淡出期间没有残留声音。淡出时长、曲线、是否被 `config.fadeout_audio` 改写均未覆盖。
3. 未覆盖：`play` 的 `loop` / `noloop` / `if_changed` / `volume` / `channel` / `queue` 变体，`stop` 的显式 `fadeout`，多通道/自定义通道，`renpy.music.get_state` 的四态（idle/playing/paused/ended）与 `is_playing`。
4. `pcm_ok` 的回退路径（`SDL_AUDIODRIVER=dummy`）未在本次证据中单独记录；无法从 `actual.jsonl` 判断真实模拟输出设备还是 dummy 驱动。
5. `play sound` 默认落到 `sound` 通道且 `loop` 默认 false，但轨迹只记录入队后立即的文件名，未验证自然播放结束后 `get_playing` 是否回到 `null`。
6. 自定义记录 `audio_*` 由 fixture 主动 `emit`，只能反映采样点；两次 emit 之间的状态变化（例如淡入完成、队列推进）不可见。

## 目标兼容等级

**允许不同（时序）** — 新引擎必须复现“在指定通道上播放/停止哪个文件”的可观察映射（`music`/`sound` 两通道在四个时点上的值必须一致），但淡入淡出时序、解码启动时机与真实音频输出允许不同。依据：`docs/compatibility/evidence/03-audio/actual.jsonl`、`expected.jsonl`、`run.log`。