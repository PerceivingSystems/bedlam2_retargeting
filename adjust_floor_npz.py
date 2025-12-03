# Copyright (c) 2025 Max Planck Society
# License: https://bedlam2.is.tuebingen.mpg.de/license.html
from processing.npz_toolkit import adjust_floor
from pathlib import Path
import argparse
import tqdm

# Path to the neutral SMPL-X body model file.
BODY_MODEL_PATH = 'body_models/SMPLX_NEUTRAL.npz'

def collect_npz_files(input_dir: Path):
    for npz_path in input_dir.rglob("*.npz"):
        if npz_path.is_file():
            yield npz_path


def main():
    parser = argparse.ArgumentParser(
        description="Adjust the floor for every NPZ found in a directory tree.")
    parser.add_argument(
        "--input_dir",
        type=Path,
        required=True,
        help="Directory containing NPZ files to adjust.",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.resolve()
    if not input_dir.is_dir():
        raise ValueError(f"Input directory '{input_dir}' does not exist or is not a directory.")

    output_dir = input_dir.with_name(f"{input_dir.name}_floor_adjusted")
    output_dir.mkdir(parents=True, exist_ok=True)

    npz_files = list(collect_npz_files(input_dir))
    if not npz_files:
        raise ValueError(f"No NPZ files found under '{input_dir}'.")

    for npz_path in tqdm.tqdm(npz_files):
        relative_path = npz_path.relative_to(input_dir)
        target_path = output_dir / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        adjust_floor(npz_path, target_path, body_model_path=BODY_MODEL_PATH)


if __name__ == "__main__":
    main()
