# 硬核的 MG Skill

**把文字内容转成可审查、可执行的 MG 动态图形导演方案。**

[English](README.en.md) · [Skill 入口](SKILL.md) · [效果展示](examples/README.md) · [贡献指南](CONTRIBUTING.md)

硬核的 MG Skill 是一个面向 AI 编程助手和创作助手的 Skill。它从中文或英文稿件中识别比较、因果、机制、证据、流程等关系，将这些关系组织成导演方法栈，再输出分镜、微时间拍、画面层级、提示词和请求体草案。

它不是视频渲染器，也不是简单的提示词合集。核心工作是回答：**这段内容应该让观众看到什么、先看什么、变化如何发生，以及什么必须保持不变。**

当前包围绕 MiniMax H3 编排输出，方案格式为 `h3-mg-plan.v7`。模型名称、时长和接口字段属于本版本的适配约定，实际调用前需要重新核对服务商文档。本仓库未进行在线视频生成或 API 兼容性验证。

## 能做什么

- **从语义出发设计画面**：先明确主张、证据和观众问题，再选择视觉表达，不把「增长」机械替换成箭头。
- **组合导演方法**：24 类语义信号、24 套结构程序、48 套执行配方、96 条原子动作，配合 18 条融合规则。
- **细化动作与阅读节奏**：12 条微运动规则和 12 条注意阅读规则，约束起势、响应、制动、停留与焦点交接。
- **保持视觉连续性**：登记主体、画面五层、元素生命周期和跨段状态，减少逐镜重新设计造成的割裂。
- **提供可检查的交付物**：JSON 方案、Markdown 导演板、逐段原生 Prompt、API 请求体草案和校验脚本。

适合产品演示、科普解释、数据叙事、品牌短片、字体动画和实拍与 MG 混合内容的前期策划。当前 Skill 将内容拆成每段 4–15 秒的规划单元；长稿按完整语义继续拆分。

## 工作流程

```text
原文与可选素材
  -> 语义分段与事实锁定
  -> 信号识别与方法路由
  -> 视觉系统与连续性设计
  -> 逐镜、微时间拍与阅读路径
  -> JSON 方案 + 导演板 + Prompt + 请求体草案
  -> 本地校验
  -> 外部生成与人工复核
```

最后一步需要自行接入视频生成服务。本仓库不包含模型权重、生成服务客户端或视频渲染引擎；仅使用规划与校验脚本不会调用视频生成 API。

## 快速开始

### 1. 获取 Skill

```bash
git clone https://github.com/tinajin2026/hardcore-mg-skill.git
cd hardcore-mg-skill
```

将整个仓库目录放入所用助手支持的 Skill 目录，保留 `SKILL.md`、`references/`、`schemas/`、`scripts/` 和 `templates/` 的相对位置。不同助手的安装入口不同；也可以直接让有文件读取能力的助手读取本仓库的 `SKILL.md`。

### 2. 提供内容

示例请求：

```text
请读取 hardcore-mg-skill/SKILL.md，使用这个 Skill 为下面的内容
制作 MG 导演方案。先只做策划，不调用视频生成 API。

内容：雨水落到屋顶，沿排水槽进入储水桶，再经过过滤装置用于浇灌。

要求：16:9，以机制解释为主，不添加原文没有提供的数据或功效，
输出 JSON 方案、Markdown 导演板和逐段 Prompt，并运行方案校验。
```

这是输入示例，不是已经渲染的效果案例。最小输入只需正文；也可以补充目标时长、画幅、参考素材以及必须原样保留的画面文字。

### 3. 运行方法路由

Python 3.10 或更高版本。方法路由和方案校验使用 Python 标准库；重建或检查 YAML 到 JSON 的运行时合同另需 PyYAML。

```bash
python3 scripts/compose_method_stack.py \
  --signals SG15,SG14,SG07 \
  --primary-signal SG15
```

此命令将已标注的信号转为确定性方法栈，不会自动理解原文，也不会生成完整导演方案。原文理解和方案撰写由使用此 Skill 的 AI 助手完成。

### 4. 校验方案

把助手生成的完整 JSON 方案命名为 `plan.json`，在仓库根目录运行：

```bash
python3 scripts/validate_h3_mg_plan.py plan.json
```

校验器检查方法绑定、时间轴、微运动、阅读路径、连续性和请求约定等规则。通过校验不代表视频已经生成，也不保证模型的最终视觉质量。`validate_output.py` 用于旧版 Markdown 交付格式，不替代 H3 JSON 方案校验。

## 效果展示

**演示视频待补充。** 首次开源仅包含 Skill、方法库、模板和脚本，没有上传效果视频，也没有用其他作品代替本项目的实际输出。

后续案例统一收录在 [examples/](examples/README.md)，以「输入内容 → 导演方案 → 实际视频 → 复核说明」呈现，便于理解方法与结果的关系。

## 仓库结构

| 路径 | 内容 |
| --- | --- |
| `SKILL.md` | 主工作流、触发条件和输出约定 |
| `agents/` | 助手展示配置 |
| `references/` | 方法库、触发矩阵、动作目录和质量规则 |
| `schemas/` | JSON 与 YAML 方案结构 |
| `templates/` | 执行提示词和差量复核模板 |
| `scripts/` | 路由、合同编译和方案校验工具 |
| `examples/` | 效果案例入口，视频待补充 |

## 开发与验证

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/compose_method_stack.py --self-test
python scripts/build_method_runtime_contract.py --check
python -m compileall -q scripts
```

完整路由穷举检查单独运行，耗时长于快速自测：

```bash
python scripts/compose_method_stack.py --exhaustive-test
```

`build_xpc_300_atlas.py` 是研究资料重建工具，需要额外提供目录、分析记录与证据文件。原始研究视频和逐镜资料不随仓库发布；日常使用直接读取已包含的模式图谱，不需要重建研究数据。图谱中的研究规模与统计属于随包方法文档的记录，不表示本仓库附带可独立复现的完整研究数据集。

## 边界与许可

- 不将缺失信息、文件名或上游描述伪装成已观察到的画面事实。
- 不在仓库、Prompt 或请求体中写入 API Key；实际生成的费用与服务条款由对应服务商决定。
- 项目独立维护，与 MiniMax 或其他平台不存在官方隶属或背书关系。
- 仓库代码与方法文档采用 [MIT License](LICENSE)。外部模型、品牌、字体、音乐和视频素材的权利不因本仓库开源而转移；展示案例应单独注明来源与授权。

欢迎通过 Issues 提交问题，通过 Pull Requests 改进方法、校验规则和已获授权的案例。提交前请阅读 [贡献指南](CONTRIBUTING.md)。
