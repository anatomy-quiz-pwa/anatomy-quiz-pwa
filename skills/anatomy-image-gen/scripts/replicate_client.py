"""Thin wrapper around the Replicate SDK.

Responsibilities:
  - Resolve API token from env var or ~/.config/replicate/token
  - Retry on transient errors with exponential backoff
  - Raise clear, actionable errors (quota, auth, bad input)
  - Provide a `run(model, inputs)` function returning (output_urls, cost_usd)

Phase 1 note: if the `replicate` SDK isn't installed or no token is present,
callers should treat this as "dry-run" and skip the actual API call.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any


class ReplicateAuthError(RuntimeError):
    """No token configured. Shows paopao where to get one."""


class ReplicateQuotaError(RuntimeError):
    """402 — account out of credit."""


class ReplicateTransientError(RuntimeError):
    """Network / 5xx / 429 that we already retried."""


TOKEN_HELP = (
    "找不到 Replicate API token。\n"
    "請擇一設定：\n"
    "  1. export REPLICATE_API_TOKEN=r8_xxxxxxxxxxxxx\n"
    "  2. 建立檔案 ~/.config/replicate/token 存放 token 字串\n\n"
    "token 申請步驟：\n"
    "  https://replicate.com → 用 GitHub 登入 → 右上頭像\n"
    "  → Account settings → API tokens → Create token"
)


def get_token() -> str | None:
    """Return the API token, or None if unconfigured."""
    token = os.getenv("REPLICATE_API_TOKEN")
    if token:
        return token.strip()
    cfg = Path.home() / ".config" / "replicate" / "token"
    if cfg.exists():
        value = cfg.read_text(encoding="utf-8").strip()
        if value:
            return value
    return None


def require_token() -> str:
    token = get_token()
    if not token:
        raise ReplicateAuthError(TOKEN_HELP)
    return token


def is_available() -> bool:
    """True if SDK importable AND token configured."""
    if get_token() is None:
        return False
    try:
        import replicate  # noqa: F401
        return True
    except ImportError:
        return False


def run(
    model: str,
    inputs: dict[str, Any],
    *,
    max_retries: int = 3,
    backoff_base: float = 2.0,
) -> list[str]:
    """Run a Replicate model and return the output URLs.

    `model` is a slug like "stability-ai/sdxl" or a pinned
    "owner/name:version_hash" string.

    Raises ReplicateAuthError / ReplicateQuotaError / ReplicateTransientError.
    """
    token = require_token()
    os.environ["REPLICATE_API_TOKEN"] = token  # SDK reads from env

    try:
        import replicate  # type: ignore
    except ImportError as exc:
        raise RuntimeError(
            "replicate SDK not installed. Run: pip install replicate"
        ) from exc

    last_error: Exception | None = None
    for attempt in range(max_retries):
        try:
            output = replicate.run(model, input=inputs)
            return _normalize_output(output)
        except Exception as exc:  # noqa: BLE001
            message = str(exc).lower()
            # Fast-fail on auth / quota — retrying won't help.
            if "402" in message or "payment" in message or "quota" in message:
                raise ReplicateQuotaError(
                    "Replicate 額度不足，請到 https://replicate.com/account/billing 儲值"
                ) from exc
            if "401" in message or "unauthor" in message or "forbidden" in message:
                raise ReplicateAuthError(
                    "Replicate token 無效或被撤銷。\n" + TOKEN_HELP
                ) from exc

            last_error = exc
            if attempt < max_retries - 1:
                sleep_for = backoff_base ** (attempt + 1)
                time.sleep(sleep_for)
                continue

    raise ReplicateTransientError(
        f"Replicate call failed after {max_retries} retries: {last_error}"
    ) from last_error


def _normalize_output(output: Any) -> list[str]:
    """Replicate returns str | list[str] | FileOutput | list[FileOutput].

    Collapse all shapes into list[str] of URLs.
    """
    if output is None:
        return []
    if isinstance(output, (list, tuple)):
        return [_stringify(o) for o in output]
    return [_stringify(output)]


def _stringify(obj: Any) -> str:
    # replicate>=0.25 returns FileOutput objects with a .url attr
    url = getattr(obj, "url", None)
    if url:
        return str(url)
    return str(obj)
