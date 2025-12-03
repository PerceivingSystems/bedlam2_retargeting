# Copyright (c) 2025 Max Planck Society
# License: https://bedlam2.is.tuebingen.mpg.de/license.html
import argparse
import csv
import random
import sys
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate target_body/source_anim CSV combinations."
    )
    parser.add_argument(
        "--bodies-dir",
        required=True,
        type=Path,
        help="Directory containing body FBX files (searched recursively).",
    )
    parser.add_argument(
        "--animations-dir",
        required=True,
        type=Path,
        help="Directory containing animation FBX files (searched recursively).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("sample.csv"),
        help="Destination CSV path (default: sample.csv).",
    )
    parser.add_argument(
        "--random-count",
        type=int,
        default=None,
        help="If set, randomly select N body-animation pairs instead of full cartesian product.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for reproducible sampling when --random-count is used.",
    )
    return parser.parse_args()


def validate_dir(path: Path, label: str) -> Path:
    if not path.exists():
        raise FileNotFoundError(f"{label} directory does not exist: {path}")
    if not path.is_dir():
        raise NotADirectoryError(f"{label} path is not a directory: {path}")
    return path


def discover_stems(directory: Path) -> List[str]:
    # Collapse to sorted unique stems for stable output and avoid duplicates.
    stems = {fbx.stem for fbx in directory.rglob("*.fbx") if fbx.is_file()}
    return sorted(stems)


def _is_self_pair(body: str, anim: str) -> bool:
    return anim == body or anim.startswith(f"{body}_")


def cartesian_pairs(bodies: Sequence[str], anims: Sequence[str]) -> List[Tuple[str, str]]:
    return [
        (body, anim)
        for body in bodies
        for anim in anims
        if not _is_self_pair(body, anim)
    ]


def sample_pairs(
    pairs: Sequence[Tuple[str, str]], count: int, rng: random.Random
) -> List[Tuple[str, str]]:
    if count > len(pairs):
        raise ValueError(
            f"Requested {count} pairs but only {len(pairs)} unique combinations available."
        )
    return rng.sample(pairs, count)


def write_csv(pairs: Iterable[Tuple[str, str]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["target_body", "source_anim"])
        writer.writerows(pairs)


def main() -> int:
    args = parse_args()
    try:
        bodies_dir = validate_dir(args.bodies_dir, "Bodies")
        animations_dir = validate_dir(args.animations_dir, "Animations")
        bodies = discover_stems(bodies_dir)
        animations = discover_stems(animations_dir)
        if not bodies:
            raise ValueError(f"No .fbx bodies found under {bodies_dir}")
        if not animations:
            raise ValueError(f"No .fbx animations found under {animations_dir}")
        available_pairs = cartesian_pairs(bodies, animations)
        if not available_pairs:
            raise ValueError("No valid body/animation pairings after filtering self matches.")
        if args.random_count is None:
            pairs = available_pairs
        else:
            if args.random_count <= 0:
                raise ValueError("--random-count must be a positive integer")
            rng = random.Random(args.seed)
            pairs = sample_pairs(available_pairs, args.random_count, rng)
        write_csv(pairs, args.output)
        print(f"Wrote {len(pairs)} pairs to {args.output}")
        return 0
    except Exception as exc:  # Surface useful context without stack trace noise.
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
