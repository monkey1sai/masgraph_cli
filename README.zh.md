<div align="center">
  <img
    src="docs/src/public/svg/logo-centered.svg#gh-light-mode-only"
    alt="MASFactory"
    width="620"
  />
  <img
    src="docs/src/public/svg/logo-dark-centered.svg#gh-dark-mode-only"
    alt="MASFactory"
    width="620"
  />
</div>
<p align="center">
    【<a href="README.md">English</a>   | Chinese】
</p>

## 📖 概述

**MASFactory** 是一个以图结构为核心的 Multi‑Agent Orchestration 框架，面向 **Vibe Graphing** 场景打造：从意图出发生成图结构设计，在可视化环境中预览与编辑迭代收敛，最终编译为可运行的工作流，并在运行时追踪节点状态、消息与共享状态变化。

在线文档：https://bupt-gamma.github.io/MASFactory/

核心能力：

- **Vibe Graphing（intent → graph）：** 从自然语言意图形成结构设计，并迭代收敛到可执行、可复用的工作流。
- **Graph 积木式搭建：** 以 `Node/Edge` 显式描述流程与字段契约，支持子图、循环、分支与复合组件。
- **可视化与可观测：** 配套 **MASFactory Visualizer** 提供拓扑预览、运行追踪与人机交互能力。
- **上下文协议（ContextBlock）：** 以结构化方式组织 Memory / RAG / MCP 等上下文源，支持自动注入与按需检索。

## ⚡ 快速开始

### 1) 安装 MASFactory（PyPI）

环境要求：Python `>= 3.10`

```bash
pip install -U masfactory
```

验证安装：

```bash
python -c "from importlib.metadata import version; print('masfactory version:', version('masfactory'))"
python -c "from masfactory import RootGraph, Graph, Loop, Agent, CustomNode; print('import ok')"
```

### 2) 安装 MASFactory Visualizer（VS Code 插件）

MASFactory Visualizer 用于图结构预览、运行追踪与人机交互。

从 VS Code 插件市场安装：

1. 打开 VS Code → Extensions（扩展）
2. 搜索：`MASFactory Visualizer`
3. 安装并 Reload

打开方式：
- 活动栏（左侧）→ **MASFactory Visualizer** → **Graph Preview**，或
- 命令面板：
  - `MASFactory Visualizer: Start Graph Preview`
  - `MASFactory Visualizer: Open Graph in Editor Tab`

## 🧩 简单示例（来自「第一行代码」）

最小两阶段 Agent 工作流：**ENTRY → analyze → answer → EXIT**。

```python
import os
from masfactory import RootGraph, Agent, OpenAIModel, NodeTemplate

model = OpenAIModel(
    api_key=os.getenv("OPENAI_API_KEY", ""),
    base_url=os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL") or None,
    model_name=os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
)

BaseAgent = NodeTemplate(Agent, model=model)

g = RootGraph(
    name="qa_two_stage",
    nodes=[
        ("analyze", BaseAgent(instructions="你是问题分析专家。", prompt_template="用户问题：{query}")),
        ("answer", BaseAgent(instructions="你是解决方案专家，基于分析给出最终回答。", prompt_template="问题：{query}\n分析：{analysis}")),
    ],
    edges=[
        ("entry", "analyze", {"query": "用户问题"}),
        ("analyze", "answer", {"query": "原始问题", "analysis": "分析结果"}),
        ("answer", "exit", {"answer": "最终回答"}),
    ],
)

g.build()
out, _attrs = g.invoke({"query": "我想学习 Python，但不知道从哪里开始"})
print(out["answer"])
```

## ▶️ 运行仓库内的多智能体复现（applications/）

多数工作流需要 `OPENAI_API_KEY`；部分脚本也会读取 `OPENAI_BASE_URL` / `BASE_URL` 与 `OPENAI_MODEL_NAME`。

```bash
# ChatDev
python -m applications.chatdev.workflow.main --task "Develop a basic Gomoku game." --name "Gomoku"

# ChatDev Lite（简化版）
python -m applications.chatdev_lite.workflow.main --task "Develop a basic Gomoku game." --name "Gomoku"

# ChatDev Lite（VibeGraphing 版本）
python -m applications.chatdev_lite_vibegraph.main --task "Write a Ping-Pong (Pong) game." --name "PingPong"

# VibeGraph Demo（intent → graph_design.json → compile → run）
python -m applications.vibegraph_demo.main

# AgentVerse · PythonCalculator
python applications/agentverse/tasksolving/pythoncalculator/run.py --task "write a simple calculator GUI using Python3."

# CAMEL role-playing demo
python applications/camel/main.py "Create a sample adder by using python"
```

## 📚 学习索引
在线文档地址：https://bupt-gamma.github.io/MASFactory/
- 快速入门：项目简介 → 安装 → Visualizer → 第一行代码
- 渐进式教程：ChatDev Lite（声明式 / 命令式 / VibeGraph）
- 开发指南：核心概念 → 消息传递 → NodeTemplate → Agent 运行机制 → 上下文接口（Memory/RAG/MCP）→ Visualizer → 模型适配器

## 🗂️ 项目目录结构

```
.
├── masfactory/                       # MASFactory 框架
│   ├── core/                         # 基础组件：Node / Edge / Gate / MessageFormatter
│   ├── components/                   # 关键功能组件
│   │   ├── agents/                   # Agent / DynamicAgent / SingleAgent
│   │   ├── controls/                 # LogicSwitch / AgentSwitch
│   │   ├── graphs/                   # Graph / RootGraph / Loop
│   │   ├── human/                    # Human-in-the-loop 节点
│   │   ├── composed_graph/           # 复合组件
│   │   └── vibe/                     # Vibe Graphing
│   ├── adapters/                     # Model / Memory / Retrieval / MCP 等适配器
│   ├── integrations/                 # 第三方集成接口 (MemoryOS / UltraRAG, etc.)
│   ├── utils/                        # Utilities (config, hook, Embedding, etc.)
│   └── visualizer/                   # MASFactory Visualizer 运行时通信桥
├── masfactory-visualizer/            # VS Code 插件 MASFactory Visualizer
├── applications/                     # 示例与复现应用
│   ├── chatdev/
│   ├── chatdev_lite/
│   ├── chatdev_lite_vibegraph/
│   ├── agentverse/
│   ├── camel/
│   ├── hugggpt2/
│   ├── metagpt/
│   └── vibegraph_demo/
├── docs/                             # VitePress 文档站
├── README.md
├── README.zh.md
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## 📄 引用

如果 MASFactory 对你的研究有帮助，欢迎引用：

```bibtex
@article{liu2026masfactory,
  title   = {MASFactory: A Graph-centric Framework for Orchestrating LLM-Based Multi-Agent Systems with Vibe Graphing},
  author  = {Yang Liu and Jinxuan Cai and Yishen Li and Qi Meng and Zedi Liu and Xin Li and Chen Qian and Chuan Shi and Cheng Yang},
  journal = {arXiv preprint arXiv:2603.06007},
  year    = {2026},
  doi     = {10.48550/arXiv.2603.06007},
  url     = {https://arxiv.org/abs/2603.06007}
}
```

## ⭐ Star 趋势

[![Star History Chart](https://api.star-history.com/svg?repos=BUPT-GAMMA/MASFactory&type=Date)](https://star-history.com/#BUPT-GAMMA/MASFactory&Date)
