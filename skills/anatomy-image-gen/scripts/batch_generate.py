"""Batch anatomy image generation from a CSV.

CSV columns (header required):
  reference_image,mode,description,output_name

Behavior:
  - Serial execution (no parallelism → avoids Replicate rate limit).
  - Every --notify-every successes, fire an optional telegram-notify.
  - On a row failure, record to errors.csv and keep going.
  - At end, print a summary (success / fail / total cost).

Dry-run: if no Replicate token, every row runs through prompt building only
so paopao can eyeball the prompts before spending money.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import generate  # noqa: E402
import prompt_builder  # noqa: E402
import replicate_client  # noqa: E402


REQUIRED_COLUMNS = {"reference_image", "mode", "description"}


def _notify(message: str) -> None:
    """Best-effort notification. Never raises."""
    # Try a telegram-notify CLI if present on PATH.
    cli = shutil.which("telegram-notify")
    if cli:
        try:
            subprocess.run([cli, message], check=False, timeout=10)
            return
        except Exception:
            pass
    # Otherwise, just stdout.
    print(f"[notify] {message}")


def _resolve_output_path(
    output_dir: Path, output_name: str | None, mode: str, description: str,
) -> Path:
    if output_name:
        return output_dir / f"{output_name}.png"
    stamp = dt.datetime.now().astimezone().strftime("%Y-%m-%d_%H%M%S")
    slug = generate._slugify(description)
    return output_dir / f"{stamp}_{mode}_{slug}.png"


def _read_rows(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open(encoding="utf-8-sig", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"CSV 少了必要欄位：{sorted(missing)}。"
                f" 現有欄位：{reader.fieldnames}"
            )
        return [dict(row) for row in reader if row.get("reference_image")]


def run_batch(
    csv_path: str | Path,
    output_dir: str | Path,
    notify_every: int = 5,
    dry_run: bool | None = None,
) -> dict[str, Any]:
    csv_path = Path(csv_path).expanduser().resolve()
    output_dir = Path(output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = _read_rows(csv_path)
    if not rows:
        raise ValueError(f"CSV 裡沒有有效列：{csv_path}")

    if dry_run is None:
        dry_run = not replicate_client.is_available()

    errors: list[dict[str, str]] = []
    successes: list[str] = []
    total = len(rows)

    _notify(
        f"📊 開始批次生成 {total} 張（{'dry-run' if dry_run else 'live'}）"
    )

    for idx, row in enumerate(rows, start=1):
        mode = row["mode"].strip()
        desc = row["description"].strip()
        ref = row["reference_image"].strip()
        name = (row.get("output_name") or "").strip() or None

        try:
            if mode not in prompt_builder.VALID_MODES:
                raise ValueError(
                    f"mode 必須是 {prompt_builder.VALID_MODES}，得到 {mode!r}"
                )
            target = _resolve_output_path(output_dir, name, mode, desc)
            result = generate.generate_anatomy_image(
                reference_image_path=ref,
                chinese_description=desc,
                mode=mode,
                output_dir=target.parent,
                dry_run=dry_run,
            )
            # Rename to requested output_name if needed (generate.py uses
            # timestamp-based naming by default).
            if not dry_run and result.get("output_path") and name:
                src = Path(result["output_path"])
                if src != target:
                    src.rename(target)
                    meta_src = src.with_suffix(".json")
                    if meta_src.exists():
                        meta_src.rename(target.with_suffix(".json"))
            successes.append(str(target))
        except Exception as exc:  # noqa: BLE001
            errors.append({
                "row": str(idx),
                "reference_image": ref,
                "mode": mode,
                "description": desc,
                "error": str(exc),
            })

        if idx % max(notify_every, 1) == 0:
            _notify(
                f"⏳ 進度 {idx}/{total}"
                f"（成功 {len(successes)} / 失敗 {len(errors)}）"
            )

    if errors:
        err_path = output_dir / "errors.csv"
        with err_path.open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["row", "reference_image", "mode", "description", "error"],
            )
            writer.writeheader()
            writer.writerows(errors)

    summary = {
        "total": total,
        "success": len(successes),
        "failed": len(errors),
        "dry_run": dry_run,
        "output_dir": str(output_dir),
    }
    _notify(
        f"✅ 批次結束：成功 {summary['success']} / 失敗 {summary['failed']}"
    )
    return summary


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Batch-generate anatomy images from a CSV."
    )
    parser.add_argument("--csv", "-c", required=True,
                        help="Path to batch CSV.")
    parser.add_argument("--output-dir", "-o", required=True)
    parser.add_argument("--notify-every", type=int, default=5,
                        help="Notify every N rows (default 5).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Force dry-run even if Replicate is available.")
    args = parser.parse_args(argv)

    try:
        summary = run_batch(
            csv_path=args.csv,
            output_dir=args.output_dir,
            notify_every=args.notify_every,
            dry_run=True if args.dry_run else None,
        )
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print()
    print("=== Batch summary ===")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    return 0 if summary["failed"] == 0 else 5


if __name__ == "__main__":
    sys.exit(_main())
