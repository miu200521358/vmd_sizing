#! env python
# -*- coding: utf-8 -*-

import os.path
import glob
import traceback
import copy
from datetime import datetime
from pathlib import Path
from PyQt5.QtGui import QQuaternion, QVector3D
import re
import sys
import winsound

import main
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
from VmdReader import VmdReader
from VpdReader import VpdReader
import utils

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VmdSizing").getChild(__name__)

def is_valid_file(base_file_path, file_type, exts, is_print=True, is_aster=False):
    logger.debug("aster: %s", is_aster)
    if is_aster:
        file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

        if len(file_path_list) == 0:
            return False

        file_path = file_path_list[0]
    else:
        file_path = base_file_path

    if not os.path.exists(file_path):
        if is_print:
            print("■■■■■■■■■■■■■■■■■")
            print("■　**ERROR**　")
            print("■　"+ file_type +"が見つかりませんでした。")
            print("■　入力パス: "+ file_path )
            print("■■■■■■■■■■■■■■■■■")

        return False
    
    if not os.path.isfile(file_path):
        if is_print:
            print("■■■■■■■■■■■■■■■■■")
            print("■　**ERROR**　")
            print("■　"+ file_type +"が正常なファイルとして見つかりませんでした。")
            print("■　入力パス: "+ file_path )
            print("■■■■■■■■■■■■■■■■■")

        return False
    
    # ボーンCSVファイル名・拡張子
    test_file_name, test_ext = os.path.splitext(os.path.basename(file_path))
    logger.debug("file_name: %s, test_ext: %s, exts: %s", test_file_name, test_ext, exts)

    if test_ext.lower() not in exts:
        if is_print:
            print("■■■■■■■■■■■■■■■■■")
            print("■　**ERROR**　")
            print("■　"+ file_type +"の拡張子が正しくありません。")
            print("■　入力パス: "+ file_path )
            print("■　設定可能拡張子: "+ ",".join(exts) )
            print("■■■■■■■■■■■■■■■■■")

        return False
    
    return True

def is_all_sizing(motion, org_pmx, rep_pmx, camera_motion, output_vmd_path=None):
    
    if org_pmx and rep_pmx and motion:
        not_org_bones = []
        not_org_morphs = []
        not_rep_bones = []
        not_rep_morphs = []

        # 両方のPMXが読めて、モーションも読み込めた場合、キーチェック
        
        # ボーン
        for k in motion.frames.keys():
            if len(motion.frames[k]) > 1 or (motion.frames[k][0].position != QVector3D() or motion.frames[k][0].rotation != QQuaternion()):
                # print("k :%s, len: %s, pos: %s, rot: %s" % ( k, len(motion.frames[k]), motion.frames[k][0].position, motion.frames[k][0].rotation))

                # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                if k not in org_pmx.bones:
                    not_org_bones.append(k)

                if k not in rep_pmx.bones:
                    not_rep_bones.append(k)

        # モーフ
        for k in motion.morphs.keys():
            if len(motion.morphs[k]) > 1 or motion.morphs[k][0].ratio != 0:
                # print("k :%s, len: %s, ratio: %s" % ( k, len(motion.morphs[k]), motion.morphs[k][0].ratio != 0))
                # if k == "瞳縦潰れ":
                #     print([x.frame for x in motion.morphs[k]])
                # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                if k not in org_pmx.morphs:
                    not_org_morphs.append(k)

                if k not in rep_pmx.morphs:
                    not_rep_morphs.append(k)

        # 何かしら不足しているか
        is_shortage = False
        
        error_file_logger = None

        if len(not_org_bones) > 0 or (not output_vmd_path and len(not_org_morphs) > 0):
            print_methods = []
            if output_vmd_path:
                error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, output_vmd_path)
                print_methods = [print, error_file_logger.info]
            else:
                print_methods = [print]

            for print_method in print_methods:
                print_method("■■■■■■■■■■■■■■■■■")
                print_method("■　**WARNING**　")
                print_method("■　作成元モデルにモーションで使用されているボーン・モーフが不足しています。")
                print_method("■　ボーン: %s" % ",".join(not_org_bones))
                print_method("■　モーフ: %s" % ",".join(not_org_morphs))
                print_method("■■■■■■■■■■■■■■■■■")

            is_shortage = True

        if len(not_rep_bones) > 0 or (not output_vmd_path and len(not_rep_morphs) > 0):
            print_methods = []
            if output_vmd_path:
                error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, output_vmd_path)
                print_methods = [print, error_file_logger.info]
            else:
                print_methods = [print]

            for print_method in print_methods:
                print_method("■■■■■■■■■■■■■■■■■")
                print_method("■　**WARNING**　")
                print_method("■　変換先モデルにモーションで使用されているボーン・モーフが不足しています。")
                print_method("■　ボーン: %s" % ",".join(not_rep_bones))
                print_method("■　モーフ: %s" % ",".join(not_rep_morphs))
                print_method("■■■■■■■■■■■■■■■■■")

            is_shortage = True

        if is_shortage == False and not output_vmd_path:
            # OKのメッセージはUIログのみ
            print("■■■■■■■■■■■■■■■■■")
            print("■　**OK**　")
            print("■　変換先モデルにモーションで使用されているボーン・モーフが揃っています。")
            print("■■■■■■■■■■■■■■■■■")
        
        if not org_pmx.can_arm_sizing:
            # 作成元モデルの腕構造チェック
            print_methods = []
            if output_vmd_path:
                error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, output_vmd_path)
                print_methods = [print, error_file_logger.info]
            else:
                print_methods = [print]

            for print_method in print_methods:
                print_method("■■■■■■■■■■■■■■■■■")
                print_method("■　**WARNING**　")
                print_method("■　作成元モデルの腕構造が標準・準標準ボーン構造でない可能性があります。")
                print_method("■　腕スタンス補正・手首位置合わせ処理をスキップします。")
                print_method("■■■■■■■■■■■■■■■■■")
        
            is_shortage = True

        if not rep_pmx.can_arm_sizing:
            # 変換先モデルの腕構造チェック
            print_methods = []
            if output_vmd_path:
                error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, output_vmd_path)
                print_methods = [print, error_file_logger.info]
            else:
                print_methods = [print]

            for print_method in print_methods:
                print_method("■■■■■■■■■■■■■■■■■")
                print_method("■　**WARNING**　")
                print_method("■　変換先モデルの腕構造が標準・準標準ボーン構造でない可能性があります。")
                print_method("■　腕スタンス補正・手首位置合わせ処理をスキップします。")
                print_method("■■■■■■■■■■■■■■■■■")
        
            is_shortage = True

        if motion.motion_cnt == 0:
            print_methods = []
            if output_vmd_path:
                error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, output_vmd_path)
                print_methods = [print, error_file_logger.info]
            else:
                print_methods = [print]

            for print_method in print_methods:
                print_method("■■■■■■■■■■■■■■■■■")
                print_method("■　**WARNING**　")
                print_method("■　ボーンモーションデータにキーフレームが登録されていません。")
                print_method("■■■■■■■■■■■■■■■■■")
        
            is_shortage = True

        if camera_motion and camera_motion.camera_cnt == 0:
            print_methods = []
            if output_vmd_path:
                error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, output_vmd_path)
                print_methods = [print, error_file_logger.info]
            else:
                print_methods = [print]

            for print_method in print_methods:
                print_method("■■■■■■■■■■■■■■■■■")
                print_method("■　**WARNING**　")
                print_method("■　カメラモーションデータにキーフレームが登録されていません。")
                print_method("■■■■■■■■■■■■■■■■■")

            is_shortage = True

    return is_shortage

def read_vmd(path, filetype="vmd", is_print=True, is_aster=False):
    if is_valid_file(path, filetype, [".vmd"], is_print, is_aster) == False:
        return None

    reader = VmdReader()
    try:
        vmd = reader.read_vmd_file(path)
    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

        # 終了音を鳴らす
        winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)

        return None
            
    return vmd

def read_vmd_modelname(base_file_path):
    if is_valid_file(base_file_path, "vmd", [".vmd"], is_print=False, is_aster=True) == False:
        return None

    file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

    if len(file_path_list) > 0 and os.path.exists(file_path_list[0]):
        
        reader = VmdReader()
        try:
            model_name = reader.read_vmd_file_modelname(file_path_list[0])
            return model_name
        except Exception:
            print("■■■■■■■■■■■■■■■■■")
            print("■　**ERROR**　")
            print("■　VMDデータの解析に失敗しました。")
            print("■■■■■■■■■■■■■■■■■")
            
            print(traceback.format_exc())

            return None
    
    return None


def read_vpd(path, filetype="vpd", is_print=True, is_aster=False):
    if is_valid_file(path, filetype, [".vpd"], is_print, is_aster) == False:
        return None

    reader = VpdReader()
    try:
        vpd = reader.read_vpd_file(path)
    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VPDデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

        # 終了音を鳴らす
        winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)

        return None
            
    return vpd

def read_vpd_modelname(base_file_path):
    if is_valid_file(base_file_path, "vpd", [".vpd"], is_print=False, is_aster=True) == False:
        return None

    file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

    if len(file_path_list) > 0 and os.path.exists(file_path_list[0]):
        
        reader = VpdReader()
        try:
            model_name = reader.read_vpd_file_modelname(file_path_list[0])
            return model_name
        except Exception:
            print("■■■■■■■■■■■■■■■■■")
            print("■　**ERROR**　")
            print("■　VPDデータの解析に失敗しました。")
            print("■■■■■■■■■■■■■■■■■")
            
            print(traceback.format_exc())

            return None
    
    return None


def read_pmx_modelname(base_file_path):
    if is_valid_file(base_file_path, "pmx", ".pmx", is_print=False, is_aster=True) == False:
        return None

    file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

    reader = PmxReader()
    try:
        model_name = reader.read_pmx_file_modelname(base_file_path)
        return model_name
    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　PMXデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())
    
    return None


def read_pmx(path, filetype="pmx", is_print=True):
    if is_valid_file(path, filetype, [".pmx"], is_print, is_aster=False) == False:
        return None

    reader = PmxReader()
    try:
        pmx = reader.read_pmx_file(path)
    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　PMXデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

        # 終了音を鳴らす
        winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)

        return None
            
    return pmx


def exec(motion, org_pmx, rep_pmx, vmd_path, org_pmx_path, rep_pmx_path, output_vmd_path, \
        is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, is_floor_hand, is_floor_hand_up, is_floor_hand_down, hand_floor_distance, leg_floor_distance, is_finger, finger_distance, vmd_choice_values, rep_choice_values, rep_rate_values, \
        camera_motion, camera_vmd_path, camera_pmx, camera_pmx_path, output_camera_vmd_path, camera_y_offset):
    print("■■■■■■■■■■■■■■■■■")
    print("■　VMDサイジング処理実行")
    print("■■■■■■■■■■■■■■■■■")

    error_file_logger = None
    
    try:
        if not output_vmd_path:
            output_vmd_path = create_output_path(vmd_path, rep_pmx_path, is_avoidance, is_hand_ik, len(vmd_choice_values) > 0)
            if output_vmd_path == None:
                return False

        if not output_camera_vmd_path:
            output_camera_vmd_path = create_output_camera_path(camera_vmd_path, rep_pmx_path)

        # 出力ディレクトリ作っとく
        new_dir = os.path.dirname(output_vmd_path)
        if os.path.exists(new_dir) == False:
            print("出力対象VMDファイル用フォルダ作成 %s" % new_dir)
            os.makedirs(new_dir, exist_ok=True)
        else:
            if os.path.isdir(new_dir) == False:
                print("■■■■■■■■■■■■■■■■■")
                print("■　**ERROR**　")
                print("■　生成予定のファイルパスのフォルダ構成が正しくないため、処理を中断します。")
                print("■　生成予定パス: "+ output_vmd_path )
                print("■■■■■■■■■■■■■■■■■")

                return False

        if output_camera_vmd_path:
            # カメラ用出力ディレクトリ作っとく
            new_dir = os.path.dirname(output_camera_vmd_path)
            if os.path.exists(new_dir) == False:
                print("出力対象カメラVMDファイル用フォルダ作成 %s" % new_dir)
                os.makedirs(new_dir, exist_ok=True)
            else:
                if os.path.isdir(new_dir) == False:
                    print("■■■■■■■■■■■■■■■■■")
                    print("■　**ERROR**　")
                    print("■　生成予定のファイルパスのフォルダ構成が正しくないため、処理を中断します。")
                    print("■　生成予定パス: "+ output_camera_vmd_path )
                    print("■■■■■■■■■■■■■■■■■")

                    return False
            
        logger.debug("フォルダ生成終了")

        # VMD読み込み
        if not motion:
            motion = read_vmd(vmd_path)

        # 作成元モデル
        if not org_pmx:
            org_pmx = read_pmx(org_pmx_path)

        # 変換先モデル
        if not rep_pmx:
            rep_pmx = read_pmx(rep_pmx_path)
        
        # カメラVMD読み込み
        if not camera_motion and camera_vmd_path and os.path.exists(camera_vmd_path):
            camera_motion = read_vmd(camera_vmd_path)
        
        # カメラPMX読み込み
        # 前のデータが無い場合、内部的に前のモーションPMXデータを保持してしまうので、とりあえずクリア
        if camera_pmx:
            # カメラPMXがある場合
            camera_pmx_data = camera_pmx
        else:
            # カメラPMXがない場合
            if camera_pmx_path and os.path.exists(camera_pmx_path):
                camera_pmx_data = read_pmx(camera_pmx_path)
            else:
                # 未指定の場合、作成元モデルをそのまま使用
                camera_pmx_data = org_pmx

        if motion and org_pmx and rep_pmx:
            # ファイル出力タイプでサイジングチェック
            is_shortage = is_all_sizing(motion, org_pmx, rep_pmx, camera_motion, output_vmd_path)

            # 実処理実行
            # 読み込んだモーションデータそのものを弄らないよう、コピーした結果を渡す
            is_success = main.main(copy.deepcopy(motion), org_pmx, rep_pmx, output_vmd_path, \
                is_avoidance, is_avoidance_finger, is_hand_ik, hand_distance, is_floor_hand, is_floor_hand_up, is_floor_hand_down, hand_floor_distance, leg_floor_distance, is_finger, finger_distance, vmd_choice_values, rep_choice_values, rep_rate_values, \
                copy.deepcopy(camera_motion), camera_vmd_path, camera_pmx_data, output_camera_vmd_path, camera_y_offset)

            logger.debug("is_shortage: %s, is_success: %s", is_shortage, is_success)

            if is_shortage or not is_success:
                print("■■■■■■■■■■■■■■■■■")
                print("■　サイジングに失敗している箇所があります。")
                print("■　ログを確認してください。")
                print("■■■■■■■■■■■■■■■■■")
                print("")
            
            # 実行後、出力ファイル存在チェック
            try:
                Path(output_vmd_path).resolve(True)
            except FileNotFoundError as e:
                print("■■■■■■■■■■■■■■■■■")
                print("■　**ERROR**　")
                print("■　出力VMDファイルが正常に作成されなかったようです。")
                print("■　パスを確認してください。")
                print("■　出力VMDファイルパス: "+ output_vmd_path )
                print("■■■■■■■■■■■■■■■■■")
                print("")
                print(e.with_traceback(sys.exc_info()[2]))

                # 終了音を鳴らす
                winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)

                return False

        else:
            print("ファイルデータが正しく読み込まれていないようです。\nもう一度ボタンをクリックしてみてください。")
            return False

    except SizingException as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が処理できないデータで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        print("")
        print(e.message)

        error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, output_vmd_path)
        
        error_file_logger.error("■■■■■■■■■■■■■■■■■")
        error_file_logger.error("■　**ERROR**　")
        error_file_logger.error("■　VMDサイジング処理が処理できないデータで終了しました。")
        error_file_logger.error("■■■■■■■■■■■■■■■■■")

        error_file_logger.error(e.message)

        # 終了音を鳴らす
        winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")

        print(traceback.format_exc())

        error_file_logger = utils.create_error_file_logger(motion, org_pmx, rep_pmx, output_vmd_path)
        
        error_file_logger.error("■■■■■■■■■■■■■■■■■")
        error_file_logger.error("■　**ERROR**　")
        error_file_logger.error("■　VMDサイジング処理が意図せぬエラーで終了しました。")
        error_file_logger.error("■■■■■■■■■■■■■■■■■")

        error_file_logger.error(traceback.format_exc())

        # 終了音を鳴らす
        winsound.PlaySound("SystemQuestion", winsound.SND_ALIAS)

    finally:
        logging.shutdown()

# モーフ組み合わせファイル用パス生成
def create_output_morph_path(vmd_path, org_pmx_path, rep_pmx_path):

    if not os.path.exists(vmd_path) or not os.path.exists(org_pmx_path) or not os.path.exists(rep_pmx_path):
        return None

    # ボーンCSVファイル名・拡張子
    org_bone_filename, _ = os.path.splitext(os.path.basename(org_pmx_path))

    # ボーンCSVファイル名・拡張子
    rep_bone_filename, _ = os.path.splitext(os.path.basename(rep_pmx_path))

    output_moprh_path = os.path.join(get_dir_path(vmd_path), os.path.basename(vmd_path).replace(".vmd", "_{0}_{1}.csv".format(org_bone_filename, rep_bone_filename)))

    if len(output_moprh_path) >= 255 and os.name == "nt":
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　生成予定のファイルパスがWindowsの制限を超えているため、処理を中断します。")
        print("■　生成予定パス: "+ output_moprh_path )
        print("■■■■■■■■■■■■■■■■■")
        return None
    
    return output_moprh_path

def create_output_path(vmd_base_path, replace_pmx_path, is_avoidance, is_arm_ik, is_morph):
    # print("vmd_path: %s " % vmd_path)
    # print("replace_pmx_path: %s" % replace_pmx_path)
    # print("is_morph: %s" % is_morph)
    		
    file_path_list = [p for p in glob.glob(vmd_base_path) if os.path.isfile(p)]

    if len(file_path_list) == 0 or ( len(file_path_list) > 0 and not os.path.exists(file_path_list[0])) or not os.path.exists(replace_pmx_path):
        return None

    vmd_path = file_path_list[0]

    # ボーンCSVファイル名・拡張子
    bone_filename, _ = os.path.splitext(os.path.basename(replace_pmx_path))

    # 腕サフィックス
    arm_suffix = ""
    if is_avoidance: arm_suffix = "A"
    if is_arm_ik: arm_suffix = "P"

    # モーフサフィックス
    morph_suffix = ""
    if is_morph: morph_suffix = "M"

    if ".vpd" in vmd_path:
        output_vmd_path = os.path.join(get_dir_path(vmd_path), os.path.basename(vmd_path).replace(".vpd", "_{1}{2}{3}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now(), bone_filename, morph_suffix, arm_suffix)))
    else:
        output_vmd_path = os.path.join(get_dir_path(vmd_path), os.path.basename(vmd_path).replace(".vmd", "_{1}{2}{3}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now(), bone_filename, morph_suffix, arm_suffix)))

    if len(output_vmd_path) >= 255 and os.name == "nt":
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　生成予定のファイルパスがWindowsの制限を超えているため、処理を中断します。")
        print("■　生成予定パス: "+ output_vmd_path )
        print("■■■■■■■■■■■■■■■■■")
        return None
    
    return output_vmd_path

def is_auto_output_path(output_vmd_path, vmd_path, replace_pmx_path, force=False):
    if not output_vmd_path:
        # 空のパスの場合、自動生成対象とみなす
        logger.debug("空パス: %s", output_vmd_path)
        return True

    # ボーンCSVファイル名・拡張子
    bone_filename, _ = os.path.splitext(os.path.basename(replace_pmx_path))

    # 新しく設定賞としている自動生成出力ファイルパス
    if ".vpd" in vmd_path:
        new_output_vmd_path = os.path.join(get_dir_path(vmd_path), os.path.basename(vmd_path).replace(".vpd", "_{0}".format(bone_filename)))
    else:
        new_output_vmd_path = os.path.join(get_dir_path(vmd_path), os.path.basename(vmd_path).replace(".vmd", "_{0}".format(bone_filename)))

    logger.debug("new_output_vmd_path: %s", new_output_vmd_path)
    logger.debug("force: %s", force)
    logger.debug("output_vmd_path: %s", output_vmd_path)

    if force and new_output_vmd_path not in output_vmd_path:
        # 強制変更が必要かつパスが変わっている場合、自動生成対象とみなす
        logger.debug("force変更あり: %s", new_output_vmd_path)
        return True

    # 新しく設定しようとしている出力ファイルパスの正規表現    
    new_output_vmd_path = escape_filepath(new_output_vmd_path)
    logger.debug("new_output_vmd_path: %s", new_output_vmd_path)

    if ".vpd" in vmd_path:
        new_output_vmd_pattern = re.compile(r'^%s%s.vpd$' % (new_output_vmd_path, r"\w?\w?_\d{8}_\d{6}"))
    else:
        new_output_vmd_pattern = re.compile(r'^%s%s.vmd$' % (new_output_vmd_path, r"\w?\w?_\d{8}_\d{6}"))

    logger.debug("new_output_vmd_pattern: %s", new_output_vmd_pattern)
    logger.debug("re.match(new_output_vmd_pattern, output_vmd_path): %s", re.match(new_output_vmd_pattern, output_vmd_path))

    return re.match(new_output_vmd_pattern, output_vmd_path) is not None

def escape_filepath(path):
    path = path.replace("\\", r"\\")
    path = path.replace("*", "\\*")
    path = path.replace("+", "\\+")
    path = path.replace(".", "\\.")
    path = path.replace("?", "\\?")
    path = path.replace("{", "\\{")
    path = path.replace("}", "\\}")
    path = path.replace("(", "\\(")
    path = path.replace(")", "\\)")
    path = path.replace("[", "\\[")
    path = path.replace("]", "\\]")
    path = path.replace("{", "\\{")
    path = path.replace("^", "\\^")
    path = path.replace("$", "\\$")
    path = path.replace("-", "\\-")
    path = path.replace("|", "\\|")
    path = path.replace("/", "\\/")

    return path

def create_output_camera_path(camera_vmd_path, replace_pmx_path):
    # print("camera_vmd_path: %s " % camera_vmd_path)
    # print("replace_pmx_path: %s" % replace_pmx_path)
    # print("is_morph: %s" % is_morph)

    if not os.path.exists(camera_vmd_path) or not os.path.exists(replace_pmx_path):
        return None

    # ボーンCSVファイル名・拡張子
    bone_filename, _ = os.path.splitext(os.path.basename(replace_pmx_path))

    output_camera_camera_vmd_path = os.path.join(get_dir_path(camera_vmd_path), os.path.basename(camera_vmd_path).replace(".vmd", "_{1}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now(), bone_filename)))

    if len(output_camera_camera_vmd_path) >= 255 and os.name == "nt":
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　生成予定のファイルパスがWindowsの制限を超えているため、処理を中断します。")
        print("■　生成予定パス: "+ output_camera_camera_vmd_path )
        print("■■■■■■■■■■■■■■■■■")
        return None
    
    return output_camera_camera_vmd_path


def is_auto_output_camera_path(output_camera_vmd_path, vmd_path, replace_pmx_path, force=False):
    if not output_camera_vmd_path:
        # 空のパスの場合、自動生成対象とみなす
        logger.debug("空パス: %s", output_camera_vmd_path)
        return True

    # ボーンCSVファイル名・拡張子
    bone_filename, _ = os.path.splitext(os.path.basename(replace_pmx_path))

    now_output_camera_vmd_path = os.path.join(get_dir_path(vmd_path), os.path.basename(vmd_path).replace(".vmd", "_{0}".format(bone_filename)))
    logger.debug("now_output_camera_vmd_path: %s", now_output_camera_vmd_path)
    logger.debug("force: %s", force)
    logger.debug("output_camera_vmd_path: %s", output_camera_vmd_path)

    if force and now_output_camera_vmd_path not in output_camera_vmd_path:
        # 強制変更が必要かつパスが変わっている場合、自動生成対象とみなす
        logger.debug("force変更あり: %s", now_output_camera_vmd_path)
        return True
    
    now_output_camera_vmd_path = escape_filepath(now_output_camera_vmd_path)
    logger.debug("now_output_camera_vmd_path: %s", now_output_camera_vmd_path)

    output_camera_vmd_pattern = re.compile(r'^%s_\d{8}_\d{6}.vmd$' % (now_output_camera_vmd_path) )
    logger.debug("output_camera_vmd_pattern: %s", output_camera_vmd_pattern)
    logger.debug("re.match(output_camera_vmd_pattern, output_camera_vmd_path): %s", re.match(output_camera_vmd_pattern, output_camera_vmd_path))

    return re.match(output_camera_vmd_pattern, output_camera_vmd_path) is not None


def is_decimal(value):
    """
    小数チェック
    符号は認めない
    :param value: チェック対象の文字列
    :rtype: チェック対象文字列が、整数または小数の場合 True True
    """
    return re.match(r"^[0-9]*[.]?[0-9]+$", value) is not None


def get_mypath(filename):
    dir_path = Path(sys.argv[0]).parent if hasattr(sys, "frozen") else Path(__file__).parent
    file_path = os.path.join(dir_path, filename)
    logger.debug("get_mypath: %s", file_path)

    return file_path

def get_dir_path(base_file_path, is_print=True):
    file_path_list = [p for p in glob.glob(base_file_path) if os.path.isfile(p)]

    if len(file_path_list) == 0:
        return ""

    try:
        # ファイルパスをオブジェクトとして解決し、親を取得する
        return str(Path(file_path_list[0]).resolve().parents[0])
    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　ファイルパスの解析に失敗しました。")
        print("■　パスに使えない文字がないか確認してください。")
        print("■　ファイルパス: "+ base_file_path )
        print("■■■■■■■■■■■■■■■■■")
        print("")
        print(e.with_traceback(sys.exc_info()[2]))
        raise e

