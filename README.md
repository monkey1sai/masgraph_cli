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
    【English   | <a href="README.zh.md">Chinese</a>】
</p>

## 📖 Overview

**MASFactory** is a graph-centric framework for orchestrating Multi-Agent Systems with **Vibe Graphing**:
start from intent, generate a graph design, preview and refine it in a visual environment, compile it into an executable workflow, and trace node states, messages, and shared state at runtime.

Documentation: https://bupt-gamma.github.io/MASFactory/

Key capabilities:

- **Vibe Graphing (intent → graph):** turn natural-language intent into a structural design, then iteratively converge to an executable, reusable workflow.
- **Graph-style composition:** describe workflow and field contracts explicitly with `Node` / `Edge`; supports subgraphs, loops, branches, and composite components.
- **Visualization and observability:** **MASFactory Visualizer** provides topology preview, runtime tracing, and human-in-the-loop interaction.
- **Context protocol (`ContextBlock`):** organize Memory / RAG / MCP context sources in a structured way, with automatic injection and on-demand retrieval.

## ⚡ Quick Start

### 1) Install MASFactory (PyPI)

Requirements: Python `>= 3.10`

```bash
pip install -U masfactory
```

Verify installation:

```bash
python -c "from importlib.metadata import version; print('masfactory version:', version('masfactory'))"
python -c "from masfactory import RootGraph, Graph, Loop, Agent, CustomNode; print('import ok')"
```

### 2) Install MASFactory Visualizer (VS Code Extension)

MASFactory Visualizer is used for graph preview, runtime tracing, and human-in-the-loop interaction.

Install from the VS Code Marketplace:

1. Open VS Code → Extensions
2. Search for `MASFactory Visualizer`
3. Install and reload

Open it via:
- Activity Bar → **MASFactory Visualizer** → **Graph Preview**, or
- Command Palette:
  - `MASFactory Visualizer: Start Graph Preview`
  - `MASFactory Visualizer: Open Graph in Editor Tab`

## 🧩 Simple Example (from "First Code")

A minimal two-stage agent workflow: **ENTRY → analyze → answer → EXIT**.

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
        ("analyze", BaseAgent(instructions="You are a problem analysis expert.", prompt_template="User question: {query}")),
        ("answer", BaseAgent(instructions="You are a solution expert. Provide the final answer based on the analysis.", prompt_template="Question: {query}\nAnalysis: {analysis}")),
    ],
    edges=[
        ("entry", "analyze", {"query": "User question"}),
        ("analyze", "answer", {"query": "Original question", "analysis": "Analysis result"}),
        ("answer", "exit", {"answer": "Final answer"}),
    ],
)

g.build()
out, _attrs = g.invoke({"query": "I want to learn Python. Where should I start?"})
print(out["answer"])
```

## ▶️ Run the Multi-Agent Reproductions in This Repo (`applications/`)

Most workflows require `OPENAI_API_KEY`. Some scripts also read `OPENAI_BASE_URL` / `BASE_URL` and `OPENAI_MODEL_NAME`.

```bash
# ChatDev
python -m applications.chatdev.workflow.main --task "Develop a basic Gomoku game." --name "Gomoku"

# ChatDev Lite (simplified)
python -m applications.chatdev_lite.workflow.main --task "Develop a basic Gomoku game." --name "Gomoku"

# ChatDev Lite (VibeGraphing version)
python -m applications.chatdev_lite_vibegraph.main --task "Write a Ping-Pong (Pong) game." --name "PingPong"

# VibeGraph Demo (intent → graph_design.json → compile → run)
python -m applications.vibegraph_demo.main

# AgentVerse · PythonCalculator
python applications/agentverse/tasksolving/pythoncalculator/run.py --task "write a simple calculator GUI using Python3."

# CAMEL role-playing demo
python applications/camel/main.py "Create a sample adder by using python"
```

## 📚 Learning Index

Documentation: https://bupt-gamma.github.io/MASFactory/

- Quick Start: Introduction → Installation → Visualizer → First Code
- Progressive Tutorials: ChatDev Lite (Declarative / Imperative / VibeGraph)
- Development Guide: Core Concepts → Message Passing → NodeTemplate → Agent Runtime → Context Adapters (Memory / RAG / MCP) → Visualizer → Model Adapters

## 🗂️ Project Structure

```text
.
├── masfactory/                       # MASFactory framework
│   ├── core/                         # Core primitives: Node / Edge / Gate / MessageFormatter
│   ├── components/                   # Main workflow components
│   │   ├── agents/                   # Agent / DynamicAgent / SingleAgent
│   │   ├── controls/                 # LogicSwitch / AgentSwitch
│   │   ├── graphs/                   # Graph / RootGraph / Loop
│   │   ├── human/                    # Human-in-the-loop nodes
│   │   ├── composed_graph/           # Composite components
│   │   └── vibe/                     # Vibe Graphing
│   ├── adapters/                     # Model / Memory / Retrieval / MCP adapters
│   ├── integrations/                 # Third-party integrations
│   ├── utils/                        # Utilities
│   └── visualizer/                   # Runtime bridge for MASFactory Visualizer
├── masfactory-visualizer/            # VS Code extension: MASFactory Visualizer
├── applications/                     # Example and reproduction apps
│   ├── chatdev/
│   ├── chatdev_lite/
│   ├── chatdev_lite_vibegraph/
│   ├── agentverse/
│   ├── camel/
│   ├── hugggpt2/
│   ├── metagpt/
│   └── vibegraph_demo/
├── docs/                             # VitePress documentation site
├── README.md
├── README.zh.md
├── pyproject.toml
├── requirements.txt
└── uv.lock
```

## 📄 Citation

If you use MASFactory in your research, please cite:

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

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=BUPT-GAMMA/MASFactory&type=Date)](https://star-history.com/#BUPT-GAMMA/MASFactory&Date)
