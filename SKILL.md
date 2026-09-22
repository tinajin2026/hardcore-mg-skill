---
name: hardcore-mg-skill
description: 将任意中文或英文帖子、稿件或内容先识别为 24 类语义信号，自动激活 24 套结构程序、48 套执行配方、96 条原子动作、12 条微运动规则和 12 条注意阅读规则，组合成证据、世界、构图、文字、运动、焦点、转场、连续性与护栏共同服务的多维方法栈，再生成 MiniMax H3 可执行的 4–15 秒 MG 导演方案、逐镜/微时间拍、五层画面、生命周期、原生 Prompt 和 API 请求体。用于“看到这段内容该想到什么画面”“内容自动触发 MG 方法论”“15 秒 MG”“MiniMax H3”“MG 分镜”“动态图形提示词”、产品/科普/品牌/数据/角色/字体/三维/活动动画策划或要求颗粒度对齐专业 MG 样片时；方法已完成去来源化蒸馏，不要求回忆原片或时间位置。
---

# 硬核的 MG Skill

把内容编译成 MiniMax H3 能执行、人能逐拍审查的 MG 导演合同。先读取稿件中的比较、因果、机制、证据、流程、价值等关系，再让多条方法围绕同一主体和同一视觉世界分工协作；细节不来自堆砌形容词、镜头或特效。

## 默认合同

- 目标模型：`MiniMax-H3`；每段 `duration_seconds` 必须是 4–15 秒整数，默认 24 FPS、2K、16:9。
- 最小输入只有 `content`。文本输入默认 `T2VA`；素材按角色路由 `I2VA | L2VA | FL2VA | Ref2VA`。
- 默认 `subtitle_mode: disabled`、`bottom_caption: forbidden`、`voiceover_transcript: forbidden`。
- 导演卡使用用户语言；H3 原生 Prompt 使用英文，锁定对白、歌词和画面文字保持原语言与标点。
- 先输出 `h3-mg-plan.v7` JSON 真源，再从同一真源渲染 Markdown 导演板和逐段 H3 Prompt。
- 只策划时不调用 API、不消耗余额；请求体不包含 API Key。
- 不添加内容没有支持的事实、功能、人物、关系、数字、因果、对白或结论。

先读 [minimax-h3-contract.md](references/minimax-h3-contract.md) 核对 H3 接口；当核验日期超过 30 天或用户要求实际生成时，重新打开其中的 MiniMax 官方来源。

## 1. 规范化输入

提取或保守推断：

```yaml
content: 用户原文
project_title: auto
source_language: auto
target_model: MiniMax-H3
resolution: 2K
aspect_ratio: "16:9"
entity_mode: neutralize
source_assets: []
reference_media: []
exact_dialogue: []
exact_lyrics: []
exact_visible_text: []
```

冻结数字、专名、引用、对白、歌词和画面文字。区分：

```text
prompt_explicit | media_observed | upstream_claim | model_inferred | default_assumption
```

只有直接检查过的图片、视频或音频才能写 `media_observed`。文件名、附件占位和上游文字不能冒充视觉/听觉事实。

## 2. 语义分段

先按完整认知任务切段，再适配 H3 时长：

1. 每段只保留一个 `core_claim`。
2. 优先在因果闭合、主体/年代变化、问题转证据、机制回装或结论稳定处切分。
3. 普通话仅用 4.5–5.2 字/秒初估；数字、英文、专名和停顿另计。
4. 超过 15 秒的语义单元拆成 `建立 -> 解释/证据 -> 回收`，各自仍需闭合。
5. 不足 4 秒的尾段与前段合并；无法合并时用可读停留补到 4 秒，不发明新信息。
6. `source_span.text` 必须是原文的连续片段，所有片段按顺序恰好覆盖原文一次。

需要更细的叙事/媒介判断时读 [narrative-routing.md](references/narrative-routing.md)。

## 3. 激活并组合方法论

必须依次打开：

- [director-cognition-engine.md](references/director-cognition-engine.md)：从判断到三种脑内候选。
- [method-composition-engine.md](references/method-composition-engine.md)：从新稿件到多维方法职责图。
- [method-trigger-lattice.yaml](references/method-trigger-lattice.yaml)：24 类信号、24 套程序和 18 条融合规则。
- [method-runtime-contract.json](references/method-runtime-contract.json)：由触发矩阵确定性编译的信号强制动作、程序 spine 与融合规则只读镜像；不得手改。
- [director-method-recipes.json](references/director-method-recipes.json)：40 个题材/媒介特征、48 套执行配方和 6 条动作冲突规则。
- [director-move-catalog.yaml](references/director-move-catalog.yaml)：96 条原子动作。
- [micro-motion-choreography.md](references/micro-motion-choreography.md)：12 条起势、错峰、范围、锚点、制动与停留规则。
- [attention-reading-choreography.md](references/attention-reading-choreography.md)：12 条首焦、读序、增量、运动预算、证据隔离与焦点交棒规则。

对每段执行：

```text
判断图谱 → 一个主信号 + 0–4 个次信号
→ 一个主程序 + 0–3 个辅助程序
→ 一个主执行配方 + 0–2 个叠加配方
→ 证据原生/机制原生/领域原生三种脑内候选
→ 按语义完整激活原子动作，不设数量配额 → 冲突消解 → 五阶段效果链
→ 逐镜自动触发微运动规则 → 起势/主变/响应/制动/停留
→ 逐镜自动触发注意阅读规则 → 首焦/读序/信息增量/阅读锁/焦点交棒
```

先写 `director_intent`，至少包含触发、观众问题、证据责任、三种候选、选择理由、被拒绝的俗套和最终脑内画面。第一个联想只能算候选：看到 AI 不自动画芯片，看到增长不自动画箭头，看到帖子不重打一行大字。

### 判断图谱

先把原文改写为：`主体 A 在条件 C 下，因为机制 M，从 S0 变为 S1，相对基线 B 产生结果 R`。缺失项必须标为未知，不能用画面补造。`operator` 决定唯一主信号；题材、品牌、媒介和情绪通常只是次信号。出现两个同等强度主信号时先拆段。

### 方法栈

主程序决定 `opening -> development -> turn -> payoff -> landing`；辅助程序必须声明插入哪个阶段以及只承担什么责任，不能另开场景和主线。执行配方把结构程序继续落到证据、媒介、持久世界和题材对象。可运行 `scripts/compose_method_stack.py --signals SG15,SG14,SG07 --primary-signal SG15`，直接从信号确定主程序、最小辅助程序、适用融合规则，并推导一个主配方、零到两个叠加配方、世界锁和动作候选；也可用 `--features ... --primary ...` 显式补充配方特征。相同输入必须得到相同结果。若五个信号无法由一个主程序和最多三个辅助程序覆盖，必须拆分语义段或降级最弱次信号，禁止硬塞成五条并行主线。

从 96 条动作中选择完成当前认知任务所必需的全部 `selected_moves`，不设最低条数或最高条数；必须包含 `N/C/M/L/Q`，其他维度只在原文、素材、格式或连续性真正触发时进入。这里的原子动作是导演方法职责，不等于时间轴上连续播放的可见动作；多个方法可以共同约束同一个微时间拍。实际执行密度由 `shots[].micro_beats` 决定，每个微时间拍仍只能有一个主动作，并为文字和结果保留稳定停留。路由输出原样保存为 `router_move_ids`；当前原文、素材、时长、事实、连续性或格式要求的替换逐项写入 `move_adaptations`，重放差分必须恰好得到最终动作。

同时写 `method_stack`：

```text
detected_signals + feature_tags + primary_feature_tag
primary/supporting programs + primary/overlay recipes
program/recipe bindings(activated_by/stages/move_ids/responsibility)
fusion_bindings(rule/signals/stages/moves/implementation/combined_effect)
router_move_ids + explicit add/remove adaptations
activations(move_id/role/triggered_by/contribution/interacts_with)
composition_logic + collision_resolutions
effect_chain(opening/development/turn/payoff/landing)
stage_bindings(stage/owner_program/move_ids/state_change)
discarded_methods + density_strategy
```

每个已检测信号的主特征必须进入 `feature_tags`；`primary_feature_tag` 必须由主信号给出；主程序必须属于主信号候选，每个次信号至少被一个已选程序承接。主信号的 `forced_moves` 与主程序完整 `spine` 必须进入画面；每个辅助程序至少贡献两条 spine 动作，主配方至少贡献四条 required moves，叠加配方至少贡献两条。每个 program/recipe binding 用 `move_ids` 指出它实际贡献的最终动作。保留路由器原始动作，再用 `move_adaptations` 逐条解释增删；不得直接改写结果。所有适用融合规则必须用结构化 binding 写清双方动作和组合效果，五个 `stage_bindings` 必须按顺序且恰好覆盖全部已选动作。

动作职责从 `spine | world | composition | evidence | text | motion | transition | continuity | guardrail` 中选择。每条动作必须绑定当前原文触发和至少一个协作动作，每个已检测信号必须实际驱动至少一条最终动作；没有协作对象的“效果”应删除。多个 W 世界同时存在时，必须明确哪个只承担局部责任、哪个保持持久世界。每段至少写一条冲突消解和两个具体放弃项。

### 微运动编排

方法栈决定“这段要做什么”，微运动规则决定“每个变化按什么顺序发生”。对每镜从 [micro-motion-choreography.md](references/micro-motion-choreography.md) 自动选择完成当前动作所需的全部规则，不设最低或最高条数，也不为覆盖 ID 添加可见动作。先判断变化范围 `local | regional | full_frame`，再确定连续锚与唯一主动作，最后编排 `attention cue -> anticipation -> primary change -> delayed response -> settle -> readable hold`。

每段必须写 `micro_motion_plan.rule_bindings`：规则 ID、当前触发、落到哪些镜头、变化范围、具体实现和所防止的失败。每镜至少被一条规则覆盖；所有可见主动作必须由 `MM03` 覆盖；含文字事件的镜头必须由 `MM09` 或 `MM11` 覆盖。`MM04` 只允许真正的全画幅章节重置，`MM10/MM12` 必须保留局部或区域语境。

### 注意与阅读编排

方法栈和微运动计划完成后，再为每镜写 `attention_reading_plan.shot_bindings`。从 [attention-reading-choreography.md](references/attention-reading-choreography.md) 自动选择完成该镜观看责任所需的全部规则，不设数量配额。每条绑定必须写清 `attention_entry`、有序 `focus_path`、唯一 `information_delta`、`motion_budget`、`reading_lock` 与 `exit_focus`。

每镜恰好绑定一次。含 `text_events` 的镜头必须激活 `AF04/AF07/AF08` 至少一条，阅读窗口的运动预算只能是 `static` 或 `low`；需要高能进入时，先完成动作和制动，再启动阅读时钟。多镜段落中除最后一镜外必须使用 `AF10`，让本镜退出焦点在对象、位置、方向、形状、颜色或概念上被下一镜首焦接住。AF 规则只进入 JSON 审计层，H3 Prompt 写具体观看路径，不输出规则 ID。

## 4. 建立视觉系统

先写一个 `visual_thesis`：这段内容最适合被理解成什么持久世界，为什么。然后登记：

- 画布、安全区、网格、边框、纹理和光源。
- 语义色：中立、活动、风险、证据、主体身份。
- 文字五角色：章节、语义印章、证据标签、数据、真实 UI/文件。
- 组件槽位：标题、主体、证据、数据、来源和段尾锚。
- 转场政策：世界内更新、章节重置、实拍/MG 接力各只设一套主语法。
- 全片方法弧：持久世界和反复母题写进 `style_bible`，章节重置写进 `transition_policy`，跨段状态与密度递进写进 `continuity_ledger`；各段不得重新发明视觉世界。
- `entity_registry`：所有可见主体只登记一次，锁定位置、尺度、朝向、材质、光源和来源。

需要组件/隐喻、排版或跨段时分别读：

- [components-metaphors.md](references/components-metaphors.md)
- [typography-layout.md](references/typography-layout.md)
- [continuity-density.md](references/continuity-density.md)

## 5. 选择 XPC 模式

必须打开 [xpc-300-pattern-atlas.md](references/xpc-300-pattern-atlas.md)，为每段选择一个主 Pattern ID；混合内容最多再选一个次 ID。图谱只保留蒸馏后的状态语法，不含原片身份、时间码或复刻入口。

```text
数据/比较 -> XPC-DATA-BASELINE-DELTA
品牌/企业 -> XPC-BRAND-MOTIF-PROOF-LOCKUP
产品/UI -> XPC-UI-ANCHOR-ACTION-RESULT
角色/剧情 -> XPC-CHARACTER-GOAL-REACTION
科普/机制 -> XPC-EXPLAIN-OVERVIEW-MECHANISM-RETURN
字体/抽象 -> XPC-TYPE-SHAPE-SEMANTIC-HIT
三维/混合 -> XPC-3D-HERO-MATERIAL-HANDOFF
活动/片头 -> XPC-TITLE-HOOK-MOTIF-LOCKUP
```

每段写 `pattern_fit` 和至少一个 `rejected_antipattern`。只抽取状态顺序和设计责任，不复制代表作品的品牌、主体、构图或文字。

蒸馏节奏预算：每 15 秒镜头代理 P25/P50/P75 为 4.2/4.7/5.9。12–15 秒默认 3–5 镜、5–9 个微时间拍；4–7 秒默认 1–2 镜、3–5 个微时间拍。高密度信息减少镜头、增加稳定微拍；运行时不回查这些统计来自哪条片。

## 6. 编排逐镜与微时间拍

使用 [h3-mg-plan.schema.json](schemas/h3-mg-plan.schema.json) 的 `h3-mg-plan.v7` 作为真源合同。每段先写 `micro_motion_plan` 与 `attention_reading_plan`，再让每镜覆盖：

```text
purpose + cut_reason + start/end
composition + five layers
primary_action + cause_chain + camera
micro_beats + text_events + audio_events
entry_state + delta + exit_state + handoff
```

五层固定为：

```text
background | structure | subject | information | transition_fx
```

每个微时间拍只允许一个主动作：

```text
owner + verb/property + from_state + to_state + purpose
-> cause
-> delayed secondary response
-> brake/settle
```

微时间拍不是动作清单计数器。多条方法与微运动规则可以共同约束同一个主变化；不得把 `MM01–MM12` 逐条变成十二个连续特效。主动作停稳后才开始计算文字和结果的阅读停留。

每镜时间连续覆盖段落，每镜内部微拍连续覆盖该镜；不得有间隙、重叠、零时长或越界。第一镜从 0 开始，最后一镜恰好落在段时长。

### 构图

- 写清景别、角度、主体坐标、前中后景、第一/二/三阅读顺序和安全区。
- 信息密度高时相机固定；只有视点变化增加信息时才切镜。
- 相机写 `type + target + start/end composition + purpose`；图形缩放不冒充相机运动。

### 元素生命周期

每个可见实体写：

```text
create_at -> activate -> transform -> retire -> continuity
```

主体进入前先登记，退出时明确保留、退场或交给下一段。线条不能先于节点出现，反馈不能先于原因发生。

### 文字与数据

- 所有可见文字逐字冻结，并写 `enter/hold/exit/binding`。
- 数据同时写单位、比较基线、时间尺度和结论。
- 不让 H3 生成大段小字号正文；真实 UI/文件优先作为参考媒体。
- 画面文字承担章节、证据、数据或界面职责，不重复旁白全文。

### 声音

- 环境、物理动作声、对白/旁白、角色可听音乐、观众音乐分层记录。
- 没有听过源音轨时标 `unverified`，不伪造同步证据。
- 只有用户明确要求 H3 生成对白/旁白时才写 `<d>[Language] exact text</d>`。

需要动效和转场路由时读 [motion-transitions.md](references/motion-transitions.md)。涉及实拍、档案或真实 UI 时读 [live-action-mg-handoff.md](references/live-action-mg-handoff.md)。

## 7. 路由 H3 模式

按 [minimax-h3-contract.md](references/minimax-h3-contract.md) 执行：

```text
text only -> T2VA
first frame -> I2VA
last frame -> L2VA
first + last frames -> FL2VA
general image/video/audio references -> Ref2VA
```

首尾帧角色与 reference 角色互斥。参考音频不能作为唯一媒体输入。每个素材都写 role、provenance、authority、used_by_shots 和 locked_attributes。

## 8. 编译 H3 原生 Prompt

使用 [h3-execution-prompt.md](templates/h3-execution-prompt.md)。先保留完整导演版，再压缩为 H3 英文 Prompt：

### T2VA / I2VA / L2VA / FL2VA

```text
integrated_multimodal_description:
overall_soundscape:
non_diegetic_music:
```

`[Shot 1]` 不写时间；后续镜头用与 JSON 一致的 `At 00:SS.mmm`。保留对象身份、开场状态、动作顺序、可见文字、声音、切点和稳定落点。

### Ref2VA

```text
subject_definitions:
summary:
retention_analysis:
detailed_description:
overall_soundscape:
non_diegetic_music:
```

不要只写“参考风格”。逐项声明素材控制的主体、属性、镜头、时间段和保留方式。

每段同时生成：

- `/v2/h3_context_ir` 预处理请求体：text 是完整导演 brief，不含 resolution。
- `/v2/video_generation` 直接生成请求体：text 与 `h3_native_prompt` 完全一致，含 resolution。

## 9. 质量判定

必须打开 [h3-mg-quality-gate.md](references/h3-mg-quality-gate.md)。按八维 100 分评分：

```text
20 semantic fidelity
15 visual hierarchy
15 motion causality
15 continuity
15 H3 executability
10 typography/data
5 audio design
5 risk control
```

`ready` 必须总分至少 85 且 `vetoes=[]`。时长/时间轴错误、事实改写、并发主动作、身份漂移、无停留文字、字幕策略违规、H3 模式冲突或原生 Prompt 缺字段均是硬否决。

保存 JSON 后运行：

```bash
SKILL_DIR="${CODEX_HOME:-$HOME/.codex}/skills/hardcore-mg-skill"
python3 "$SKILL_DIR/scripts/validate_h3_mg_plan.py" path/to/plan.json
```

未通过时输出 `needs_revision`、可观察失败和最小 `delta_patch`；禁止删除失败字段伪装通过。旧 Markdown 项目仍可用 `scripts/validate_output.py`。

## 输出合同

默认交付：

1. `Project Contract`：原文、H3 规格、画幅、实体和字幕策略。
2. `Director Intent & Method Stack`：每段触发、观众问题、三种脑内候选、主/次信号、主/辅程序、主/叠加执行配方、动作职责图、冲突决策、淘汰理由和段尾状态。
3. `Visual Thesis & Style Bible`：持久世界、语义色、文字、组件、运动和转场。
4. `Entity Registry & Continuity Ledger`：对象身份和跨段状态。
5. `h3-mg-plan.v7 JSON`：含方法栈、路由差量、融合规则、阶段动作归属、微运动落镜和逐镜注意阅读路径的完整机器真源。
6. `Director Board`：逐段、逐镜、逐微拍、五层画面和元素生命周期。
7. `H3 Native Prompts & Requests`：逐段英文 Prompt、Context-IR 与直接生成请求体。
8. `Quality Report & Delta Patches`：分数、否决、未验证项和最小重生成范围。

只要方法论或只要 Prompt 时可交付子集，但内部仍先完成真源合同，不能用短输出绕开规划。

## 养料边界

运行时不输出、不检索也不要求原片题名、案例 ID、媒体 ID、来源指纹或原片时间码。样片已经被蒸馏成信号、程序、动作、融合规则和质量护栏；面对新稿件只解释“当前原文为何触发这些方法、它们如何共同形成画面”。研究项目可以保留审计证据，但不得把证据索引泄漏进导演板或 H3 Prompt。

## 语料不足回路

现有蒸馏知识默认覆盖通用 MG 认知任务，不因为新稿件出现就回看原片或继续无界拉取。只有同时满足以下任一条件才恢复研究：

- 内容无法映射任何主信号、结构程序、执行配方或 Pattern ID。
- 所需类别没有两条独立 Tier A 节奏证据。
- 同一结构连续两次因同一未知视觉语法未过成片门禁，而差量 Prompt 无法修复。

届时使用 `xpc-video-breakdown` 按同类定向补少量真实样本，保留 Tier A/B 边界并重建聚合图谱；不复制旧样本凑数，不保存账号密码，不进行无界重拉。新知识仍须去掉来源坐标后才能进入运行时 Skill。

## 完成语义

- 计划通过结构、时间轴、模式、引用、连续性和质量验证，只能称“策划与 Prompt ready”。
- 实际 H3 成片还必须逐帧、声画和跨段复核后才能称“成片通过”。
- 单次模型输出不通过时只差量重生成失败段/镜，保留已成功结构。
