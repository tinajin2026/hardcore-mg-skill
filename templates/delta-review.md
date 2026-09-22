# 渲染后差量复核模板

```yaml
segment_id: S01
reviewed_media: path_or_id
review_timecode: "00:00-00:15"

preserve:
  - 已成功且不得被重写的对象、布局、颜色、镜头或节奏

observed_failures:
  - time: "00:03-00:05"
    symptom: 可直接看到的失败
    root_cause: identity_lock | hierarchy | density | handoff | text | data | motion | model_artifact
    evidence: 截图、帧号或可复现描述

patch:
  - target: 对象/文字/状态/时间拍
    change: 最小修改
    preserve: 必须维持的成功部分

acceptance:
  - 修订后可观察、可反驳的条件

continuity_check:
  previous_end_matches: true_or_false
  next_initial_matches: true_or_false

text_policy:
  subtitle_mode: disabled
  bottom_caption: forbidden
  voiceover_transcript: forbidden
```

只修失败项。若根因是信息并发过多，删减或拆状态；不要用“更高级、更丝滑、更科技”掩盖。若对象漂移，补位置、尺度、朝向、光源和层状态，不要整体换 Prompt。
