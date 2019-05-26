#! env python
# -*- coding: utf-8 -*-

import os.path
import traceback
from datetime import datetime
from pathlib import Path
from PyQt5.QtGui import QQuaternion, QVector3D

import main
from PmxModel import PmxModel
from PmxReader import PmxReader
from VmdReader import VmdReader
from ModelBone import ModelBone

def is_executable(vmd_path, org_pmx_path, rep_pmx_path):

    # 調整対象vmdファイル
    if is_valid_file(vmd_path, "調整対象VMDファイル") == False:
        return False

    # トレース元モデルPmxファイル
    if is_valid_file(org_pmx_path, "トレース元モデルPMXファイル") == False:
        return False

    # トレース変換先モデルPmxファイル
    if is_valid_file(rep_pmx_path, "トレース変換先モデルPMXファイル") == False:
        return False

    return True

def is_valid_file(file_path, file_type):

    if not os.path.exists(file_path):
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　"+ file_type +"が見つかりませんでした。")
        print("■　入力パス: "+ file_path )
        print("■■■■■■■■■■■■■■■■■")

        return False
    
    if not os.path.isfile(file_path):
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　"+ file_type +"が正常なファイルとして見つかりませんでした。")
        print("■　入力パス: "+ file_path )
        print("■■■■■■■■■■■■■■■■■")

        return False
    
    return True

def is_all_sizing(vmd_path, org_pmx_path, rep_pmx_path):
    if is_executable(vmd_path, org_pmx_path, rep_pmx_path):
        # 実行可能な場合、全サイジングが可能かチェック
        motion = read_vmd(vmd_path)
        org_pmx = read_pmx(org_pmx_path)
        rep_pmx = read_pmx(rep_pmx_path)

        if org_pmx and rep_pmx and motion:
            not_org_bones = []
            not_org_morphs = []
            not_rep_bones = []
            not_rep_morphs = []

            # 両方のPMXが読めて、モーションも読み込めた場合、キーチェック
            
            # ボーン
            for k in motion.frames.keys():
                if len(motion.frames[k]) > 1 or (motion.frames[k][0].position != QVector3D() or motion.frames[k][0].rotation != QQuaternion()):
                    # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                    if k not in org_pmx.bones:
                        not_org_bones.append(k)

                    if k not in rep_pmx.bones:
                        not_rep_bones.append(k)

            # モーフ
            for k in motion.morphs.keys():
                if len(motion.morphs[k]) > 1 or motion.morphs[k][0].ratio != 0:
                    # キーが存在しており、かつ初期値ではない値が入っている場合、警告対象
                    if k not in org_pmx.morphs:
                        not_org_morphs.append(k)

                    if k not in rep_pmx.morphs:
                        not_rep_morphs.append(k)

            # 何かしら不足しているか
            is_shortage = False

            if len(not_org_bones) > 0 or len(not_org_morphs) > 0:
                print("■■■■■■■■■■■■■■■■■")
                print("■　**WARNING**　")
                print("■　トレース元のモデルにモーションで使用されているボーン・モーフが不足しています。")
                print("■　ボーン: %s" % ",".join(not_org_bones))
                print("■　モーフ: %s" % ",".join(not_org_morphs))
                print("■■■■■■■■■■■■■■■■■")

                is_shortage = True

            if len(not_rep_bones) > 0 or len(not_rep_morphs) > 0:
                print("■■■■■■■■■■■■■■■■■")
                print("■　**WARNING**　")
                print("■　変換後のモデルにモーションで使用されているボーン・モーフが不足しています。")
                print("■　ボーン: %s" % ",".join(not_rep_bones))
                print("■　モーフ: %s" % ",".join(not_rep_morphs))
                print("■■■■■■■■■■■■■■■■■")

                is_shortage = True

            if is_shortage == False:
                print("■■■■■■■■■■■■■■■■■")
                print("■　**OK**　")
                print("■　変換後のモデルにモーションで使用されているボーン・モーフが揃っています。")
                print("■■■■■■■■■■■■■■■■■")

                return True

    return False                

def read_vmd(path):
    reader = VmdReader()
    try:
        vmd = reader.read_vmd_file(path)
    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

        return None
            
    return vmd


def read_pmx(path):
    reader = PmxReader()
    try:
        pmx = reader.read_pmx_file(path)
    except Exception as e:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　PMXデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

        return None
            
    return pmx


def exec(vmd_path, org_pmx_path, rep_pmx_path, output_vmd_path, is_avoidance):
    print("■■■■■■■■■■■■■■■■■")
    print("■　VMDサイジング処理実行")
    print("■■■■■■■■■■■■■■■■■")

    try:
        if not output_vmd_path:
            output_vmd_path = create_output_path(vmd_path, rep_pmx_path)
            if output_vmd_path == None:
                return False
        
        # ディレクトリ作っとく
        new_dir = os.path.dirname(output_vmd_path)
        if os.path.exists(new_dir) == False:
            print("出力対象vmdファイル用フォルダ作成 %s" % new_dir)
            os.makedirs(new_dir, exist_ok=True)
        else:
            if os.path.isdir(new_dir) == False:
                print("■■■■■■■■■■■■■■■■■")
                print("■　**ERROR**　")
                print("■　生成予定のファイルパスのフォルダ構成が正しくないため、処理を中断します。")
                print("■　生成予定パス: "+ output_vmd_path )
                print("■■■■■■■■■■■■■■■■■")

                return False

        # VMD読み込み
        motion = read_vmd(vmd_path)

        # トレース元モデル
        org_pmx = read_pmx(org_pmx_path)

        # 変換先モデル
        rep_pmx = read_pmx(rep_pmx_path)

        if motion and org_pmx and read_pmx:
            main.main(motion, org_pmx, rep_pmx, output_vmd_path, is_avoidance)

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMDサイジング処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")

        print(traceback.format_exc())

def create_output_path(vmd_path, replace_pmx_path):
    # print("vmd_path: %s " % vmd_path)
    # print("replace_pmx_path: %s" % replace_pmx_path)

    if not os.path.exists(vmd_path) or not os.path.exists(replace_pmx_path):
        return None

    # ボーンCSVファイル名・拡張子
    bone_filename, _ = os.path.splitext(os.path.basename(replace_pmx_path))

    output_vmd_path = os.path.join(str(Path(vmd_path).resolve().parents[0]), os.path.basename(vmd_path).replace(".vmd", "_{1}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now(), bone_filename)))

    if len(output_vmd_path) >= 255 and os.name == "nt":
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　生成予定のファイルパスがWindowsの制限を超えているため、処理を中断します。")
        print("■　生成予定パス: "+ output_vmd_path )
        print("■■■■■■■■■■■■■■■■■")
        return None
    
    return output_vmd_path
