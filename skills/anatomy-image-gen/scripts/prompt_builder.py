"""Build English prompts for Replicate from Chinese descriptions + mode.

Offline-safe: if `anthropic` SDK is unavailable or ANTHROPIC_API_KEY is not set,
falls back to a template-based English prompt that still carries Boneman brand
keywords and mode-specific technical keywords.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Literal

Mode = Literal["skeleton", "muscle", "realistic"]
VALID_MODES: tuple[Mode, ...] = ("skeleton", "muscle", "realistic")


# ---------------------------------------------------------------------------
# Boneman brand style (fallback when /mnt/skills/user/boneman-style/ not found)
# ---------------------------------------------------------------------------

BONEMAN_BRAND_KEYWORDS = (
    "clean educational illustration style, "
    "professional anatomy textbook quality, "
    "clear lines, high contrast, neutral background, "
    "accurate human proportions"
)


MODE_POSITIVE: dict[str, str] = {
    "skeleton": (
        "anatomical skeleton line drawing, stick-figure style with bone structure, "
        "side-view biomechanical diagram, simplified joint markers, "
        "black lines on white background, gait analysis diagram"
    ),
    "muscle": (
        "medical illustration of muscle anatomy, labeled muscle groups, "
        "anatomical accuracy, semi-transparent skin showing deep muscles, "
        "textbook quality color illustration"
    ),
    "realistic": (
        "photorealistic human demonstration, "
        "athletic person performing the movement, "
        "studio lighting, neutral gym background, "
        "high resolution photograph"
    ),
}


MODE_NEGATIVE: dict[str, str] = {
    "skeleton": (
        "photorealistic, color, shading, muscle texture, background clutter, "
        "cartoon, chibi, low quality, wrong bone count, extra limbs"
    ),
    "muscle": (
        "cartoon, chibi, low quality, deformed anatomy, wrong muscle placement, "
        "extra limbs, blurry, text artifacts, watermark"
    ),
    "realistic": (
        "cartoon, anime, illustration, painting, deformed body, "
        "extra limbs, low quality, blurry, watermark, text"
    ),
}


# ---------------------------------------------------------------------------
# Optional: integrate boneman-style skill (only if available)
# ---------------------------------------------------------------------------

def _try_boneman_style(chinese: str, mode: str) -> str | None:
    """Try to call the boneman-style skill. Return None if unavailable."""
    candidate_paths = [
        Path("/mnt/skills/user/boneman-style"),
        Path.home() / ".claude" / "skills" / "boneman-style",
    ]
    for p in candidate_paths:
        if p.exists():
            # Look for a Python entrypoint. We do NOT import arbitrary code
            # from an unknown location; instead we check for a known file.
            entry = p / "scripts" / "build_prompt.py"
            if entry.exists():
                try:
                    import importlib.util

                    spec = importlib.util.spec_from_file_location(
                        "boneman_style_build_prompt", entry
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        fn = getattr(module, "build_prompt", None)
                        if callable(fn):
                            result = fn(chinese, mode)
                            if isinstance(result, str) and result.strip():
                                return result
                except Exception:
                    # Never fail on boneman-style hiccup — fall back silently.
                    return None
    return None


# ---------------------------------------------------------------------------
# Optional: translate via Anthropic SDK (only if key present)
# ---------------------------------------------------------------------------

def _try_anthropic_translate(chinese: str, mode: str) -> str | None:
    """Translate Chinese description to a Boneman-styled English prompt.

    Returns None if SDK not installed or API key missing — caller must fall
    back to the template.
    """
    if not os.getenv("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic  # type: ignore
    except ImportError:
        return None

    system = (
        "You translate Chinese anatomy/biomechanics descriptions into concise "
        "English prompts for an image diffusion model. Output ONLY the English "
        "prompt, no preamble. Keep the medical/biomechanical meaning precise. "
        "Use Taiwanese medical terminology when disambiguating."
    )
    user = (
        f"Mode: {mode}\n"
        f"Chinese description: {chinese}\n\n"
        "Translate to an English diffusion prompt. Focus on: viewpoint, body "
        "parts, phase of movement, and what should be highlighted. Keep it "
        "under 40 words. Do not add style keywords (those are appended "
        "separately)."
    )
    try:
        client = anthropic.Anthropic()
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # Response content is a list of blocks.
        for block in msg.content:
            text = getattr(block, "text", None)
            if text:
                return text.strip()
    except Exception:
        return None
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_prompt(chinese_description: str, mode: str) -> tuple[str, str]:
    """Return (positive_prompt, negative_prompt) for the given Chinese + mode.

    Resolution order for the "subject" portion of the positive prompt:
      1. boneman-style skill (if available on disk)
      2. Anthropic SDK translation (if key set and SDK installed)
      3. Fallback: raw Chinese string kept verbatim + English keywords
    """
    if mode not in VALID_MODES:
        raise ValueError(
            f"mode must be one of {VALID_MODES}, got {mode!r}"
        )

    subject: str | None = _try_boneman_style(chinese_description, mode)
    if subject is None:
        subject = _try_anthropic_translate(chinese_description, mode)

    if subject is None:
        # Last-resort fallback: keep Chinese inline (SDXL handles it passably)
        # and lean on the English keyword blocks.
        subject = chinese_description.strip()

    positive = (
        f"{subject}, "
        f"{MODE_POSITIVE[mode]}, "
        f"{BONEMAN_BRAND_KEYWORDS}"
    )
    negative = MODE_NEGATIVE[mode]
    return positive, negative


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build an English Replicate prompt from a Chinese description."
    )
    parser.add_argument(
        "--description",
        "-d",
        required=True,
        help="中文描述，例如：側面視角，顯示髖屈肌群，跑步擺盪期",
    )
    parser.add_argument(
        "--mode",
        "-m",
        required=True,
        choices=VALID_MODES,
        help="生成模式",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON instead of plain text.",
    )
    args = parser.parse_args(argv)

    positive, negative = build_prompt(args.description, args.mode)

    if args.json:
        print(json.dumps(
            {"positive": positive, "negative": negative},
            ensure_ascii=False,
            indent=2,
        ))
    else:
        print("=== POSITIVE ===")
        print(positive)
        print()
        print("=== NEGATIVE ===")
        print(negative)
    return 0


if __name__ == "__main__":
    sys.exit(_main())
