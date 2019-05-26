# -*- coding: utf-8 -*-
#

from PmxModel import PmxModel
from PmxReader import PmxReader
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QColor

if __name__=="__main__":

    pmxreader = PmxReader()
    try:
        pmx = pmxreader.read_pmx_file( "D:/MMD/MikuMikuDance_v926x64/UserFile/Model/VOCALOID/GUMI/ままま式GUMI β/GUMIβ版修正準標準.pmx" )
    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　PMXデータの解析に失敗しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        import traceback
        print(traceback.format_exc())
        