from __future__ import annotations

import json
import os
import re
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
        name = str(message.get("name") or "").strip()
        content = message.get("content")
        if isinstance(content, str):
            body = content.strip()
        else:
            body = json.dumps(content, ensure_ascii=False, indent=2, default=str)
        if not body:
            continue
        if role == "TOOL" and name:
            rendered.append(f"{role} ({name}):\n{body}")
        else:
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


def _has_tool_result_message(messages: list[dict[str, Any]]) -> bool:
    for message in messages:
        if str(message.get("role") or "").strip().lower() == "tool":
            return True
    return False


def _get_tool_result_names(messages: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for message in messages:
        if str(message.get("role") or "").strip().lower() != "tool":
            continue
        name = str(message.get("name") or "").strip()
        if name:
            names.add(name)
    return names


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


def _build_tool_choice_schema(
    tools: list[dict[str, Any]],
    final_schema: dict[str, Any] | None,
    *,
    allow_final: bool,
    allowed_tool_names: list[str] | None = None,
) -> dict[str, Any]:
    tool_names = [str(tool.get("name") or "") for tool in tools if str(tool.get("name") or "").strip()]
    if allowed_tool_names:
        allowed = {name for name in allowed_tool_names if name}
        tool_names = [name for name in tool_names if name in allowed]
    response_types = ["tool_call", "final"] if allow_final else ["tool_call"]
    properties: dict[str, Any] = {
        "response_type": {
            "type": "string",
            "enum": response_types,
        },
        "tool_name": {
            "type": "string",
            "enum": tool_names or [""],
        },
        "arguments": {
            "type": "object",
            "additionalProperties": True,
        },
        "final_text": {
            "type": "string",
        },
    }
    if final_schema is not None:
        properties["final_json"] = final_schema
    return {
        "type": "object",
        "properties": properties,
        "required": ["response_type"],
        "additionalProperties": False,
    }


def _render_tool_protocol(
    tools: list[dict[str, Any]],
    *,
    expects_json_output: bool,
    require_tool_call: bool,
    allowed_tool_names: list[str] | None = None,
) -> str:
    filtered_tools = tools
    if allowed_tool_names:
        allowed = {name for name in allowed_tool_names if name}
        filtered_tools = [tool for tool in tools if str(tool.get("name") or "") in allowed]
    lines = [
        "TOOL CALL COMPATIBILITY MODE:",
        "You may request exactly one tool call at a time using structured output.",
        "If a tool is needed next, set response_type='tool_call', choose exactly one tool_name, and provide JSON arguments.",
    ]
    if require_tool_call:
        lines.append("This turn requires a tool call. Do not return a final answer yet.")
    else:
        lines.append("If no tool is needed, set response_type='final'.")
        if expects_json_output:
            lines.append("When response_type='final', populate final_json with the final structured output.")
        else:
            lines.append("When response_type='final', populate final_text with the final answer.")
    if allowed_tool_names:
        lines.append(f"Only these tools are valid for this turn: {', '.join(allowed_tool_names)}")
    lines.append("Available tools:")
    for tool in filtered_tools:
        name = str(tool.get("name") or "").strip()
        description = str(tool.get("description") or "").strip()
        parameters = tool.get("parameters") or {}
        lines.append(f"- {name}: {description}")
        lines.append(json.dumps(parameters, ensure_ascii=False, indent=2))
    return "\n".join(lines)


def _select_required_tools(tools: list[dict[str, Any]], messages: list[dict[str, Any]]) -> list[str] | None:
    available = {
        str(tool.get("name") or "").strip()
        for tool in tools
        if str(tool.get("name") or "").strip()
    }
    used = _get_tool_result_names(messages)

    if "codes_check_and_processing_tool" in available and "codes_check_and_processing_tool" not in used:
        return ["codes_check_and_processing_tool"]
    if (
        "check_code_completeness_tool" in available
        and "codes_check_and_processing_tool" in used
        and "check_code_completeness_tool" not in used
    ):
        return ["check_code_completeness_tool"]
    if "run_tests_tool" in available and "run_tests_tool" not in used:
        return ["run_tests_tool"]
    return None


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
        system_prompt = _extract_system_prompt(messages)

        prompt_text = _render_conversation_prompt(messages)
        required_fields = _extract_required_fields(messages)
        use_schema = bool(required_fields) and _expects_json_output(messages)
        final_schema = _build_json_schema(required_fields) if use_schema else None
        forced_tools = _select_required_tools(tools or [], messages) if tools else None
        require_tool_call = bool(tools) and (forced_tools is not None or not _has_tool_result_message(messages))

        if tools:
            tool_protocol = _render_tool_protocol(
                tools,
                expects_json_output=use_schema,
                require_tool_call=require_tool_call,
                allowed_tool_names=forced_tools,
            )
            system_prompt = f"{system_prompt}\n\n{tool_protocol}" if system_prompt else tool_protocol

        command = [
            self._cli_command,
            "-p",
            "--output-format",
            "json",
            "--permission-mode",
            self._permission_mode,
            "--no-session-persistence",
        ]
        command.extend(["--tools", ""])
        if self._model_name:
            command.extend(["--model", self._model_name])
        if system_prompt:
            command.extend(["--system-prompt", system_prompt])
        if tools:
            command.extend([
                "--json-schema",
                json.dumps(
                    _build_tool_choice_schema(
                        tools,
                        final_schema,
                        allow_final=not require_tool_call,
                        allowed_tool_names=forced_tools,
                    ),
                    ensure_ascii=False,
                ),
            ])
        elif use_schema:
            command.extend(["--json-schema", json.dumps(final_schema, ensure_ascii=False)])
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

        structured_output = parsed.get("structured_output")

        if tools and isinstance(structured_output, dict):
            response_type = structured_output.get("response_type")
            if response_type == "tool_call":
                tool_name = str(structured_output.get("tool_name") or "").strip()
                if not tool_name:
                    raise RuntimeError(f"Claude CLI tool-call response missing tool_name: {parsed}")
                arguments = structured_output.get("arguments")
                if not isinstance(arguments, dict):
                    arguments = {}
                return {
                    "type": ModelResponseType.TOOL_CALL,
                    "content": [{
                        "id": "claude-cli-tool-call",
                        "name": tool_name,
                        "arguments": arguments,
                    }],
                    "raw_response": parsed,
                }
            if response_type == "final":
                if use_schema and isinstance(structured_output.get("final_json"), dict):
                    content = json.dumps(structured_output["final_json"], ensure_ascii=False)
                else:
                    content = structured_output.get("final_text", "")
            else:
                raise RuntimeError(f"Claude CLI returned unknown response_type: {parsed}")
        elif use_schema and isinstance(structured_output, dict):
            content = json.dumps(structured_output, ensure_ascii=False)
        else:
            content = parsed.get("result", "")

        return {
            "type": ModelResponseType.CONTENT,
            "content": content,
            "raw_response": parsed,
        }


__all__ = ["ClaudeCliModel"]