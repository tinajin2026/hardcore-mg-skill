# Documentary MG Generator

**Turn written content into inspectable motion-graphics direction plans.**

[中文文档](README.md) · [Skill](SKILL.md) · [Showcase](examples/README.md)

An agent skill for planning motion graphics from Chinese or English content. It maps semantic relationships to directing methods, then specifies shots, micro-beats, visual layers, reading order, continuity, prompts, and draft API request bodies.

This is a planning and validation toolkit, not a video renderer. An AI assistant interprets the source text and authors the plan; the Python router operates on explicitly supplied signal IDs.

## Included

- 24 semantic signals and 24 structural programs.
- 48 execution recipes, 96 atomic directing moves, and 18 fusion rules.
- 12 micro-motion rules and 12 attention/reading rules.
- Structured `h3-mg-plan.v7` plans, directing templates, and deterministic validators.

The included adapter targets MiniMax H3 and plans 4–15 second segments. These are the package's stored conventions, not a claim of verified current API support. Live generation and API compatibility have not been tested for this release. Check the provider's current documentation before submitting requests.

## Getting Started

```bash
git clone https://github.com/tinajin2026/documentary-mg-generator.git
cd documentary-mg-generator
```

Place the entire directory in your assistant's supported skills location, or ask a file-capable assistant to read `SKILL.md`. Preserve the relative directory structure. The main skill and most reference materials are written in Chinese.

Example request:

```text
Read documentary-mg-generator/SKILL.md and use it to plan a 16:9
motion-graphics explanation. Plan only; do not call a video API.

Content: Rain falls onto a roof, flows through a gutter into a storage
barrel, and passes through a filter before being used for irrigation.

Do not invent performance claims or numbers. Produce the JSON plan,
directing board, and per-segment prompts, then validate the plan.
```

Python 3.10+ is required for the scripts. Routing and plan validation use the standard library. PyYAML is only needed for runtime-contract compilation/checking.

```bash
python3 scripts/compose_method_stack.py --signals SG15,SG14,SG07 --primary-signal SG15
python3 scripts/compose_method_stack.py --self-test
```

Once an assistant has produced a complete `plan.json`:

```bash
python3 scripts/validate_h3_mg_plan.py plan.json
```

Passing validation checks planning constraints, not the quality or existence of a rendered video. See the [Chinese README](README.md) for development checks and repository layout.

## Showcase and Scope

Demo videos are pending. No rendered examples are included in this initial release. Future authorized examples will pair source content, plans, actual video, and review notes in [examples/](examples/README.md).

The research-atlas rebuild script requires external research inputs that are not distributed here. Use the included distilled atlas for normal operation; the complete research dataset is not included for independent reproduction of its historical statistics.

No model weights, rendering engine, or generation-service client is included. Planning scripts do not make video-generation API calls. This independent project is not officially affiliated with MiniMax or other platforms.

## License

Code and method documentation are available under the [MIT License](LICENSE). External models, footage, music, fonts, and trademarks retain their respective rights. Contributions must not include secrets, private data, or unlicensed media; see [CONTRIBUTING.md](CONTRIBUTING.md).
