# Copyright (c) 2025 Max Planck Society
# License: https://bedlam2.is.tuebingen.mpg.de/license.html
import argparse
import os
from pathlib import Path
import sys
import subprocess
import time
from multiprocessing import Pool
import json

PATHS_JSON_PATH = "paths.json"

def worker(blender_app_path, input, output, anim_format="SMPL-X", tpose=False, fps=30):
    # $BLENDERPATH --background --python fbx_toolkit.py -- --smplx_animation_path "$INPUT" --out_fbx_path "$OUTPUT"
    script_name = "processing/fbx_toolkit.py"
    subprocess_args = [blender_app_path, "--background", "--python", script_name, "--"]
    subprocess_args.extend(["--smplx_animation_path", input])
    subprocess_args.extend(["--out_fbx_path", output])
    subprocess_args.extend(["--anim_format", anim_format])
    subprocess_args.extend(["--target_fps", str(fps)])
    if tpose:
        subprocess_args.append("--tpose")
    subprocess.run(subprocess_args)
    return True


def worker_args(args):
    return worker(*args)


def process_dir(input_dir, output_dir, processes, anim_format="SMPL-X", fps=30, tpose=False):
    # Load Blender app path from paths.json
    blender_app_path = None
    with open(PATHS_JSON_PATH, 'r') as f:
        paths_data = json.load(f)
        blender_app_path = paths_data.get("BLENDER_APP_PATH", None)
    if blender_app_path is None:
        raise ValueError(f"Blender app path not found in {PATHS_JSON_PATH}")

    # Get list of source target files and sort by name
    filenames = sorted(input_dir.rglob("*.npz"))
    print("Looking for .npz files in", input_dir)
    num_files = len(filenames)

    print(f"Found .npz files: {num_files}")
    print(f"Starting pool with {processes} processes\n", file=sys.stderr)
    pool = Pool(processes)

    start_time = time.perf_counter()
    tasklist = []
    for input_path in filenames:

        # Please set your own naming convention if needed
        body_name = input_path.parent.parent.name
        if body_name == "moving_body_para":  # BEDLAM B0 naming convention
            body_name = input_path.parent.parent.parent.name

        body_name_suffix = input_path.parent.name
        if tpose:
            output_path = output_dir / "bodies" / f"{body_name}.fbx"
        else:
            output_path = output_dir / "animations" / f"{body_name}_{body_name_suffix}.fbx"

        tasklist.append(
            (
                blender_app_path,
                str(input_path),
                str(output_path),
                str(anim_format),
                tpose,
                str(fps)
            )
        )

    pool.map(worker_args, tasklist)
    pool.close()
    pool.join()

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time
    print(f"\nProcessed {num_files} files in {elapsed_time:.2f} seconds.")


def main():

    parser = argparse.ArgumentParser(description="Convert SMPL-X NPZ animations to FBX using the Blender add-on.")
    parser.add_argument('--processes', type=int, default=os.cpu_count(),)
    parser.add_argument('--input_dir', type=Path, required=True,
                        help="Input a directory or SMPL-X or AMASS NPZ animation file.")
    parser.add_argument('--output_dir', type=Path, required=True,
                        help="Destination output directory or FBX path.")
    parser.add_argument('--target_fps', type=int, default=30,
                        help="Frame rate.")
    parser.add_argument('--anim_format', choices=['SMPL-X', 'AMASS'], default='SMPL-X',
                        help="Coordinate system expected by the importer")
    parser.add_argument('--tpose', action=argparse.BooleanOptionalAction, default=False,
                        help="Generate and export a static T-pose with the given betas instead of the animation.")

    args = parser.parse_args()

    process_dir(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        processes=args.processes,
        anim_format=args.anim_format,
        fps=args.target_fps,
        tpose=args.tpose
    )



if __name__ == '__main__':
    main()
