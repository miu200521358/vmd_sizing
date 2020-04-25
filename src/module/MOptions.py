# -*- coding: utf-8 -*-
#
import os
import argparse

from mmd.PmxReader import PmxReader
from mmd.VmdReader import VmdReader
from mmd.VpdReader import VpdReader
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFileUtils
from utils.MException import SizingException
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class MOptions():

    def __init__(self, version_name, logging_level, data_set_list, arm_options, monitor, is_file, outout_datetime):
        self.version_name = version_name
        self.logging_level = logging_level
        self.data_set_list = data_set_list
        self.arm_options = arm_options
        self.monitor = monitor
        self.is_file = is_file
        self.outout_datetime = outout_datetime
    
    # 複数件のファイルセットの足IKの比率を再設定する
    def calc_leg_ratio(self):
        # まず一番小さいXZ比率と一番大きいXZ比率を取得する
        min_xz_ratio = 99999999999
        max_xz_ratio = -99999999999
        for data_set_idx, data_set in enumerate(self.data_set_list):
            if data_set.original_xz_ratio < min_xz_ratio:
                min_xz_ratio = data_set.original_xz_ratio
            
            if data_set.original_xz_ratio > max_xz_ratio:
                max_xz_ratio = data_set.original_xz_ratio
        
        # XZ比率の差(差分の1.2倍をリミットとする)
        total_xz_ratio = min((min_xz_ratio + ((max_xz_ratio - min_xz_ratio) / 2)), 1.2)
        logger.test("total_xz_ratio: %s", total_xz_ratio)

        logger.info("")

        log_txt = "足の長さの比率 ---------\n"

        for data_set_idx, data_set in enumerate(self.data_set_list):
            if len(self.data_set_list) > 1:
                # XZ比率は合計から導き出した比率
                data_set.xz_ratio = total_xz_ratio
                data_set.y_ratio = data_set.original_y_ratio
            else:
                # セットが1件（一人モーションの場合はそのまま）
                data_set.xz_ratio = data_set.original_xz_ratio
                data_set.y_ratio = data_set.original_y_ratio

            log_txt = "{0}【No.{1}】　xz: {2}, y: {3} (元: xz: {4})\n".format(log_txt, (data_set_idx + 1), data_set.xz_ratio, data_set.y_ratio, data_set.original_xz_ratio)

        logger.info(log_txt)

    @classmethod
    def parse(cls, version_name: str):
        parser = argparse.ArgumentParser()
        parser.add_argument("--motion_path", required=True, type=(lambda x: list(map(str, x.split(';')))))
        parser.add_argument("--org_model_path", required=True, type=(lambda x: list(map(str, x.split(';')))))
        parser.add_argument("--rep_model_path", required=True, type=(lambda x: list(map(str, x.split(';')))))
        parser.add_argument("--detail_stance_flg", required=True, type=(lambda x: list(map(int, x.split(';')))))
        parser.add_argument("--twist_flg", required=True, type=(lambda x: list(map(int, x.split(';')))))
        parser.add_argument("--arm_process_flg_avoidance", type=int, default=0)
        parser.add_argument("--avoidance_target_list", default=[], type=(lambda x: list(map(str, x.split(';')))))
        parser.add_argument("--arm_process_flg_alignment", type=int, default=0)
        parser.add_argument("--alignment_finger_flg", type=int, default=0)
        parser.add_argument("--alignment_floor_flg", type=int, default=0)
        parser.add_argument("--alignment_distance_wrist", type=float, default=1.7)
        parser.add_argument("--alignment_distance_finger", type=float, default=1.4)
        parser.add_argument("--alignment_distance_floor", type=float, default=1.8)
        parser.add_argument("--arm_check_skip_flg", type=int, default=0)
        parser.add_argument("--verbose", type=int, default=20)

        args = parser.parse_args()

        # ログディレクトリ作成
        os.makedirs("log", exist_ok=True)

        MLogger.initialize(level=args.verbose, is_file=True)

        try:
            arm_process_flg_avoidance = True if args.arm_process_flg_avoidance == 1 else False
            arm_process_flg_alignment = True if args.arm_process_flg_alignment == 1 else False
            alignment_finger_flg = True if args.alignment_finger_flg == 1 else False
            alignment_floor_flg = True if args.alignment_floor_flg == 1 else False
            arm_check_skip_flg = True if args.arm_check_skip_flg == 1 else False

            arm_options = MArmProcessOptions(
                arm_process_flg_avoidance, \
                args.avoidance_target_list, \
                arm_process_flg_alignment, \
                alignment_finger_flg, \
                alignment_floor_flg, \
                args.alignment_distance_wrist, \
                args.alignment_distance_finger, \
                args.alignment_distance_floor, \
                arm_check_skip_flg
            )

            data_set_list = []
            for set_no, (motion_path, org_model_path, rep_model_path, detail_stance_flg_val, twist_flg_val) in enumerate( \
                zip(args.motion_path, args.org_model_path, args.rep_model_path, args.detail_stance_flg, args.twist_flg)): # noqa

                display_set_no = "【No.{0}】".format(set_no + 1)

                # モーションパス --------
                logger.info("%s 調整対象モーションVMD/VPDファイル 読み込み開始", display_set_no)
                
                file_name, input_ext = os.path.splitext(os.path.basename(motion_path))
                if input_ext.lower() == ".vmd":
                    motion_reader = VmdReader(motion_path)
                elif input_ext.lower() == ".vpd":
                    motion_reader = VpdReader(motion_path)
                else:
                    raise SizingException("%s.motion_path 読み込み失敗(拡張子不正): %s", display_set_no, os.path.basename(motion_path), decoration=MLogger.DECORATION_BOX)
                
                motion = motion_reader.read_data()

                logger.info("%s 調整対象モーションVMD/VPDファイル 読み込み成功 %s", display_set_no, os.path.basename(motion_path))

                # 元モデル ----------
                logger.info("%s モーション作成元モデルPMXファイル 読み込み開始", display_set_no)

                file_name, input_ext = os.path.splitext(os.path.basename(org_model_path))
                if input_ext.lower() == ".pmx":
                    org_model_reader = PmxReader(org_model_path)
                else:
                    raise SizingException("%s.org_model_path 読み込み失敗(拡張子不正): %s", display_set_no, os.path.basename(org_model_path), decoration=MLogger.DECORATION_BOX)
                
                org_model = org_model_reader.read_data()

                logger.info("%s モーション作成元モデルPMXファイル 読み込み成功 %s", display_set_no, os.path.basename(org_model_path))

                # 先モデル ----------
                logger.info("%s モーション変換先モデルPMXファイル 読み込み開始", display_set_no)

                file_name, input_ext = os.path.splitext(os.path.basename(rep_model_path))
                if input_ext.lower() == ".pmx":
                    rep_model_reader = PmxReader(rep_model_path)
                else:
                    raise SizingException("%s.rep_model_path 読み込み失敗(拡張子不正): %s", display_set_no, os.path.basename(rep_model_path), decoration=MLogger.DECORATION_BOX)
                
                rep_model = rep_model_reader.read_data()

                logger.info("%s モーション変換先モデルPMXファイル 読み込み成功 %s", display_set_no, os.path.basename(rep_model_path))

                detail_stance_flg = True if detail_stance_flg_val == 1 else False
                twist_flg = True if twist_flg_val == 1 else False

                # 出力ファイルパス
                output_vmd_path = MFileUtils.get_output_vmd_path(motion_path, rep_model_path, detail_stance_flg, twist_flg, arm_process_flg_avoidance, arm_process_flg_alignment, False, "", True)

                data_set = MOptionsDataSet(
                    motion,
                    org_model,
                    rep_model,
                    output_vmd_path,
                    detail_stance_flg,
                    twist_flg,
                    []
                )

                data_set_list.append(data_set)

            options = MOptions(\
                version_name=version_name, \
                logging_level=args.verbose, \
                data_set_list=data_set_list, \
                arm_options=arm_options, \
                monitor=None, \
                is_file=True, \
                outout_datetime=logger.outout_datetime)

            return options
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception as e:
            logger.critical("サイジング処理が意図せぬエラーで終了しました。", e, decoration=MLogger.DECORATION_BOX)


class MOptionsDataSet():

    def __init__(self, motion, org_model, rep_model, output_vmd_path, detail_stance_flg, twist_flg, morph_list):
        self.motion = motion
        self.org_model = org_model
        self.rep_model = rep_model
        self.output_vmd_path = output_vmd_path
        self.detail_stance_flg = detail_stance_flg
        self.twist_flg = twist_flg
        self.morph_list = morph_list
        self.org_motion = self.motion.copy()
        self.test_params = None
        self.full_arms = False

        # 本来の足IKの比率
        self.original_xz_ratio = 1
        self.original_y_ratio = 1

        # 実際に計算に使う足IKの比率
        self.xz_ratio = 1
        self.y_ratio = 1


class MArmProcessOptions():

    def __init__(self, avoidance: bool, avoidance_target_list: list, alignment: bool, alignment_finger_flg: bool, alignment_floor_flg: bool, \
                 alignment_distance_wrist: float, alignment_distance_finger: float, alignment_distance_floor: float, arm_check_skip_flg: bool):
        self.avoidance = avoidance
        self.avoidance_target_list = avoidance_target_list
        self.alignment = alignment
        self.alignment_finger_flg = alignment_finger_flg
        self.alignment_floor_flg = alignment_floor_flg
        self.alignment_distance_wrist = alignment_distance_wrist
        self.alignment_distance_finger = alignment_distance_finger
        self.alignment_distance_floor = alignment_distance_floor
        self.arm_check_skip_flg = arm_check_skip_flg


class MCsvOptions():

    def __init__(self, version_name, logging_level, motion):
        self.version_name = version_name
        self.logging_level = logging_level
        self.motion = motion
    

class MVmdOptions():

    def __init__(self, version_name, logging_level, bone_csv_path, morph_csv_path, camera_csv_path):
        self.version_name = version_name
        self.logging_level = logging_level
        self.bone_csv_path = bone_csv_path
        self.morph_csv_path = morph_csv_path
        self.camera_csv_path = camera_csv_path
    

    