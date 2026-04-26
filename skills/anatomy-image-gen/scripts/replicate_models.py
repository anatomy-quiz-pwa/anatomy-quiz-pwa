"""Central registry of which Replicate model to use for each mode.

Keep this in sync with ../references/replicate_models.md — paopao may edit
either file; code reads from this module, the markdown is the human-readable
rationale and upgrade log.

To pin a version, use "owner/name:version_hash" in the slug.
"""

from __future__ import annotations

from typing import Any

# ----------------------------------------------------------------------------
# Model slugs per mode.
#
# 2026-04-26: Replicate de-listed `stability-ai/sdxl` and the older Jagilley
# ControlNet models (404 on dispatch). Switched to Black Forest Labs' Flux
# family which is currently the most reliable and cheapest text-to-image
# stack on Replicate. Trade-off: pure text-to-image, no ControlNet pose
# guidance from a reference photo. Pose control returns once we identify a
# verified-active ControlNet model.
# ----------------------------------------------------------------------------

MODEL_SLUGS: dict[str, str] = {
    "skeleton":  "black-forest-labs/flux-schnell",
    "muscle":    "black-forest-labs/flux-schnell",
    "realistic": "black-forest-labs/flux-dev",
}


# Schema family per slug. Determines how `build_inputs` shapes the request.
#   - "flux"          → prompt only (no negative_prompt, no image)
#   - "sdxl"          → prompt + negative_prompt + optional image
#   - "controlnet"    → prompt + negative_prompt + image (image required)
SCHEMA_FAMILY: dict[str, str] = {
    "black-forest-labs/flux-schnell": "flux",
    "black-forest-labs/flux-dev":     "flux",
    "stability-ai/sdxl":              "sdxl",
    "jagilley/controlnet-pose":       "controlnet",
}


def get_model_slug(mode: str) -> str:
    try:
        return MODEL_SLUGS[mode]
    except KeyError as exc:
        raise KeyError(
            f"No model registered for mode={mode!r}. "
            f"Valid modes: {sorted(MODEL_SLUGS)}"
        ) from exc


def get_schema_family(slug: str) -> str:
    """Return the input-schema family for a slug. Defaults to 'flux'."""
    base = slug.split(":", 1)[0]  # strip optional :version_hash
    return SCHEMA_FAMILY.get(base, "flux")


def accepts_reference_image(slug: str) -> bool:
    return get_schema_family(slug) in {"sdxl", "controlnet"}


def build_inputs(
    *,
    slug: str,
    positive: str,
    negative: str,
    reference_image_data_uri: str | None,
    seed: int | None,
) -> dict[str, Any]:
    """Shape the input dict to match the model's accepted schema.

    Centralised here so generate.py stays model-agnostic.
    """
    family = get_schema_family(slug)

    if family == "flux":
        inputs: dict[str, Any] = {
            "prompt": positive,
            "aspect_ratio": "1:1",
            "output_format": "png",
        }
        if seed is not None:
            inputs["seed"] = seed
        return inputs

    if family in {"sdxl", "controlnet"}:
        inputs = {
            "prompt": positive,
            "negative_prompt": negative,
        }
        if reference_image_data_uri is not None:
            inputs["image"] = reference_image_data_uri
        elif family == "controlnet":
            raise ValueError(
                f"{slug} requires a reference image but none was provided."
            )
        if seed is not None:
            inputs["seed"] = seed
        return inputs

    raise ValueError(f"Unknown schema family: {family}")
