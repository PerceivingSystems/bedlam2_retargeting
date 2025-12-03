# Copyright (c) 2025 Max Planck Society
# License: https://bedlam2.is.tuebingen.mpg.de/license.html
# Author: Giorgio Becherini
#         + edited by Anastasios Yiannakidis

import argparse
from pathlib import Path
import numpy as np
import smplx
import torch.cuda

# Path to the neutral SMPL-X body model file.
BODY_MODEL_PATH = '../body_models/SMPLX_NEUTRAL.npz'


def adjust_floor(retargeted_npz_path, out_npz_path, body_model_path=BODY_MODEL_PATH):
    """
    Rebuilds SMPL-X with floor adjuster.

    Parameters
    ----------
    retargeted_npz_path : Path
        NPZ containing 'poses' and 'trans' from the retargeting step.
    out_npz_path : Path
        Output NPZ path where the rebuilt animation is written.
    body_model_path : str, optional
        Path to the SMPL-X body model file.
    """

    data_retargeted = np.load(retargeted_npz_path, allow_pickle=True)
    betas = data_retargeted['betas']
    poses = data_retargeted['poses']
    trans = data_retargeted['trans']
    batch_size = poses.shape[0]
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    bm_args = {
        "model_path": body_model_path,
        "model_type": 'smplx',
        "num_betas": len(betas.squeeze()),
        "gender": 'neutral',
        "batch_size": batch_size,
        "flat_hand_mean": True,
        "use_pca": False,
    }

    model = smplx.create(**bm_args).to(device)
    betas = torch.tensor(betas, dtype=torch.float32, device=device).unsqueeze(0).repeat(batch_size, 1)
    poses = torch.tensor(poses, dtype=torch.float32, device=device)
    trans = torch.tensor(trans, dtype=torch.float32, device=device)

    model_out = model(
        betas=betas,
        global_orient=poses[:, :3],
        body_pose=poses[:, 3:66],
        left_hand_pose=poses[:, 75:120],
        right_hand_pose=poses[:, 120:165],
        jaw_pose=poses[:, 66:69],
        leye_pose=poses[:, 69:72],
        reye_pose=poses[:, 72:75],
        transl=trans,
    )
    v_seq = model_out.vertices.detach().cpu().numpy()

    floor_offset = np.median(v_seq[..., 1].min(axis=1))

    # Spatial normalization: center horizontal axes and lift to floor level.
    trans[:, [0, 2]] -= trans[0:1, [0, 2]]
    trans[:, 1] -= floor_offset

    data_retargeted = dict(data_retargeted)
    data_retargeted['trans'] = trans.cpu().numpy()

    out_npz_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz_path, **data_retargeted)


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild an animation NPZ with adjusted floor.")
    parser.add_argument('--retargeted_npz_path', type=Path, required=True,
                        help="NPZ file containing retargeted 'poses' and 'trans'.")
    parser.add_argument('--out_npz_path', type=Path, required=True,
                        help="Destination NPZ file for the rebuilt animation.")
    args = parser.parse_args()

    adjust_floor(args.retargeted_npz_path, args.out_npz_path)


if __name__ == '__main__':
    main()