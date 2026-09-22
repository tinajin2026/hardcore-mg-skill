#!/usr/bin/env python3
"""
[INPUT]: 读取 references/method-trigger-lattice.yaml 的信号、程序与融合规则。
[OUTPUT]: 确定性生成或核对 references/method-runtime-contract.json，供纯标准库验证器读取。
[POS]: documentary-mg-generator 的方法路由合同编译器，隔离 YAML 构建依赖与运行时校验依赖。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


SKILL_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LATTICE = SKILL_ROOT / "references/method-trigger-lattice.yaml"
DEFAULT_OUTPUT = SKILL_ROOT / "references/method-runtime-contract.json"


def compile_contract(lattice: dict[str, Any]) -> dict[str, Any]:
    signals = lattice.get("signals", [])
    programs = lattice.get("programs", [])
    fusion_rules = lattice.get("fusion_rules", [])
    signal_ids = {f"SG{index:02d}" for index in range(1, 25)}
    program_ids = {f"DP{index:02d}" for index in range(1, 25)}
    if {item.get("id") for item in signals} != signal_ids:
        raise ValueError("lattice must define exactly SG01-SG24")
    if {item.get("id") for item in programs} != program_ids:
        raise ValueError("lattice must define exactly DP01-DP24")
    if {item.get("id") for item in fusion_rules} != {f"FR{index:02d}" for index in range(1, 19)}:
        raise ValueError("lattice must define exactly FR01-FR18")

    signal_contracts = {
        item["id"]: {
            "candidate_programs": item["candidate_programs"],
            "recipe_features": item["recipe_features"],
            "forced_moves": item["forced_moves"],
        }
        for item in signals
    }
    program_contracts = {
        item["id"]: {
            "spine": item["spine"],
            "fit": item["fit"],
            "support": item["support"],
        }
        for item in programs
    }
    for signal_id, signal in signal_contracts.items():
        for program_id in signal["candidate_programs"]:
            if signal_id not in program_contracts[program_id]["fit"]:
                raise ValueError(f"{signal_id} -> {program_id} is not mirrored by program.fit")
    for program_id, program in program_contracts.items():
        for signal_id in program["fit"]:
            if program_id not in signal_contracts[signal_id]["candidate_programs"]:
                raise ValueError(f"{program_id} -> {signal_id} is not mirrored by signal candidates")

    return {
        "version": "method-runtime-contract.v1",
        "_contract": {
            "[INPUT]": "由去来源化方法触发矩阵确定性编译，不包含原片身份或原片时间码。",
            "[OUTPUT]": "向 H3 方法栈验证器提供信号强制动作、程序 spine、双向适配与融合规则。",
            "[POS]": "方法触发矩阵的运行时只读镜像；YAML 是编辑真源，本文件由脚本重建。",
            "[PROTOCOL]": "变更时更新此头部，然后检查 CLAUDE.md",
        },
        "signal_contracts": signal_contracts,
        "program_contracts": program_contracts,
        "fusion_rules": fusion_rules,
    }


def render(contract: dict[str, Any]) -> str:
    return json.dumps(contract, ensure_ascii=False, separators=(",", ":")) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compile the source-blind MG method runtime contract.")
    parser.add_argument("--lattice", type=Path, default=DEFAULT_LATTICE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        lattice = yaml.safe_load(args.lattice.read_text(encoding="utf-8"))
        expected = render(compile_contract(lattice))
        if args.check:
            if not args.output.exists() or args.output.read_text(encoding="utf-8") != expected:
                raise ValueError("runtime contract is stale; rebuild it without --check")
            print("METHOD_CONTRACT_VALID signals=24 programs=24 fusion_rules=18")
            return 0
        args.output.write_text(expected, encoding="utf-8")
        print(f"METHOD_CONTRACT_WRITTEN {args.output}")
        return 0
    except (OSError, TypeError, ValueError, yaml.YAMLError) as exc:
        print(f"method contract error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
