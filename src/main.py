# -*- coding: utf-8 -*-
#
import argparse
import math
import numpy as np
import os
import datetime
from pathlib import Path
from PyQt5.QtGui import QQuaternion, QVector3D, QMatrix4x4, QVector4D
import logging
import csv

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from ModelBone import ModelBole

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

level = {0:logging.ERROR,
            1:logging.WARNING,
            2:logging.INFO,
            3:logging.DEBUG}

def main(vmd_path, trace_bone_path, replace_bone_path, replace_vertex_path):   
    logger.info("vmd: %s", vmd_path)
    logger.info("トレース元: %s", trace_bone_path)
    logger.info("トレース先(ボーン): %s", replace_bone_path)
    logger.info("トレース先(頂点): %s", replace_vertex_path)

    # ボーンCSVファイル名・拡張子
    bone_filename, _ = os.path.splitext(os.path.basename(replace_bone_path))

    # VMD読み込み
    reader = VmdReader()
    motion = reader.read_vmd_file(vmd_path)

    # トレース元モデル
    trace_model = load_model_bones(trace_bone_path)

    # トレース移植先モデル
    replace_model = load_model_bones(replace_bone_path)

    # 移植先のセンターとグルーブは、トレース元の比率に合わせる
    adjust_center(trace_model, replace_model, "センター")
    adjust_center(trace_model, replace_model, "グルーブ")

    # サイズ比較
    lengths = compare_length(trace_model, replace_model)

    # 変換サイズに合わせてモーション変換
    for k, v in motion.frames.items():
        for bf in v:
            if k in lengths:
                if k == "右足ＩＫ" or k == "左足ＩＫ":
                    # 移動量を倍率変換
                    bf.position = bf.position * lengths[k]
                elif k == "センター" or k == "グルーブ":
                    # 移動量を倍率変換
                    bf.position = bf.position * lengths[k]
                # else:
                #     if k in ["左肩" ,"左腕" ,"左腕捩" ,"左ひじ" ,"左手捩" ,"左手首" ,"右肩" ,"右腕" ,"右腕捩" ,"右ひじ" ,"右手捩" ,"右手首"] and os.path.exists(replace_vertex_path):
                #         # 腕系で頂点CSVが存在している場合
                #     # # 一旦オイラー角に変換
                #     # ea = bf.rotation.toEulerAngles()
                #     # # オイラー角のXとZを倍率変換
                #     # ea.setX(ea.x() * lengths[k])
                #     # ea.setZ(ea.z() * lengths[k])
                #     # if k != "上半身" and k != "下半身":
                #     #     # 上半身と下半身のY回転は全身回転と同等なので、加味しない
                #     #     ea.setY(ea.y() * lengths[k])
                #     # # 元に戻して角度配置
                #     # bf.rotation = QQuaternion.fromEulerAngles(ea)

    new_filepath = os.path.join(str(Path(vmd_path).resolve().parents[0]), os.path.basename(vmd_path).replace(".vmd", "_{1}_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.datetime.now(), bone_filename)))

    # ディクショナリ型の疑似二次元配列から、一次元配列に変換
    bone_frames = []
    for k,v in motion.frames.items():
        for bf in v:
            bone_frames.append(bf)
    
    morph_frames = []
    for k,v in motion.morphs.items():
        for mf in v:
            # logger.info("k: %s, mf: %s, %s", k, mf.frame, mf.ratio)
            morph_frames.append(mf)

    writer = VmdWriter()
    writer.write_vmd_file(new_filepath, bone_frames, morph_frames, None)

    logger.info("output: %s", new_filepath)

# 手の位置の計算
def calc_hand(model_bone, direction):

    # ローカル位置
    trans_vs = [0 for i in range(6)]
    # 肩のローカル位置
    trans_vs[0] = model_bone["{0}肩".format(direction)].position
    # 腕捩りのローカル位置
    trans_vs[1] = model_bone["{0}腕捩".format(direction)].position
    # 腕のローカル位置
    trans_vs[2] = model_bone["{0}腕".format(direction)].position
    # ひじのローカル位置
    trans_vs[3] = model_bone["{0}ひじ".format(direction)].position
    # 手捩のローカル位置
    trans_vs[4] = model_bone["{0}手捩".format(direction)].position
    # 手首のローカル位置
    trans_vs[5] = model_bone["{0}手首".format(direction)].position
    
    # 加算用クォータニオン
    add_qs = [0 for i in range(6)]
    # 肩の回転
    add_qs[0] = model_bone["{0}肩".format(direction)].rotation
    # 腕捩りの回転
    add_qs[1] = model_bone["{0}腕捩".format(direction)].rotation
    # 腕の回転
    add_qs[2] = model_bone["{0}腕".format(direction)].rotation
    # ひじの回転
    add_qs[3] = model_bone["{0}ひじ".format(direction)].rotation
    # 手捩の回転
    add_qs[4] = model_bone["{0}手捩".format(direction)].rotation
    # 手首の回転(回転は取れるが、不要なので初期値設定)
    add_qs[5] = QQuaternion()

    # 行列
    matrixs = [0 for i in range(6)]

    for n in range(len(matrixs)):
        # 行列を生成
        matrixs[n] = QMatrix4x4()
        # 移動
        matrixs[n].translate(trans_vs[n])
        # 回転
        matrixs[n].rotate(add_qs[n])

        # logger.debug("matrixs n: %s, %s", n, matrixs[n])

    # 手首の位置
    wrist_pos = matrixs[0] * matrixs[1] * matrixs[2] * matrixs[3] * matrixs[4] * QVector4D(trans_vs[5], 1)

    return wrist_pos.toVector3D()


def adjust_center(trace_model, replace_model, bone_name):
    if bone_name in trace_model and bone_name in replace_model and "左足" in trace_model and "左足" in replace_model:
        # 移植元にも移植先にも対象ボーンがある場合
        # 左足付け根のY位置
        leg_y = trace_model["左足"].position.y()
        # センター（もしくはグルーブ）のY位置
        center_y = trace_model[bone_name].position.y()
        # 足のどの辺りにセンターがあるか判定
        ratio_y = center_y / leg_y
        
        # トレース元と同じ比率の位置にセンターを置く
        replace_model[bone_name].len = replace_model["左足"].position.y() * ratio_y

def compare_length(trace_model, replace_model):
    lengths = {}

    for k, v in replace_model.items():
        # 移植先モデルのボーン構造チェック
        if k in trace_model:
            # 同じ項目がトレース元にもある場合
            trace_bone_length = trace_model[k].len
            replace_bone_length = replace_model[k].len

            # 0割対策を入れて、倍率取得
            length = replace_bone_length if trace_bone_length == 0 else replace_bone_length / trace_bone_length

            # length.setX(length.x() if np.isnan(length.x()) == False and np.isinf(length.x()) == False else 0)
            # length.setY(length.y() if np.isnan(length.y()) == False and np.isinf(length.y()) == False else 0)
            # length.setZ(length.z() if np.isnan(length.z()) == False and np.isinf(length.z()) == False else 0)
            logger.info("bone: %s, trace: %s, replace: %s, length: %s", k, trace_bone_length, replace_bone_length, length)

            lengths[k] = length
    
    return lengths

# モデルボーン構造を解析する
def load_model_bones(bone_path):
    # キー：ボーン名, 値：ボーンデータ
    bones = {}

    # ボーンファイルを開く
    with open(bone_path, "r", encoding=get_file_encoding(bone_path)) as bf:
        reader = csv.reader(bf)

        for row in reader:
            if row[0] == "IKLink":
                # IKリンク行
                if row[1] in bones:
                    bones[row[1]].links.append(row[2])
                else:
                    logger.warn("IKボーンなし: %s", row[1])
            elif row[0] == "Bone":
                # 通常ボーン行                 
                bone = ModelBole()
                bone.name = row[1]
                bone.parent = row[13]
                bone.position = QVector3D(float(row[5]), float(row[6]), float(row[7]))

                bones[bone.name] = bone
    
    for k, v in bones.items():
        if "ＩＫ" in k:
            # IKの場合、リンクボーンの離れている方を採用する
            farer_pos = QVector3D(0,0,0)
            for l in v.links:
                if l in bones and farer_pos.length() < bones[l].position.length():
                    # 存在するボーンで、大きい方を採用
                    farer_pos = bones[l].position
            # 最も大きな値（離れている）のを採用
            v.len = (v.position - farer_pos).length()
        elif k == "グルーブ" or k == "センター":
            # 親がグルーブの場合、センターとの連動は行わない
            v.len = v.position.length()
        else:
            # IK以外の場合、親ボーンとの間の長さを「親ボーン」に設定する
            if v.parent is not None and v.parent in bones and v.parent != "グルーブ" and v.parent != "センター":
                # 親ボーンを採用
                pos = v.position - bones[v.parent].position
                if v.len > 0:
                    # 既にある場合、平均値を求めて設定する
                    bones[v.parent].len = (v.len + pos.length()) / 2
                else:
                    # 0の場合はそのまま追加
                    bones[v.parent].len = pos.length()
            else:
                # 自分が最親の場合、そのまま長さ
                v.len = v.position.length()

    return bones


# ファイルのエンコードを取得する
def get_file_encoding(file_path):

    try: 
        f = open(file_path, "rb")
        fbytes = f.read()
        f.close()
    except:
        raise Exception("unknown encoding!")
        
    codelst = ('utf_8', 'shift-jis')
    
    for encoding in codelst:
        try:
            fstr = fbytes.decode(encoding) # bytes文字列から指定文字コードの文字列に変換
            fstr = fstr.encode('utf-8') # uft-8文字列に変換
            # 問題なく変換できたらエンコードを返す
            logger.debug("%s: encoding: %s", file_path, encoding)
            return encoding
        except:
            pass
            
    raise Exception("unknown encoding!")
    
if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vmd_path', dest='vmd_path', help='input vmd', type=str)
    parser.add_argument('--trace_bone_path', dest='trace_bone_path', help='input trace bone csv', type=str)
    parser.add_argument('--replace_bone_path', dest='replace_bone_path', help='replace trace bone csv', type=str)
    parser.add_argument('--replace_vertex_path', dest='replace_vertex_path', help='replace trace vertex csv', type=str)
    parser.add_argument('--verbose', dest='verbose', help='verbose', type=int)
    args = parser.parse_args()

    logger.setLevel(level[args.verbose])

    main(args.vmd_path, args.trace_bone_path, args.replace_bone_path, args.replace_vertex_path)