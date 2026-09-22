#!/usr/bin/env python3
"""
[INPUT]: 接收 h3-mg-plan.v7 单段的 attention_reading_plan、已校验镜头列表与上层错误回调。
[OUTPUT]: 校验 AF01-AF12 的逐镜焦点路径、语义增量、运动预算、阅读锁与跨镜焦点交棒。
[POS]: scripts 的注意与阅读执行合同，把安静阶段研究落实为每镜唯一且可审计的观看路径。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from typing import Any, Callable


ErrorCallback = Callable[[str, str], None]
RULE_IDS = {f"AF{index:02d}" for index in range(1, 13)}
READING_RULE_IDS = {"AF04", "AF07", "AF08"}
MOTION_BUDGETS = {"static", "low", "medium", "high"}
REQUIRED_FIELDS = {
    "shot_id",
    "rule_ids",
    "attention_entry",
    "focus_path",
    "information_delta",
    "motion_budget",
    "reading_lock",
    "exit_focus",
}


def nonempty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def text_list(value: Any, error: ErrorCallback, path: str) -> list[str]:
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


def validate_attention_reading_plan(
    value: Any,
    shots: list[dict[str, Any]],
    error: ErrorCallback,
    path: str,
) -> None:
    if not isinstance(value, dict):
        error(path, "must be an object")
        return
    if set(value) != {"shot_bindings"}:
        missing = {"shot_bindings"} - set(value)
        extra = set(value) - {"shot_bindings"}
        if missing:
            error(path, f"missing keys {sorted(missing)}")
        if extra:
            error(path, f"unexpected keys {sorted(extra)}")
    bindings = value.get("shot_bindings")
    if not isinstance(bindings, list) or not bindings:
        error(f"{path}.shot_bindings", "must be a non-empty array")
        return

    known_ids = [str(shot.get("shot_id")) for shot in shots if nonempty_text(shot.get("shot_id"))]
    shots_by_id = {str(shot.get("shot_id")): shot for shot in shots}
    bound_ids: list[str] = []
    for index, item in enumerate(bindings):
        item_path = f"{path}.shot_bindings[{index}]"
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
        shot_id = item.get("shot_id")
        if not nonempty_text(shot_id):
            error(f"{item_path}.shot_id", "must be a non-empty string")
            continue
        shot_id = str(shot_id)
        bound_ids.append(shot_id)
        if shot_id not in shots_by_id:
            error(f"{item_path}.shot_id", f"unknown shot {shot_id!r}")
        rules = text_list(item.get("rule_ids"), error, f"{item_path}.rule_ids")
        unknown_rules = set(rules) - RULE_IDS
        if unknown_rules:
            error(f"{item_path}.rule_ids", f"unknown rules {sorted(unknown_rules)}")
        text_list(item.get("focus_path"), error, f"{item_path}.focus_path")
        for field in ("attention_entry", "information_delta", "reading_lock", "exit_focus"):
            if not nonempty_text(item.get(field)):
                error(f"{item_path}.{field}", "must be a non-empty string")
        motion_budget = item.get("motion_budget")
        if motion_budget not in MOTION_BUDGETS:
            error(f"{item_path}.motion_budget", "must be static, low, medium, or high")
        shot = shots_by_id.get(shot_id, {})
        if shot.get("text_events"):
            if not set(rules).intersection(READING_RULE_IDS):
                error(f"{item_path}.rule_ids", "text shot lacks AF04, AF07, or AF08 reading coverage")
            if motion_budget not in {"static", "low"}:
                error(f"{item_path}.motion_budget", "text reading window must use static or low motion")
        if index < len(known_ids) - 1 and "AF10" not in rules:
            error(f"{item_path}.rule_ids", "non-final shot lacks AF10 focus handoff")

    if len(bound_ids) != len(set(bound_ids)):
        error(f"{path}.shot_bindings", "must bind each shot exactly once")
    if bound_ids != known_ids:
        error(f"{path}.shot_bindings", f"must follow shot order exactly {known_ids!r}")
