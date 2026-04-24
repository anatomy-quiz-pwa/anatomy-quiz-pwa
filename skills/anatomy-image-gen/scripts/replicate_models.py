"""Central registry of which Replicate model to use for each mode.

Keep this in sync with ../references/replicate_models.md — paopao may edit
either file; code reads from this module, the markdown is the human-readable
rationale and upgrade log.

To pin a version, use "owner/name:version_hash" in the slug.
"""

from __future__ import annotations

# Default model slugs. Override per call via the MODEL_OVERRIDES env dict,
# or by editing this file directly.
MODEL_SLUGS: dict[str, str] = {
    "skeleton": "jagilley/controlnet-pose",
    "muscle": "stability-ai/sdxl",
    "realistic": "black-forest-labs/flux-dev",
}


def get_model_slug(mode: str) -> str:
    try:
        return MODEL_SLUGS[mode]
    except KeyError as exc:
        raise KeyError(
            f"No model registered for mode={mode!r}. "
            f"Valid modes: {sorted(MODEL_SLUGS)}"
        ) from exc
