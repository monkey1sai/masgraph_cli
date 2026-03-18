from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from masfactory import ClaudeCliModel, OpenAIModel
from applications.chatdev_lite_vibegraph.workflow import build_chatdev_lite_vibegraph

parser = argparse.ArgumentParser(description='ChatDev command-line arguments')
parser.add_argument('--org', type=str, default="DefaultOrganization", help="Organization name; software will be generated in WareHouse/name_org_timestamp directory")
parser.add_argument('--task', type=str, default="Write a Ping-Pong (Pong) game, use Python and ultimately provide an application that can be run directly.", help="Task prompt for software development")
parser.add_argument('--name', type=str, default="PingPong", help="Software name; software will be generated in WareHouse/name_org_timestamp directory")
parser.add_argument('--provider', type=str, default='openai', choices=['openai', 'claude-cli'], help='Model provider backend')
parser.add_argument('--model', type=str, default=None, help='Model name. Defaults to gpt-4o-mini for OpenAI and sonnet for claude-cli')
parser.add_argument('--api_key', type=str, default=None, help="API key, default is empty, uses environment variable OPENAI_API_KEY")
parser.add_argument('--base_url', type=str, default=None, help="API base URL, default is empty, uses environment variable BASE_URL")
parser.add_argument('--cli-command', type=str, default='claude', help='Claude Code CLI executable path when provider=claude-cli')
parser.add_argument('--cli-timeout', type=int, default=900, help='Claude CLI timeout in seconds when provider=claude-cli')
args = parser.parse_args()

base_url = args.base_url or os.getenv("OPENAI_BASE_URL") or os.getenv("BASE_URL")

if args.provider == 'claude-cli':
    model = ClaudeCliModel(
        model_name=args.model or os.getenv('CLAUDE_MODEL') or 'sonnet',
        cli_command=args.cli_command,
        timeout_seconds=args.cli_timeout,
        working_dir=str(_REPO_ROOT),
    )
else:
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("Missing OpenAI API key: set OPENAI_API_KEY or pass --api_key")
    model = OpenAIModel(model_name=args.model or os.getenv('OPENAI_MODEL_NAME') or 'gpt-4o-mini', api_key=api_key, base_url=base_url)

graph = build_chatdev_lite_vibegraph(model=model)
graph.build()
start_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
graph.invoke(
    input={},
    attributes={
        "task": args.task,
        "project_name": args.name,
        "org_name": args.org,
        "start_time": start_time,
        "name": args.name,
        "org": args.org,
    },
)
