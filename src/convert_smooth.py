#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
import re
import logging
import traceback
import argparse
import os.path
import sys
import copy
from datetime import datetime
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QMatrix4x4, QVector4D
import math

from VmdWriter import VmdWriter, VmdBoneFrame
from VmdReader import VmdReader
from PmxModel import PmxModel, SizingException
from PmxReader import PmxReader
import wrapperutils, sub_arm_ik, utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

is_print = True

def main(vmd_path, pos_repeat, rot_repeat):

    try:
        # VMD読み込み
        motion = VmdReader().read_vmd_file(vmd_path)
        smoothed_frames = []

        if len(motion.frames.values()) > 0:
            smooth_vmd_fpath = re.sub(r'\.vmd$', "_bone_smooth_{0:%Y%m%d_%H%M%S}.vmd".format(datetime.now()), vmd_path)
            
            for bone_name, motion_frames in motion.frames.items():
                if len(motion_frames) <= 1:
                    continue

                frames_by_bone = {}
                for e, bf in enumerate(motion_frames):
                    frames_by_bone[bf.frame] = bf

                start_frameno = motion_frames[0].frame
                last_frameno = motion_frames[-1].frame

                for cnt in range(max(pos_repeat, rot_repeat)):

                    if cnt > 0:
                        # 2回目以降はフィルタあり
                        smooth_filter(bone_name, frames_by_bone, pos_repeat > cnt, rot_repeat > cnt, {"freq": 30, "mincutoff": 0.01, "beta": 0.5, "dcutoff": 0.8})
                    
                    if cnt == 0:
                        prev_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, start_frameno, is_only=True, is_exist=True, is_read=True)
                        if not prev_bf: break

                        now_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True, is_read=True)
                        if not now_bf: break

                        next_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True, is_read=True)
                        if not next_bf: break

                        prev_prev_bf = None

                        # 最初に根性打ち
                        while now_bf.frame <= last_frameno:
                            split_bf(frames_by_bone, bone_name, prev_prev_bf, prev_bf, now_bf, next_bf)

                            prev_prev_bf = prev_bf
                            
                            prev_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, now_bf.frame, is_only=True, is_exist=True, is_read=True)
                            if not prev_bf: break

                            now_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True, is_read=True)
                            if not now_bf: break

                            next_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True, is_read=True)
                            # if not next_bf: break

                            if not next_bf:
                                # 次がない場合、一旦prevの次に伸ばす
                                next_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=False)
                                next_bf.position += QVector3D(0.1, 0.1, 0.1)
                                next_bf.rotation *= 1.1
                                frames_by_bone[next_bf.frame] = next_bf
                            else:
                                if next_bf.frame > last_frameno:
                                    # 次以降は見なくていいので終了
                                    break

                        # 全体をフィルタに掛ける
                        for _ in range(3):
                            smooth_filter(bone_name, frames_by_bone, True, True, {"freq": 30, "mincutoff": 0.01, "beta": 0.8, "dcutoff": 1})

                    if cnt > 0:

                        prev_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, start_frameno, is_only=True, is_exist=True)
                        if not prev_bf: break

                        now_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
                        if not now_bf: break

                        next_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
                        if not next_bf: break

                        # 2回目以降はベジェ曲線同士を結合する
                        while now_bf.frame <= last_frameno:
                        
                            next_bf = smooth_bf(frames_by_bone, bone_name, prev_bf, now_bf, next_bf, cnt, last_frameno)
                            
                            if not now_bf or not next_bf: break

                            # 二回目以降はnextまで補間曲線が設定できたので次
                            prev_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, next_bf.frame, is_only=True, is_exist=True)
                            if not prev_bf: break

                            now_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
                            if not now_bf: break

                            next_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
                            # if not next_bf: break

                            if not next_bf:
                                # 次がない場合、一旦prevの次に伸ばす
                                next_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=False)
                                next_bf.position += QVector3D(1, 0, 0)
                                next_bf.rotation *= 1.1
                            else:
                                if next_bf.frame > last_frameno:
                                    # 次以降は見なくていいので終了
                                    break

                    print("ボーン: %s %s回目" % (bone_name, (cnt + 1)))

                for bf in frames_by_bone.values():
                    if bf.key == True:
                        smoothed_frames.append(bf)

            morph_frames = []
            for k,v in motion.morphs.items():
                for mf in v:
                    morph_frames.append(mf)

            writer = VmdWriter()
            
            # ボーンモーション生成
            writer.write_vmd_file(smooth_vmd_fpath, "Smooth Vmd", smoothed_frames, morph_frames, [], [], [], motion.showiks)

            print("スムージングVMD出力成功: %s" % smooth_vmd_fpath)
        else:
            print("スムージング対象となるキーがないため、終了します。")

        if len(motion.cameras) > 0:
            smooth_vmd_fpath = re.sub(r'\.vmd$', "_camera_{0:%Y%m%d_%H%M%S}.csv".format(datetime.now()), vmd_path)

            print("未実装")

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMD解析処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

def split_bf(frames_by_bone, bone_name, prev_prev_bf, prev_bf, now_bf, next_bf):
    # 0回目の場合、根性打ち

    for fno in range(prev_bf.frame + 1, now_bf.frame):
        target_bf = VmdBoneFrame()
        target_bf.frame = fno
        target_bf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
        target_bf.format_name = bone_name

        # 現在の補間曲線ではなく、なめらかに繋いだ場合の角度を設定する
        target_rot, rt = get_smooth_middle_rot(prev_bf, now_bf, next_bf, target_bf)
        target_bf.rotation = target_rot
        
        # 現在の補間曲線ではなく、なめらかに繋いだ場合の位置を設定する
        target_pos, mt = get_smooth_middle_pos(prev_bf, now_bf, next_bf, target_bf)
        target_bf.position = target_pos

        target_bf.key = True
        frames_by_bone[target_bf.frame] = target_bf

    if prev_prev_bf:
        beforeno = int(prev_bf.frame - (prev_bf.frame - prev_prev_bf.frame) * 0.5)
        afterno = int(prev_bf.frame + (now_bf.frame - prev_bf.frame) * 0.5)

        filter_frames_by_bone = {}
        for fno in range(beforeno, afterno):
            # 前々回との間を滑らかに繋ぐための配列を用意する
            filter_frames_by_bone[fno] = copy.deepcopy(frames_by_bone[fno])

        # 前々回との連結部分をフィルタに掛ける
        config = {"freq": 30, "mincutoff": 0.01, "beta": 0.8, "dcutoff": 1}
        for _ in range(5):
            smooth_filter(bone_name, filter_frames_by_bone, True, True, config)

        # 元に戻す
        for f in filter_frames_by_bone.values():
            frames_by_bone[f.frame] = f

# bf同士をベジェ曲線で繋ぐ
def smooth_bf(frames_by_bone, bone_name, prev_bf, now_bf, next_bf, offset, last_frameno):

    is_smooth = True
    successed_next_bf = None

    while is_smooth:
    
        # ひとまず補間曲線で繋ぐ
        is_smooth = smooth_complement_bf(frames_by_bone, bone_name, prev_bf, now_bf, next_bf, offset)
    
        if is_smooth:
            for fno in range(prev_bf.frame + 1, next_bf.frame):
                frames_by_bone[fno].key = False

            # 補間曲線が繋げた場合、次へ
            successed_next_bf = copy.deepcopy(next_bf)

            next_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, next_bf.frame + 1, is_only=False, is_exist=True)
            if not next_bf:
                # 次が見つからなければ、最後のnextを登録して終了
                if successed_next_bf:
                    successed_next_bf.key = True
                    frames_by_bone[successed_next_bf.frame] = successed_next_bf
                break

            now_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, int(prev_bf.frame + ((next_bf.frame - prev_bf.frame) / 2)), is_only=False, is_exist=True)
            if not now_bf or (now_bf and now_bf.frame == last_frameno): break
        else:
            # 補間曲線が繋げなかった場合、終了
            if successed_next_bf:
                successed_next_bf.key = True
                frames_by_bone[successed_next_bf.frame] = successed_next_bf
            else:
                # 一回も補間曲線が登録出来なかった場合、とりあえずnowを登録して次にいく
                now_bf.key = True
                frames_by_bone[now_bf.frame] = now_bf
                successed_next_bf = now_bf
            break

    return successed_next_bf


def smooth_complement_bf(frames_by_bone, bone_name, prev_bf, now_bf, next_bf, offset):

    is_smooth_rot_result = smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_rot, \
        utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs, offset, utils.calc_smooth_bezier_rot)
    is_smooth_pos_x_result = smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_x, \
        utils.MX_x1_idxs, utils.MX_y1_idxs, utils.MX_x2_idxs, utils.MX_y2_idxs, offset, utils.calc_smooth_bezier_pos)
    is_smooth_pos_y_result = smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_y, \
        utils.MY_x1_idxs, utils.MY_y1_idxs, utils.MY_x2_idxs, utils.MY_y2_idxs, offset, utils.calc_smooth_bezier_pos)
    is_smooth_pos_z_result = smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_z, \
        utils.MZ_x1_idxs, utils.MZ_y1_idxs, utils.MZ_x2_idxs, utils.MZ_y2_idxs, offset, utils.calc_smooth_bezier_pos)

    is_smooth = is_smooth_rot_result == is_smooth_pos_x_result == is_smooth_pos_y_result == is_smooth_pos_z_result
    
    # is_join = False

    # if is_smooth:
    #     # 補間曲線同士を結合する
    #     is_join_rot_result = join_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_rot, \
    #         utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs, offset, utils.join_smooth_bezier)
    #     is_join_pos_x_result = join_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_x, \
    #         utils.MX_x1_idxs, utils.MX_y1_idxs, utils.MX_x2_idxs, utils.MX_y2_idxs, offset, utils.join_smooth_bezier)
    #     is_join_pos_y_result = join_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_y, \
    #         utils.MY_x1_idxs, utils.MY_y1_idxs, utils.MY_x2_idxs, utils.MY_y2_idxs, offset, utils.join_smooth_bezier)
    #     is_join_pos_z_result = join_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_z, \
    #         utils.MZ_x1_idxs, utils.MZ_y1_idxs, utils.MZ_x2_idxs, utils.MZ_y2_idxs, offset, utils.join_smooth_bezier)

    #     is_join = is_join_rot_result == is_join_pos_x_result == is_join_pos_y_result == is_join_pos_z_result

    return is_smooth

# 滑らかに繋ぐベジェ曲線
def smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y, x1_idxs, y1_idxs, x2_idxs, y2_idxs, offset, calc_smooth_bezier):
    if not (prev_bf.frame < now_bf.frame < next_bf.frame):
        # フレーム範囲外はNG
        return False

    x1 = prev_bf.frame
    x2 = now_bf.frame
    x3 = next_bf.frame

    y1 = get_smooth_bezier_y(prev_bf, prev_bf)
    y2 = get_smooth_bezier_y(prev_bf, now_bf)
    y3 = get_smooth_bezier_y(prev_bf, next_bf)

    is_smooth, result, bz = calc_smooth_bezier(x1, y1, x2, y2, x3, y3, offset)

    if not is_smooth:
        # ベジェ曲線計算対象外の場合、とりあえずTRUEで終了
        return True

    if result == True:
        # 中間の始点を、中bfに設定する
        next_bf.complement[x1_idxs[0]] = next_bf.complement[x1_idxs[1]] = \
            next_bf.complement[x1_idxs[2]] = next_bf.complement[x1_idxs[3]] = bz[1].x()
        next_bf.complement[y1_idxs[0]] = next_bf.complement[y1_idxs[1]] = \
            next_bf.complement[y1_idxs[2]] = next_bf.complement[y1_idxs[3]] = bz[1].y()

        # 中間の終点を、中bfに設定する
        next_bf.complement[x2_idxs[0]] = next_bf.complement[x2_idxs[1]] = \
            next_bf.complement[x2_idxs[2]] = next_bf.complement[x2_idxs[3]] = bz[2].x()
        next_bf.complement[y2_idxs[0]] = next_bf.complement[y2_idxs[1]] = \
            next_bf.complement[y2_idxs[2]] = next_bf.complement[y2_idxs[3]] = bz[2].y()

        return True

    return False


# # 滑らかに繋ぐベジェ曲線
# def join_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y, x1_idxs, y1_idxs, x2_idxs, y2_idxs, offset, join_smooth_bezier):
#     if not (prev_bf.frame < now_bf.frame < next_bf.frame):
#         # フレーム範囲外はNG
#         return False
    
#     # 前後に分けて登録する

#     bz1 = [
#         QVector2D(0, 0),
#         QVector2D(now_bf.complement[x1_idxs[3]], now_bf.complement[y1_idxs[3]]),
#         QVector2D(now_bf.complement[x2_idxs[3]], now_bf.complement[y2_idxs[3]]),
#         QVector2D(utils.COMPLEMENT_MMD_MAX, utils.COMPLEMENT_MMD_MAX)
#     ]

#     bz2 = [
#         QVector2D(0, 0),
#         QVector2D(next_bf.complement[x1_idxs[3]], next_bf.complement[y1_idxs[3]]),
#         QVector2D(next_bf.complement[x2_idxs[3]], next_bf.complement[y2_idxs[3]]),
#         QVector2D(utils.COMPLEMENT_MMD_MAX, utils.COMPLEMENT_MMD_MAX)
#     ]

#     is_join, bz = join_smooth_bezier(bz1, bz2, offset, ((now_bf.frame - prev_bf.frame) / (next_bf.frame - prev_bf.frame)))

#     if is_join == True:
#         # 中間の始点を、中bfに設定する
#         next_bf.complement[x1_idxs[0]] = next_bf.complement[x1_idxs[1]] = \
#             next_bf.complement[x1_idxs[2]] = next_bf.complement[x1_idxs[3]] = bz[1].x()
#         next_bf.complement[y1_idxs[0]] = next_bf.complement[y1_idxs[1]] = \
#             next_bf.complement[y1_idxs[2]] = next_bf.complement[y1_idxs[3]] = bz[1].y()

#         # 中間の終点を、中bfに設定する
#         next_bf.complement[x2_idxs[0]] = next_bf.complement[x2_idxs[1]] = \
#             next_bf.complement[x2_idxs[2]] = next_bf.complement[x2_idxs[3]] = bz[2].x()
#         next_bf.complement[y2_idxs[0]] = next_bf.complement[y2_idxs[1]] = \
#             next_bf.complement[y2_idxs[2]] = next_bf.complement[y2_idxs[3]] = bz[2].y()

#         return True

#     return False

def get_smooth_bezier_y_rot(before_bf, after_bf):
    return after_bf.rotation

def get_smooth_bezier_y_pos_x(before_bf, after_bf):
    return after_bf.position.x()

def get_smooth_bezier_y_pos_y(before_bf, after_bf):
    return after_bf.position.y()

def get_smooth_bezier_y_pos_z(before_bf, after_bf):
    return after_bf.position.z()

# 滑らかにした移動
def get_smooth_middle_pos(prev_bf, now_bf, next_bf, target_bf):
    p = prev_bf.position
    w = now_bf.position
    n = next_bf.position

    # 変化量
    t = (target_bf.frame - prev_bf.frame) / ( now_bf.frame - prev_bf.frame)

    # デフォルト値
    d = w + (w - p)

    out = get_smooth_middle_by_vec3(p, w, n, d, t, now_bf.frame)

    # 円周上の座標とデフォルト値の内積（差分）
    diff = 1 - abs(QVector3D.dotProduct(target_bf.position.normalized(), out.normalized()))

    # 計算結果と実際の変化量を返す
    return out, diff

# 滑らかにした回転
def get_smooth_middle_rot(prev_bf, now_bf, next_bf, target_bf):
    p = prev_bf.rotation.toEulerAngles()
    w = now_bf.rotation.toEulerAngles()
    n = next_bf.rotation.toEulerAngles()

    # 変化量
    t = (target_bf.frame - prev_bf.frame) / ( now_bf.frame - prev_bf.frame)

    # デフォルト値
    d = QQuaternion.slerp(prev_bf.rotation, next_bf.rotation, t).toEulerAngles()

    out = get_smooth_middle_by_vec3(p, w, n, d, t, now_bf.frame)

    out_qq = QQuaternion.fromEulerAngles(out)

    # 現在の回転と角度の中間地点との差(離れているほど値を大きくする)
    dot_diff = 1 - abs(QQuaternion.dotProduct(out_qq, target_bf.rotation))

    return out_qq, dot_diff

# vec3での滑らかな変化
def get_smooth_middle_by_vec3(op, ow, on, d, t, f):
    # 念のためコピー
    p = copy.deepcopy(op)
    w = copy.deepcopy(ow)
    n = copy.deepcopy(on)

    # 半径は3点間の距離の最長の半分
    r = max(p.distanceToPoint(w), p.distanceToPoint(n),  w.distanceToPoint(n)) / 2

    if round(r, 1) == 0:
        # 半径が取れなかった場合、そもそもまったく移動がないので、線分移動
        return (p + n) * t

    if p == w or p == n or w == n:
        # 半径が0の場合か、どれか同じ値の場合、線対称な値を使用する
        n = d

    try:
        # 3点を通る球体の原点を求める
        c, radius = utils.calc_sphere_center(p, w, n, r)
    except ZeroDivisionError as e:
        utils.output_message("covert ゼロ割エラー: f: %s, p: %s, w: %s, n: %s, t: %s" % (f, p, w, n, t), is_print)
        raise e

    if round(radius, 1) == 0:
        # 半径が取れなかった場合、そもそもまったく移動がないので、線分移動
        return (p + n) * t

    # prev -> now の t分の回転量
    pn_qq = QQuaternion.rotationTo((p - c).normalized(), (c - c).normalized())
    pw_qq = QQuaternion.rotationTo((p - c).normalized(), (w - c).normalized())
    # 球形補間の移動量
    t_qq = QQuaternion.slerp(pn_qq, pw_qq, t)

    out = t_qq * (p - c) + c

    # 値の変化がない場合、上書き
    if p.x() == w.x() == n.x():
        out.setX(w.x())
    if p.y() == w.y() == n.y():
        out.setY(w.y())
    if p.z() == w.z() == n.z():
        out.setZ(w.z())

    # 有効な値に変換
    utils.set_effective_value_vec3(out)

    return out


# 補間曲線を考慮した指定フレーム番号の位置
# https://www55.atwiki.jp/kumiho_k/pages/15.html
# https://harigane.at.webry.info/201103/article_1.html
def calc_bone_by_complement_by_bone(frames_by_bone, bone_name, frameno, is_only, is_exist, is_key=False, is_read=False):
    fill_bf = VmdBoneFrame()
    fill_bf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
    fill_bf.format_name = bone_name
    fill_bf.frame = frameno

    now_framenos = [x for x in sorted(frames_by_bone.keys()) if x == frameno]
    
    if len(now_framenos) == 1:
        if is_read:
            if frames_by_bone[frameno].read == True:
                return frames_by_bone[frameno]
            else:
                pass
        else:
            # キー指定がある場合、キーが有効である場合のみ返す
            if is_key:
                if frames_by_bone[frameno].key == True:
                    return frames_by_bone[frameno]
                else:
                    pass
            else:
                # 指定フレームがある場合、それを返す
                if is_exist:
                    # 存在しているものの場合、コピーしないでそのもの
                    return frames_by_bone[frameno]
                else:
                    return copy.deepcopy(frames_by_bone[frameno])
    elif is_only and is_exist:
        # 指定フレームがなく、かつそれ固定指定で、既存の場合、None
        return None

    after_framenos = [x for x in sorted(frames_by_bone.keys()) if x > frameno]
    
    if len(after_framenos) == 0:
        if is_exist == True:
            # 存在固定で、最後までいっても見つからなければ、None
            return None
        elif is_only == True:
            # 最後まで行っても見つからなければ、最終項目を該当フレーム用に設定して返す
            last_frameno = [x for x in sorted(frames_by_bone.keys())][-1]
            fill_bf = copy.deepcopy(frames_by_bone[last_frameno])
            return fill_bf

    if is_read == True:
        # キーONの場合、有効なのを返す
        for af in after_framenos:
            if frames_by_bone[af].read == True:
                return frames_by_bone[af]
    elif is_key == True:
        # キーONの場合、有効なのを返す
        for af in after_framenos:
            if frames_by_bone[af].key == True:
                return frames_by_bone[af]
    elif is_exist == True:
        # 既存指定の場合、自身のフレーム（指定フレームの直後のフレーム）
        return copy.deepcopy(frames_by_bone[after_framenos[0]])

    # 前フレーム
    prev_framenos = [x for x in sorted(frames_by_bone.keys()) if x < fill_bf.frame]
    prev_bf = None

    # 指定されたフレーム直前の有効キー(数が多いのからチェック)
    for p in reversed(prev_framenos):
        if frames_by_bone[p].key == True:
            prev_bf = frames_by_bone[p]
            break
    if not prev_bf:
        # 有効な前キーが取れない場合、暫定的に現在フレームの値を保持する
        prev_bf = copy.deepcopy(fill_bf)

    # 計算対象フレーム
    calc_bf = None

    # 次フレーム
    next_next_framenos = [x for x in sorted(frames_by_bone.keys()) if x > fill_bf.frame]
    next_bf = None

    # 指定されたフレーム直後のキー
    for p in next_next_framenos:
        next_bf = frames_by_bone[p]
        break
    
    if next_bf:
        # 次がある場合、次を採用
        calc_bf = copy.deepcopy(next_bf)
    else:
        if len(now_framenos) > 0:
            # 現在がある場合、現在キー
            calc_bf = copy.deepcopy(frames_by_bone[now_framenos[0]])
        else:
            # 現在も次もない場合、過去を計算対象とする
            calc_bf = copy.deepcopy(prev_bf)

        calc_bf.frame = frameno
    
    # 補間曲線を元に間を埋める
    fill_bf.rotation = calc_bone_by_complement_rot(prev_bf, calc_bf, fill_bf)
    fill_bf.position = calc_bone_by_complement_pos(prev_bf, calc_bf, fill_bf)
    
    return fill_bf

def calc_bone_by_complement_rot(prev_bf, calc_bf, fill_bf):
    if prev_bf.rotation != calc_bf.rotation:
        # 回転補間曲線
        _, _, rn = utils.calc_interpolate_bezier(calc_bf.complement[utils.R_x1_idxs[3]], calc_bf.complement[utils.R_y1_idxs[3]], \
            calc_bf.complement[utils.R_x2_idxs[3]], calc_bf.complement[utils.R_y2_idxs[3]], prev_bf.frame, calc_bf.frame, fill_bf.frame)
        return QQuaternion.slerp(prev_bf.rotation, calc_bf.rotation, rn)

    return copy.deepcopy(prev_bf.rotation)

def calc_bone_by_complement_pos(prev_bf, calc_bf, fill_bf):

    # 補間曲線を元に間を埋める
    if prev_bf.position != calc_bf.position:
        # http://rantyen.blog.fc2.com/blog-entry-65.html
        # X移動補間曲線
        _, _, xn = utils.calc_interpolate_bezier(calc_bf.complement[0], calc_bf.complement[4], calc_bf.complement[8], calc_bf.complement[12], prev_bf.frame, calc_bf.frame, fill_bf.frame)
        # Y移動補間曲線
        _, _, yn = utils.calc_interpolate_bezier(calc_bf.complement[16], calc_bf.complement[20], calc_bf.complement[24], calc_bf.complement[28], prev_bf.frame, calc_bf.frame, fill_bf.frame)
        # Z移動補間曲線
        _, _, zn = utils.calc_interpolate_bezier(calc_bf.complement[32], calc_bf.complement[36], calc_bf.complement[40], calc_bf.complement[44], prev_bf.frame, calc_bf.frame, fill_bf.frame)

        fill_pos = QVector3D()
        fill_pos.setX(prev_bf.position.x() + (( calc_bf.position.x() - prev_bf.position.x()) * xn))
        fill_pos.setY(prev_bf.position.y() + (( calc_bf.position.y() - prev_bf.position.y()) * yn))
        fill_pos.setZ(prev_bf.position.z() + (( calc_bf.position.z() - prev_bf.position.z()) * zn))
        
        return fill_pos
    
    return copy.deepcopy(prev_bf.position)
     
# -----------------------------

def smooth_filter(bone_name, frames_by_bone, is_pos_filter, is_rot_filter, config):
    # 移動用フィルタ
    pxfilter = OneEuroFilter(**config)
    pyfilter = OneEuroFilter(**config)
    pzfilter = OneEuroFilter(**config)

    # 回転用フィルタ
    rxfilter = OneEuroFilter(**config)
    ryfilter = OneEuroFilter(**config)
    rzfilter = OneEuroFilter(**config)
    # rwfilter = OneEuroFilter(**config)

    for e, frameno in enumerate(sorted(frames_by_bone.keys())):
        prev_bf = frames_by_bone[frameno]

        # # 間のキーは一旦落とす
        # if 0 < e < len(frames_by_bone.keys()) - 1:
        #     bf.key = False

        now_bf = calc_bone_by_complement_by_bone(frames_by_bone, bone_name, frameno + 1, is_only=False, is_exist=True)

        if not now_bf:
            break

        # if is_pos_filter and QVector3D.dotProduct(prev_bf.position, now_bf.position) < 0.99:
        # XYZそれぞれにフィルターをかける
        px = pxfilter(now_bf.position.x(), now_bf.frame)
        py = pyfilter(now_bf.position.y(), now_bf.frame)
        pz = pzfilter(now_bf.position.z(), now_bf.frame)
        now_bf.position = QVector3D(px, py, pz)
        # else:
        #     # 移動のフィルタ許容してない場合、スルー
        #     pxfilter.skip(now_bf.position.x(), now_bf.frame)
        #     pyfilter.skip(now_bf.position.y(), now_bf.frame)
        #     pzfilter.skip(now_bf.position.z(), now_bf.frame)

        # 同じ回転を表すクォータニオンが正負2通りあるので、wの符号が正のほうに統一する
        # if rotation.scalar() < 0:
        #     rotation.setX(rotation.x() * -1)
        #     rotation.setY(rotation.y() * -1)
        #     rotation.setZ(rotation.z() * -1)
        #     rotation.setScalar(rotation.scalar() * -1)
        
        # if is_rot_filter and QQuaternion.dotProduct(prev_bf.rotation, now_bf.rotation) < 0.99:
        # XYZそれぞれにフィルターをかける(オイラー角)
        r = now_bf.rotation.toEulerAngles()
        rx = rxfilter(r.x(), now_bf.frame)
        ry = ryfilter(r.y(), now_bf.frame)
        rz = rzfilter(r.z(), now_bf.frame)
        # rw = rwfilter(rotation.scalar(), bf.frame)

        # クォータニオンに戻して保持
        now_bf.rotation = QQuaternion.fromEulerAngles(rx, ry, rz)
        # else:
        #     # 回転のフィルタ許容してない場合、スルー
        #     rxfilter.skip(now_bf.rotation.x(), now_bf.frame)
        #     ryfilter.skip(now_bf.rotation.y(), now_bf.frame)
        #     rzfilter.skip(now_bf.rotation.z(), now_bf.frame)
        #     # rwfilter.skip(bf.rotation.scalar(), bf.frame)

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
    parser.add_argument('--pos_repeat', dest='pos_repeat', help='pos_repeat', type=int)
    parser.add_argument('--rot_repeat', dest='rot_repeat', help='rot_repeat', type=int)

    args = parser.parse_args()

    if wrapperutils.is_valid_file(args.vmd_path, "VMDファイル", ".vmd", True) == False:
        sys.exit(-1)

    main(args.vmd_path, args.pos_repeat, args.rot_repeat)