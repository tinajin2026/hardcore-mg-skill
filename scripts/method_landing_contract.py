#!/usr/bin/env python3
"""
[INPUT]: 接收已选信号/程序/动作、程序与配方 binding、融合 binding 和五阶段动作归属。
[OUTPUT]: 校验方法贡献是否落入声明阶段，并验证每条适用融合规则由双方程序动作共同实现。
[POS]: hardcore-mg-skill 的方法落地交叉合同，补足单字段验证无法发现的装饰性方法选择。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any


ErrorCallback = Callable[[str, str], None]
EFFECT_STAGES = {"opening", "development", "turn", "payoff", "landing"}


def array(value: Any, path: str, error: ErrorCallback, minimum: int = 0) -> list[Any]:
    if not isinstance(value, list):
        error(path, "must be an array")
        return []
    if len(value) < minimum:
        error(path, f"must contain at least {minimum} item(s)")
    return value


def text(value: Any, path: str, error: ErrorCallback) -> str:
    if not isinstance(value, str) or not value.strip():
        error(path, "must be a non-empty string")
        return ""
    return value


def binding_maps(bindings: Any, id_key: str) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    stages: dict[str, set[str]] = {}
    moves: dict[str, set[str]] = {}
    if isinstance(bindings, list):
        for binding in bindings:
            if isinstance(binding, dict) and isinstance(binding.get(id_key), str):
                method_id = binding[id_key]
                stages[method_id] = set(binding.get("stages", []))
                moves[method_id] = set(binding.get("move_ids", []))
    return stages, moves


def validate_method_landing(
    fusion_bindings: Any,
    signal_ids: set[str],
    primary_signal_id: str,
    programs: set[str],
    primary_program: str,
    selected_moves: set[str],
    program_bindings: Any,
    recipe_bindings: Any,
    stage_bindings: Any,
    fusion_rules: dict[str, dict[str, Any]],
    path: str,
    error: ErrorCallback,
) -> None:
    program_stages, program_moves = binding_maps(program_bindings, "program_id")
    recipe_stages, recipe_moves = binding_maps(recipe_bindings, "recipe_id")
    stage_by_move: dict[str, str] = {}
    stage_moves: dict[str, set[str]] = {}
    for raw in stage_bindings if isinstance(stage_bindings, list) else []:
        if isinstance(raw, dict):
            stage = str(raw.get("stage", ""))
            moves = set(raw.get("move_ids", []))
            stage_moves[stage] = moves
            stage_by_move.update({str(move_id): stage for move_id in moves})

    for label, stages_by_id, moves_by_id in (
        ("program_bindings", program_stages, program_moves),
        ("recipe_bindings", recipe_stages, recipe_moves),
    ):
        for method_id, moves in moves_by_id.items():
            outside = {move_id for move_id in moves if stage_by_move.get(move_id) not in stages_by_id.get(method_id, set())}
            if outside:
                error(f"{path}.{label}", f"{method_id} binds moves outside its declared stages {sorted(outside)}")

    for raw in stage_bindings if isinstance(stage_bindings, list) else []:
        if isinstance(raw, dict):
            stage = str(raw.get("stage", ""))
            owner = str(raw.get("owner_program_id", ""))
            if not stage_moves.get(stage, set()).intersection(program_moves.get(owner, set())):
                error(f"{path}.stage_bindings", f"stage {stage} contains no move contributed by owner {owner}")

    expected = [
        rule_id
        for rule_id, rule in fusion_rules.items()
        if rule["when"][0] == primary_signal_id and set(rule["when"]).issubset(signal_ids)
    ]
    normalized: list[str] = []
    for index, raw in enumerate(array(fusion_bindings, f"{path}.fusion_bindings", error)):
        item_path = f"{path}.fusion_bindings[{index}]"
        if not isinstance(raw, dict):
            error(item_path, "must be an object")
            continue
        for key in ("rule_id", "activated_by", "stages", "move_ids", "implementation", "combined_effect"):
            if key not in raw:
                error(item_path, f"missing {key}")
        rule_id = text(raw.get("rule_id"), f"{item_path}.rule_id", error)
        if rule_id not in fusion_rules:
            error(f"{item_path}.rule_id", "must reference FR01 through FR18")
            continue
        if rule_id in normalized:
            error(f"{item_path}.rule_id", "duplicate fusion rule")
        normalized.append(rule_id)
        rule = fusion_rules[rule_id]
        activated_by = array(raw.get("activated_by"), f"{item_path}.activated_by", error, 2)
        if activated_by != rule["when"]:
            error(f"{item_path}.activated_by", f"must exactly equal {rule['when']}")
        stages = array(raw.get("stages"), f"{item_path}.stages", error, 1)
        if len(stages) > 2 or len(stages) != len(set(stages)) or not set(stages).issubset(EFFECT_STAGES):
            error(f"{item_path}.stages", "must contain one or two unique effect stages")
        moves = array(raw.get("move_ids"), f"{item_path}.move_ids", error, 2)
        move_set = {str(move_id) for move_id in moves}
        if len(moves) != len(move_set) or not move_set.issubset(selected_moves):
            error(f"{item_path}.move_ids", "must contain unique selected moves")
        primary_moves = program_moves.get(rule["primary"], set())
        support_moves = program_moves.get(rule["support"], set())
        if not move_set.issubset(primary_moves | support_moves):
            error(f"{item_path}.move_ids", "must use only moves actually contributed by the fused programs")
        if not move_set.intersection(primary_moves) or not move_set.intersection(support_moves):
            error(f"{item_path}.move_ids", "must contain actual move contributions from both fused programs")
        if primary_program != rule["primary"] or rule["support"] not in programs:
            error(item_path, f"requires primary {rule['primary']} and support {rule['support']}")
        if not set(stages).issubset(program_stages.get(rule["support"], set())):
            error(f"{item_path}.stages", "must stay inside the supporting program insertion stages")
        if any(stage_by_move.get(move_id) not in stages for move_id in move_set):
            error(f"{item_path}.move_ids", "fusion moves must land inside the declared fusion stages")
        text(raw.get("implementation"), f"{item_path}.implementation", error)
        text(raw.get("combined_effect"), f"{item_path}.combined_effect", error)
    if normalized != expected:
        error(f"{path}.fusion_bindings", f"must exactly bind applicable fusion rules {expected}")
