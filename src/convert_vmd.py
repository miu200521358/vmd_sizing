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
                    bf.frame = int(row[1])

                    # 位置
                    bf.position = QVector3D(float(row[2]), float(row[3]), float(row[4]))

                    # 回転
                    bf.rotation = QQuaternion.fromEulerAngles(float(row[5]), float(row[6])*-1, float(row[7])*-1)

                    # 補間曲線
                    bf.complement = [int(row[8]), int(row[9]), int(row[10]),int(row[11]),int(row[12]),int(row[13]),int(row[14]),int(row[15]),int(row[16]),int(row[17]),int(row[18]),int(row[19]),int(row[20]),int(row[21]),int(row[22]),int(row[23]),int(row[24]),int(row[25]),int(row[26]),int(row[27]),int(row[28]),int(row[29]),int(row[30]),int(row[31]),int(row[32]),int(row[33]),int(row[34]),int(row[35]),int(row[36]),int(row[37]),int(row[38]),int(row[39]),int(row[40]),int(row[41]),int(row[42]),int(row[43]),int(row[44]),int(row[45]),int(row[46]),int(row[47]),int(row[48]),int(row[49]),int(row[50]),int(row[51]),int(row[52]),int(row[53]),int(row[54]),int(row[55]),int(row[56]),int(row[57]),int(row[58]),int(row[59]),int(row[60]),int(row[61]),int(row[62]),int(row[63]),int(row[64]),int(row[65]),int(row[66]),int(row[67]),int(row[68]),int(row[69]),int(row[70]),int(row[71])]

                    bone_frames.append(bf)
                
                    # logger.info("bf: %s %s", bf.name, bf)

        if csv_morph_path:
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
                    mf.frame = int(row[1])

                    # 位置
                    mf.ratio = float(row[2])

                    morph_frames.append(mf)

        writer = VmdWriter()

        if len(morph_frames) > 0 or len(bone_frames) > 0:            
            # ボーン・モーフモーション生成
            output_vmd_path = re.sub(r'\.csv$', "_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), csv_bone_path)
            writer.write_vmd_file(output_vmd_path, "CSV Convert Model", bone_frames, morph_frames, [], [], [], [])

            print("ボーン・モーフVMD出力成功: %s" % output_vmd_path)

        if csv_camera_path:
            # ボーンCSV読み込み
            with open(csv_camera_path, encoding='cp932', mode='r') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーを読み飛ばす

                for row in reader:
                    cf = VmdCameraFrame()

                    # フレーム
                    cf.frame = int(row[0])

                    # 位置
                    cf.position = QVector3D(float(row[1]), float(row[2]), float(row[3]))

                    # 回転（オイラー角）
                    cf.euler = QVector3D(float(row[4]), float(row[5]), float(row[6]))

                    # 距離
                    cf.length = float(row[7])

                    # 視野角
                    cf.angle = int(row[8])

                    # 補間曲線
                    cf.complement = [int(row[9]),int(row[10]),int(row[11]),int(row[12]),int(row[13]),int(row[14]),int(row[15]),int(row[16]),int(row[17]),int(row[18]),int(row[19]),int(row[20]),int(row[21]),int(row[22]),int(row[23]),int(row[24]),int(row[25]),int(row[26]),int(row[27]),int(row[28]),int(row[29]),int(row[30]),int(row[31]),int(row[32])]

                    camera_frames.append(cf)
                
                    # logger.info("bf: %s %s", bf.name, bf)

        if len(camera_frames) > 0:            
            # カメラモーション生成
            output_vmd_path = re.sub(r'\.csv$', "_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), csv_camera_path)
            writer.write_vmd_file(output_vmd_path, "CSV Convert Model", camera_frames, [], [], [], [], [])

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