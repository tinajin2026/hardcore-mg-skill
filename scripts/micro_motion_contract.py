#!/usr/bin/env python3
"""
[INPUT]: 接收 h3-mg-plan.v7 单段的 micro_motion_plan、已校验镜头列表与上层错误回调。
[OUTPUT]: 校验 MM01-MM12 规则落镜、变化范围、动作包络、文字停留与逐镜完整覆盖。
[POS]: scripts 的微运动执行合同，把高时间分辨率研究规则绑定到真实镜头而非停留在方法名列表。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from typing import Any, Callable


ErrorCallback = Callable[[str, str], None]
RULE_IDS = {f"MM{index:02d}" for index in range(1, 13)}
SCOPES = {"local", "regional", "full_frame"}
REQUIRED_FIELDS = {
    "rule_id",
    "triggered_by",
    "applies_to_shots",
    "change_scope",
    "implementation",
    "failure_prevented",
}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_text_list(value: Any, error: ErrorCallback, path: str) -> list[str]:
    if not isinstance(value, list) or not value:
        error(path, "must be a non-empty array")
        return []
    checked: list[str] = []
    for index, item in enumerate(value):
        if not nonempty_text(item):
            error(f"{path}[{index}]", "must be a non-empty string")
        else:
            checked.append(item)
    if len(checked) != len(set(checked)):
        error(path, "must not contain duplicates")
    return checked


def validate_micro_motion_plan(
    value: Any,
    shots: list[dict[str, Any]],
    error: ErrorCallback,
    path: str,
) -> None:
    if not isinstance(value, dict):
        error(path, "must be an object")
        return
    if set(value) != {"rule_bindings"}:
        missing = {"rule_bindings"} - set(value)
        extra = set(value) - {"rule_bindings"}
        if missing:
            error(path, f"missing keys {sorted(missing)}")
        if extra:
            error(path, f"unexpected keys {sorted(extra)}")
    bindings = value.get("rule_bindings")
    if not isinstance(bindings, list) or not bindings:
        error(f"{path}.rule_bindings", "must be a non-empty array")
        return

    known_shots = {shot.get("shot_id") for shot in shots if nonempty_text(shot.get("shot_id"))}
    rules_by_shot: dict[str, set[str]] = {shot_id: set() for shot_id in known_shots}
    seen_bindings: set[tuple[str, tuple[str, ...]]] = set()
    for index, item in enumerate(bindings):
        item_path = f"{path}.rule_bindings[{index}]"
        if not isinstance(item, dict):
            error(item_path, "must be an object")
            continue
        if set(item) != REQUIRED_FIELDS:
            missing = REQUIRED_FIELDS - set(item)
            extra = set(item) - REQUIRED_FIELDS
            if missing:
                error(item_path, f"missing keys {sorted(missing)}")
            if extra:
                error(item_path, f"unexpected keys {sorted(extra)}")
        rule_id = item.get("rule_id")
        if rule_id not in RULE_IDS:
            error(f"{item_path}.rule_id", "must equal MM01-MM12")
        triggered_by = validate_text_list(item.get("triggered_by"), error, f"{item_path}.triggered_by")
        shot_ids = validate_text_list(item.get("applies_to_shots"), error, f"{item_path}.applies_to_shots")
        scope = item.get("change_scope")
        if scope not in SCOPES:
            error(f"{item_path}.change_scope", "must be local, regional, or full_frame")
        for field in ("implementation", "failure_prevented"):
            if not nonempty_text(item.get(field)):
                error(f"{item_path}.{field}", "must be a non-empty string")
        if not triggered_by:
            continue
        signature = (str(rule_id), tuple(shot_ids))
        if signature in seen_bindings:
            error(item_path, "duplicates a rule and shot binding")
        seen_bindings.add(signature)
        for shot_id in shot_ids:
            if shot_id not in known_shots:
                error(f"{item_path}.applies_to_shots", f"unknown shot {shot_id!r}")
            else:
                rules_by_shot[shot_id].add(str(rule_id))
        if rule_id == "MM04" and scope != "full_frame":
            error(f"{item_path}.change_scope", "MM04 chapter reset must use full_frame scope")
        if rule_id in {"MM10", "MM12"} and scope == "full_frame":
            error(f"{item_path}.change_scope", f"{rule_id} must preserve context with local or regional scope")

    for shot in shots:
        shot_id = shot.get("shot_id")
        rules = rules_by_shot.get(str(shot_id), set())
        if not rules:
            error(path, f"{shot_id} is not covered by any micro-motion rule")
            continue
        if "MM03" not in rules:
            error(path, f"{shot_id} lacks MM03 action envelope coverage")
        if shot.get("text_events") and not rules.intersection({"MM09", "MM11"}):
            error(path, f"{shot_id} has text events but lacks MM09 or MM11 reading coverage")
