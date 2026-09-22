#!/usr/bin/env python3
"""
[INPUT]: 依赖 XPC 目录/替换目录 JSONL、逐镜分析 JSON 与 final 时间轴 JSON。
[OUTPUT]: 对外提供不含题名、媒体 ID、时间码、指纹、原帧或逐镜原文的 MG 状态语法图谱，并打印外部审计数量摘要。
[POS]: hardcore-mg-skill 的证据编译器，把研究项目转换为无来源依赖的节奏、类别路由和组合责任。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


CATEGORY_BLUEPRINTS = {
    "信息图表与数据解释": {
        "pattern_id": "XPC-DATA-BASELINE-DELTA",
        "timeline": "0.0–2.0s 对象/单位与基线；2.0–6.0s 比较对象同尺度进入；6.0–10.5s 差值或趋势只动一个变量；10.5–13.0s 结论印章；13.0–15.0s 稳定读数并保留下一段锚。",
        "layers": "背景坐标层、基准层、比较层、数据标签层、结论层；高密度时相机固定。",
        "avoid": "没有单位的数字、同时增长多组数据、结论刚出现就切走。",
    },
    "品牌叙事与企业传播": {
        "pattern_id": "XPC-BRAND-MOTIF-PROOF-LOCKUP",
        "timeline": "0.0–2.0s 品牌母题或核心矛盾；2.0–5.0s 母题转为价值动作；5.0–10.0s 产品/现场/证据接力；10.0–13.0s 回收核心判断；13.0–15.0s 原创标识或品牌落版稳定。",
        "layers": "持久母题层、真实证据窗口、价值文字层、产品/人物层、落版层。",
        "avoid": "只做氛围不证明价值、连续口号轰炸、未经授权复刻 Logo。",
    },
    "产品功能与UI演示": {
        "pattern_id": "XPC-UI-ANCHOR-ACTION-RESULT",
        "timeline": "0.0–2.0s 锁定产品/UI 入口；2.0–5.0s 用户动作或输入；5.0–9.0s 界面状态增量变化；9.0–12.5s 输出/收益可见；12.5–15.0s 回到产品身份和下一功能入口。",
        "layers": "设备/窗口身份层、真实 UI 层、交互焦点层、结果层、品牌/下一步层。",
        "avoid": "重画清晰真实 UI、整屏同时动、功能结果没有因果输入。",
    },
    "角色IP与剧情叙事": {
        "pattern_id": "XPC-CHARACTER-GOAL-REACTION",
        "timeline": "0.0–2.5s 角色、目标和空间关系；2.5–6.0s 单一动作启动；6.0–9.5s 环境/道具晚半拍反馈；9.5–12.5s 表情或姿态反应；12.5–15.0s 后果定格或动作钩子。",
        "layers": "场景层、角色身份层、目标道具层、动作反馈层、对白/标签层。",
        "avoid": "角色无目标地漂浮、嘴型与对白无约束、同一镜头新增无来源角色。",
    },
    "科普知识与公共传播": {
        "pattern_id": "XPC-EXPLAIN-OVERVIEW-MECHANISM-RETURN",
        "timeline": "0.0–2.0s 问题/现象；2.0–4.5s 系统总览；4.5–9.5s 放大唯一局部并演示机制；9.5–12.5s 结果/风险；12.5–15.0s 回装全局并落下可记忆结论。",
        "layers": "现象层、系统总览层、局部机制层、路径/因果层、结论层。",
        "avoid": "逐句配图、机制拆开后不回装、解释性重建伪装成真实史料。",
    },
    "字体图形与抽象实验": {
        "pattern_id": "XPC-TYPE-SHAPE-SEMANTIC-HIT",
        "timeline": "0.0–1.5s 几何/字体基元建立；1.5–5.0s 一次主形变；5.0–8.5s 形态匹配进入第二语义；8.5–12.0s 文字命中并可读；12.0–15.0s 图形回收为稳定标记。",
        "layers": "底色/网格层、几何基元层、字形层、遮罩层、最终标记层。",
        "avoid": "无语义变形、每秒换字体、故障/粒子/扫描并发。",
    },
    "三维与混合媒介": {
        "pattern_id": "XPC-3D-HERO-MATERIAL-HANDOFF",
        "timeline": "0.0–2.5s 英雄对象与材质光源锁定；2.5–6.0s 绕行/剖分二选一；6.0–9.5s 部件或媒介匹配接力；9.5–12.5s 功能/场景结果；12.5–15.0s 回到英雄角度与材质状态。",
        "layers": "环境/反射层、英雄对象层、结构/部件层、混合媒介窗口、文字/落版层。",
        "avoid": "镜头和对象同时大幅旋转、材质跨镜漂移、分解后不回到同一对象。",
    },
    "活动包装与片头视觉": {
        "pattern_id": "XPC-TITLE-HOOK-MOTIF-LOCKUP",
        "timeline": "0.0–1.5s 单一高能钩子；1.5–4.0s 主题母题建立；4.0–8.5s 2–3 次同语法变奏；8.5–12.0s 活动/节目文字命中；12.0–15.0s 日期、主题或片名稳定落版。",
        "layers": "背景能量层、主题母题层、素材窗口层、标题层、活动信息层。",
        "avoid": "每个变奏换一套转场、落版不足一秒、标题与主体同时抢焦点。",
    },
}


TRANSITION_FAMILIES = {
    "hard_cut": re.compile(r"硬切"),
    "morph_or_match": re.compile(r"形态|匹配"),
    "directional_continuity": re.compile(r"方向|连续|延续"),
    "mask_or_wipe": re.compile(r"遮罩|擦除|擦拭|扫屏|覆盖"),
    "fade_or_field_reset": re.compile(r"淡入|淡出|黑场|白场"),
    "zoom_or_portal": re.compile(r"推近|推进|拉远|缩放|穿越"),
    "slot_replace": re.compile(r"替换|切换|置换"),
}


MOTION_PRIMITIVES = {
    "reveal": re.compile(r"出现|显现|进入|浮现|展开|亮起"),
    "replace": re.compile(r"替换|切换|变化|转为|变成"),
    "align": re.compile(r"对齐|并列|排列"),
    "stack": re.compile(r"叠加|堆叠|层叠"),
    "connect": re.compile(r"连接|连线|关联"),
    "propagate": re.compile(r"流动|传播|延伸|沿着|沿路径"),
    "isolate": re.compile(r"突出|高亮|聚焦|强调"),
    "magnify": re.compile(r"放大|推近|局部"),
    "decompose": re.compile(r"分解|拆解|拆分|剖面"),
    "reassemble": re.compile(r"回装|重组|合并|汇聚"),
    "count": re.compile(r"数字|递增|计数|增长"),
    "clear": re.compile(r"清场|退场|消失|淡出|移出"),
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    # 只按 ASCII LF 分隔，保留 JSON 字符串内合法的 U+2028/U+2029。
    return [json.loads(line) for line in path.read_text(encoding="utf-8").split("\n") if line.strip()]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def manifest_hash(paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda item: item.name):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = (len(ordered) - 1) * quantile
    low = math.floor(index)
    high = math.ceil(index)
    if low == high:
        return ordered[low]
    return ordered[low] * (high - index) + ordered[high] * (index - low)


def canonical_scale(value: str) -> str:
    if re.search(r"界面|屏幕|录屏|网页", value):
        return "interface_or_screen"
    if re.search(r"图形|图表|信息图", value):
        return "graphic"
    if re.search(r"特写|近景", value):
        return "close"
    if re.search(r"大全景|全景|远景", value):
        return "wide"
    if re.search(r"中景|中近景|中远景", value):
        return "medium"
    return "other"


def find_record(stem: str, records: list[dict[str, Any]]) -> dict[str, Any] | None:
    for record in records:
        if stem == record.get("storyboard_name") or stem.endswith("_" + str(record.get("media_id", ""))):
            return record
    return None


def infer_tier(record: dict[str, Any], final: dict[str, Any]) -> str:
    tier = record.get("evidence_tier")
    if tier in {"A", "B"}:
        return tier
    return "A" if final.get("segmentation", {}).get("algorithm") == "mg-hybrid-v2" else "B"


def build_dataset(args: argparse.Namespace) -> dict[str, Any]:
    records = load_jsonl(args.catalog) + load_jsonl(args.replacement_catalog)
    analysis_paths = sorted(args.analysis_dir.glob("*.json"))
    final_paths = sorted(args.finals_dir.glob("*.final.json"))
    finals = {path.name.removesuffix(".final.json"): path for path in final_paths}
    items = []
    transition_counts = Counter()
    motion_counts = Counter()
    scale_counts = Counter()

    for analysis_path in analysis_paths:
        stem = analysis_path.stem
        record = find_record(stem, records)
        if record is None:
            raise ValueError(f"no catalog record for {stem}")
        final_path = finals.get(stem)
        if final_path is None:
            raise ValueError(f"no final timeline for {stem}")
        analysis = json.loads(analysis_path.read_text(encoding="utf-8"))
        final = json.loads(final_path.read_text(encoding="utf-8"))
        rows = final.get("rows", [])
        shots = analysis.get("shots", {})
        if len(rows) != len(shots):
            raise ValueError(f"shot mismatch for {stem}: {len(rows)} rows != {len(shots)} analyses")
        tier = infer_tier(record, final)
        durations = [float(row["时长"]) for row in rows]
        video_duration = float(final.get("video", {}).get("duration") or sum(durations))
        items.append(
            {
                "media_id": record["media_id"],
                "title": record["title"],
                "category": record["primary_category"],
                "tier": tier,
                "duration": video_duration,
                "shot_count": len(rows),
                "shot_durations": durations,
            }
        )
        for shot in shots.values():
            scale_counts[canonical_scale(str(shot.get("景别", "")))] += 1
            transition = str(shot.get("剪辑衔接", ""))
            action = " ".join(
                str(shot.get(field, ""))
                for field in ("主体与动作", "剪辑衔接", "与前镜关系", "节奏感")
            )
            for name, pattern in TRANSITION_FAMILIES.items():
                if pattern.search(transition):
                    transition_counts[name] += 1
            for name, pattern in MOTION_PRIMITIVES.items():
                if pattern.search(action):
                    motion_counts[name] += 1

    if len(items) != args.expected:
        raise ValueError(f"expected {args.expected} detailed items, got {len(items)}")
    categories = sorted({item["category"] for item in items})
    if set(categories) != set(CATEGORY_BLUEPRINTS):
        raise ValueError(f"category mismatch: {categories}")
    tier_counts = Counter(item["tier"] for item in items)
    shot_count = sum(item["shot_count"] for item in items)
    if tier_counts != Counter({"A": 89, "B": 211}):
        raise ValueError(f"tier mismatch: {dict(tier_counts)}")
    if shot_count != 6902:
        raise ValueError(f"shot mismatch: {shot_count}")

    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_category[item["category"]].append(item)
    category_stats = {}
    for category, category_items in by_category.items():
        tier_a = [item for item in category_items if item["tier"] == "A"]
        shot_durations = [duration for item in tier_a for duration in item["shot_durations"]]
        density = [item["shot_count"] / (item["duration"] / 15.0) for item in tier_a]
        representatives = sorted(
            category_items,
            key=lambda item: (item["tier"] != "A", -item["shot_count"], item["media_id"]),
        )[:3]
        category_stats[category] = {
            "sample_count": len(category_items),
            "tier_a": len(tier_a),
            "tier_b": len(category_items) - len(tier_a),
            "shot_seconds_p25": percentile(shot_durations, 0.25),
            "shot_seconds_p50": percentile(shot_durations, 0.50),
            "shot_seconds_p75": percentile(shot_durations, 0.75),
            "shots_per_15s_p50": percentile(density, 0.50),
            "representatives": representatives,
        }

    all_a_durations = [duration for item in items if item["tier"] == "A" for duration in item["shot_durations"]]
    all_a_density = [item["shot_count"] / (item["duration"] / 15.0) for item in items if item["tier"] == "A"]
    return {
        "items": items,
        "sample_count": len(items),
        "shot_count": shot_count,
        "category_count": len(categories),
        "tier_counts": tier_counts,
        "category_stats": category_stats,
        "scale_counts": scale_counts,
        "transition_counts": transition_counts,
        "motion_counts": motion_counts,
        "overall_timing": {
            "shot_seconds_p25": percentile(all_a_durations, 0.25),
            "shot_seconds_p50": percentile(all_a_durations, 0.50),
            "shot_seconds_p75": percentile(all_a_durations, 0.75),
            "shots_per_15s_p25": percentile(all_a_density, 0.25),
            "shots_per_15s_p50": percentile(all_a_density, 0.50),
            "shots_per_15s_p75": percentile(all_a_density, 0.75),
        },
        "fingerprints": {
            "catalog_sha256": sha256_file(args.catalog),
            "replacement_catalog_sha256": sha256_file(args.replacement_catalog),
            "analysis_manifest_sha256": manifest_hash(analysis_paths),
            "finals_manifest_sha256": manifest_hash(final_paths),
        },
    }


def render_markdown(dataset: dict[str, Any]) -> str:
    route_roles = {
        "信息图表与数据解释": ("建立基线、只改变一个变量、形成可核对结论", "可作为产品/流程/比较程序的 payoff 数据层"),
        "品牌叙事与企业传播": ("用持久母题连接价值动作、事实证明和记忆落版", "可吸收产品、人物或证据，但不能替代证明"),
        "产品功能与UI演示": ("锁定产品入口，展示输入、状态变化和使用结果", "可组合机制剖面与数据结果，产品身份始终优先"),
        "角色IP与剧情叙事": ("建立目标、动作、环境反馈、反应和后果", "可组合风险或品牌母题，不能让包装夺走角色主线"),
        "科普知识与公共传播": ("从现象进入系统局部，解释机制并回装结论", "可组合因果、数据或风险，解释责任优先"),
        "字体图形与抽象实验": ("让字形/几何的状态变化直接等于语义变化", "只适合作为主命题或转场语法，不覆盖事实证据"),
        "三维与混合媒介": ("锁定英雄对象和材质，以拆解或媒介接力证明功能", "可承载产品、机制和活动包装，必须回到对象身份"),
        "活动包装与片头视觉": ("以单一钩子和母题变奏形成标题记忆", "只在 HOOK/章节/落版承担高能，不移植到解释主体"),
    }
    lines = [
        "# 八类 MG 状态语法",
        "",
        "## 养料边界",
        "",
        "本图谱只保留从大规模分镜研究中蒸馏出的状态顺序、图层责任、节奏预算和否决项。运行时不需要也不得检索原片题名、媒体 ID、案例编号、时间码或来源指纹。",
        "",
        "八类语法不是八种固定风格。它们是认知任务的段落骨架，具体画面由当前稿件触发的信号、复合程序和原子动作共同生成。",
        "",
        "## 节奏预算",
        "",
        "- 4–7 秒：1–2 镜、3–5 微拍，主程序闭合，不超过一个辅助程序。",
        "- 8–11 秒：2–3 镜、4–7 微拍，允许两个辅助责任但仍只有一个主动作链。",
        "- 12–15 秒：3–5 镜、5–9 微拍，最多三个辅助程序，并保留 0.8–2.0 秒 landing。",
        "- 高密度机制、关系和数据减少镜头、增加固定坐标内的微更新；高能包装才接近镜头上限。",
        "",
        "## 八类路由",
        "",
        "| 类别 | Pattern ID | 核心认知责任 | 作为辅助时的边界 |",
        "|---|---|---|---|",
    ]
    for category, blueprint in CATEGORY_BLUEPRINTS.items():
        responsibility, support_boundary = route_roles[category]
        lines.append(f"| {category} | `{blueprint['pattern_id']}` | {responsibility} | {support_boundary} |")
    lines.append("")
    for category, blueprint in CATEGORY_BLUEPRINTS.items():
        responsibility, support_boundary = route_roles[category]
        lines.extend(
            [
                f"### {category} | `{blueprint['pattern_id']}`",
                "",
                f"- 认知责任：{responsibility}。",
                f"- 15 秒状态骨架：{blueprint['timeline']}",
                f"- 图层责任：{blueprint['layers']}",
                f"- 组合边界：{support_boundary}。",
                f"- 否决项：{blueprint['avoid']}",
                "",
            ]
        )
    lines.extend(
        [
            "## 组合规则",
            "",
            "1. 每段只选择一个主 Pattern ID，它决定 opening 到 landing 的宏观状态顺序。",
            "2. 次 Pattern ID 最多一个，只能增强局部图层或阶段，不能带入第二套主世界。",
            "3. 具体的多维组合由 `method-trigger-lattice.yaml` 决定；Pattern ID 不替代语义信号和方法职责图。",
            "4. 每个微拍只有一个主动作，辅助反馈延后启动并在下一信息进入前制动。",
            "5. 文字、数据、证据、产品和角色谁承担核心判断，谁才是第一阅读；其他全部降级。",
            "6. Prompt 写当前主体、坐标、状态和动作，不写 Pattern ID、程序 ID、样片身份或研究统计。",
            "",
        ]
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an aggregate MG pattern atlas from XPC detailed evidence")
    parser.add_argument("--catalog", type=Path, required=True)
    parser.add_argument("--replacement-catalog", type=Path, required=True)
    parser.add_argument("--analysis-dir", type=Path, required=True)
    parser.add_argument("--finals-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--expected", type=int, default=300)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset = build_dataset(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_markdown(dataset), encoding="utf-8")
    print(
        "ATLAS_VALID "
        f"samples={dataset['sample_count']} shots={dataset['shot_count']} "
        f"categories={dataset['category_count']} tier_a={dataset['tier_counts']['A']} tier_b={dataset['tier_counts']['B']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
