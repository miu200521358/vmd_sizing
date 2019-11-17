#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
import re
import logging
import traceback
import argparse
import os.path
import sys
from datetime import datetime

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
import wrapperutils, sub_arm_ik

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(vmd_path, slice_frames):

    logger.info("slice_frames: %s", slice_frames)

    try:
        # VMD読み込み
        motion = VmdReader().read_vmd_file(vmd_path)

        if len(motion.frames.values()) > 0:
            # ボーンキー分割
            bone_fpath = re.sub(r'\.vmd$', "_slice_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), vmd_path)

            

            print("ボーンキー分割VMD出力成功: %s" % bone_fpath)

        if len(motion.cameras) > 0:
            # カメラキー分割VMD
            camera_fpath = re.sub(r'\.vmd$', "_camera_{0:%Y%m%d_%H%M%S}.csv".format(datetime.now()), vmd_path)


            print("カメラキー分割VMD出力成功: %s" % camera_fpath)

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMD解析処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())


if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vmd_path', dest='vmd_path', help='input vmd', type=str)
    args = parser.parse_args()

    if wrapperutils.is_valid_file(args.vmd_path, "VMDファイル", ".vmd", True) == False:
        sys.exit(-1)

    main(args.vmd_path)