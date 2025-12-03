# Copyright (c) 2025 Max Planck Society
# License: https://bedlam2.is.tuebingen.mpg.de/license.html
# Author: Giorgio Becherini

import argparse
import numpy as np
import os
from pathlib import Path
import sys
import bpy


def convert_to_fbx(smplx_animation_path, output_path, target_fps, snap_to_ground_plane=False, target_format='UNREAL',
                   rest_position='GROUNDED', anim_format='SMPL-X'):
    """
    Import an SMPL-X animation NPZ into Blender and export it as an FBX file.

    Parameters
    ----------
    smplx_animation_path : Path
        NPZ animation file containing SMPL-X motion data.
    output_path : Path
        Target FBX file path.
    target_fps : int
        Frame rate used during baking.
    snap_to_ground_plane : bool, optional
        If set, aligns the animation to the ground plane.
    target_format : str, optional
        Export preset for FBX (e.g. 'UNREAL').
    rest_position : str, optional
        Initial rest pose during import.
    anim_format : str, optional
        Animation format ('SMPL-X' or 'AMASS').

    Returns
    -------
    bool
        True if export succeeded; False if input validation failed.
    """

    if anim_format not in ['SMPL-X', 'AMASS']:
        raise ValueError('anim_format must be "SMPL-X" or "AMASS"')

    smplx_animation_path, output_path = Path(smplx_animation_path), Path(output_path)

    if (not smplx_animation_path.exists()) or (smplx_animation_path.suffix != ".npz"):
        print(f"ERROR: Invalid input path: {smplx_animation_path}")
        return False

    if output_path.suffix != ".fbx":
        print(f"ERROR: Invalid output path: {output_path}")
        return False

    # Import animation, do not create keyframed pose correctives for faster import
    bpy.data.window_managers["WinMan"].smplx_tool.smplx_version = 'locked_head'  # Use SMPL-X locked head (no head bun)
    bpy.data.window_managers["WinMan"].smplx_tool.smplx_uv = "UV_2023"  # Use 2023 UV map

    bpy.ops.object.smplx_add_animation(filepath=str(smplx_animation_path), anim_format=anim_format,
                                       keyframe_corrective_pose_weights=False, target_framerate=target_fps,
                                       rest_position=rest_position)

    if snap_to_ground_plane:
        bpy.ops.object.smplx_snap_ground_plane()

    # Export FBX with baked shape and without pose correctives
    output_path.parent.mkdir(parents=True, exist_ok=True)

    bpy.ops.object.smplx_export_fbx(filepath=str(output_path), export_shape_keys="NONE", target_format=target_format)
    return True


def export_tpose_npz(smplx_animation_path, betas_npz_path=None):
    """
    Create a temporary NPZ containing a neutral T-pose using the shape
    parameters found in the input animation.

    Parameters
    ----------
    smplx_animation_path : Path
        NPZ containing body shape coefficients ('betas').

    Returns
    -------
    str
        Path to the generated temporary NPZ file.
    """
    betas = np.load(smplx_animation_path, allow_pickle=True)['betas']

    out_data = dict(
        betas=betas,
        poses=np.zeros((1, 165)),
        trans=np.zeros((1, 3)),
        mocap_frame_rate=30,
        model_type='smplx_locked_head',
        gender='neutral'
    )

    os.makedirs(betas_npz_path.parent, exist_ok=True)
    np.savez_compressed(betas_npz_path, **out_data)


def main():
    parser = argparse.ArgumentParser(description="Convert SMPL-X NPZ animations to FBX using the Blender add-on.")
    parser.add_argument('--smplx_animation_path', type=Path, required=True,
                        help="Input SMPL-X or AMASS NPZ animation file.")
    parser.add_argument('--out_fbx_path', type=Path, required=True,
                        help="Destination FBX path.")
    parser.add_argument('--target_fps', type=int, default=30,
                        help="Frame rate.")
    parser.add_argument('--anim_format', choices=['SMPL-X', 'AMASS'], default='SMPL-X',
                        help="Coordinate system expected by the importer")
    parser.add_argument('--tpose', action=argparse.BooleanOptionalAction, default=False,
                        help="Generate and export a static T-pose with the given betas instead of the animation.")

    if bpy.app.background and "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1:]  # get all args after "--"
        args = parser.parse_args(argv)
    else:
        args = parser.parse_args()

    bpy.ops.preferences.addon_enable(module='smplx_blender_addon')

    if args.tpose:
        betas_npz_path = Path(args.out_fbx_path.with_suffix('.npz'))
        export_tpose_npz(args.smplx_animation_path, betas_npz_path)
        smplx_animation_path = betas_npz_path
    else:
        smplx_animation_path = args.smplx_animation_path

    convert_to_fbx(smplx_animation_path, args.out_fbx_path, args.target_fps, anim_format=args.anim_format)


if __name__ == '__main__':
    main()
