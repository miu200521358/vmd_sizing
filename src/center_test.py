# -*- coding: utf-8 -*-
#
import argparse
import os.path
import logging
import copy
import traceback
import re
from math import acos, degrees, atan2
from datetime import datetime
from pathlib import Path
from PyQt5.QtGui import QQuaternion, QVector3D, QMatrix4x4, QVector4D
import glob

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
error_file_logger = logging.getLogger("error")

level = {0:logging.ERROR,
            1:logging.WARNING,
            2:logging.INFO,
            3:logging.DEBUG}

if __name__=="__main__":

    for pmx_path in glob.glob("D:/MMD/MikuMikuDance_v926x64/UserFile/Model/**/*.pmx", recursive=True):
        try:
            pmx_model = PmxReader().read_pmx_file(pmx_path)

            logger.info("pmx_model: %s", pmx_path)
            if "右足ＩＫ" in pmx_model.bones and len(pmx_model.bones["右足ＩＫ"].ik.link) > 2:
                logger.warning("IKリンク数多いよ: %s", [ pmx_model.bone_indexes[l.bone_index] for l in pmx_model.bones["右足ＩＫ"].ik.link])
        except Exception as e:
            pass

    # try:
    #     # VMD読み込み
    #     # motion = VmdReader().read_vmd_file(args.vmd_path)

    #     # # 作成元モデル
    #     # logger.info("trace_pmx_path: %s", args.trace_pmx_path)
    #     # org_pmx = PmxReader().read_pmx_file(args.trace_pmx_path)

    #     # 変換先モデル
    #     logger.info("replace_pmx_path: %s", args.replace_pmx_path)
    #     rep_pmx = PmxReader().read_pmx_file(args.replace_pmx_path)
        
    #     # logger.info("rep_pmx.bones[右足ＩＫ].ik.link: %s", rep_pmx.bones["右足ＩＫ"].ik.link)
    #     # logger.info("rep_pmx.bone_indexes[rep_pmx.bones[センター].parent_index]: %s", rep_pmx.bone_indexes[rep_pmx.bones["センター"].parent_index])

    #     if len(rep_pmx.bones["右足ＩＫ"].ik.link) > 2:
    #         logger.warning("IKリンク数多いよ")

    #     # if rep_pmx.bone_indexes[rep_pmx.bones["センター"].parent_index] == rep_pmx.bones["グルーブ"].index:
    #     #     logger.warn("センター・グルーブ反転")

    #     # # 出力ファイルパス
    #     # bone_filename, _ = os.path.splitext(os.path.basename(args.replace_pmx_path))
    #     # output_vmd_path = os.path.join(str(Path(args.vmd_path).resolve().parents[0]), os.path.basename(args.vmd_path).replace(".vmd", "_{1}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now(), bone_filename)))

    #     # # 接触回避処理
    #     # is_avoidance = True if args.avoidance == 1 else False

    #     # # 腕IKによる位置調整
    #     # is_hand_ik = True if args.hand_ik == 1 else False

    #     # main(motion, org_pmx, rep_pmx, output_vmd_path, is_avoidance, True, is_hand_ik, args.hand_distance, [], [], []) 

    # except SizingException as e:
    #     print("■■■■■■■■■■■■■■■■■")
    #     print("■　**ERROR**　")
    #     print("■　VMDサイジング処理が処理できないデータで終了しました。")
    #     print("■■■■■■■■■■■■■■■■■")
    #     print("")
    #     print(e.message)

    # except Exception as e:
    #     print("■■■■■■■■■■■■■■■■■")
    #     print("■　**ERROR**　")
    #     print("■　VMDサイジング処理が意図せぬエラーで終了しました。")
    #     print("■■■■■■■■■■■■■■■■■")

    #     print(traceback.format_exc())

