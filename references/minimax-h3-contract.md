# MiniMax H3 执行合同

## 目录

1. 已核验事实
2. 模式路由
3. 输入媒体边界
4. H3 原生 Prompt
5. MG 适配规则
6. API 请求体
7. 版本复核

## 已核验事实

核验日期：2026-08-24。只把以下 MiniMax 一手来源当作接口事实：

- [Create H3-Context-IR Task](https://platform.minimax.io/docs/api-reference/video-generation-v2-h3-context-ir)
- [Create Video Generation Task](https://platform.minimax.io/docs/api-reference/video-generation-v2-create)
- [MiniMax H3 official release](https://www.minimax.io/news/minimax-h3-open-source)
- [Official base-mode Prompt Writing Guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md)
- [Official reference-mode Prompt Writing Guide](https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_ref_en.md)

当前合同：

| 字段 | 约束 |
|---|---|
| model | `MiniMax-H3` |
| duration | 4–15 秒整数 |
| output fps | 24 FPS |
| resolution | `768P` 或 `2K` |
| ratio | `21:9` `16:9` `4:3` `1:1` `3:4` `9:16`；部分模式可 `adaptive` |
| output audio | 32 kHz stereo |
| Context-IR endpoint | `POST /v2/h3_context_ir`，只返回增强 Prompt，不生成视频 |
| generation endpoint | `POST /v2/video_generation` |

不要在 Skill 内写入 API Key。只有用户明确要求并授权实际生成时，才从进程环境读取凭证；策划任务只输出请求体。

## 模式路由

素材的**角色**决定模式，附件数量本身不决定模式。

| Mode | 输入 | ratio |
|---|---|---|
| `T2VA` | 只有 text | 必须显式非 `adaptive` |
| `I2VA` | text + 1 张 `first_frame` | `adaptive`，由图片决定 |
| `L2VA` | text + 1 张 `last_frame` | `adaptive`，由图片决定 |
| `FL2VA` | text + `first_frame` + `last_frame` | `adaptive`，由图片决定 |
| `Ref2VA` | text + 任意组合的 `reference_image/video/audio` | 可显式或 `adaptive` |

硬规则：

1. `first_frame`/`last_frame` 与 `reference_image/video/audio` 互斥。
2. 同一图片若控制 0 秒具体构图，使用 `first_frame`，不能仅因它也是“参考”就选 Ref2VA。
3. 风格板、角色定妆、动作视频、节奏音频属于 Ref2VA，不把它们伪装成首帧。
4. 同时需要首尾帧和全参考素材时，不发明混合语法；拆为两阶段生成或先让用户选择主控制面。
5. 每个请求必须有一个非空 text 项。

## 输入媒体边界

### 图片

- JPG/JPEG/PNG/WEBP/HEIC/HEIF。
- 单文件不超过 30 MB。
- 宽高均在 256–5760 px。
- 宽高比在 0.4–2.5。
- `first_frame` 最多 1、`last_frame` 最多 1、reference images 最多 9。

### 视频

- 仅 Ref2VA；MP4/MOV，H.264/H.265，音频 AAC/MP3。
- 最多 3 条；每条 2–15 秒，总时长不超过 15 秒。
- 单文件不超过 50 MB，帧率 23.976–60 FPS，宽高与比例同图片范围。

### 音频

- 仅 Ref2VA；WAV/MP3。
- 最多 3 条；每条 2–15 秒，总时长不超过 15 秒；单文件不超过 15 MB。
- 音频不能作为唯一媒体输入，必须同时存在 reference image 或 reference video。

### 请求总量

- 全部文件合计最多 12 个。
- 请求体不超过 64 MB；大文件使用可访问 URL，不把大段 Base64 塞进策划产物。
- 只有实际检查过的媒体才能写 `image_observed/video_observed/audio_observed`；文件名或上游描述只能写 `upstream_claim`。

## H3 原生 Prompt

原生描述统一使用英文。用户锁定的对白、歌词和画面文字保留原语言、大小写、标点和顺序，不翻译、不改写。

### T2VA / I2VA / L2VA / FL2VA

三个核心字段固定按顺序出现：

```text
integrated_multimodal_description: [Shot 1] ...
overall_soundscape: ...
non_diegetic_music: ...
```

- `[Shot 1]` 不写切点时间。
- `[Shot 2]` 起使用严格递增的 `At 00:03.500, the camera cuts to ...`。
- 切镜必须增加主体、空间、状态、视点或时间信息；只改变轻微景别时优先运镜。
- 运镜写成 `type + meaningful amplitude + meaningful speed + target + purpose` 的自然句，不堆标签。
- `overall_soundscape` 只汇总环境声、物理动作声和非语言人声；不重复对白和音乐。
- `non_diegetic_music` 只写观众听见、角色听不见的音乐；没有时写 `N/A`。

首尾帧模式在 Prompt 第一行增加官方对齐句：

```text
I2VA: For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
FL2VA: How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.
L2VA: How the reference pictures align with the target video — <Picture 1> (from [Shot N]) aligns with the S.SS-second mark of the target video.
```

`S.SS` 必须等于有效时长并保留两位小数。FL2VA 优先单镜连续插值；只有用户明确要求多镜才切镜。

### Ref2VA

六段固定按顺序出现：

```text
subject_definitions:
summary:
retention_analysis:
detailed_description:
overall_soundscape:
non_diegetic_music:
```

- `<Subject N>` 表示真正复用的可见内容；一主体可来自多个素材，一素材可定义多个主体。
- `<Picture N>` 只在图片本身作为关键帧、构图锚或分镜参考时独立登记。
- `<Video N>` 表示源视频、延续起点、运镜/剪辑/节奏等整段关系；从视频抽取的人物或物体仍登记为 Subject。
- `<Audio N>` 表示复制/引用的音频信号、声线、节奏或音乐；明确 `fully_copy | partially_copy | style_reference | timing_reference`。
- `retention_analysis` 逐项声明哪些镜头、属性和时间段保留，不能只写“参考整体风格”。

## MG 适配规则

H3 的 Prompt 是生成器语言，不能代替导演卡。先在 JSON 中完整设计，再压缩为原生 Prompt：

```text
source span
-> core claim
-> XPC pattern
-> initial state
-> shot timeline
-> layer ownership
-> element lifecycle
-> audio/continuity
-> stable landing
-> H3 native prompt
```

### 图层

每镜固定检查五层：

1. `background`：画布、环境、光源、纹理和安全区。
2. `structure`：网格、路径、窗口、坐标、舞台或档案框架。
3. `subject`：产品、角色、文档、图表或英雄对象。
4. `information`：章节、标签、数据、真实 UI、可见文字。
5. `transition_fx`：只服务于语义接力的遮罩、匹配形态、清场或光场。

空层使用空数组，不用“若干科技元素”占位。

### 动作

每个微时间拍只允许一个 `primary_action`。完整动作写明：

```text
owner + property/verb + from_state + to_state + start/end
-> physical_or_graphic_cause
-> delayed_secondary_response
-> brake_or_settle
```

“丝滑、高级、震撼、酷炫”不是动作。缓动可写为导演建议，但只有渲染/时间线验证后才能声明已实现。

### 文字

- H3 Prompt 中实际可见文字用英文双引号包裹，原文不改。
- 文字事件必须有 `enter/hold/exit`；数据同时记录单位、基线和时间尺度。
- 不让 H3 在一个 15 秒段里生成大段小字号正文。真实 UI 或文件优先作为参考图/视频输入。
- 默认 `subtitle_mode=disabled`、`bottom_caption=forbidden`、`voiceover_transcript=forbidden`。

### 声音

- 旁白不自动塞进生成 Prompt；只有用户明确要 H3 直接生成对白/旁白时，才用 `<d>[Language] exact text</d>`。
- 画外音后明确相应屏幕角色嘴唇闭合。
- 音效跟随可观察的物理/图形事件；非叙事 UI 不要每个元素都发声。
- 音乐写乐器、速度、节奏和动态，不写抽象“高级感”。

## API 请求体

策划默认交付两个请求体，不发送：

### Context-IR 预处理

```json
{
  "endpoint": "/v2/h3_context_ir",
  "method": "POST",
  "body": {
    "model": "MiniMax-H3",
    "content": [{"type": "text", "text": "DIRECTOR_BRIEF"}],
    "duration": 15,
    "ratio": "16:9"
  }
}
```

### 直接生成

```json
{
  "endpoint": "/v2/video_generation",
  "method": "POST",
  "body": {
    "model": "MiniMax-H3",
    "content": [{"type": "text", "text": "H3_NATIVE_PROMPT"}],
    "resolution": "2K",
    "duration": 15,
    "ratio": "16:9"
  }
}
```

实际素材项追加到 `content`，角色使用本页模式表。不要在 JSON 中保存 Authorization header。

## 版本复核

MiniMax H3 是快速变化的外部接口。发生任一情况时必须重新打开官方文档：

- 用户要求实际调用 API。
- 当前日期晚于本页核验日 30 天。
- API 返回字段、时长、ratio、role 或分辨率错误。
- MiniMax 发布 H3 新 checkpoint、Context-IR 新格式或 Prompt Guide 新 revision。

复核后先更新本页和验证器，再生成请求；不要在单个项目里临时绕开合同。
