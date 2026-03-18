from __future__ import annotations

import json
import os
import subprocess
from typing import Any

from .model import Model, ModelResponseType


def _extract_system_prompt(messages: list[dict[str, Any]]) -> str | None:
    parts: list[str] = []
    for message in messages:
        if message.get("role") != "system":
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content.strip())
    if not parts:
        return None
    return "\n\n".join(parts)


def _render_conversation_prompt(messages: list[dict[str, Any]]) -> str:
    rendered: list[str] = []
    for message in messages:
        role = str(message.get("role") or "user").strip().upper()
        if role == "SYSTEM":
            continue
        content = message.get("content")
        if isinstance(content, str):
            body = content.strip()
        else:
            body = json.dumps(content, ensure_ascii=False, indent=2, default=str)
        if not body:
            continue
        rendered.append(f"{role}:\n{body}")
    if not rendered:
        return "USER:\nPlease answer the request."
    return "\n\n".join(rendered)


def _extract_required_fields(messages: list[dict[str, Any]]) -> dict[str, Any]:
    marker = "REQUIRED OUTPUT FIELDS AND THEIR DESCRIPTIONS:"
    for message in reversed(messages):
        content = message.get("content")
        if not isinstance(content, str) or marker not in content:
            continue
        suffix = content.split(marker, 1)[1].strip()
        start = suffix.find("{")
        end = suffix.rfind("}")
        if start == -1 or end == -1 or end <= start:
            continue
        try:
            parsed = json.loads(suffix[start : end + 1])
        except Exception:
            continue
        if isinstance(parsed, dict):
            return parsed
    return {}


def _expects_json_output(messages: list[dict[str, Any]]) -> bool:
    hints = (
        "single JSON object",
        "strictly valid JSON",
        "must strictly and only contain a single JSON object",
    )
    for message in messages:
        content = message.get("content")
        if not isinstance(content, str):
            continue
        lowered = content.lower()
        if any(hint.lower() in lowered for hint in hints):
            return True
    return False


def _build_json_schema(required_fields: dict[str, Any]) -> dict[str, Any]:
    property_schema = {
        "type": ["string", "number", "integer", "boolean", "object", "array", "null"]
    }
    properties = {key: dict(property_schema) for key in required_fields.keys()}
    return {
        "type": "object",
        "properties": properties,
        "required": list(required_fields.keys()),
        "additionalProperties": True,
    }


class ClaudeCliModel(Model):
    """Model adapter that uses the local Claude Code CLI in non-interactive mode."""

    def __init__(
        self,
        model_name: str | None = None,
        cli_command: str = "claude",
        invoke_settings: dict | None = None,
        timeout_seconds: int = 600,
        working_dir: str | None = None,
        permission_mode: str = "bypassPermissions",
    ):
        super().__init__(model_name=model_name or "sonnet", invoke_settings=invoke_settings)
        self._cli_command = cli_command
        self._timeout_seconds = int(timeout_seconds)
        self._working_dir = working_dir
        self._permission_mode = permission_mode
        self._description = {
            "id": self._model_name,
            "object": "local_cli_model",
            "provider": "claude-code-cli",
            "cli_command": cli_command,
        }
        self._settings_mapping = {
            "temperature": {"name": "temperature", "type": float, "section": [0.0, 1.0]},
            "max_tokens": {"name": "max_tokens", "type": int},
        }

    def invoke(
        self,
        messages: list[dict],
        tools: list[dict] | None,
        settings: dict | None = None,
        **kwargs,
    ) -> dict:
        merged_settings = self._parse_settings(settings)
        if tools:
            extra_system_note = (
                "Tool calling is unavailable in ClaudeCliModel compatibility mode. "
                "Answer directly without requesting tools."
            )
        else:
            extra_system_note = None

        system_prompt = _extract_system_prompt(messages)
        if extra_system_note:
            system_prompt = f"{system_prompt}\n\n{extra_system_note}" if system_prompt else extra_system_note

        prompt_text = _render_conversation_prompt(messages)
        required_fields = _extract_required_fields(messages)
        use_schema = bool(required_fields) and _expects_json_output(messages)

        command = [
            self._cli_command,
            "-p",
            "--output-format",
            "json",
            "--permission-mode",
            self._permission_mode,
            "--no-session-persistence",
            "--tools",
            "",
        ]
        if self._model_name:
            command.extend(["--model", self._model_name])
        if system_prompt:
            command.extend(["--system-prompt", system_prompt])
        if use_schema:
            command.extend(["--json-schema", json.dumps(_build_json_schema(required_fields), ensure_ascii=False)])
        command.append(prompt_text)

        env = os.environ.copy()
        if "max_tokens" in merged_settings:
            env.setdefault("CLAUDE_CODE_MAX_OUTPUT_TOKENS", str(merged_settings["max_tokens"]))

        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=self._working_dir,
            timeout=self._timeout_seconds,
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            stdout = (completed.stdout or "").strip()
            details = stderr or stdout or f"exit code {completed.returncode}"
            raise RuntimeError(f"Claude CLI invocation failed: {details}")

        raw_output = (completed.stdout or "").strip()
        if not raw_output:
            raise RuntimeError("Claude CLI returned empty output")

        try:
            parsed = json.loads(raw_output)
        except Exception as exc:
            raise RuntimeError(f"Claude CLI returned non-JSON output: {raw_output}") from exc

        if parsed.get("is_error"):
            raise RuntimeError(f"Claude CLI error: {parsed}")

        if use_schema and isinstance(parsed.get("structured_output"), dict):
            content: object = json.dumps(parsed["structured_output"], ensure_ascii=False)
        else:
            content = parsed.get("result", "")

        return {
            "type": ModelResponseType.CONTENT,
            "content": content,
            "raw_response": parsed,
        }


__all__ = ["ClaudeCliModel"]