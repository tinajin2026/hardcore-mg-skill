#!/usr/bin/env python3
"""
[INPUT]: 读取 h3-mg-plan.v7 JSON、同 Skill 的 Schema、方法栈/微运动/注意阅读合同与 MiniMax H3/八类 MG 约束。
[OUTPUT]: 校验编导意图、方法组合、MM01-MM12 与 AF01-AF12 落镜、4–15 秒时间轴、引用模式、Prompt、连续性与质量门禁。
[POS]: documentary-mg-generator 的 H3 确定性验收器；证明策划合同完整，不冒充生成后视觉验收。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path
from typing import Any

from attention_reading_contract import validate_attention_reading_plan
from method_stack_contract import validate_method_stack
from micro_motion_contract import validate_micro_motion_plan


EPSILON = 0.001
PATTERN_IDS = {
    "XPC-DATA-BASELINE-DELTA",
    "XPC-BRAND-MOTIF-PROOF-LOCKUP",
    "XPC-UI-ANCHOR-ACTION-RESULT",
    "XPC-CHARACTER-GOAL-REACTION",
    "XPC-EXPLAIN-OVERVIEW-MECHANISM-RETURN",
    "XPC-TYPE-SHAPE-SEMANTIC-HIT",
    "XPC-3D-HERO-MATERIAL-HANDOFF",
    "XPC-TITLE-HOOK-MOTIF-LOCKUP",
}
H3_MODES = {"T2VA", "I2VA", "L2VA", "FL2VA", "Ref2VA"}
MOVE_ID = re.compile(r"^[NRWCTEKMXHLQ]0[1-8]$")
RATIOS = {"adaptive", "21:9", "16:9", "4:3", "1:1", "3:4", "9:16"}
REFERENCE_ROLES = {"reference_image", "reference_video", "reference_audio"}
FRAME_ROLES = {"first_frame", "last_frame"}
QUALITY_MAX = {
    "semantic_fidelity": 20,
    "visual_hierarchy": 15,
    "motion_causality": 15,
    "continuity": 15,
    "h3_executability": 15,
    "typography_data": 10,
    "audio_design": 5,
    "risk_control": 5,
}
PROHIBITED_POLICY = [
    re.compile(r"subtitle_mode\s*[:=]\s*(?:enabled|direct|burned_in)", re.IGNORECASE),
    re.compile(r"bottom_caption\s*[:=]\s*(?:enabled|true|required)", re.IGNORECASE),
    re.compile(r"(?:生成|添加|显示).{0,8}(?:底部字幕|旁白字幕|逐字字幕)"),
    re.compile(r"(?:add|show|generate).{0,16}(?:bottom captions?|voiceover subtitles?|burned-in subtitles?)", re.IGNORECASE),
]


class PlanValidator:
    def __init__(self, allow_needs_revision: bool = False) -> None:
        self.errors: list[str] = []
        self.allow_needs_revision = allow_needs_revision
        self.shot_count = 0
        self.beat_count = 0

    def error(self, path: str, message: str) -> None:
        self.errors.append(f"{path}: {message}")

    def require_object(self, value: Any, path: str) -> dict[str, Any]:
        if not isinstance(value, dict):
            self.error(path, "must be an object")
            return {}
        return value

    def require_list(self, value: Any, path: str, minimum: int = 0) -> list[Any]:
        if not isinstance(value, list):
            self.error(path, "must be an array")
            return []
        if len(value) < minimum:
            self.error(path, f"must contain at least {minimum} item(s)")
        return value

    def require_keys(self, value: dict[str, Any], keys: set[str], path: str) -> None:
        for key in sorted(keys):
            if key not in value:
                self.error(path, f"missing {key}")

    def require_text(self, value: Any, path: str, minimum: int = 1) -> str:
        if not isinstance(value, str) or len(value.strip()) < minimum:
            self.error(path, f"must be a non-empty string of at least {minimum} character(s)")
            return ""
        self.check_policy(value, path)
        return value

    def require_number(self, value: Any, path: str) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            self.error(path, "must be a number")
            return None
        return float(value)

    def check_policy(self, text: str, path: str) -> None:
        for pattern in PROHIBITED_POLICY:
            match = pattern.search(text)
            if match:
                self.error(path, f"prohibited subtitle policy near {match.group(0)!r}")

    def validate(self, plan: Any) -> list[str]:
        root = self.require_object(plan, "$")
        self.require_keys(
            root,
            {"schema_version", "project", "style_bible", "entity_registry", "continuity_ledger", "segments"},
            "$",
        )
        if root.get("schema_version") != "h3-mg-plan.v7":
            self.error("$.schema_version", "must equal h3-mg-plan.v7")
        project = self.validate_project(root.get("project"))
        self.validate_style(root.get("style_bible"))
        entity_ids, entity_segments = self.validate_entities(root.get("entity_registry"))
        self.validate_continuity_ledger(root.get("continuity_ledger"))
        segments = self.require_list(root.get("segments"), "$.segments", 1)
        segment_ids = {str(segment.get("segment_id")) for segment in segments if isinstance(segment, dict)}
        for entity_id, first_segment in entity_segments.items():
            if first_segment not in segment_ids:
                self.error(f"$.entity_registry[{entity_id}]", f"first_segment {first_segment!r} does not exist")
        self.validate_source_coverage(project.get("source_script", ""), segments)
        previous_end: dict[str, Any] | None = None
        for index, segment in enumerate(segments, 1):
            path = f"$.segments[{index - 1}]"
            current = self.validate_segment(segment, path, index, project, entity_ids)
            if previous_end is not None and current:
                initial_state = current.get("initial_state", {})
                if previous_end.get("signature") != initial_state.get("signature"):
                    self.error(
                        f"{path}.initial_state.signature",
                        f"must equal previous end signature {previous_end.get('signature')!r}",
                    )
                if previous_end.get("open_motion") != "none":
                    self.error(f"{path}.initial_state", "previous segment leaves unresolved motion")
            previous_end = current.get("end_state") if current else previous_end
        return self.errors

    def validate_project(self, value: Any) -> dict[str, Any]:
        path = "$.project"
        project = self.require_object(value, path)
        required = {
            "title",
            "source_script",
            "source_language",
            "target_model",
            "output_fps",
            "resolution",
            "aspect_ratio",
            "subtitle_mode",
            "bottom_caption",
            "voiceover_transcript",
        }
        self.require_keys(project, required, path)
        for key in ("title", "source_script", "source_language"):
            self.require_text(project.get(key), f"{path}.{key}")
        expected = {
            "target_model": "MiniMax-H3",
            "output_fps": 24,
            "subtitle_mode": "disabled",
            "bottom_caption": "forbidden",
            "voiceover_transcript": "forbidden",
        }
        for key, expected_value in expected.items():
            if project.get(key) != expected_value:
                self.error(f"{path}.{key}", f"must equal {expected_value!r}")
        if project.get("resolution") not in {"768P", "2K"}:
            self.error(f"{path}.resolution", "must be 768P or 2K")
        if project.get("aspect_ratio") not in RATIOS:
            self.error(f"{path}.aspect_ratio", "unsupported H3 ratio")
        return project

    def validate_style(self, value: Any) -> None:
        path = "$.style_bible"
        style = self.require_object(value, path)
        fields = {
            "visual_thesis",
            "canvas",
            "palette_semantics",
            "typography_roles",
            "component_slots",
            "motion_policy",
            "transition_policy",
        }
        self.require_keys(style, fields, path)
        for key in ("visual_thesis", "canvas", "motion_policy", "transition_policy"):
            self.require_text(style.get(key), f"{path}.{key}")
        for key in ("palette_semantics", "typography_roles", "component_slots"):
            items = self.require_list(style.get(key), f"{path}.{key}", 1)
            for index, item in enumerate(items):
                self.require_text(item, f"{path}.{key}[{index}]")

    def validate_entities(self, value: Any) -> tuple[set[str], dict[str, str]]:
        entities = self.require_list(value, "$.entity_registry", 1)
        entity_ids: set[str] = set()
        first_segments: dict[str, str] = {}
        for index, value in enumerate(entities):
            path = f"$.entity_registry[{index}]"
            entity = self.require_object(value, path)
            self.require_keys(entity, {"entity_id", "role", "source", "identity_lock", "first_segment"}, path)
            entity_id = self.require_text(entity.get("entity_id"), f"{path}.entity_id")
            if not re.fullmatch(r"E[0-9]{2,}", entity_id):
                self.error(f"{path}.entity_id", "must match E00")
            if entity_id in entity_ids:
                self.error(f"{path}.entity_id", "duplicate entity id")
            entity_ids.add(entity_id)
            for key in ("role", "identity_lock", "first_segment"):
                self.require_text(entity.get(key), f"{path}.{key}")
            if entity.get("source") not in {
                "prompt_explicit",
                "media_observed",
                "upstream_claim",
                "model_inferred",
                "default_assumption",
            }:
                self.error(f"{path}.source", "unsupported provenance")
            first_segments[entity_id] = str(entity.get("first_segment", ""))
        return entity_ids, first_segments

    def validate_continuity_ledger(self, value: Any) -> None:
        path = "$.continuity_ledger"
        ledger = self.require_object(value, path)
        fields = {"world_lock", "object_locks", "palette_lock", "type_lock", "transition_lock"}
        self.require_keys(ledger, fields, path)
        for key in ("world_lock", "type_lock", "transition_lock"):
            self.require_text(ledger.get(key), f"{path}.{key}")
        for key in ("object_locks", "palette_lock"):
            values = self.require_list(ledger.get(key), f"{path}.{key}", 1)
            for index, item in enumerate(values):
                self.require_text(item, f"{path}.{key}[{index}]")

    def validate_source_coverage(self, source_script: str, segments: list[Any]) -> None:
        cursor = 0
        span_ids: set[str] = set()
        for index, value in enumerate(segments):
            path = f"$.segments[{index}].source_span"
            segment = self.require_object(value, f"$.segments[{index}]")
            span = self.require_object(segment.get("source_span"), path)
            span_id = self.require_text(span.get("span_id"), f"{path}.span_id")
            text = self.require_text(span.get("text"), f"{path}.text")
            if span_id in span_ids:
                self.error(f"{path}.span_id", "duplicate source span id")
            span_ids.add(span_id)
            position = source_script.find(text, cursor) if text else -1
            if position < 0:
                self.error(f"{path}.text", "must occur in source_script in segment order")
                continue
            if source_script[cursor:position].strip():
                self.error(path, "leaves uncovered non-whitespace source text before this span")
            cursor = position + len(text)
        if source_script[cursor:].strip():
            self.error("$.segments", "source spans do not cover the source_script tail")

    def validate_segment(
        self,
        value: Any,
        path: str,
        index: int,
        project: dict[str, Any],
        entity_ids: set[str],
    ) -> dict[str, Any]:
        segment = self.require_object(value, path)
        required = {
            "segment_id",
            "source_span",
            "duration_seconds",
            "core_claim",
            "director_intent",
            "narrative_function",
            "density_mode",
            "selected_pattern_ids",
            "selected_moves",
            "method_stack",
            "micro_motion_plan", "attention_reading_plan",
            "h3_mode",
            "reference_bindings",
            "initial_state",
            "shots",
            "element_lifecycle",
            "end_state",
            "h3_native_prompt",
            "context_ir_request",
            "h3_request",
            "quality",
        }
        self.require_keys(segment, required, path)
        expected_id = f"S{index:02d}"
        if segment.get("segment_id") != expected_id:
            self.error(f"{path}.segment_id", f"must equal {expected_id}")
        duration = segment.get("duration_seconds")
        if isinstance(duration, bool) or not isinstance(duration, int) or not 4 <= duration <= 15:
            self.error(f"{path}.duration_seconds", "must be an integer from 4 through 15")
            duration = 0
        self.require_text(segment.get("core_claim"), f"{path}.core_claim")
        self.validate_director_intent(segment.get("director_intent"), f"{path}.director_intent")
        patterns = self.require_list(segment.get("selected_pattern_ids"), f"{path}.selected_pattern_ids", 1)
        if len(patterns) > 2:
            self.error(f"{path}.selected_pattern_ids", "must contain at most two Pattern IDs")
        for pattern in patterns:
            if pattern not in PATTERN_IDS:
                self.error(f"{path}.selected_pattern_ids", f"unknown Pattern ID {pattern!r}")
        self.validate_selected_moves(segment.get("selected_moves"), f"{path}.selected_moves")
        validate_method_stack(segment.get("method_stack"), segment.get("selected_moves"), self.error, f"{path}.method_stack")
        mode = segment.get("h3_mode")
        if mode not in H3_MODES:
            self.error(f"{path}.h3_mode", "unsupported H3 mode")
        self.validate_bindings(segment.get("reference_bindings"), f"{path}.reference_bindings", mode)
        initial_state = self.validate_state(segment.get("initial_state"), f"{path}.initial_state", entity_ids)
        end_state = self.validate_state(segment.get("end_state"), f"{path}.end_state", entity_ids)
        shots = self.validate_shots(segment.get("shots"), f"{path}.shots", duration, entity_ids)
        validate_micro_motion_plan(segment.get("micro_motion_plan"), shots, self.error, f"{path}.micro_motion_plan")
        validate_attention_reading_plan(segment.get("attention_reading_plan"), shots, self.error, f"{path}.attention_reading_plan")
        self.validate_lifecycles(segment.get("element_lifecycle"), f"{path}.element_lifecycle", duration, entity_ids)
        prompt = self.require_text(segment.get("h3_native_prompt"), f"{path}.h3_native_prompt", 80)
        self.validate_prompt(prompt, f"{path}.h3_native_prompt", mode, shots, duration)
        self.validate_api_request(
            segment.get("context_ir_request"),
            f"{path}.context_ir_request",
            "/v2/h3_context_ir",
            mode,
            duration,
            project,
            prompt,
            require_prompt_match=False,
        )
        self.validate_api_request(
            segment.get("h3_request"),
            f"{path}.h3_request",
            "/v2/video_generation",
            mode,
            duration,
            project,
            prompt,
            require_prompt_match=True,
        )
        self.validate_quality(segment.get("quality"), f"{path}.quality")
        segment["initial_state"] = initial_state
        segment["end_state"] = end_state
        return segment

    def validate_director_intent(self, value: Any, path: str) -> None:
        intent = self.require_object(value, path)
        required = {
            "trigger",
            "audience_question",
            "evidence_need",
            "candidate_images",
            "selected_picture",
            "selection_reason",
            "rejected_cliches",
            "uncertainty",
        }
        self.require_keys(intent, required, path)
        for key in (
            "trigger",
            "audience_question",
            "selected_picture",
            "selection_reason",
            "uncertainty",
        ):
            self.require_text(intent.get(key), f"{path}.{key}")
        if intent.get("evidence_need") not in {
            "existence",
            "source",
            "relation",
            "mechanism",
            "comparison",
            "mood",
        }:
            self.error(f"{path}.evidence_need", "unsupported evidence responsibility")

        candidates = self.require_list(intent.get("candidate_images"), f"{path}.candidate_images", 3)
        if len(candidates) != 3:
            self.error(f"{path}.candidate_images", "must contain exactly three director candidates")
        candidate_types: set[str] = set()
        selected_pictures: list[str] = []
        for index, value in enumerate(candidates):
            item_path = f"{path}.candidate_images[{index}]"
            candidate = self.require_object(value, item_path)
            self.require_keys(candidate, {"type", "picture", "decision", "reason"}, item_path)
            candidate_type = candidate.get("type")
            if candidate_type not in {"evidence_native", "mechanism_native", "domain_native"}:
                self.error(f"{item_path}.type", "unsupported candidate type")
            elif candidate_type in candidate_types:
                self.error(f"{item_path}.type", "duplicate candidate type")
            else:
                candidate_types.add(candidate_type)
            picture = self.require_text(candidate.get("picture"), f"{item_path}.picture")
            decision = candidate.get("decision")
            if decision not in {"selected", "rejected"}:
                self.error(f"{item_path}.decision", "must be selected or rejected")
            elif decision == "selected":
                selected_pictures.append(picture)
            self.require_text(candidate.get("reason"), f"{item_path}.reason")
        if candidate_types != {"evidence_native", "mechanism_native", "domain_native"}:
            self.error(f"{path}.candidate_images", "must cover evidence, mechanism, and domain-native candidates")
        if len(selected_pictures) != 1:
            self.error(f"{path}.candidate_images", "must select exactly one candidate")
        elif intent.get("selected_picture") != selected_pictures[0]:
            self.error(f"{path}.selected_picture", "must equal the selected candidate picture")

        cliches = self.require_list(intent.get("rejected_cliches"), f"{path}.rejected_cliches", 1)
        for index, cliche in enumerate(cliches):
            self.require_text(cliche, f"{path}.rejected_cliches[{index}]")

    def validate_selected_moves(self, value: Any, path: str) -> None:
        moves = self.require_list(value, path, 1)
        move_ids: set[str] = set()
        categories: set[str] = set()
        for index, value in enumerate(moves):
            item_path = f"{path}[{index}]"
            move = self.require_object(value, item_path)
            self.require_keys(move, {"move_id", "application"}, item_path)
            move_id = self.require_text(move.get("move_id"), f"{item_path}.move_id")
            self.require_text(move.get("application"), f"{item_path}.application")
            if not MOVE_ID.fullmatch(move_id):
                self.error(f"{item_path}.move_id", "must reference N/R/W/C/T/E/K/M/X/H/L/Q 01-08")
            if move_id in move_ids:
                self.error(f"{item_path}.move_id", "duplicate atomic move")
            move_ids.add(move_id)
            if move_id:
                categories.add(move_id[0])
        missing_mandatory = {"N", "C", "M", "L", "Q"} - categories
        if missing_mandatory:
            self.error(path, f"missing mandatory move dimensions {sorted(missing_mandatory)}")

    def validate_state(self, value: Any, path: str, entity_ids: set[str]) -> dict[str, Any]:
        state = self.require_object(value, path)
        self.require_keys(state, {"signature", "visible_entities", "layout", "palette", "open_motion"}, path)
        for key in ("signature", "layout", "palette", "open_motion"):
            self.require_text(state.get(key), f"{path}.{key}")
        visible = self.require_list(state.get("visible_entities"), f"{path}.visible_entities")
        for index, entity_id in enumerate(visible):
            if entity_id not in entity_ids:
                self.error(f"{path}.visible_entities[{index}]", f"unknown entity {entity_id!r}")
        return state

    def validate_bindings(self, value: Any, path: str, mode: Any) -> None:
        bindings = self.require_list(value, path)
        roles = []
        for index, value in enumerate(bindings):
            item_path = f"{path}[{index}]"
            binding = self.require_object(value, item_path)
            required = {"asset_id", "role", "provenance", "authority", "used_by_shots", "locked_attributes"}
            self.require_keys(binding, required, item_path)
            for key in ("asset_id", "authority"):
                self.require_text(binding.get(key), f"{item_path}.{key}")
            role = binding.get("role")
            if role not in FRAME_ROLES | REFERENCE_ROLES:
                self.error(f"{item_path}.role", "unsupported media role")
            roles.append(role)
            for key in ("used_by_shots", "locked_attributes"):
                items = self.require_list(binding.get(key), f"{item_path}.{key}", 1)
                for item_index, item in enumerate(items):
                    self.require_text(item, f"{item_path}.{key}[{item_index}]")
        self.check_mode_roles(mode, roles, path)

    def check_mode_roles(self, mode: Any, roles: list[Any], path: str) -> None:
        role_set = set(roles)
        if role_set & FRAME_ROLES and role_set & REFERENCE_ROLES:
            self.error(path, "first/last-frame and reference roles are mutually exclusive")
        expected = {
            "T2VA": set(),
            "I2VA": {"first_frame"},
            "L2VA": {"last_frame"},
            "FL2VA": {"first_frame", "last_frame"},
        }
        if mode in expected and role_set != expected[mode]:
            self.error(path, f"{mode} requires roles {sorted(expected[mode])}, got {sorted(role_set)}")
        if mode == "Ref2VA":
            if not role_set or not role_set <= REFERENCE_ROLES:
                self.error(path, "Ref2VA requires only reference_image/video/audio roles")
            if role_set == {"reference_audio"}:
                self.error(path, "reference audio cannot be the sole media input")

    def validate_shots(self, value: Any, path: str, duration: int, entity_ids: set[str]) -> list[dict[str, Any]]:
        shots = self.require_list(value, path, 1)
        previous_end = 0.0
        total_beats = 0
        checked: list[dict[str, Any]] = []
        for index, value in enumerate(shots, 1):
            item_path = f"{path}[{index - 1}]"
            shot = self.require_object(value, item_path)
            required = {
                "shot_id",
                "start",
                "end",
                "purpose",
                "cut_reason",
                "composition",
                "layers",
                "primary_action",
                "cause_chain",
                "camera",
                "micro_beats",
                "text_events",
                "audio_events",
                "entry_state",
                "delta",
                "exit_state",
                "handoff",
            }
            self.require_keys(shot, required, item_path)
            if shot.get("shot_id") != f"Shot {index}":
                self.error(f"{item_path}.shot_id", f"must equal Shot {index}")
            start = self.require_number(shot.get("start"), f"{item_path}.start")
            end = self.require_number(shot.get("end"), f"{item_path}.end")
            if start is None or end is None:
                continue
            if abs(start - previous_end) > EPSILON:
                self.error(f"{item_path}.start", f"must continuously follow {previous_end:.3f}")
            if end <= start:
                self.error(f"{item_path}.end", "must be greater than start")
            if end > duration + EPSILON:
                self.error(f"{item_path}.end", "exceeds segment duration")
            for key in ("purpose", "cut_reason", "composition", "entry_state", "delta", "exit_state", "handoff"):
                self.require_text(shot.get(key), f"{item_path}.{key}")
            self.validate_layers(shot.get("layers"), f"{item_path}.layers")
            self.validate_action(shot.get("primary_action"), f"{item_path}.primary_action", entity_ids)
            chain = self.require_list(shot.get("cause_chain"), f"{item_path}.cause_chain", 2)
            for chain_index, step in enumerate(chain):
                self.require_text(step, f"{item_path}.cause_chain[{chain_index}]")
            self.validate_camera(shot.get("camera"), f"{item_path}.camera")
            beats = self.validate_timed_events(
                shot.get("micro_beats"), f"{item_path}.micro_beats", start, end, "micro"
            )
            total_beats += len(beats)
            self.validate_timed_events(shot.get("text_events"), f"{item_path}.text_events", start, end, "text")
            self.validate_timed_events(shot.get("audio_events"), f"{item_path}.audio_events", start, end, "audio")
            previous_end = end
            checked.append(shot)
        if duration and abs(previous_end - duration) > EPSILON:
            self.error(path, f"shots must end at segment duration {duration}, got {previous_end:.3f}")
        minimum_beats = max(3, math.ceil(duration / 3)) if duration else 3
        if total_beats < minimum_beats:
            self.error(path, f"needs at least {minimum_beats} micro beats for {duration}s, got {total_beats}")
        self.shot_count += len(checked)
        self.beat_count += total_beats
        return checked

    def validate_layers(self, value: Any, path: str) -> None:
        layers = self.require_object(value, path)
        keys = {"background", "structure", "subject", "information", "transition_fx"}
        self.require_keys(layers, keys, path)
        for key in keys:
            items = self.require_list(layers.get(key), f"{path}.{key}", 1 if key == "subject" else 0)
            for index, item in enumerate(items):
                self.require_text(item, f"{path}.{key}[{index}]")

    def validate_action(self, value: Any, path: str, entity_ids: set[str]) -> None:
        action = self.require_object(value, path)
        keys = {"owner", "verb", "from_state", "to_state", "purpose", "settle"}
        self.require_keys(action, keys, path)
        for key in keys:
            self.require_text(action.get(key), f"{path}.{key}")
        if action.get("owner") not in entity_ids:
            self.error(f"{path}.owner", f"unknown entity {action.get('owner')!r}")

    def validate_camera(self, value: Any, path: str) -> None:
        camera = self.require_object(value, path)
        keys = {"type", "target", "purpose", "start_frame", "end_frame"}
        self.require_keys(camera, keys, path)
        for key in keys:
            self.require_text(camera.get(key), f"{path}.{key}")

    def validate_timed_events(
        self,
        value: Any,
        path: str,
        shot_start: float,
        shot_end: float,
        event_type: str,
    ) -> list[dict[str, Any]]:
        events = self.require_list(value, path, 1 if event_type == "micro" else 0)
        checked = []
        previous_end = shot_start
        for index, value in enumerate(events):
            item_path = f"{path}[{index}]"
            event = self.require_object(value, item_path)
            start = self.require_number(event.get("start"), f"{item_path}.start")
            end = self.require_number(event.get("end"), f"{item_path}.end")
            if start is None or end is None:
                continue
            if start < shot_start - EPSILON or end > shot_end + EPSILON or end <= start:
                self.error(item_path, "event must be a positive interval inside its shot")
            if event_type == "micro":
                required = {"owner", "change", "secondary_response", "settle"}
                self.require_keys(event, required | {"start", "end"}, item_path)
                if abs(start - previous_end) > EPSILON:
                    self.error(f"{item_path}.start", f"micro beats must continuously follow {previous_end:.3f}")
                for key in required:
                    self.require_text(event.get(key), f"{item_path}.{key}")
                previous_end = end
            elif event_type == "text":
                required = {"exact_text", "role", "enter", "hold", "exit", "binding"}
                self.require_keys(event, required | {"start", "end"}, item_path)
                for key in ("exact_text", "enter", "hold", "exit", "binding"):
                    self.require_text(event.get(key), f"{item_path}.{key}")
            else:
                required = {"layer", "event", "sync_status"}
                self.require_keys(event, required | {"start", "end"}, item_path)
                self.require_text(event.get("event"), f"{item_path}.event")
            checked.append(event)
        if event_type == "micro" and abs(previous_end - shot_end) > EPSILON:
            self.error(path, f"micro beats must end at shot end {shot_end:.3f}, got {previous_end:.3f}")
        return checked

    def validate_lifecycles(self, value: Any, path: str, duration: int, entity_ids: set[str]) -> None:
        lifecycles = self.require_list(value, path, 1)
        seen: set[str] = set()
        for index, value in enumerate(lifecycles):
            item_path = f"{path}[{index}]"
            item = self.require_object(value, item_path)
            keys = {"entity_id", "create_at", "activate", "transform", "retire", "continuity"}
            self.require_keys(item, keys, item_path)
            entity_id = item.get("entity_id")
            if entity_id not in entity_ids:
                self.error(f"{item_path}.entity_id", f"unknown entity {entity_id!r}")
            if entity_id in seen:
                self.error(f"{item_path}.entity_id", "duplicate lifecycle in segment")
            seen.add(entity_id)
            create_at = self.require_number(item.get("create_at"), f"{item_path}.create_at")
            if create_at is not None and not 0 <= create_at <= duration:
                self.error(f"{item_path}.create_at", "must lie inside the segment")
            for key in ("activate", "transform", "retire", "continuity"):
                self.require_text(item.get(key), f"{item_path}.{key}")

    def validate_prompt(
        self,
        prompt: str,
        path: str,
        mode: Any,
        shots: list[dict[str, Any]],
        duration: int,
    ) -> None:
        if mode == "Ref2VA":
            fields = [
                "subject_definitions:",
                "summary:",
                "retention_analysis:",
                "detailed_description:",
                "overall_soundscape:",
                "non_diegetic_music:",
            ]
            positions = [prompt.find(field) for field in fields]
            if -1 in positions or positions != sorted(positions):
                self.error(path, "Ref2VA prompt must contain the six official fields in order")
        else:
            fields = ["integrated_multimodal_description:", "overall_soundscape:", "non_diegetic_music:"]
            positions = [prompt.find(field) for field in fields]
            if -1 in positions or positions != sorted(positions):
                self.error(path, "base-mode prompt must contain the three official fields in order")
        for index, shot in enumerate(shots, 1):
            token = f"[Shot {index}]"
            position = prompt.find(token)
            if position < 0:
                self.error(path, f"missing {token}")
            if index > 1:
                timestamp = format_timestamp(float(shot.get("start", 0)))
                local = prompt[position : position + 100] if position >= 0 else ""
                if f"At {timestamp}" not in local:
                    self.error(path, f"{token} must declare cut time At {timestamp}")
        if mode == "I2VA" and not prompt.startswith("For the target video, at 0.00 seconds"):
            self.error(path, "I2VA prompt must begin with the official first-frame alignment")
        if mode == "FL2VA":
            expected = f"{duration:.2f}-second mark"
            if not prompt.startswith("How the reference pictures align") or expected not in prompt[:500]:
                self.error(path, f"FL2VA prompt must align the last frame to the {expected}")
        if mode == "L2VA":
            expected = f"{duration:.2f}-second mark"
            if not prompt.startswith("How the reference pictures align") or expected not in prompt[:500]:
                self.error(path, f"L2VA prompt must align the last frame to the {expected}")

    def validate_api_request(
        self,
        value: Any,
        path: str,
        endpoint: str,
        mode: Any,
        duration: int,
        project: dict[str, Any],
        prompt: str,
        require_prompt_match: bool,
    ) -> None:
        request = self.require_object(value, path)
        self.require_keys(request, {"endpoint", "method", "body"}, path)
        if request.get("endpoint") != endpoint:
            self.error(f"{path}.endpoint", f"must equal {endpoint}")
        if request.get("method") != "POST":
            self.error(f"{path}.method", "must equal POST")
        body = self.require_object(request.get("body"), f"{path}.body")
        required = {"model", "content", "duration", "ratio"}
        if endpoint == "/v2/video_generation":
            required.add("resolution")
        self.require_keys(body, required, f"{path}.body")
        if body.get("model") != "MiniMax-H3":
            self.error(f"{path}.body.model", "must equal MiniMax-H3")
        if body.get("duration") != duration:
            self.error(f"{path}.body.duration", "must equal segment duration")
        if endpoint == "/v2/video_generation" and body.get("resolution") != project.get("resolution"):
            self.error(f"{path}.body.resolution", "must equal project resolution")
        ratio = body.get("ratio")
        if ratio not in RATIOS:
            self.error(f"{path}.body.ratio", "unsupported ratio")
        if mode == "T2VA" and ratio == "adaptive":
            self.error(f"{path}.body.ratio", "T2VA cannot use adaptive")
        if mode in {"I2VA", "L2VA", "FL2VA"} and ratio != "adaptive":
            self.error(f"{path}.body.ratio", f"{mode} must use adaptive")
        content = self.require_list(body.get("content"), f"{path}.body.content", 1)
        text_items = []
        roles = []
        for index, item_value in enumerate(content):
            item_path = f"{path}.body.content[{index}]"
            item = self.require_object(item_value, item_path)
            item_type = item.get("type")
            if item_type == "text":
                text_items.append(self.require_text(item.get("text"), f"{item_path}.text"))
            elif item_type in {"image_url", "video_url", "audio_url"}:
                self.require_text(item.get(item_type), f"{item_path}.{item_type}")
                roles.append(item.get("role"))
            else:
                self.error(f"{item_path}.type", "unsupported content type")
        if len(text_items) != 1:
            self.error(f"{path}.body.content", "must contain exactly one text item")
        if require_prompt_match and text_items and text_items[0] != prompt:
            self.error(f"{path}.body.content", "generation text must exactly equal h3_native_prompt")
        self.check_mode_roles(mode, roles, f"{path}.body.content")

    def validate_quality(self, value: Any, path: str) -> None:
        quality = self.require_object(value, path)
        required = {"dimensions", "total", "status", "vetoes", "pattern_fit", "rejected_antipatterns", "delta_patch"}
        self.require_keys(quality, required, path)
        dimensions = self.require_object(quality.get("dimensions"), f"{path}.dimensions")
        self.require_keys(dimensions, set(QUALITY_MAX), f"{path}.dimensions")
        computed = 0
        for name, maximum in QUALITY_MAX.items():
            score = dimensions.get(name)
            if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= maximum:
                self.error(f"{path}.dimensions.{name}", f"must be an integer from 0 through {maximum}")
            else:
                computed += score
        if quality.get("total") != computed:
            self.error(f"{path}.total", f"must equal dimension sum {computed}")
        vetoes = self.require_list(quality.get("vetoes"), f"{path}.vetoes")
        status = quality.get("status")
        if status == "ready":
            if computed < 85:
                self.error(path, "ready requires total >= 85")
            if vetoes:
                self.error(path, "ready requires an empty vetoes list")
        elif status == "needs_revision":
            patches = self.require_list(quality.get("delta_patch"), f"{path}.delta_patch", 1)
            if not self.allow_needs_revision:
                self.error(path, "needs_revision is not accepted without --allow-needs-revision")
            for index, patch in enumerate(patches):
                self.require_text(patch, f"{path}.delta_patch[{index}]")
        else:
            self.error(f"{path}.status", "must be ready or needs_revision")
        self.require_text(quality.get("pattern_fit"), f"{path}.pattern_fit")
        rejected = self.require_list(quality.get("rejected_antipatterns"), f"{path}.rejected_antipatterns", 1)
        for index, item in enumerate(rejected):
            self.require_text(item, f"{path}.rejected_antipatterns[{index}]")


def format_timestamp(seconds: float) -> str:
    milliseconds = int(round(seconds * 1000))
    minutes, remainder = divmod(milliseconds, 60_000)
    whole_seconds, millis = divmod(remainder, 1000)
    return f"{minutes:02d}:{whole_seconds:02d}.{millis:03d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a MiniMax H3 MG director plan")
    parser.add_argument("plan", type=Path)
    parser.add_argument("--allow-needs-revision", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    schema_path = Path(__file__).resolve().parent.parent / "schemas" / "h3-mg-plan.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    if schema.get("$id") != "https://local.codex/skills/documentary-mg-generator/h3-mg-plan.schema.json":
        raise SystemExit("FAIL: H3 MG schema is missing or has an unexpected $id")
    validator = PlanValidator(allow_needs_revision=args.allow_needs_revision)
    errors = validator.validate(plan)
    if errors:
        raise SystemExit("FAIL:\n" + "\n".join(errors))
    print(
        f"PASS: {args.plan} segments={len(plan['segments'])} "
        f"shots={validator.shot_count} micro_beats={validator.beat_count} H3 plan is contract-ready"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
