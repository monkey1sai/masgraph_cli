from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from masfactory import ClaudeCliModel, OpenAIModel, RootGraph, VibeGraph
from applications.chatdev_lite.chatdev.codes import Codes
from applications.chatdev_lite.chatdev.documents import Documents
from applications.chatdev_lite.components.tools import (
    RuntimeContext,
    check_code_completeness_tool,
    codes_check_and_processing_tool,
    run_tests_tool,
    set_runtime,
)


parser = argparse.ArgumentParser(description="VibeGraph Demo")
parser.add_argument("--provider", type=str, default="openai", choices=["openai", "claude-cli"], help="Model provider backend")
parser.add_argument("--model", type=str, default=None, help="Invoke model name. Defaults to gpt-4o-mini for OpenAI and sonnet for claude-cli")
parser.add_argument("--api_key", type=str, default=None, help="OpenAI API key")
parser.add_argument("--base_url", type=str, default=None, help="OpenAI API base URL")
parser.add_argument("--build_model", type=str, default=None, help="Build model name (defaults to --model)")
parser.add_argument("--build_api_key", type=str, default=None, help="Build model API key (defaults to --api_key)")
parser.add_argument("--build_base_url", type=str, default=None, help="Build model base URL (defaults to --base_url)")
parser.add_argument("--cli-command", type=str, default="claude", help="Claude Code CLI executable path when provider=claude-cli")
parser.add_argument("--cli-timeout", type=int, default=900, help="Claude CLI timeout in seconds when provider=claude-cli")
args = parser.parse_args()

base_url = args.base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")

if args.provider == "claude-cli":
    model_name = args.model or os.getenv("CLAUDE_MODEL") or "sonnet"
    build_model_name = args.build_model or model_name
    model = ClaudeCliModel(
        model_name=model_name,
        cli_command=args.cli_command,
        timeout_seconds=args.cli_timeout,
        working_dir=str(Path(__file__).resolve().parents[2]),
    )
    build_model = ClaudeCliModel(
        model_name=build_model_name,
        cli_command=args.cli_command,
        timeout_seconds=args.cli_timeout,
        working_dir=str(Path(__file__).resolve().parents[2]),
    )
else:
    model_name = args.model or os.getenv("OPENAI_MODEL_NAME") or "gpt-4o-mini"
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OpenAI API key: set OPENAI_API_KEY or pass --api_key")

    model = OpenAIModel(model_name=model_name, api_key=api_key, base_url=base_url)
    build_model_name = args.build_model or model_name
    build_base_url = args.build_base_url or base_url
    build_api_key = args.build_api_key or api_key
    build_model = OpenAIModel(
        model_name=build_model_name,
        api_key=build_api_key,
        base_url=build_base_url,
    )

assets_dir = Path(__file__).resolve().parent / "assets"
build_instruction = (assets_dir / "build.txt").read_text(encoding="utf-8")
cache_path = str(assets_dir / "cache" / "graph_design.json")
(assets_dir / "cache").mkdir(parents=True, exist_ok=True)

graph = RootGraph(name="vibegraph_demo")

output_root = assets_dir / "output" / "WareHouse"
output_root.mkdir(parents=True, exist_ok=True)
run_dir = output_root / f"vibegraph_demo_{time.strftime('%Y%m%d%H%M%S', time.localtime())}"
run_dir.mkdir(parents=True, exist_ok=True)

code_manager = Codes()
requirement_manager = Documents()
manual_manager = Documents()
code_manager.directory = str(run_dir)
requirement_manager.directory = str(run_dir)
manual_manager.directory = str(run_dir)

runtime_attributes = {
    "directory": str(run_dir),
    "task": "Build a small runnable software project from the generated graph.",
    "project_name": "vibegraph_demo",
    "org_name": "DefaultOrganization",
    "start_time": time.strftime('%Y%m%d%H%M%S', time.localtime()),
    "gui": "Prefer simple command-line interaction unless the task clearly requires GUI.",
    "code_manager": code_manager,
    "requirement_manager": requirement_manager,
    "manual_manager": manual_manager,
    "git_management": False,
    "test_reports": "",
    "exist_bugs_flag": True,
    "error_summary": "",
    "image_model": None,
}

set_runtime(
    RuntimeContext(
        directory=str(run_dir),
        code_manager=code_manager,
        requirement_manager=requirement_manager,
        manual_manager=manual_manager,
        git_management=False,
        attributes=runtime_attributes,
    )
)

vibe = graph.create_node(
    VibeGraph,
    name="vibe_graph",
    invoke_model=model,
    build_instructions=build_instruction,
    build_model=build_model,
    build_cache_path=cache_path,
    invoke_tools=[
        codes_check_and_processing_tool,
        check_code_completeness_tool,
        run_tests_tool,
    ],
)

graph.edge_from_entry(receiver=vibe, keys={})
graph.edge_to_exit(sender=vibe, keys={})

graph.build()
graph.invoke(input={}, attributes=runtime_attributes)
