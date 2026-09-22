#!/usr/bin/env python3
"""
[INPUT]: 读取 hardcore-mg-skill 产出的 Markdown/YAML 项目合同、段落卡或执行 Prompt。
[OUTPUT]: 报告缺失结构、未替换占位符、底部旁白字幕指令和跨段接口错误，成功时退出码为 0。
[POS]: Skill 的确定性输出门禁，只校验合同和明确禁项，视觉质量仍需播放/逐帧复核。
[PROTOCOL]: 变更时更新此头部，然后检查 CLAUDE.md
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path


REQUIRED_MARKERS = [
    "Core Claim",
    "Initial State",
    "Timeline",
    "End State",
    "subtitle_mode: disabled",
    "bottom_caption: forbidden",
    "voiceover_transcript: forbidden",
]
PLACEHOLDER = re.compile(r"\{\{[^}]+\}\}|\b(?:TODO|TBD)\b", re.IGNORECASE)
PROHIBITED = [
    re.compile(r"subtitle_mode\s*:\s*(?:direct|enabled|burned_in)", re.IGNORECASE),
    re.compile(r"bottom_caption\s*:\s*(?:enabled|true|required)", re.IGNORECASE),
    re.compile(r"(?:生成|添加|显示).{0,8}(?:底部字幕|旁白字幕|逐字字幕)"),
]


def collect_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(item for item in path.rglob("*") if item.suffix.lower() in {".md", ".yaml", ".yml"})


def validate(path: Path, allow_template: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    if "Execution Prompt" in text or "### Core Claim" in text:
        for marker in REQUIRED_MARKERS:
            if marker not in text:
                errors.append(f"{path}: missing {marker}")
    if not allow_template and PLACEHOLDER.search(text):
        errors.append(f"{path}: contains unresolved placeholder")
    for pattern in PROHIBITED:
        match = pattern.search(text)
        if match:
            errors.append(f"{path}: prohibited text policy near {match.group(0)!r}")
    for line in text.splitlines():
        if "voiceover_transcript" not in line or ":" not in line:
            continue
        value = line.split(":", 1)[1].strip().lower()
        if value not in {"forbidden", "disabled", "none"}:
            errors.append(f"{path}: prohibited voiceover_transcript value {value!r}")
    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate documentary MG project outputs")
    parser.add_argument("path", type=Path)
    parser.add_argument("--allow-template", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    files = collect_files(args.path)
    if not files:
        raise SystemExit("FAIL: no Markdown/YAML files found")
    errors = [error for path in files for error in validate(path, args.allow_template)]
    if errors:
        raise SystemExit("FAIL:\n" + "\n".join(errors))
    print(f"PASS: validated {len(files)} file(s); no unresolved contract or forbidden subtitle directives")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
