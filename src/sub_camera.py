# -*- coding: utf-8 -*-
# カメラ縮尺処理
# 
import logging
import copy
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import utils, sub_move

logger = logging.getLogger("VmdSizing").getChild(__name__)

#
# カメラ縮尺処理を実行
#
# 現在のアルゴリズムは以下のようになっている。
# X   : モデルのxz補正値
# Y   : モデルの左右目ボーン高さの平均値、または頭ボーンの高さのある方(目優先)
# Z   : モデルのxz補正値 + モデルのZオフセット(必要か未知数)
# 距離: モデルのxz補正値
#
def exec(motion, trace_model, replace_model, output_vmd_path):

    if motion.camera_cnt == 0:
        # カメラフレームがなかったら処理しない
        return True

    # 足IKのXYZの比率
    # 横と前後方向の移動はこれと同じ幅に補正されるので。
    xz_ratio, dummy, leg_ik_stance = sub_move.calc_leg_ik_ratio(trace_model, replace_model)

    # 目ボーンの高さ比率
    #
    # 本当は頭の一番上にある頂点のY座標の邦画いいが、発見する方法が難しい。
    # ウェイトでは「頭についた大きな装飾品」(BASARAの毛利元就とかわかりやすい)に問題がある。
    # それでもボーンウェイトでやる場合は弱参照を採用せず、一番Yの高い位置にある頭ボーン100%を採用すべきか。
    y_ratio = sub_move.calc_eye_level_ratio(trace_model, replace_model)
    if y_ratio is None:
        # 目ボーンでの比率が求められなかった場合は頭ボーンでの比率を求める
        y_ratio = sub_move.calc_head_ratio(trace_model, replace_model)
        if y_ratio is None:
            # 頭まで取れなかった場合は高さを弄らないことにする
            print("どちらかのモデルに左右目、頭のボーンがなかったので高さの補正を行いません")
            y_ratio = 1.0

    # センターのZ軸オフセットを計算
    offset_target_bone = "センター"
    sub_move.cal_center_z_offset(trace_model, replace_model, offset_target_bone)

    # 情報提供
    print("カメラ補正: x=%s, y=%s, z=%s + %s 距離=%s" % (xz_ratio, y_ratio, xz_ratio, replace_model.bones[offset_target_bone].offset_z, xz_ratio))

    # 移動縮尺
    for cf in motion.cameras:
        # IK比率をそのまま掛ける
        cf.position.setX( cf.position.x() * xz_ratio )
        cf.position.setY( cf.position.y() * y_ratio )
        cf.position.setZ( cf.position.z() * xz_ratio + replace_model.bones[offset_target_bone].offset_z)
        cf.length = cf.length * xz_ratio

    print("カメラ調整終了")

    return True
