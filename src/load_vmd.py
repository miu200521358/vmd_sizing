#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
import re
import logging
import traceback
import argparse
import os.path
import sys

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
import wrapperutils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vmd_path', dest='vmd_path', help='input vmd', type=str)
    args = parser.parse_args()

    if not args.vmd_path:
        print("VMDパスを指定してください。 load_vmd.exe --vmd_path=<VMDファイルフルパス>")
        sys.exit(-1)

    fpath = re.sub(r'\.vmd$', ".csv", args.vmd_path.lower())
    try:
        # 解析対象VMDファイル
        if wrapperutils.is_valid_file(args.vmd_path, "解析対象VMDファイル", ".vmd"):

            with open(fpath, encoding='shift-jis', mode='w') as f:
                # VMD読み込み
                motion = VmdReader().read_vmd_file(args.vmd_path)
                
                s = "ボーン名,フレーム,位置X,位置Y,位置Z,回転X,回転Y,回転Z,【X_x1】,Y_x1,Z_x1,R_x1,【X_y1】,Y_y1,Z_y1,R_y1,【X_x2】,Y_x2,Z_x2,R_x2,【X_y2】,Y_y2,Z_y2,R_y2,【Y_x1】,Z_x1,R_x1,X_y1,【Y_y1】,Z_y1,R_y1,X_x2,【Y_x2】,Z_x2,R_x2,X_y2,【Y_y2】,Z_y2,R_y2,1,【Z_x1】,R_x1,X_y1,Y_y1,【Z_y1】,R_y1,X_x2,Y_x2,【Z_x2】,R_x2,X_y2,Y_y2,【Z_y2】,R_y2,1,0,【R_x1】,X_y1,Y_y1,Z_y1,【R_y1】,X_x2,Y_x2,Z_x2,【R_x2】,X_y2,Y_y2,Z_y2,【R_y2】,01,00,00"
                f.write(s)
                f.write("\n")

                for bf_list in motion.frames.values():
                    for bf in bf_list:
                        s = "{0},{1},{2},{3},{4},{5},{6},{7},{8}".format(bf.format_name, bf.frame, bf.position.x(), bf.position.y(), bf.position.z(), bf.rotation.toEulerAngles().x(), bf.rotation.toEulerAngles().y()*-1, bf.rotation.toEulerAngles().z()*-1,','.join([str(i) for i in bf.complement]))
                        f.write(s)
                        f.write("\n")

            print("出力成功: %s" % fpath)

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMD解析処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())
