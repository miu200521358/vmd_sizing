#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
import re
import logging
import traceback
import argparse
import os.path
import sys
from datetime import datetime
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D
import math
import numpy as np

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
import wrapperutils, sub_arm_ik, utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main(vmd_path):

    try:
        # VMD読み込み
        motion = VmdReader().read_vmd_file(vmd_path)

        if len(motion.frames.values()) > 0:
            smooth_vmd_fpath = re.sub(r'\.vmd$', "_bone_smooth_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), vmd_path)
            
            for k, v in motion.frames.items():
                # 3個以上キーがある場合、2番目のキーから補間曲線を分割し始める
                if len(v) > 2:
                    split_frame(motion, k, 1, utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs)

                # for bf_idx, bf in enumerate(v):
                #     # 始めはスルー
                #     if bf_idx <= 1:
                #         continue
                    
                #     # 最後は分割しない
                #     if bf_idx == len(v) - 1:
                #         break
                    

                #     # キー名で補間曲線を分割
                #     sub_arm_ik.reset_complement_frame(motion, k, bf_idx, utils.MX_x1_idxs, utils.MX_y1_idxs, utils.MX_x2_idxs, utils.MX_y2_idxs)
                #     sub_arm_ik.reset_complement_frame(motion, k, bf_idx, utils.MY_x1_idxs, utils.MY_y1_idxs, utils.MY_x2_idxs, utils.MY_y2_idxs)
                #     sub_arm_ik.reset_complement_frame(motion, k, bf_idx, utils.MZ_x1_idxs, utils.MZ_y1_idxs, utils.MZ_x2_idxs, utils.MZ_y2_idxs)
                #     sub_arm_ik.reset_complement_frame(motion, k, bf_idx, utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs)


                # split_frames = {"rot_x": {k: []}, "rot_y": {k: []}, "rot_z": {k: []}, "mov_x": {k: []}, "mov_y": {k: []}, "mov_z": {k: []}}

                # prev_bf_frame = 0

                # # 一旦キーを埋める
                # for bf_idx, bf in enumerate(v):
                #     if bf.frame > prev_bf_frame:
                #         for fill_bf_frame in range(prev_bf_frame + 1, bf.frame):
                #             fillbf = utils.calc_bone_by_complement(motion.frames, k, fill_bf_frame, True)
                #             motion.frames[k].insert(fill_bf_frame, fillbf)
                        
                #     prev_bf_frame = bf.frame

                # # 移動と回転を滑らかに
                # smooth_rotation(motion.frames[k], 3)
                # smooth_move(motion.frames[k], 3)
                # smooth_filter(k, motion.frames[k], {"freq": 30, "mincutoff": 0.1, "beta": 0.5, "dcutoff": 0.8})

                # # 間引き（必要なキーだけONにする）
                # reduce_frames(motion.frames[k], 0.5, 5)


            # ディクショナリ型の疑似二次元配列から、一次元配列に変換
            bone_frames = []
            for k,v in motion.frames.items():
                for bf in v:
                    if bf.key == True:
                        bone_frames.append(bf)
            
            morph_frames = []
            for k,v in motion.morphs.items():
                for mf in v:
                    morph_frames.append(mf)

            writer = VmdWriter()
            
            # ボーンモーション生成
            writer.write_vmd_file(smooth_vmd_fpath, "Smooth Vmd", bone_frames, morph_frames, [], [], [], motion.showiks)

            print("補間曲線つきVMD出力成功: %s" % smooth_vmd_fpath)

        if len(motion.cameras) > 0:
            smooth_vmd_fpath = re.sub(r'\.vmd$', "_camera_{0:%Y%m%d_%H%M%S}.csv".format(datetime.now()), vmd_path)

            print("未実装")

            # with open(camera_fpath, encoding='cp932', mode='w') as f:
                
            #     # s = "フレーム,位置X,位置Y,位置Z,回転X,回転Y,回転Z,距離,視野角,パース,X_x1,Y_x1,Z_x1,R_x1,L_x1,VA_x1, X_y1,Y_y1,Z_y1,R_y1,L_y1,VA_y1,X_x2,Y_x2,Z_x2,R_x2,L_x2,VA_x2, X_y2,Y_y2,Z_y2,R_y2,L_y2,VA_y2"
            #     f.write(s)
            #     f.write("\n")

            #     for cf in motion.cameras:
            #         s = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}".format(cf.frame, cf.position.x(), cf.position.y(), cf.position.z(), cf.euler.x(), cf.euler.y(), cf.euler.z(), -cf.length, cf.angle, cf.perspective,','.join([str(i) for i in cf.complement]))
            #         f.write(s)
            #         f.write("\n")

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMD解析処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

def split_frame(motion, link_name, bf_idx, x1_idxs, y1_idxs, x2_idxs, y2_idxs):
    if bf_idx == len(motion.frames[link_name]) - 1:
        return

    test = np.random(3)

    # 前のは、一つ前
    prev_bf = motion.frames[link_name][bf_idx - 1]
    # 後ろはとりあえず最後
    next_bf = motion.frames[link_name][-1]
    # 現在のbf
    now_bf = motion.frames[link_name][bf_idx]

    next_x1v = next_bf.complement[x1_idxs[3]]
    next_y1v = next_bf.complement[y1_idxs[3]]
    next_x2v = next_bf.complement[x2_idxs[3]]
    next_y2v = next_bf.complement[y2_idxs[3]]

    logger.info("k: %s, prev: %s, now: %s, next: %s", link_name, prev_bf.frame, now_bf.frame, next_bf.frame)

    sub_arm_ik.split_complement(motion, next_x1v, next_y1v, next_x2v, next_y2v, prev_bf, next_bf, now_bf, x1_idxs, y1_idxs, x2_idxs, y2_idxs, link_name, ",")


def reduce_frames(frames, threshold_pos, threshold_rot):
    reduced_frames = reduce_bone_frame(frames, frames, 0, len(frames) - 1, threshold_pos, threshold_rot, False)
    
    for rf in reduced_frames:
        active_bf_idx = [e for e, x in enumerate(frames) if x.frame == rf.frame]
        if active_bf_idx:
            logger.info("active: %s, name: %s", frames[active_bf_idx[0]].frame, frames[active_bf_idx[0]].format_name)
            frames[active_bf_idx[0]].key = True

# キーフレームを間引く
# オリジナル：https://github.com/errno-mmd/smoothvmd/blob/master/reducevmd.cc
def reduce_bone_frame(total_frames, v, head, tail, threshold_pos, threshold_rot, bezier):
    # 移動のエラー最大値
    max_pos_err = float(0.0)
    # 回転のエラー最大値
    max_rot_err = float(0.0)
    # 移動：エラー最大値のindex
    max_idx_pos = 0
    # 回転：エラー最大値のindex
    max_idx_rot = 0
    # 最初から最後までのフレーム数
    total = tail - head
    head_frame = v[head]
    tail_frame = v[tail]
    bezier_interpolation_limit = 60

    # if bezier and tail - head < bezier_interpolation_limit:
    #     optimize_bezier_parameter(tail_frame, v, head, tail)

    for i in range(head + 1, tail , 1):
        # 移動
        f = [x for x in total_frames if x.frame == i][0]
        pos_err = (f.position - v[i].position).length()

        if pos_err > max_pos_err:
            max_idx_pos = i
            max_pos_err = pos_err

        t = float(i - head) / total

        # 回転
        ip_rot = QQuaternion.slerp(v[head].rotation, v[tail].rotation, t)
        q_err = (ip_rot * v[i].rotation.inverted()).normalized()

        # フィルタではなく、ここで正負反転させてプラスに寄せる
        if q_err.scalar() < 0:
            q_err.setX(q_err.x() * -1)
            q_err.setY(q_err.y() * -1)
            q_err.setX(q_err.z() * -1)
            q_err.setScalar(q_err.scalar() * -1)
            
        #  math.acos(q_err.scalar()) * 2 * 180 / math.pi
        rot_err = math.degrees(math.acos(q_err.scalar()))
        # logger.info("rot_err: %s, %s", rot_err, max_rot_err)
        
        if rot_err > max_rot_err:
            max_idx_rot = i
            max_rot_err = rot_err

    v1 = []
    if max_pos_err > threshold_pos:
        v1 = reduce_bone_frame(total_frames, v, head, max_idx_pos, threshold_pos, threshold_rot, bezier)
        v2 = reduce_bone_frame(total_frames, v, max_idx_pos, tail, threshold_pos, threshold_rot, bezier)
        
        v1.extend(v2)
    else:
        if max_rot_err > threshold_rot:
            v1 = reduce_bone_frame(total_frames, v, head, max_idx_rot, threshold_pos, threshold_rot, bezier)
            v2 = reduce_bone_frame(total_frames, v, max_idx_rot, tail, threshold_pos, threshold_rot, bezier)

            v1.extend(v2)
        else:
            v1.append(v[head])

    return v1



def smooth_filter(key, frames, config):
    # 移動用フィルタ
    pxfilter = OneEuroFilter(**config)
    pyfilter = OneEuroFilter(**config)
    pzfilter = OneEuroFilter(**config)

    # 回転用フィルタ
    rxfilter = OneEuroFilter(**config)
    ryfilter = OneEuroFilter(**config)
    rzfilter = OneEuroFilter(**config)
    rwfilter = OneEuroFilter(**config)

    for n, bf in enumerate(frames):
        if "ＩＫ" in key:

            # IKの場合、次のフレームと全く同値の場合、フィルタをかけない
            if bf.frame < len(frames) - 1 \
            and bf.position == frames[n+1].position \
            and bf.rotation == frames[n+1].rotation:
                
                # 位置と回転が同じ場合、同値とみなす
                logger.debug("IK同値: %s %s", n, bf.name)

                # 処理をスキップして次に行く
                pxfilter.skip(bf.position.x(), bf.frame)
                pyfilter.skip(bf.position.y(), bf.frame)
                pzfilter.skip(bf.position.z(), bf.frame)

                rxfilter.skip(bf.rotation.x(), bf.frame)
                ryfilter.skip(bf.rotation.y(), bf.frame)
                rzfilter.skip(bf.rotation.z(), bf.frame)
                rwfilter.skip(bf.rotation.scalar(), bf.frame)

                continue

        # XYZそれぞれにフィルターをかける
        px = pxfilter(bf.position.x(), bf.frame)
        py = pyfilter(bf.position.y(), bf.frame)
        pz = pzfilter(bf.position.z(), bf.frame)
        bf.position = QVector3D(px, py, pz)

        rotation = bf.rotation

        # 同じ回転を表すクォータニオンが正負2通りあるので、wの符号が正のほうに統一する
        # if rotation.scalar() < 0:
        #     rotation.setX(rotation.x() * -1)
        #     rotation.setY(rotation.y() * -1)
        #     rotation.setZ(rotation.z() * -1)
        #     rotation.setScalar(rotation.scalar() * -1)
        
        # XYZそれぞれにフィルターをかける(オイラー角)
        r = rotation.toEulerAngles()
        rx = rxfilter(r.x(), bf.frame)
        ry = ryfilter(r.y(), bf.frame)
        rz = rzfilter(r.z(), bf.frame)
        # rw = rwfilter(rotation.scalar(), bf.frame)

        # クォータニオンに戻して保持
        bf.rotation = QQuaternion.fromEulerAngles(rx, ry, rz)
    

# 回転を滑らかにする
def smooth_rotation(frames, smooth_times):
    # 関節の角度円滑化
    for n in range(smooth_times):
        for frame in range(len(frames)):
            if frame >= 2:
                prev2_bf = frames[frame - 2]
                prev1_bf = frames[frame - 1]
                now_bf = frames[frame]

                if prev2_bf != now_bf.rotation:
                    # 角度が違っていたら、球形補正開始
                    euler = QQuaternion.slerp(prev2_bf.rotation, now_bf.rotation, 0.5).toEulerAngles()
                    utils.set_effective_value_vec3(euler)
                    prev1_bf.rotation = QQuaternion.fromEulerAngles(euler)

def smooth_move(frames, smooth_times):
    # 移動の位置円滑化
    for n in range(smooth_times):
        for frame in range(len(frames)):
            if 2 <= frame <= len(frames) - 1:
                prev2_bf = frames[frame - 2]
                prev1_bf = frames[frame - 1]
                now_bf = frames[frame]

                # 移動ボーンのどこかが動いていたら
                if now_bf != prev2_bf:
                    if 3 <= frame <= len(frames) - 2:
                        # 5F取れるようであれば、5F
                        prev3_bf = frames[frame - 3]
                        next_bf = frames[frame + 1]
                    else:
                        # 取れないようであれば、3Fで採用
                        prev3_bf = prev2_bf
                        next_bf = now_bf

                    # 線形補正(prev1自身は含めず、突飛な値を落とす)
                    new_prev1_pos = prev2_bf.position + now_bf.position + prev3_bf.position + next_bf.position
                    new_prev1_pos /= 4
                    prev1_bf.position = new_prev1_pos

# OneEuroFilter
# オリジナル：https://www.cristal.univ-lille.fr/~casiez/1euro/
# ----------------------------------------------------------------------------

class LowPassFilter(object):

    def __init__(self, alpha):
        self.__setAlpha(alpha)
        self.__y = self.__s = None

    def __setAlpha(self, alpha):
        alpha = float(alpha)
        if alpha<=0 or alpha>1.0:
            raise ValueError("alpha (%s) should be in (0.0, 1.0]"%alpha)
        self.__alpha = alpha

    def __call__(self, value, timestamp=None, alpha=None):        
        if alpha is not None:
            self.__setAlpha(alpha)
        if self.__y is None:
            s = value
        else:
            s = self.__alpha*value + (1.0-self.__alpha)*self.__s
        self.__y = value
        self.__s = s
        return s

    def lastValue(self):
        return self.__y
    
    # IK用処理スキップ
    def skip(self, value):
        self.__y = value
        self.__s = value

        return value

# ----------------------------------------------------------------------------

class OneEuroFilter(object):

    def __init__(self, freq, mincutoff=1.0, beta=0.0, dcutoff=1.0):
        if freq<=0:
            raise ValueError("freq should be >0")
        if mincutoff<=0:
            raise ValueError("mincutoff should be >0")
        if dcutoff<=0:
            raise ValueError("dcutoff should be >0")
        self.__freq = float(freq)
        self.__mincutoff = float(mincutoff)
        self.__beta = float(beta)
        self.__dcutoff = float(dcutoff)
        self.__x = LowPassFilter(self.__alpha(self.__mincutoff))
        self.__dx = LowPassFilter(self.__alpha(self.__dcutoff))
        self.__lasttime = None
        
    def __alpha(self, cutoff):
        te    = 1.0 / self.__freq
        tau   = 1.0 / (2*math.pi*cutoff)
        return  1.0 / (1.0 + tau/te)

    def __call__(self, x, timestamp=None):
        # ---- update the sampling frequency based on timestamps
        if self.__lasttime and timestamp:
            self.__freq = 1.0 / (timestamp-self.__lasttime)
        self.__lasttime = timestamp
        # ---- estimate the current variation per second
        prev_x = self.__x.lastValue()
        dx = 0.0 if prev_x is None else (x-prev_x)*self.__freq # FIXME: 0.0 or value?
        edx = self.__dx(dx, timestamp, alpha=self.__alpha(self.__dcutoff))
        # ---- use it to update the cutoff frequency
        cutoff = self.__mincutoff + self.__beta*math.fabs(edx)
        # ---- filter the given value
        return self.__x(x, timestamp, alpha=self.__alpha(cutoff))

    # IK用処理スキップ
    def skip(self, x, timestamp=None):
        # ---- update the sampling frequency based on timestamps
        if self.__lasttime and timestamp and self.__lasttime != timestamp:
            self.__freq = 1.0 / (timestamp-self.__lasttime)
        self.__lasttime = timestamp
        prev_x = self.__x.lastValue()
        self.__dx.skip(prev_x)
        self.__x.skip(x)


if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vmd_path', dest='vmd_path', help='input vmd', type=str)
    args = parser.parse_args()

    if wrapperutils.is_valid_file(args.vmd_path, "VMDファイル", ".vmd", True) == False:
        sys.exit(-1)

    main(args.vmd_path)