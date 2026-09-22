# 单段执行 Prompt 模板

```markdown
## {{segment_id}} | {{timecode}} | {{narrative_function}}

### Technical
- duration: {{duration_seconds}}
- aspect_ratio: {{aspect_ratio}}
- resolution: {{resolution}}
- fps: {{fps}}
- media_mode: {{media_mode}}
- entity_mode: {{entity_mode}}

### Core Claim
{{core_claim}}

### Initial State
继承 {{inherited_objects}}；布局为 {{inherited_layout}}；时间坐标为 {{inherited_time}}。

### Timeline
- {{beat_1_range}}：{{beat_1_visual_state_and_action}}
- {{beat_2_range}}：{{beat_2_visual_state_and_action}}
- {{beat_3_range}}：{{beat_3_visual_state_and_action}}
- {{hold_range}}：保持 {{readable_hold_state}}，不增加新焦点。

### Composition & Components
{{composition}}
{{component_geometry}}
主焦点：{{primary_focus}}。次焦点：{{secondary_focus}}。

### Live / Archive / UI Treatment
{{source_asset_usage}}
真实素材负责：{{live_or_source_responsibility}}。
MG 负责：{{mg_responsibility}}。
接力锚：{{handoff_anchor}}。

### Typography & Data
- chapter_title: {{chapter_title_or_none}}
- semantic_stamp: {{semantic_stamp_or_none}}
- evidence_labels: {{evidence_labels}}
- data: {{data_with_unit_baseline_time}}
- ui_or_document: {{preserved_source_text}}
- subtitle_mode: disabled
- bottom_caption: forbidden
- voiceover_transcript: forbidden

### Color & Material
{{semantic_color_usage}}
{{material_usage}}

### Motion
唯一主动作：{{primary_action}}。
辅助状态：{{secondary_state_change}}。
{{verified_sound_sync_or_unverified}}

### End State
保留 {{visible_objects}}；布局为 {{end_layout}}；时间坐标为 {{end_time}}；未完成运动为 none。
下一段从 {{next_segment_interface}} 开始。

### Risk Controls
- {{risk_1}}
- {{risk_2}}
- {{risk_3}}
```

压缩执行版时，保留技术规格、核心判断、状态、坐标、动作顺序、时间拍、文字内容、单位和段尾接口。删除重复形容词、无语义氛围和长黑名单。
