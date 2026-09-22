#!/usr/bin/env python3
"""
[INPUT]: 接收 h3-mg-plan.v7 单段的 method_stack、selected_moves、运行时方法合同与上层错误回调。
[OUTPUT]: 校验信号强制动作、程序 spine、融合规则、配方覆盖、路由差量、阶段归属与动作职责图的一致性。
[POS]: documentary-mg-generator 的方法组合合同模块，被 H3 主验证器复用，避免把多维方法退化为 ID 清单。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

from compose_method_stack import compose, resolve_programs
from method_landing_contract import validate_method_landing


ErrorCallback = Callable[[str, str], None]
SIGNAL_ID = re.compile(r"^SG(?:0[1-9]|1[0-9]|2[0-4])$")
PROGRAM_ID = re.compile(r"^DP(?:0[1-9]|1[0-9]|2[0-4])$")
MOVE_ID = re.compile(r"^[NRWCTEKMXHLQ]0[1-8]$")
ROLES = {
    "spine",
    "world",
    "composition",
    "evidence",
    "text",
    "motion",
    "transition",
    "continuity",
    "guardrail",
}
REQUIRED_ROLES = {"spine", "composition", "motion", "continuity", "guardrail"}
EFFECT_STAGES = {"opening", "development", "turn", "payoff", "landing"}
RECIPE_CATALOG = json.loads(
    (Path(__file__).resolve().parent.parent / "references/director-method-recipes.json").read_text(encoding="utf-8")
)
METHOD_CONTRACT = json.loads(
    (Path(__file__).resolve().parent.parent / "references/method-runtime-contract.json").read_text(encoding="utf-8")
)
FEATURE_TAGS = set(RECIPE_CATALOG["feature_tags"])
RECIPE_IDS = {recipe["id"] for recipe in RECIPE_CATALOG["recipes"]}
RECIPES_BY_ID = {recipe["id"]: recipe for recipe in RECIPE_CATALOG["recipes"]}
SIGNAL_BRIDGE = RECIPE_CATALOG["signal_feature_bridge"]
SIGNAL_CONTRACTS = METHOD_CONTRACT["signal_contracts"]
PROGRAM_CONTRACTS = METHOD_CONTRACT["program_contracts"]
FUSION_RULES = {rule["id"]: rule for rule in METHOD_CONTRACT["fusion_rules"]}


def object_or_empty(value: Any, path: str, error: ErrorCallback) -> dict[str, Any]:
    if not isinstance(value, dict):
        error(path, "must be an object")
        return {}
    return value


def list_or_empty(value: Any, path: str, error: ErrorCallback, minimum: int = 0) -> list[Any]:
    if not isinstance(value, list):
        error(path, "must be an array")
        return []
    if len(value) < minimum:
        error(path, f"must contain at least {minimum} item(s)")
    return value


def text_or_empty(value: Any, path: str, error: ErrorCallback) -> str:
    if not isinstance(value, str) or not value.strip():
        error(path, "must be a non-empty string")
        return ""
    return value


def require_keys(value: dict[str, Any], keys: set[str], path: str, error: ErrorCallback) -> None:
    for key in sorted(keys):
        if key not in value:
            error(path, f"missing {key}")


def validate_signals(value: Any, path: str, error: ErrorCallback) -> tuple[set[str], str]:
    signals = list_or_empty(value, path, error, 1)
    if len(signals) > 5:
        error(path, "must contain at most five signals")
    ids: set[str] = set()
    primary_count = 0
    primary_id = ""
    for index, raw in enumerate(signals):
        item_path = f"{path}[{index}]"
        signal = object_or_empty(raw, item_path, error)
        require_keys(signal, {"signal_id", "strength", "source_evidence", "visual_obligation"}, item_path, error)
        signal_id = text_or_empty(signal.get("signal_id"), f"{item_path}.signal_id", error)
        if not SIGNAL_ID.fullmatch(signal_id):
            error(f"{item_path}.signal_id", "must reference SG01 through SG24")
        if signal_id in ids:
            error(f"{item_path}.signal_id", "duplicate semantic signal")
        ids.add(signal_id)
        strength = signal.get("strength")
        if strength not in {"primary", "secondary"}:
            error(f"{item_path}.strength", "must be primary or secondary")
        elif strength == "primary":
            primary_count += 1
            primary_id = signal_id
        text_or_empty(signal.get("source_evidence"), f"{item_path}.source_evidence", error)
        text_or_empty(signal.get("visual_obligation"), f"{item_path}.visual_obligation", error)
    if primary_count != 1:
        error(path, "must contain exactly one primary signal")
    return ids, primary_id


def validate_programs(stack: dict[str, Any], path: str, error: ErrorCallback) -> set[str]:
    primary = text_or_empty(stack.get("primary_program_id"), f"{path}.primary_program_id", error)
    if not PROGRAM_ID.fullmatch(primary):
        error(f"{path}.primary_program_id", "must reference DP01 through DP24")
    support = list_or_empty(stack.get("supporting_program_ids"), f"{path}.supporting_program_ids", error)
    if len(support) > 3:
        error(f"{path}.supporting_program_ids", "must contain at most three supporting programs")
    programs = {primary}
    for index, program_id in enumerate(support):
        item_path = f"{path}.supporting_program_ids[{index}]"
        program_id = text_or_empty(program_id, item_path, error)
        if not PROGRAM_ID.fullmatch(program_id):
            error(item_path, "must reference DP01 through DP24")
        if program_id in programs:
            error(item_path, "duplicate or primary program repeated as support")
        programs.add(program_id)
    return programs


def validate_program_router(
    signal_ids: set[str],
    primary_signal_id: str,
    primary_program: str,
    programs: set[str],
    path: str,
    error: ErrorCallback,
) -> None:
    if not primary_signal_id or primary_signal_id not in SIGNAL_BRIDGE or not signal_ids.issubset(SIGNAL_BRIDGE):
        return
    request = {
        "signal_ids": [primary_signal_id, *sorted(signal_ids - {primary_signal_id})],
        "primary_signal_id": primary_signal_id,
    }
    expected = resolve_programs(RECIPE_CATALOG, request, METHOD_CONTRACT)
    if primary_program != expected["primary_program_id"]:
        error(f"{path}.primary_program_id", f"deterministic program router requires {expected['primary_program_id']}")
    required_support = set(expected["supporting_program_ids"])
    actual_support = programs - {primary_program}
    if actual_support != required_support:
        error(f"{path}.supporting_program_ids", f"deterministic program router requires exactly {sorted(required_support)}")


def validate_recipe_router(
    stack: dict[str, Any],
    signal_ids: set[str],
    primary_signal_id: str,
    path: str,
    error: ErrorCallback,
) -> tuple[set[str], dict[str, Any] | None]:
    tags = list_or_empty(stack.get("feature_tags"), f"{path}.feature_tags", error, 1)
    if len(tags) > 16:
        error(f"{path}.feature_tags", "must contain at most 16 feature tags")
    normalized = [text_or_empty(tag, f"{path}.feature_tags[{index}]", error) for index, tag in enumerate(tags)]
    if len(normalized) != len(set(normalized)):
        error(f"{path}.feature_tags", "must not contain duplicate feature tags")
    unknown = set(normalized) - FEATURE_TAGS
    if unknown:
        error(f"{path}.feature_tags", f"unknown recipe feature tags {sorted(unknown)}")
    primary_tag = text_or_empty(stack.get("primary_feature_tag"), f"{path}.primary_feature_tag", error)
    if primary_tag not in normalized:
        error(f"{path}.primary_feature_tag", "must also appear in feature_tags")
    for signal_id in sorted(signal_ids):
        required_feature = SIGNAL_BRIDGE.get(signal_id, {}).get("primary")
        if required_feature and required_feature not in normalized:
            error(f"{path}.feature_tags", f"detected signal {signal_id} requires primary feature {required_feature}")
    expected_primary_tag = SIGNAL_BRIDGE.get(primary_signal_id, {}).get("primary")
    if expected_primary_tag and primary_tag != expected_primary_tag:
        error(f"{path}.primary_feature_tag", f"primary signal {primary_signal_id} requires {expected_primary_tag}")
    primary_recipe = text_or_empty(stack.get("primary_recipe_id"), f"{path}.primary_recipe_id", error)
    if primary_recipe not in RECIPE_IDS:
        error(f"{path}.primary_recipe_id", "must reference a known director recipe")
    overlays = list_or_empty(stack.get("overlay_recipe_ids"), f"{path}.overlay_recipe_ids", error)
    if len(overlays) > 2:
        error(f"{path}.overlay_recipe_ids", "must contain at most two overlay recipes")
    selected = {primary_recipe}
    normalized_overlays: list[str] = []
    for index, recipe_id in enumerate(overlays):
        item_path = f"{path}.overlay_recipe_ids[{index}]"
        recipe_id = text_or_empty(recipe_id, item_path, error)
        if recipe_id not in RECIPE_IDS:
            error(item_path, "must reference a known director recipe")
        if recipe_id in selected:
            error(item_path, "duplicate or primary recipe repeated as overlay")
        selected.add(recipe_id)
        normalized_overlays.append(recipe_id)
    routed: dict[str, Any] | None = None
    if not unknown and primary_tag in normalized and primary_recipe in RECIPE_IDS and selected <= RECIPE_IDS:
        try:
            routed = compose({"feature_tags": normalized, "primary_feature_tag": primary_tag})
        except ValueError as exc:
            error(f"{path}.feature_tags", f"cannot produce deterministic route: {exc}")
        if routed:
            expected_primary = routed["primary_recipe"]["id"]
            expected_overlays = [item["id"] for item in routed["overlay_recipes"]]
            if primary_recipe != expected_primary:
                error(f"{path}.primary_recipe_id", f"deterministic router requires {expected_primary}")
            if normalized_overlays != expected_overlays:
                error(f"{path}.overlay_recipe_ids", f"deterministic router requires {expected_overlays}")
    return selected, routed


def selected_move_ids(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {
        str(item.get("move_id"))
        for item in value
        if isinstance(item, dict) and MOVE_ID.fullmatch(str(item.get("move_id", "")))
    }


def normalized_binding_signals(value: Any, signal_ids: set[str], path: str, error: ErrorCallback) -> set[str]:
    activated = list_or_empty(value, path, error, 1)
    normalized: set[str] = set()
    for index, signal_id in enumerate(activated):
        item_path = f"{path}[{index}]"
        signal_id = text_or_empty(signal_id, item_path, error)
        if signal_id not in signal_ids:
            error(item_path, f"must reference a detected signal, got {signal_id!r}")
        if signal_id in normalized:
            error(item_path, "duplicate binding signal")
        normalized.add(signal_id)
    return normalized


def normalized_binding_stages(value: Any, path: str, error: ErrorCallback) -> set[str]:
    stages = list_or_empty(value, path, error, 1)
    normalized: set[str] = set()
    for index, stage in enumerate(stages):
        item_path = f"{path}[{index}]"
        if stage not in EFFECT_STAGES:
            error(item_path, f"unsupported effect stage {stage!r}")
        if stage in normalized:
            error(item_path, "duplicate effect stage")
        normalized.add(str(stage))
    return normalized


def normalized_binding_moves(value: Any, selected_moves: set[str], path: str, error: ErrorCallback) -> set[str]:
    moves = list_or_empty(value, path, error, 2)
    normalized: set[str] = set()
    for index, move_id in enumerate(moves):
        item_path = f"{path}[{index}]"
        move_id = text_or_empty(move_id, item_path, error)
        if not MOVE_ID.fullmatch(move_id):
            error(item_path, "must reference a valid atomic move")
        if move_id not in selected_moves:
            error(item_path, "must reference a selected move")
        if move_id in normalized:
            error(item_path, "duplicate binding move")
        normalized.add(move_id)
    return normalized


def validate_program_bindings(
    value: Any,
    programs: set[str],
    primary_program: str,
    signal_ids: set[str],
    primary_signal_id: str,
    selected_moves: set[str],
    path: str,
    error: ErrorCallback,
) -> None:
    bindings = list_or_empty(value, path, error, 1)
    bound_ids: set[str] = set()
    covered_signals: set[str] = set()
    primary_count = 0
    for index, raw in enumerate(bindings):
        item_path = f"{path}[{index}]"
        binding = object_or_empty(raw, item_path, error)
        require_keys(binding, {"program_id", "role", "activated_by", "stages", "move_ids", "responsibility"}, item_path, error)
        program_id = text_or_empty(binding.get("program_id"), f"{item_path}.program_id", error)
        if program_id in bound_ids:
            error(f"{item_path}.program_id", "duplicate program binding")
        bound_ids.add(program_id)
        role = binding.get("role")
        activated_by = normalized_binding_signals(binding.get("activated_by"), signal_ids, f"{item_path}.activated_by", error)
        stages = normalized_binding_stages(binding.get("stages"), f"{item_path}.stages", error)
        moves = normalized_binding_moves(binding.get("move_ids"), selected_moves, f"{item_path}.move_ids", error)
        spine = set(PROGRAM_CONTRACTS.get(program_id, {}).get("spine", []))
        if not moves.issubset(spine):
            error(f"{item_path}.move_ids", f"must use only {program_id} spine moves; invalid={sorted(moves - spine)}")
        text_or_empty(binding.get("responsibility"), f"{item_path}.responsibility", error)
        covered_signals.update(activated_by)
        for signal_id in activated_by:
            if program_id not in SIGNAL_BRIDGE.get(signal_id, {}).get("programs", []):
                error(f"{item_path}.activated_by", f"signal {signal_id} cannot activate {program_id}")
        if role == "primary":
            primary_count += 1
            if program_id != primary_program:
                error(f"{item_path}.program_id", f"primary binding must reference {primary_program}")
            if stages != EFFECT_STAGES:
                error(f"{item_path}.stages", "primary program must own all five effect stages")
            missing_spine = spine - moves
            if missing_spine:
                error(f"{item_path}.move_ids", f"primary program binding must contain complete spine {sorted(missing_spine)}")
            if primary_signal_id and primary_signal_id not in activated_by:
                error(f"{item_path}.activated_by", f"primary program must be activated by {primary_signal_id}")
        elif role == "supporting":
            if program_id == primary_program:
                error(f"{item_path}.program_id", "primary program cannot be bound as supporting")
            if len(stages) > 2:
                error(f"{item_path}.stages", "supporting program may enter at only one or two stages")
            if len(moves) < 2:
                error(f"{item_path}.move_ids", "supporting program binding must contain at least two spine moves")
        else:
            error(f"{item_path}.role", "must be primary or supporting")
    if bound_ids != programs:
        error(path, f"bindings must exactly cover selected programs; missing={sorted(programs - bound_ids)}, extra={sorted(bound_ids - programs)}")
    if primary_count != 1:
        error(path, "must contain exactly one primary program binding")
    if covered_signals != signal_ids:
        error(path, f"program bindings leave signals uncovered: {sorted(signal_ids - covered_signals)}")


def validate_recipe_bindings(
    value: Any,
    recipes: set[str],
    primary_recipe: str,
    signal_ids: set[str],
    primary_signal_id: str,
    selected_moves: set[str],
    path: str,
    error: ErrorCallback,
) -> None:
    bindings = list_or_empty(value, path, error, 1)
    bound_ids: set[str] = set()
    covered_signals: set[str] = set()
    primary_count = 0
    for index, raw in enumerate(bindings):
        item_path = f"{path}[{index}]"
        binding = object_or_empty(raw, item_path, error)
        require_keys(binding, {"recipe_id", "role", "activated_by", "stages", "move_ids", "responsibility"}, item_path, error)
        recipe_id = text_or_empty(binding.get("recipe_id"), f"{item_path}.recipe_id", error)
        if recipe_id in bound_ids:
            error(f"{item_path}.recipe_id", "duplicate recipe binding")
        bound_ids.add(recipe_id)
        role = binding.get("role")
        activated_by = normalized_binding_signals(binding.get("activated_by"), signal_ids, f"{item_path}.activated_by", error)
        stages = normalized_binding_stages(binding.get("stages"), f"{item_path}.stages", error)
        moves = normalized_binding_moves(binding.get("move_ids"), selected_moves, f"{item_path}.move_ids", error)
        recipe = RECIPES_BY_ID.get(recipe_id, {})
        required_moves = set(recipe.get("required_moves", []))
        expected_moves = selected_moves.intersection(required_moves)
        if moves != expected_moves:
            error(f"{item_path}.move_ids", f"must exactly expose selected required-move contribution {sorted(expected_moves)}")
        recipe_features = set(recipe.get("required_all", []) + recipe.get("required_any", []) + recipe.get("boost", []))
        for signal_id in activated_by:
            bridge = SIGNAL_BRIDGE.get(signal_id, {})
            if recipe_features.isdisjoint({bridge.get("primary"), *bridge.get("features", [])}):
                error(f"{item_path}.activated_by", f"signal {signal_id} has no feature path into {recipe_id}")
        text_or_empty(binding.get("responsibility"), f"{item_path}.responsibility", error)
        covered_signals.update(activated_by)
        if role == "primary":
            primary_count += 1
            if recipe_id != primary_recipe:
                error(f"{item_path}.recipe_id", f"primary binding must reference {primary_recipe}")
            if stages != EFFECT_STAGES:
                error(f"{item_path}.stages", "primary recipe must own all five effect stages")
            if len(moves) < 4:
                error(f"{item_path}.move_ids", "primary recipe binding must contain at least four required moves")
            if primary_signal_id and primary_signal_id not in activated_by:
                error(f"{item_path}.activated_by", f"primary recipe must be activated by {primary_signal_id}")
        elif role == "overlay":
            if recipe_id == primary_recipe:
                error(f"{item_path}.recipe_id", "primary recipe cannot be bound as overlay")
            if len(stages) > 2:
                error(f"{item_path}.stages", "overlay recipe may enter at only one or two stages")
            if len(moves) < 2:
                error(f"{item_path}.move_ids", "overlay recipe binding must contain at least two required moves")
        else:
            error(f"{item_path}.role", "must be primary or overlay")
    if bound_ids != recipes:
        error(path, f"bindings must exactly cover selected recipes; missing={sorted(recipes - bound_ids)}, extra={sorted(bound_ids - recipes)}")
    if primary_count != 1:
        error(path, "must contain exactly one primary recipe binding")
    if covered_signals != signal_ids:
        error(path, f"recipe bindings leave signals uncovered: {sorted(signal_ids - covered_signals)}")


def validate_route_trace(
    stack: dict[str, Any],
    routed: dict[str, Any] | None,
    selected_moves: Any,
    path: str,
    error: ErrorCallback,
) -> None:
    raw_router_moves = list_or_empty(stack.get("router_move_ids"), f"{path}.router_move_ids", error, 1)
    router_moves: list[str] = []
    for index, move_id in enumerate(raw_router_moves):
        item_path = f"{path}.router_move_ids[{index}]"
        move_id = text_or_empty(move_id, item_path, error)
        if not MOVE_ID.fullmatch(move_id):
            error(item_path, "must reference a valid atomic move")
        if move_id in router_moves:
            error(item_path, "duplicate router move")
        router_moves.append(move_id)
    if routed and router_moves != routed["resolved_move_ids"]:
        error(f"{path}.router_move_ids", f"must exactly preserve deterministic router output {routed['resolved_move_ids']}")

    adaptations = list_or_empty(stack.get("move_adaptations"), f"{path}.move_adaptations", error)
    removed: set[str] = set()
    added: set[str] = set()
    touched: set[str] = set()
    allowed_constraints = {
        "source_semantics",
        "available_media",
        "duration_budget",
        "fact_boundary",
        "continuity",
        "delivery_format",
    }
    router_set = set(router_moves)
    for index, raw in enumerate(adaptations):
        item_path = f"{path}.move_adaptations[{index}]"
        item = object_or_empty(raw, item_path, error)
        require_keys(item, {"operation", "move_id", "reason", "constraint"}, item_path, error)
        operation = item.get("operation")
        move_id = text_or_empty(item.get("move_id"), f"{item_path}.move_id", error)
        if not MOVE_ID.fullmatch(move_id):
            error(f"{item_path}.move_id", "must reference a valid atomic move")
        if move_id in touched:
            error(f"{item_path}.move_id", "each move may be adapted at most once")
        touched.add(move_id)
        text_or_empty(item.get("reason"), f"{item_path}.reason", error)
        if item.get("constraint") not in allowed_constraints:
            error(f"{item_path}.constraint", "unsupported adaptation constraint")
        if operation == "remove":
            if move_id not in router_set:
                error(f"{item_path}.move_id", "remove must target a router move")
            removed.add(move_id)
        elif operation == "add":
            if move_id in router_set:
                error(f"{item_path}.move_id", "add must introduce a move absent from the router baseline")
            added.add(move_id)
        else:
            error(f"{item_path}.operation", "must be add or remove")
    replayed = (router_set - removed) | added
    selected = selected_move_ids(selected_moves)
    if replayed != selected:
        error(
            f"{path}.move_adaptations",
            f"replayed route must equal selected_moves; missing adaptations for remove={sorted(replayed - selected)}, add={sorted(selected - replayed)}",
        )


def validate_method_move_coverage(
    selected_moves: Any,
    primary_signal_id: str,
    primary_program: str,
    programs: set[str],
    primary_recipe: str,
    recipes: set[str],
    path: str,
    error: ErrorCallback,
) -> None:
    selected = selected_move_ids(selected_moves)
    forced = set(SIGNAL_CONTRACTS.get(primary_signal_id, {}).get("forced_moves", []))
    if not forced.issubset(selected):
        error(path, f"primary signal {primary_signal_id} forced moves missing {sorted(forced - selected)}")
    spine = set(PROGRAM_CONTRACTS.get(primary_program, {}).get("spine", []))
    if not spine.issubset(selected):
        error(path, f"primary program {primary_program} spine missing {sorted(spine - selected)}")
    for program_id in sorted(programs - {primary_program}):
        overlap = selected.intersection(PROGRAM_CONTRACTS.get(program_id, {}).get("spine", []))
        if len(overlap) < 2:
            error(path, f"supporting program {program_id} contributes fewer than two spine moves")
    primary_overlap = selected.intersection(RECIPES_BY_ID.get(primary_recipe, {}).get("required_moves", []))
    if len(primary_overlap) < 4:
        error(path, f"primary recipe {primary_recipe} contributes fewer than four required moves")
    for recipe_id in sorted(recipes - {primary_recipe}):
        overlap = selected.intersection(RECIPES_BY_ID.get(recipe_id, {}).get("required_moves", []))
        if len(overlap) < 2:
            error(path, f"overlay recipe {recipe_id} contributes fewer than two required moves")


def validate_stage_bindings(
    value: Any,
    program_bindings: Any,
    programs: set[str],
    primary_program: str,
    move_ids: set[str],
    path: str,
    error: ErrorCallback,
) -> None:
    bindings = list_or_empty(value, path, error, 5)
    expected_order = ["opening", "development", "turn", "payoff", "landing"]
    actual_order: list[str] = []
    covered_moves: set[str] = set()
    owners: set[str] = set()
    declared_stages: dict[str, set[str]] = {}
    if isinstance(program_bindings, list):
        for raw in program_bindings:
            if isinstance(raw, dict) and isinstance(raw.get("program_id"), str):
                declared_stages[raw["program_id"]] = set(raw.get("stages", []))
    for index, raw in enumerate(bindings):
        item_path = f"{path}[{index}]"
        binding = object_or_empty(raw, item_path, error)
        require_keys(binding, {"stage", "owner_program_id", "move_ids", "state_change"}, item_path, error)
        stage = str(binding.get("stage", ""))
        actual_order.append(stage)
        owner = text_or_empty(binding.get("owner_program_id"), f"{item_path}.owner_program_id", error)
        if owner not in programs:
            error(f"{item_path}.owner_program_id", "must reference a selected program")
        elif stage not in declared_stages.get(owner, set()):
            error(f"{item_path}.owner_program_id", f"program binding does not declare stage {stage}")
        owners.add(owner)
        stage_moves = list_or_empty(binding.get("move_ids"), f"{item_path}.move_ids", error, 1)
        for move_index, move_id in enumerate(stage_moves):
            move_path = f"{item_path}.move_ids[{move_index}]"
            if move_id not in move_ids:
                error(move_path, "must reference a selected move")
            if move_id in covered_moves:
                error(move_path, "a move may belong to only one effect stage")
            covered_moves.add(str(move_id))
        text_or_empty(binding.get("state_change"), f"{item_path}.state_change", error)
    if actual_order != expected_order:
        error(path, f"stages must appear exactly in order {expected_order}")
    if covered_moves != move_ids:
        error(path, f"stage bindings must exactly cover selected moves; missing={sorted(move_ids - covered_moves)}, extra={sorted(covered_moves - move_ids)}")
    if bindings and (
        bindings[0].get("owner_program_id") != primary_program
        or bindings[-1].get("owner_program_id") != primary_program
    ):
        error(path, "primary program must own opening and landing")
    missing_support = programs - {primary_program} - owners
    if missing_support:
        error(path, f"supporting programs without an owned stage {sorted(missing_support)}")


def validate_activations(
    value: Any,
    selected_moves: Any,
    signal_ids: set[str],
    path: str,
    error: ErrorCallback,
) -> set[str]:
    activations = list_or_empty(value, path, error, 1)
    expected = selected_move_ids(selected_moves)
    actual: set[str] = set()
    roles: set[str] = set()
    covered_signals: set[str] = set()
    interactions: dict[str, set[str]] = {}
    for index, raw in enumerate(activations):
        item_path = f"{path}[{index}]"
        activation = object_or_empty(raw, item_path, error)
        require_keys(
            activation,
            {"move_id", "role", "triggered_by", "contribution", "interacts_with"},
            item_path,
            error,
        )
        move_id = text_or_empty(activation.get("move_id"), f"{item_path}.move_id", error)
        if not MOVE_ID.fullmatch(move_id):
            error(f"{item_path}.move_id", "must reference a valid atomic move")
        if move_id in actual:
            error(f"{item_path}.move_id", "duplicate method activation")
        actual.add(move_id)
        role = activation.get("role")
        if role not in ROLES:
            error(f"{item_path}.role", f"unsupported method role {role!r}")
        else:
            roles.add(role)
        triggered_by = list_or_empty(activation.get("triggered_by"), f"{item_path}.triggered_by", error, 1)
        for trigger_index, signal_id in enumerate(triggered_by):
            if signal_id not in signal_ids:
                error(f"{item_path}.triggered_by[{trigger_index}]", f"unknown detected signal {signal_id!r}")
            else:
                covered_signals.add(str(signal_id))
        text_or_empty(activation.get("contribution"), f"{item_path}.contribution", error)
        linked = list_or_empty(activation.get("interacts_with"), f"{item_path}.interacts_with", error, 1)
        linked_ids = set()
        for link_index, linked_id in enumerate(linked):
            link_path = f"{item_path}.interacts_with[{link_index}]"
            if linked_id == move_id:
                error(link_path, "cannot interact with itself")
            if not MOVE_ID.fullmatch(str(linked_id)):
                error(link_path, "must reference a valid atomic move")
            linked_ids.add(str(linked_id))
        interactions[move_id] = linked_ids
    if actual != expected:
        error(path, f"activation move ids must exactly equal selected_moves; missing={sorted(expected - actual)}, extra={sorted(actual - expected)}")
    missing_roles = REQUIRED_ROLES - roles
    if missing_roles:
        error(path, f"missing required method roles {sorted(missing_roles)}")
    if covered_signals != signal_ids:
        error(path, f"detected signals without an activated move: {sorted(signal_ids - covered_signals)}")
    for move_id, linked_ids in interactions.items():
        unknown = linked_ids - actual
        if unknown:
            error(path, f"{move_id} interacts with unselected moves {sorted(unknown)}")
    return actual


def validate_collisions(value: Any, move_ids: set[str], path: str, error: ErrorCallback) -> set[frozenset[str]]:
    collisions = list_or_empty(value, path, error, 1)
    pairs: set[frozenset[str]] = set()
    for index, raw in enumerate(collisions):
        item_path = f"{path}[{index}]"
        collision = object_or_empty(raw, item_path, error)
        require_keys(collision, {"between", "decision", "reason"}, item_path, error)
        between = list_or_empty(collision.get("between"), f"{item_path}.between", error, 2)
        if len(between) != 2:
            error(f"{item_path}.between", "must contain exactly two competing moves")
        for move_index, move_id in enumerate(between):
            if move_id not in move_ids:
                error(f"{item_path}.between[{move_index}]", f"must reference a selected move, got {move_id!r}")
        if len(between) == 2:
            pairs.add(frozenset(str(move_id) for move_id in between))
        text_or_empty(collision.get("decision"), f"{item_path}.decision", error)
        text_or_empty(collision.get("reason"), f"{item_path}.reason", error)
    return pairs


def validate_world_collisions(
    move_ids: set[str],
    primary_program: str,
    collision_pairs: set[frozenset[str]],
    path: str,
    error: ErrorCallback,
) -> None:
    worlds = sorted(move_id for move_id in move_ids if move_id.startswith("W"))
    primary_world = next(
        (move_id for move_id in PROGRAM_CONTRACTS.get(primary_program, {}).get("spine", []) if move_id.startswith("W")),
        worlds[0] if worlds else "",
    )
    if primary_world not in worlds:
        return
    for world in worlds:
        if world != primary_world and frozenset({primary_world, world}) not in collision_pairs:
            error(path, f"competing world {world} must be explicitly resolved against primary world {primary_world}")


def validate_effect_chain(value: Any, path: str, error: ErrorCallback) -> None:
    chain = object_or_empty(value, path, error)
    require_keys(chain, EFFECT_STAGES, path, error)
    if set(chain) != EFFECT_STAGES:
        error(path, f"must contain exactly the five effect stages {sorted(EFFECT_STAGES)}")
    for stage in sorted(EFFECT_STAGES):
        text_or_empty(chain.get(stage), f"{path}.{stage}", error)


def validate_discarded(value: Any, selected_methods: set[str], move_ids: set[str], path: str, error: ErrorCallback) -> None:
    discarded = list_or_empty(value, path, error, 2)
    seen: set[str] = set()
    for index, raw in enumerate(discarded):
        item_path = f"{path}[{index}]"
        item = object_or_empty(raw, item_path, error)
        require_keys(item, {"method_id", "reason"}, item_path, error)
        method_id = text_or_empty(item.get("method_id"), f"{item_path}.method_id", error)
        if not (PROGRAM_ID.fullmatch(method_id) or MOVE_ID.fullmatch(method_id) or method_id in RECIPE_IDS):
            error(f"{item_path}.method_id", "must reference a DP program, DR recipe, or atomic move")
        if method_id in selected_methods or method_id in move_ids:
            error(f"{item_path}.method_id", "discarded method cannot also be selected")
        if method_id in seen:
            error(f"{item_path}.method_id", "duplicate discarded method")
        seen.add(method_id)
        text_or_empty(item.get("reason"), f"{item_path}.reason", error)


def validate_method_stack(value: Any, selected_moves: Any, error: ErrorCallback, path: str) -> None:
    stack = object_or_empty(value, path, error)
    required = {
        "detected_signals",
        "feature_tags",
        "primary_feature_tag",
        "primary_program_id",
        "supporting_program_ids",
        "program_bindings",
        "fusion_bindings",
        "primary_recipe_id",
        "overlay_recipe_ids",
        "recipe_bindings",
        "router_move_ids",
        "move_adaptations",
        "activations",
        "composition_logic",
        "collision_resolutions",
        "effect_chain",
        "stage_bindings",
        "discarded_methods",
        "density_strategy",
    }
    require_keys(stack, required, path, error)
    signal_ids, primary_signal_id = validate_signals(
        stack.get("detected_signals"), f"{path}.detected_signals", error
    )
    recipes, routed = validate_recipe_router(stack, signal_ids, primary_signal_id, path, error)
    programs = validate_programs(stack, path, error)
    primary_program = str(stack.get("primary_program_id", ""))
    selected_ids = selected_move_ids(selected_moves)
    validate_program_router(signal_ids, primary_signal_id, primary_program, programs, path, error)
    if primary_signal_id and primary_program not in SIGNAL_BRIDGE.get(primary_signal_id, {}).get("programs", []):
        error(
            f"{path}.primary_program_id",
            f"primary signal {primary_signal_id} cannot activate {primary_program}",
        )
    for signal_id in sorted(signal_ids - {primary_signal_id}):
        candidates = set(SIGNAL_BRIDGE.get(signal_id, {}).get("programs", []))
        if candidates and not candidates.intersection(programs):
            error(
                f"{path}.supporting_program_ids",
                f"secondary signal {signal_id} must activate one of {sorted(candidates)}",
            )
    validate_program_bindings(
        stack.get("program_bindings"),
        programs,
        primary_program,
        signal_ids,
        primary_signal_id,
        selected_ids,
        f"{path}.program_bindings",
        error,
    )
    validate_recipe_bindings(
        stack.get("recipe_bindings"),
        recipes,
        str(stack.get("primary_recipe_id", "")),
        signal_ids,
        primary_signal_id,
        selected_ids,
        f"{path}.recipe_bindings",
        error,
    )
    validate_route_trace(stack, routed, selected_moves, path, error)
    validate_method_move_coverage(
        selected_moves,
        primary_signal_id,
        primary_program,
        programs,
        str(stack.get("primary_recipe_id", "")),
        recipes,
        f"{path}.activations",
        error,
    )
    move_ids = validate_activations(
        stack.get("activations"),
        selected_moves,
        signal_ids,
        f"{path}.activations",
        error,
    )
    text_or_empty(stack.get("composition_logic"), f"{path}.composition_logic", error)
    collision_pairs = validate_collisions(
        stack.get("collision_resolutions"), move_ids, f"{path}.collision_resolutions", error
    )
    validate_world_collisions(move_ids, primary_program, collision_pairs, f"{path}.collision_resolutions", error)
    validate_effect_chain(stack.get("effect_chain"), f"{path}.effect_chain", error)
    validate_stage_bindings(
        stack.get("stage_bindings"),
        stack.get("program_bindings"),
        programs,
        primary_program,
        move_ids,
        f"{path}.stage_bindings",
        error,
    )
    validate_method_landing(
        stack.get("fusion_bindings"),
        signal_ids,
        primary_signal_id,
        programs,
        primary_program,
        move_ids,
        stack.get("program_bindings"),
        stack.get("recipe_bindings"),
        stack.get("stage_bindings"),
        FUSION_RULES,
        path,
        error,
    )
    validate_discarded(stack.get("discarded_methods"), programs | recipes, move_ids, f"{path}.discarded_methods", error)
    text_or_empty(stack.get("density_strategy"), f"{path}.density_strategy", error)
