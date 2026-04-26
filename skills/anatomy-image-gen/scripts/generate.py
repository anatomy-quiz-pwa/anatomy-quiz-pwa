"""Single-image anatomy generation.

Usage:
    python generate.py \\
        --reference /path/to/pose.jpg \\
        --description "側面視角，顯示髖屈肌群，跑步擺盪期" \\
        --mode muscle \\
        --output-dir ~/Boneman/generated

Dry-run mode (no Replicate token): prints the resolved prompt and exits.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any

# Allow running as a script OR `python -m scripts.generate`.
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import prompt_builder  # noqa: E402
import replicate_client  # noqa: E402
import replicate_models  # noqa: E402


SUPPORTED_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _slugify(text: str, max_len: int = 40) -> str:
    # Keep ASCII word chars + hyphens; drop everything else.
    cleaned = re.sub(r"[^\w\-一-龥]+", "-", text, flags=re.UNICODE)
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned[:max_len] or "img"


def _validate_reference(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"參考圖不存在：{path}")
    if path.suffix.lower() not in SUPPORTED_EXT:
        raise ValueError(
            f"不支援的副檔名 {path.suffix}；請用 {sorted(SUPPORTED_EXT)}"
        )


def _model_inputs(
    slug: str,
    reference_image: Path,
    positive: str,
    negative: str,
    seed: int | None,
) -> dict[str, Any]:
    """Shape inputs to match the chosen model's accepted schema.

    Delegates to replicate_models.build_inputs so the per-family schema
    knowledge stays in one place.
    """
    image_uri: str | None = None
    if replicate_models.accepts_reference_image(slug):
        image_uri = _image_to_data_uri(reference_image)
    return replicate_models.build_inputs(
        slug=slug,
        positive=positive,
        negative=negative,
        reference_image_data_uri=image_uri,
        seed=seed,
    )


def _image_to_data_uri(path: Path) -> str:
    """Convert a local image to a data URI.

    Replicate also accepts public URLs; for local files we inline as data URI
    which is fine for typical reference photos (<5MB).
    """
    import base64
    import mimetypes

    mime = mimetypes.guess_type(str(path))[0] or "image/jpeg"
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url) as resp, dest.open("wb") as fh:
        fh.write(resp.read())


def generate_anatomy_image(
    reference_image_path: str | Path,
    chinese_description: str,
    mode: str,
    output_dir: str | Path = "./output",
    seed: int | None = None,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    """Generate a single anatomy image.

    Returns a dict with keys:
      - output_path: str | None   (None in dry-run)
      - metadata_path: str | None
      - prompt, negative_prompt, model, mode, dry_run, reference_image
    """
    ref = Path(reference_image_path).expanduser().resolve()
    _validate_reference(ref)

    out_dir = Path(output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    positive, negative = prompt_builder.build_prompt(chinese_description, mode)
    model = replicate_models.get_model_slug(mode)

    if dry_run is None:
        dry_run = not replicate_client.is_available()

    timestamp = dt.datetime.now().astimezone()
    stamp = timestamp.strftime("%Y-%m-%d_%H%M%S")
    slug = _slugify(chinese_description)
    base_name = f"{stamp}_{mode}_{slug}"

    result: dict[str, Any] = {
        "prompt": positive,
        "negative_prompt": negative,
        "model": model,
        "mode": mode,
        "reference_image": str(ref),
        "seed": seed,
        "timestamp": timestamp.isoformat(),
        "dry_run": dry_run,
        "output_path": None,
        "metadata_path": None,
    }

    if dry_run:
        return result

    inputs = _model_inputs(model, ref, positive, negative, seed)
    urls = replicate_client.run(model, inputs)
    if not urls:
        raise RuntimeError("Replicate returned no output URLs.")

    image_path = out_dir / f"{base_name}.png"
    _download(urls[0], image_path)

    meta_path = out_dir / f"{base_name}.json"
    meta_payload = {**result, "output_path": str(image_path), "output_urls": urls}
    meta_path.write_text(
        json.dumps(meta_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result["output_path"] = str(image_path)
    result["metadata_path"] = str(meta_path)
    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate a single anatomy image via Replicate.",
    )
    parser.add_argument("--reference", "-r", required=True,
                        help="Path to pose reference image (jpg/png/webp).")
    parser.add_argument("--description", "-d", required=True,
                        help="中文描述")
    parser.add_argument("--mode", "-m", required=True,
                        choices=prompt_builder.VALID_MODES)
    parser.add_argument("--output-dir", "-o", default="./output")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="Force dry-run even if Replicate is available.")
    args = parser.parse_args(argv)

    try:
        result = generate_anatomy_image(
            reference_image_path=args.reference,
            chinese_description=args.description,
            mode=args.mode,
            output_dir=args.output_dir,
            seed=args.seed,
            dry_run=True if args.dry_run else None,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    except replicate_client.ReplicateAuthError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 3
    except replicate_client.ReplicateQuotaError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 4
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if result["dry_run"]:
        print("[dry-run] Replicate token 未設定或不可用，僅輸出預覽：")
        print(f"  model:     {result['model']}")
        print(f"  mode:      {result['mode']}")
        print(f"  reference: {result['reference_image']}")
        print(f"  positive:  {result['prompt']}")
        print(f"  negative:  {result['negative_prompt']}")
        print()
        print("若要實際生成，請設定 REPLICATE_API_TOKEN 後再跑一次。")
        return 0

    print(f"OK  image:    {result['output_path']}")
    print(f"    metadata: {result['metadata_path']}")
    return 0


if __name__ == "__main__":
    sys.exit(_main())
