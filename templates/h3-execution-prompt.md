# MiniMax H3 单段执行模板

先完成 `h3-mg-plan.v7` 导演卡，再把同一事实压缩进 H3 原生 Prompt。不要直接填 Prompt 跳过语义信号、方法组合、微运动、注意阅读编排、编导候选、状态、图层和生命周期。

## 导演卡

```text
Segment {{segment_id}} | {{duration_seconds}}s | {{h3_mode}}
Source span: {{exact_source_span}}
Core claim: {{one_claim}}
Director intent:
  trigger / audience question / evidence need: {{three_fields}}
  evidence-native candidate: {{picture_and_decision_reason}}
  mechanism-native candidate: {{picture_and_decision_reason}}
  domain-native candidate: {{picture_and_decision_reason}}
  selected picture / reason: {{picture_and_selection_reason}}
  rejected cliches / uncertainty: {{guardrails}}
Pattern: {{primary_pattern_id}} + {{optional_secondary_pattern_id}}
Pattern fit: {{why_this_pattern}}
Method stack:
  signals: {{one_primary_and_zero_to_four_secondary_signals_with_source_evidence}}
  programs: {{one_primary_and_zero_to_three_supporting_programs}}
  program bindings: {{activated_signals_declared_stages_actual_spine_moves_and_responsibility}}
  recipes: {{one_primary_and_zero_to_two_overlay_execution_recipes}}
  recipe bindings: {{activated_signals_declared_stages_actual_required_moves_and_responsibility}}
  fusion bindings: {{rule_signals_stages_bilateral_moves_implementation_and_combined_effect}}
  router moves / adaptations: {{deterministic_baseline_and_every_explained_add_or_remove}}
  activations: {{all_semantically_required_move_roles_triggers_contributions_and_interactions}}
  composition logic: {{how_all_methods_share_one_subject_world_and_state_chain}}
  collision resolutions: {{competing_methods_and_final_responsibility_split}}
  effect chain: {{opening_to_development_to_turn_to_payoff_to_landing}}
  stage bindings: {{five_ordered_stages_each_with_owner_program_moves_and_state_change}}
  discarded methods: {{at_least_two_specific_rejections}}
  density strategy: {{how_the_stack_fits_the_duration}}
Micro-motion plan:
  rule bindings: {{MM01_to_MM12_triggered_by_applies_to_shots_change_scope_implementation_failure_prevented}}
  coverage: {{every_shot_has_MM03_and_text_shots_have_MM09_or_MM11}}
Attention/read plan:
  shot bindings: {{each_shot_once_with_AF_rules_attention_entry_ordered_focus_path_one_information_delta_motion_budget_reading_lock_exit_focus}}
  coverage: {{text_shots_use_AF04_AF07_or_AF08_and_nonfinal_shots_use_AF10}}

Initial state signature: {{signature}}
Visible entities: {{entity_ids}}
Layout / palette / light: {{locked_state}}

Shot {{n}} | {{start}}–{{end}}
Purpose / cut reason: {{new_information_and_why_cut}}
Composition: {{shot_size_angle_positions_depth_first_second_third_read}}
Layers:
  background: {{canvas_environment_light_texture}}
  structure: {{grid_path_window_stage_or_frame}}
  subject: {{registered_entities_and_state}}
  information: {{exact_text_data_ui_or_document}}
  transition_fx: {{semantic_transition_or_empty}}
Primary action: {{owner}} {{verb}} from {{from_state}} to {{to_state}} for {{purpose}}
Cause chain: {{cause}} -> {{primary_change}} -> {{delayed_response}} -> {{settle}}
Camera: {{type_amplitude_speed_target_start_end_purpose}}
Micro beats:
  {{start}}–{{end}} {{owner}} {{change}}; secondary {{response}}; settle {{brake}}
Text events: {{exact_text_enter_hold_exit_binding_or_empty}}
Audio events: {{ambience_foley_dialogue_music_time_and_sync_status_or_empty}}
Entry / delta / exit / handoff: {{four_states}}

Element lifecycle:
  {{entity_id}} create {{time}}; activate {{event}}; transform {{path}}; retire {{event}}; continuity {{lock}}

End state signature: {{signature}}
Quality: {{dimension_scores}} = {{total}}/100; vetoes {{empty_or_list}}
```

## 基础模式原生 Prompt

T2VA 直接从三个字段开始。I2VA/L2VA/FL2VA 在第一行追加 `references/minimax-h3-contract.md` 的官方对齐句。

```text
integrated_multimodal_description: [Shot 1] {{English style, opening composition, registered subjects, layers, primary action, causal response, camera, visible text in exact double quotes, diegetic sound, and stable exit state.}} [Shot 2] At {{00:SS.mmm}}, the camera cuts to {{new information, inherited identities, next state change, synchronized sound, and landing.}}

overall_soundscape: {{1–4 English sentences for ambience, physical action sounds, and non-verbal human sound.}}

non_diegetic_music: {{1–3 English sentences for instruments, tempo, rhythm, dynamics, or N/A.}}
```

要求：

- `[Shot 1]` 无时间戳，后续镜头切点与 JSON 完全一致。
- 原生描述用英文；对白、歌词和画面文字保持用户原文。
- 每镜保留对象身份、起点、动作顺序、声音、切点和稳定落点，不把导演卡压成剧情摘要。
- 不在 Prompt 写 Pattern ID、质量分、底部字幕或旁白全文。

## Ref2VA 原生 Prompt

```text
subject_definitions:
{{stable Subject/Picture/Video/Audio labels and what each source controls}}

summary:
{{task type, target, and main reference relationships}}

retention_analysis:
{{per reference: full/partial/style/timing retention, attributes, shots, and time ranges}}

detailed_description:
[Shot 1] {{English audiovisual timeline with explicit reference use.}} [Shot 2] At {{00:SS.mmm}}, {{cut and inherited state.}}

overall_soundscape:
{{ambience and physical sound}}

non_diegetic_music:
{{audience-only music or N/A}}
```

## 请求体

```json
{
  "endpoint": "/v2/video_generation",
  "method": "POST",
  "body": {
    "model": "MiniMax-H3",
    "content": [
      {"type": "text", "text": "{{h3_native_prompt}}"}
    ],
    "resolution": "{{768P_or_2K}}",
    "duration": "{{integer_4_to_15}}",
    "ratio": "{{mode_compatible_ratio}}"
  }
}
```

引用素材按模式追加到 `content`；不保存 Authorization header。Context-IR 预处理使用同构请求体但 endpoint 为 `/v2/h3_context_ir` 且不含 `resolution`。
