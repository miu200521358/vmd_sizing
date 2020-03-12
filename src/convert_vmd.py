#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
import re
import logging
import traceback
import argparse
import os.path
import sys
import csv
from datetime import datetime
from PyQt5.QtGui import QQuaternion, QVector3D

from VmdWriter import VmdWriter, VmdBoneFrame, VmdMorphFrame, VmdCameraFrame
from VmdReader import VmdReader, VmdMotion
import wrapperutils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(csv_bone_path, csv_morph_path, csv_camera_path):

    try:
        bone_frames = []
        morph_frames = []
        camera_frames = []

        if csv_bone_path:
            output_vmd_path = re.sub(r'\.csv$', "_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), csv_bone_path)

            # ボーンCSV読み込み
            with open(csv_bone_path, encoding='cp932', mode='r') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーを読み飛ばす

                for row in reader:
                    bf = VmdBoneFrame()

                    # ボーン名
                    bf.format_name = row[0]

                    # ボーン名（バイト）
                    bf.name = bf.format_name.encode('cp932').decode('shift_jis').encode('shift_jis')

                    # フレーム
                    bf.frame = int(float(row[1]))

                    # 位置
                    bf.position = QVector3D(float(row[2]), float(row[3]), float(row[4]))

                    # 回転
                    bf.rotation = QQuaternion.fromEulerAngles(float(row[5]), float(row[6])*-1, float(row[7])*-1)

                    # 補間曲線(一旦floatで読み込んで指数等も読み込んだ後、intに変換)
                    bf.complement = [int(float(row[8])), int(float(row[9])), int(float(row[10])),int(float(row[11])),int(float(row[12])),int(float(row[13])),int(float(row[14])),int(float(row[15])),int(float(row[16])),int(float(row[17])),int(float(row[18])),int(float(row[19])),int(float(row[20])),int(float(row[21])),int(float(row[22])),int(float(row[23])),int(float(row[24])),int(float(row[25])),int(float(row[26])),int(float(row[27])),int(float(row[28])),int(float(row[29])),int(float(row[30])),int(float(row[31])),int(float(row[32])),int(float(row[33])),int(float(row[34])),int(float(row[35])),int(float(row[36])),int(float(row[37])),int(float(row[38])),int(float(row[39])),int(float(row[40])),int(float(row[41])),int(float(row[42])),int(float(row[43])),int(float(row[44])),int(float(row[45])),int(float(row[46])),int(float(row[47])),int(float(row[48])),int(float(row[49])),int(float(row[50])),int(float(row[51])),int(float(row[52])),int(float(row[53])),int(float(row[54])),int(float(row[55])),int(float(row[56])),int(float(row[57])),int(float(row[58])),int(float(row[59])),int(float(row[60])),int(float(row[61])),int(float(row[62])),int(float(row[63])),int(float(row[64])),int(float(row[65])),int(float(row[66])),int(float(row[67])),int(float(row[68])),int(float(row[69])),int(float(row[70])),int(float(row[71]))]

                    bone_frames.append(bf)
                
                    # logger.debug("bf: %s %s", bf.name, bf)

        if csv_morph_path:
            output_vmd_path = re.sub(r'\.csv$', "_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), csv_morph_path)

            # モーフCSV読み込み
            with open(csv_morph_path, encoding='cp932', mode='r') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーを読み飛ばす

                for row in reader:
                    mf = VmdMorphFrame()

                    # ボーン名
                    mf.format_name = row[0]

                    # ボーン名（バイト）
                    mf.name = mf.format_name.encode('cp932').decode('shift_jis').encode('shift_jis')

                    # フレーム
                    mf.frame = int(float(row[1]))

                    # 位置
                    mf.ratio = float(row[2])

                    morph_frames.append(mf)

        writer = VmdWriter()

        if len(morph_frames) > 0 or len(bone_frames) > 0:            
            # ボーン・モーフモーション生成
            writer.write_vmd_file(output_vmd_path, "CSV Convert Model", bone_frames, morph_frames, [], [], [], [])

            print("ボーン・モーフVMD出力成功: %s" % output_vmd_path)

        if csv_camera_path:
            # カメラCSV読み込み
            with open(csv_camera_path, encoding='cp932', mode='r') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーを読み飛ばす

                for row in reader:
                    cf = VmdCameraFrame()

                    # フレーム
                    cf.frame = int(float(row[0]))

                    # 位置
                    cf.position = QVector3D(float(row[1]), float(row[2]), float(row[3]))

                    # 回転（オイラー角）
                    cf.euler = QVector3D(float(row[4]), float(row[5]), float(row[6]))

                    # 距離
                    cf.length = -(float(row[7]))

                    # 視野角
                    cf.angle = int(float(row[8]))

                    # パース
                    cf.perspective = int(float(row[9]))

                    # 補間曲線
                    cf.complement = [int(float(row[10])),int(float(row[11])),int(float(row[12])),int(float(row[13])),int(float(row[14])),int(float(row[15])),int(float(row[16])),int(float(row[17])),int(float(row[18])),int(float(row[19])),int(float(row[20])),int(float(row[21])),int(float(row[22])),int(float(row[23])),int(float(row[24])),int(float(row[25])),int(float(row[26])),int(float(row[27])),int(float(row[28])),int(float(row[29])),int(float(row[30])),int(float(row[31])),int(float(row[32])),int(float(row[33]))]

                    camera_frames.append(cf)
                
                    # logger.debug("bf: %s %s", bf.name, bf)

        if len(camera_frames) > 0:            
            # カメラモーション生成
            output_vmd_path = re.sub(r'\.csv$', "_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), csv_camera_path)
            writer.write_vmd_file(output_vmd_path, "CSV Convert Model", [], [], camera_frames, [], [], [])

            print("カメラVMD出力成功: %s" % output_vmd_path)

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　CSV解析処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())


if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--csv_bone_path', dest='csv_bone_path', help='input csv bone', type=str)
    parser.add_argument('--csv_morph_path', dest='csv_morph_path', help='input csv morph', type=str)
    parser.add_argument('--csv_camera_path', dest='csv_camera_path', help='input csv camera', type=str)
    args = parser.parse_args()

    if wrapperutils.is_valid_file(args.csv_bone_path, "ボーンCSVファイル", ".csv", True) == False:
        sys.exit(-1)

    if wrapperutils.is_valid_file(args.csv_bone_path, "モーフCSVファイル", ".csv", True) == False:
        sys.exit(-1)

    if wrapperutils.is_valid_file(args.csv_bone_path, "カメラCSVファイル", ".csv", True) == False:
        sys.exit(-1)

    main(args.csv_bone_path, args.csv_morph_path, args.csv_camera_path)