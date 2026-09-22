#!/usr/bin/env python3
"""
[INPUT]: 读取当前语义段的 SG01–SG24 信号或显式特征，以及 references/director-method-recipes.json。
[OUTPUT]: 输出主/辅程序与融合规则、主/叠配方、按语义完整激活的动作、世界锁与冲突消解，并穷举验证一至五信号请求和 48 配方可达性。
[POS]: hardcore-mg-skill 的确定性方法组合器，把语义判断编译为可审计导演方法栈。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from functools import lru_cache
from itertools import combinations
from pathlib import Path
from typing import Any


MOVE_ID = re.compile(r"^[NRWCTEKMXHLQ](?:0[1-8])$")
EVIDENCE_FEATURES = {"QUOTE", "DOCUMENT", "UI", "ARCHIVE", "LIVE_ACTION"}
DENSE_FEATURES = {"DATA", "MECHANISM", "DOCUMENT", "RANKING", "RELATION", "PROCESS"}
WORLD_MOVES = {f"W{index:02d}" for index in range(1, 9)}
MOTION_MOVES = {f"M{index:02d}" for index in range(1, 9)}
TEXT_MOVES = {f"T{index:02d}" for index in range(1, 9)}


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    path = Path(__file__).resolve().parent.parent / "references" / "director-method-recipes.json"
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def load_method_contract() -> dict[str, Any]:
    path = Path(__file__).resolve().parent.parent / "references" / "method-runtime-contract.json"
    return json.loads(path.read_text(encoding="utf-8"))


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(items))


def normalize_request(raw: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    bridge = catalog["signal_feature_bridge"]
    known_signals = set(bridge)
    known_features = set(catalog["feature_tags"])
    signal_ids = unique([str(item).strip().upper() for item in raw.get("signal_ids", []) if str(item).strip()])
    unknown_signals = sorted(set(signal_ids) - known_signals)
    if unknown_signals:
        raise ValueError(f"unknown signal_ids: {unknown_signals}")
    if len(signal_ids) > 5:
        raise ValueError("signal_ids may contain at most one primary and four secondary signals")

    primary_signal_id = str(raw.get("primary_signal_id") or "").strip().upper() or None
    if primary_signal_id and primary_signal_id not in signal_ids:
        raise ValueError("primary_signal_id must also appear in signal_ids")
    if signal_ids and not primary_signal_id:
        primary_signal_id = signal_ids[0]

    explicit_features = [str(item).strip().upper() for item in raw.get("feature_tags", []) if str(item).strip()]
    inferred_features = [feature for signal_id in signal_ids for feature in bridge[signal_id]["features"]]
    features = unique(explicit_features + inferred_features)
    if not features:
        raise ValueError("provide at least one signal_id or semantic feature_tag")
    unknown = sorted(set(features) - known_features)
    if unknown:
        raise ValueError(f"unknown feature_tags: {unknown}")

    inferred_primary = bridge[primary_signal_id]["primary"] if primary_signal_id else features[0]
    primary = str(raw.get("primary_feature_tag") or inferred_primary).strip().upper()
    if primary not in features:
        raise ValueError("primary_feature_tag must also appear in feature_tags")
    max_overlays = raw.get("max_overlays", 2)
    if not isinstance(max_overlays, int) or not 0 <= max_overlays <= 2:
        raise ValueError("max_overlays must be an integer from 0 to 2")
    return {
        "feature_tags": features,
        "primary_feature_tag": primary,
        "max_overlays": max_overlays,
        "signal_ids": signal_ids,
        "primary_signal_id": primary_signal_id,
        "primary_signal": raw.get("primary_signal"),
        "secondary_signals": raw.get("secondary_signals", []),
    }


def recipe_score(recipe: dict[str, Any], request: dict[str, Any]) -> int | None:
    features = set(request["feature_tags"])
    required_all = set(recipe["required_all"])
    required_any = set(recipe["required_any"])
    if not required_all.issubset(features):
        return None
    if required_any and not required_any.intersection(features):
        return None
    if set(recipe["exclude"]).intersection(features):
        return None

    score = 6 * len(required_all)
    score += 4 * len(required_any.intersection(features))
    score += 2 * len(set(recipe["boost"]).intersection(features))
    if request["primary_feature_tag"] in required_all | required_any:
        score += 10
    if recipe["role"] == "overlay":
        score -= 2
    return score


def recipe_projection(recipe: dict[str, Any], score: int) -> dict[str, Any]:
    return {
        "id": recipe["id"],
        "name": recipe["name"],
        "score": score,
        "state_sequence": recipe["state_sequence"],
        "media_policy": recipe["media_policy"],
        "failure": recipe["failure"],
    }


def resolve_programs(
    catalog: dict[str, Any],
    request: dict[str, Any],
    method_contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    signal_ids = request["signal_ids"]
    primary_signal_id = request["primary_signal_id"]
    if not signal_ids or not primary_signal_id:
        return {"primary_program_id": None, "supporting_program_ids": [], "fusion_rule_ids": []}
    method_contract = method_contract or load_method_contract()
    bridge = catalog["signal_feature_bridge"]
    applicable = [
        rule
        for rule in method_contract["fusion_rules"]
        if rule["when"][0] == primary_signal_id and set(rule["when"]).issubset(signal_ids)
    ]
    fusion_primaries = {rule["primary"] for rule in applicable}
    if len(fusion_primaries) > 1:
        raise ValueError(f"applicable fusion rules disagree on primary program: {sorted(fusion_primaries)}")
    primary_program = next(iter(fusion_primaries), bridge[primary_signal_id]["programs"][0])
    required_support = {rule["support"] for rule in applicable if rule["support"] != primary_program}
    candidates = sorted(
        {
            program_id
            for signal_id in signal_ids
            for program_id in bridge[signal_id]["programs"]
            if program_id != primary_program
        }
    )
    selected_support: tuple[str, ...] | None = None
    for size in range(len(required_support), min(3, len(candidates)) + 1):
        for candidate_group in combinations(candidates, size):
            candidate_set = set(candidate_group)
            if not required_support.issubset(candidate_set):
                continue
            selected = {primary_program, *candidate_set}
            if all(selected.intersection(bridge[signal_id]["programs"]) for signal_id in signal_ids):
                selected_support = candidate_group
                break
        if selected_support is not None:
            break
    if selected_support is None:
        raise ValueError(
            f"no <=3 supporting-program set covers signals {signal_ids}; "
            "split the semantic segment or demote a secondary signal"
        )
    return {
        "primary_program_id": primary_program,
        "supporting_program_ids": list(selected_support),
        "fusion_rule_ids": [rule["id"] for rule in applicable],
    }


def choose_recipes(catalog: dict[str, Any], request: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    scored: list[tuple[int, dict[str, Any]]] = []
    for recipe in catalog["recipes"]:
        score = recipe_score(recipe, request)
        if score is not None:
            scored.append((score, recipe))
    if not scored:
        raise ValueError("no method recipe matches the supplied feature_tags")

    scored.sort(key=lambda item: (-item[0], item[1]["id"]))
    primary_candidates = [item for item in scored if item[1]["role"] != "overlay"]
    if not primary_candidates:
        raise ValueError("feature_tags only matched overlay recipes; add the segment's semantic operator")
    primary_score, primary = primary_candidates[0]

    covered = set(primary["required_any"] + primary["required_all"] + primary["boost"])
    covered.intersection_update(request["feature_tags"])
    existing_moves = set(primary["required_moves"])
    overlays: list[tuple[int, dict[str, Any]]] = []
    remaining = [(score, recipe) for score, recipe in scored if recipe["id"] != primary["id"]]
    while len(overlays) < request["max_overlays"]:
        ranked: list[tuple[int, int, str, int, dict[str, Any]]] = []
        for score, recipe in remaining:
            recipe_coverage = set(recipe["required_any"] + recipe["required_all"] + recipe["boost"])
            recipe_coverage.intersection_update(request["feature_tags"])
            new_features = recipe_coverage - covered
            new_moves = set(recipe["required_moves"]) - existing_moves
            if not new_features or len(new_moves) < 2:
                continue
            overlay_bonus = 2 if recipe["role"] == "overlay" else 0
            ranked.append((len(new_features), score + overlay_bonus, recipe["id"], score, recipe))
        if not ranked:
            break
        ranked.sort(key=lambda item: (-item[0], -item[1], item[2]))
        _, _, _, score, selected = ranked[0]
        overlays.append((score, selected))
        coverage = set(selected["required_any"] + selected["required_all"] + selected["boost"])
        covered.update(coverage.intersection(request["feature_tags"]))
        existing_moves.update(selected["required_moves"])
        remaining = [(item_score, item) for item_score, item in remaining if item["id"] != selected["id"]]

    selected_ids = {primary["id"], *(recipe["id"] for _, recipe in overlays)}
    rejected = [recipe_projection(recipe, score) for score, recipe in scored if recipe["id"] not in selected_ids][:5]
    return primary, [recipe for _, recipe in overlays], rejected


def resolve_moves(
    catalog: dict[str, Any],
    request: dict[str, Any],
    primary: dict[str, Any],
    overlays: list[dict[str, Any]],
) -> tuple[list[str], list[str], str, list[str]]:
    conflicts: list[str] = []
    candidates = unique(primary["required_moves"] + [move for item in overlays for move in item["required_moves"]])

    if EVIDENCE_FEATURES.intersection(request["feature_tags"]) and "R08" in candidates:
        candidates.remove("R08")
        conflicts.append("CF01：已有真实材料或一手来源，移除解释性重建 R08。")

    if "L05" in candidates and "L06" in candidates:
        keep = "L06" if DENSE_FEATURES.intersection(request["feature_tags"]) else "L05"
        drop = "L05" if keep == "L06" else "L06"
        candidates.remove(drop)
        conflicts.append(f"CF02：节奏责任冲突，保留 {keep}，移除 {drop}。")

    primary_worlds = [move for move in primary["required_moves"] + primary["optional_moves"] if move in WORLD_MOVES]
    overlay_worlds = [move for item in overlays for move in item["required_moves"] + item["optional_moves"] if move in WORLD_MOVES]
    world_move = (primary_worlds + overlay_worlds + ["W08"])[0]
    world_name = primary["worlds"][0]
    removed_worlds = [move for move in candidates if move in WORLD_MOVES and move != world_move]
    candidates = [move for move in candidates if move not in WORLD_MOVES]
    candidates.insert(min(2, len(candidates)), world_move)
    if removed_worlds:
        conflicts.append(f"CF04：持久世界只保留 {world_move}「{world_name}」，移除并列世界 {removed_worlds}。")

    candidates = unique(candidates)
    if len(set(candidates).intersection(MOTION_MOVES)) > 1:
        conflicts.append("CF05：保留多种运动职责，但每个 M 动作必须分配到互不重叠的微时间拍。")
    if len(set(candidates).intersection(TEXT_MOVES)) > 1:
        conflicts.append("CF06：保留多种文字职责，但同一时刻最多一个主文字角色。")

    categories = unique([move[0] for move in candidates])
    mandatory = set(catalog["mandatory_dimensions"])
    if not mandatory.issubset(categories):
        raise ValueError(f"resolved method stack lacks required dimensions: {categories}")
    if any(not MOVE_ID.fullmatch(move) for move in candidates):
        raise ValueError("recipe catalog contains an invalid atomic move id")

    local_worlds = unique([world for item in overlays for world in item["worlds"] if world != world_name])
    return candidates, conflicts, world_name, local_worlds


def compose(raw: dict[str, Any], catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    catalog = catalog or load_catalog()
    request = normalize_request(raw, catalog)
    program_route = resolve_programs(catalog, request)
    primary, overlays, rejected = choose_recipes(catalog, request)
    moves, conflicts, world, local_worlds = resolve_moves(catalog, request, primary, overlays)
    score_lookup = {recipe["id"]: recipe_score(recipe, request) or 0 for recipe in catalog["recipes"]}
    overlay_items = [recipe_projection(recipe, score_lookup[recipe["id"]]) for recipe in overlays]

    overlay_names = "、".join(item["name"] for item in overlays) or "无"
    return {
        "router_version": catalog["version"],
        "signal_ids": request["signal_ids"],
        "primary_signal_id": request["primary_signal_id"],
        "feature_tags": request["feature_tags"],
        "primary_feature_tag": request["primary_feature_tag"],
        "primary_signal": request["primary_signal"],
        "secondary_signals": request["secondary_signals"],
        **program_route,
        "primary_recipe": recipe_projection(primary, score_lookup[primary["id"]]),
        "overlay_recipes": overlay_items,
        "world_lock": world,
        "local_world_options": local_worlds,
        "resolved_move_ids": moves,
        "dimensions": unique([move[0] for move in moves]),
        "combination_logic": f"以「{primary['name']}」承载主认知骨架；「{overlay_names}」只补充证据、媒介、格式或结尾责任，不另开叙事主线。",
        "expected_visual_effect": f"在「{world}」中按“{primary['state_sequence']}”推进；所有叠加方法进入固定槽位，关键变化后稳定回收。",
        "media_policies": unique([primary["media_policy"]] + [item["media_policy"] for item in overlays]),
        "failure_signals": unique([primary["failure"]] + [item["failure"] for item in overlays]),
        "conflict_resolutions": conflicts or ["未发现互斥动作；仍执行单主世界、单拍单主动作和证据优先门禁。"],
        "rejected_candidates": rejected,
    }


def validate_result(result: dict[str, Any], catalog: dict[str, Any]) -> None:
    moves = result["resolved_move_ids"]
    if len(moves) != len(set(moves)):
        raise AssertionError("duplicate resolved moves")
    if not set(catalog["mandatory_dimensions"]).issubset(result["dimensions"]):
        raise AssertionError("mandatory decision dimensions missing")
    if len(result["overlay_recipes"]) > 2:
        raise AssertionError("too many overlay recipes")
    if result["signal_ids"]:
        selected_programs = {result["primary_program_id"], *result["supporting_program_ids"]}
        if len(result["supporting_program_ids"]) > 3:
            raise AssertionError("too many supporting programs")
        for signal_id in result["signal_ids"]:
            if not selected_programs.intersection(catalog["signal_feature_bridge"][signal_id]["programs"]):
                raise AssertionError(f"signal {signal_id} is not covered by the program route")


def run_self_test() -> None:
    catalog = load_catalog()
    cases = [
        {"primary_feature_tag": "QUOTE", "feature_tags": ["QUOTE", "DATA", "RELATION", "INVESTIGATION"]},
        {"primary_feature_tag": "UI", "feature_tags": ["UI", "PRODUCT", "LIVE_ACTION", "PROCESS"]},
        {"primary_feature_tag": "HISTORY", "feature_tags": ["HISTORY", "POLICY", "DATA", "LONGFORM", "DOCUMENT"]},
        {"primary_feature_tag": "MECHANISM", "feature_tags": ["MECHANISM", "CAUSE", "FAILURE", "PROCESS"]},
        {"primary_feature_tag": "PRODUCT", "feature_tags": ["PRODUCT", "HIGH_ENERGY", "HOOK", "LIVE_ACTION"]},
        {"primary_feature_tag": "ANNUAL", "feature_tags": ["ANNUAL", "RANKING", "DATA", "LONGFORM"]},
        {"primary_signal_id": "SG15", "signal_ids": ["SG15", "SG14", "SG07"]},
    ]
    summaries = []
    for index, case in enumerate(cases, start=1):
        first = compose(case, catalog)
        second = compose(case, catalog)
        if first != second:
            raise AssertionError(f"case {index} is not deterministic")
        validate_result(first, catalog)
        summaries.append(
            {
                "case": index,
                "primary": first["primary_recipe"]["id"],
                "overlays": [item["id"] for item in first["overlay_recipes"]],
                "moves": len(first["resolved_move_ids"]),
                "dimensions": len(first["dimensions"]),
            }
        )
    print(json.dumps({"status": "ok", "cases": summaries}, ensure_ascii=False, indent=2))


def validate_recipe_shapes(catalog: dict[str, Any]) -> None:
    recipes = catalog.get("recipes", [])
    if len(recipes) != 48:
        raise AssertionError(f"expected 48 recipes, got {len(recipes)}")
    required = {
        "id",
        "name",
        "role",
        "required_all",
        "required_any",
        "boost",
        "exclude",
        "required_moves",
        "optional_moves",
        "worlds",
        "state_sequence",
        "media_policy",
        "failure",
    }
    known_features = set(catalog["feature_tags"])
    seen: set[str] = set()
    for recipe in recipes:
        missing = required - set(recipe)
        if missing:
            raise AssertionError(f"recipe {recipe.get('id')} missing {sorted(missing)}")
        recipe_id = recipe["id"]
        if recipe_id in seen:
            raise AssertionError(f"duplicate recipe id {recipe_id}")
        seen.add(recipe_id)
        if recipe["role"] not in {"either", "overlay"}:
            raise AssertionError(f"recipe {recipe_id} has invalid role")
        recipe_features = set(recipe["required_all"] + recipe["required_any"] + recipe["boost"] + recipe["exclude"])
        if not recipe_features.issubset(known_features):
            raise AssertionError(f"recipe {recipe_id} references unknown features")
        moves = recipe["required_moves"] + recipe["optional_moves"]
        if any(not MOVE_ID.fullmatch(move) for move in moves):
            raise AssertionError(f"recipe {recipe_id} references invalid moves")


def run_exhaustive_test() -> None:
    catalog = load_catalog()
    validate_recipe_shapes(catalog)
    signal_ids = sorted(catalog["signal_feature_bridge"])
    selected_recipes: set[str] = set()
    move_counts: list[int] = []
    dimension_counts: list[int] = []
    valid_by_count = {count: 0 for count in range(1, 6)}
    rejected_by_count = {count: 0 for count in range(1, 6)}
    checked_routes = 0
    for primary in signal_ids:
        secondary_ids = [signal_id for signal_id in signal_ids if signal_id != primary]
        for secondary_count in range(5):
            signal_count = secondary_count + 1
            for secondary_group in combinations(secondary_ids, secondary_count):
                signals = [primary, *secondary_group]
                request = {"signal_ids": signals, "primary_signal_id": primary}
                checked_routes += 1
                try:
                    first = compose(request, catalog)
                    second = compose(request, catalog)
                except ValueError as exc:
                    if signal_count == 5 and "split the semantic segment" in str(exc):
                        rejected_by_count[signal_count] += 1
                        continue
                    raise AssertionError(f"signal route {signals} failed unexpectedly: {exc}") from exc
                if first != second:
                    raise AssertionError(f"signal route {signals} is not deterministic")
                validate_result(first, catalog)
                valid_by_count[signal_count] += 1
                selected_recipes.add(first["primary_recipe"]["id"])
                selected_recipes.update(item["id"] for item in first["overlay_recipes"])
                move_counts.append(len(first["resolved_move_ids"]))
                dimension_counts.append(len(first["dimensions"]))
    if any(rejected_by_count[count] for count in range(1, 5)):
        raise AssertionError(f"one-to-four signal routes must never exceed program capacity: {rejected_by_count}")
    anchors = sorted(
        {feature for recipe in catalog["recipes"] if recipe["role"] != "overlay" for feature in recipe["required_any"]}
    )
    recipe_routes: dict[str, dict[str, Any]] = {}
    for recipe in catalog["recipes"]:
        any_options = recipe["required_any"] or [None]
        variants: list[list[str]] = []
        for any_feature in any_options:
            base = unique(recipe["required_all"] + ([any_feature] if any_feature else []))
            variants.extend(unique(base + recipe["boost"][:count]) for count in range(len(recipe["boost"]) + 1))
            variants.append(unique(base + recipe["boost"]))
        anchor_options: list[str | None] = [None] if recipe["role"] != "overlay" else anchors
        for features in variants:
            for anchor in anchor_options:
                candidate_features = unique(([anchor] if anchor else []) + features)
                for primary in candidate_features:
                    try:
                        result = compose({"feature_tags": candidate_features, "primary_feature_tag": primary}, catalog)
                    except ValueError:
                        continue
                    chosen = [result["primary_recipe"]["id"]] + [item["id"] for item in result["overlay_recipes"]]
                    if recipe["id"] in chosen:
                        validate_result(result, catalog)
                        recipe_routes[recipe["id"]] = {"features": candidate_features, "primary": primary}
                        break
                if recipe["id"] in recipe_routes:
                    break
            if recipe["id"] in recipe_routes:
                break
    unreachable = sorted({recipe["id"] for recipe in catalog["recipes"]} - set(recipe_routes))
    if unreachable:
        raise AssertionError(f"unreachable recipes: {unreachable}")
    print(
        json.dumps(
            {
                "status": "ok",
                "recipe_shapes": len(catalog["recipes"]),
                "signal_routes_checked": checked_routes,
                "deterministic_routes": sum(valid_by_count.values()),
                "capacity_rejections": sum(rejected_by_count.values()),
                "valid_by_signal_count": valid_by_count,
                "rejected_by_signal_count": rejected_by_count,
                "selected_recipe_coverage": len(selected_recipes),
                "reachable_recipe_routes": len(recipe_routes),
                "move_count_range": [min(move_counts), max(move_counts)],
                "dimension_count_range": [min(dimension_counts), max(dimension_counts)],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose a deterministic documentary MG method stack.")
    parser.add_argument("input", nargs="?", help="JSON file containing feature_tags and primary_feature_tag")
    parser.add_argument("--features", help="Comma-separated feature tags")
    parser.add_argument("--primary", help="Primary feature tag; defaults to the first feature")
    parser.add_argument("--signals", help="Comma-separated SG01-SG24 semantic signal ids")
    parser.add_argument("--primary-signal", help="Primary signal id; defaults to the first signal")
    parser.add_argument("--max-overlays", type=int, default=2)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--exhaustive-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.self_test:
            run_self_test()
            return 0
        if args.exhaustive_test:
            run_exhaustive_test()
            return 0
        if args.input:
            raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
        elif args.features or args.signals:
            raw = {
                "feature_tags": args.features.split(",") if args.features else [],
                "primary_feature_tag": args.primary,
                "signal_ids": args.signals.split(",") if args.signals else [],
                "primary_signal_id": args.primary_signal,
                "max_overlays": args.max_overlays,
            }
        else:
            raise ValueError("provide an input JSON file, --features, --signals, --self-test, or --exhaustive-test")
        result = compose(raw)
        validate_result(result, load_catalog())
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, json.JSONDecodeError, TypeError, ValueError, AssertionError) as exc:
        print(f"method stack error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
