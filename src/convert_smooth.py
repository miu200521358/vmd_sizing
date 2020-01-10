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

is_print = False

def main(vmd_path, pmx_path, pos_repeat, rot_repeat):

    try:
        # VMD読み込み
        motion = VmdReader().read_vmd_file(vmd_path)
        smoothed_frames = []

        # PMX読み込み
        model = PmxReader().read_pmx_file(pmx_path)

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
                        # 2回目以降は円滑化
                        # smooth_pos_rot(model, frames_by_bone, bone_name)
                        smooth_filter(model, bone_name, frames_by_bone, pos_repeat > cnt, rot_repeat > cnt, {"freq": 30, "mincutoff": 0.1, "beta": 0.5, "dcutoff": 0.8})

                    # フィルターをかけたら一旦キークリア
                    for bf in frames_by_bone.values():
                        if start_frameno < bf.frame < last_frameno:
                            bf.key = False
                    
                    prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, start_frameno, is_only=True, is_exist=True)
                    if not prev_bf: break

                    now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
                    if not now_bf: break

                    next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
                    if not next_bf: break

                    # now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, int(prev_bf.frame + (next_bf.frame - prev_bf.frame) / 2), is_only=False, is_exist=(cnt == 0))
                    # if not now_bf: break

                    while now_bf.frame <= last_frameno:
                        if cnt == 0:
                            # 一回目は根性打ち
                            split_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf)
                        else:
                            # 二回目以降はベジェ曲線で繋ぐ
                            smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf)

                        prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame, is_only=True, is_exist=True)
                        if not prev_bf: break

                        now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
                        if not now_bf: break

                        next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
                        # if not next_bf: break

                        if not next_bf:
                            # 次がない場合、一旦prevの次に伸ばす
                            next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, int(prev_bf.frame + (prev_bf.frame - now_bf.frame) / 2), is_only=False, is_exist=False)
                        else:
                            if next_bf.frame > last_frameno:
                                # 次の次を見てた場合は終了
                                break

                        # now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, int((prev_bf.frame + next_bf.frame) / 2), is_only=False, is_exist=False)
                        # if not now_bf: break

                    print("ボーン: %s %s回目" % (bone_name, (cnt + 1)))

                for bf in frames_by_bone.values():
                    # if bf.key == True:
                    smoothed_frames.append(bf)

            morph_frames = []
            for k,v in motion.morphs.items():
                for mf in v:
                    morph_frames.append(mf)

            writer = VmdWriter()
            
            # ボーンモーション生成
            writer.write_vmd_file(smooth_vmd_fpath, "Smooth Vmd", smoothed_frames, morph_frames, [], [], [], motion.showiks)

            print("スムージングVMD出力成功: %s" % smooth_vmd_fpath)

        if len(motion.cameras) > 0:
            smooth_vmd_fpath = re.sub(r'\.vmd$', "_camera_{0:%Y%m%d_%H%M%S}.csv".format(datetime.now()), vmd_path)

            print("未実装")

    except Exception:
        print("■■■■■■■■■■■■■■■■■")
        print("■　**ERROR**　")
        print("■　VMD解析処理が意図せぬエラーで終了しました。")
        print("■■■■■■■■■■■■■■■■■")
        
        print(traceback.format_exc())

def split_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf):
    # 0回目の場合、根性打ち

    for f in range(prev_bf.frame + 1, now_bf.frame):
        target_bf = VmdBoneFrame()
        target_bf.frame = f
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

    # for f in range(now_bf.frame + 1, next_bf.frame):
    #     target_bf = VmdBoneFrame()
    #     target_bf.frame = f
    #     target_bf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
    #     target_bf.format_name = bone_name

    #     # 現在の補間曲線ではなく、なめらかに繋いだ場合の角度を設定する
    #     target_rot, rt = get_smooth_middle_rot(prev_bf, next_bf, now_bf, target_bf)
    #     target_bf.rotation = target_rot
        
    #     # 現在の補間曲線ではなく、なめらかに繋いだ場合の位置を設定する
    #     target_pos, mt = get_smooth_middle_pos(prev_bf, next_bf, now_bf, target_bf)
    #     target_bf.position = target_pos

    #     target_bf.key = True
    #     frames_by_bone[target_bf.frame] = target_bf


def smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf):

    # 現在の補間曲線ではなく、なめらかに繋いだ場合の角度を設定する
    now_rot, rt = get_smooth_middle_rot(prev_bf, now_bf, next_bf)
    now_bf.rotation = now_rot
    
    # 現在の補間曲線ではなく、なめらかに繋いだ場合の位置を設定する
    now_pos, mt = get_smooth_middle_pos(prev_bf, now_bf, next_bf)
    now_bf.position = now_pos

    # ひとまず補間曲線で繋ぐ
    is_split = join_complement_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, is_add)
    
    if not is_split:
        # 分割できなかった場合、中を細分する

        # 前半 ---------------
        near_bf = VmdBoneFrame()
        near_bf.frame = int((prev_bf.frame + now_bf.frame) / 2)
        near_bf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
        near_bf.format_name = bone_name

        # # 現在の補間曲線ではなく、なめらかに繋いだ場合の角度を設定する
        # near_rot, rt = get_smooth_middle_rot(prev_bf, near_bf, now_bf)
        # near_bf.rotation = near_rot
        
        # # 現在の補間曲線ではなく、なめらかに繋いだ場合の位置を設定する
        # near_pos, mt = get_smooth_middle_pos(prev_bf, near_bf, now_bf)
        # near_bf.position = near_pos

        smooth_bf(model, frames_by_bone, bone_name, prev_bf, near_bf, now_bf, is_add)

        # 後半 -----------
        far_bf = VmdBoneFrame()
        far_bf.frame = int((now_bf.frame + next_bf.frame) / 2)
        far_bf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
        far_bf.format_name = bone_name

        # # 現在の補間曲線ではなく、なめらかに繋いだ場合の角度を設定する
        # far_rot, rt = get_smooth_middle_rot(now_bf, far_bf, next_bf)
        # far_bf.rotation = far_rot
        
        # # 現在の補間曲線ではなく、なめらかに繋いだ場合の位置を設定する
        # far_pos, mt = get_smooth_middle_pos(now_bf, far_bf, next_bf)
        # far_bf.position = far_pos

        smooth_bf(model, frames_by_bone, bone_name, now_bf, far_bf, next_bf, is_add)


def join_complement_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, is_add):

    is_rot_result = True
    if model.bones[bone_name].getRotatable():
        is_rot_result = smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_rot, utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs)

    is_pos_x_result = True
    is_pos_y_result = True
    is_pos_z_result = True
    if model.bones[bone_name].getTranslatable():
        is_pos_x_result = smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_x, utils.MX_x1_idxs, utils.MX_y1_idxs, utils.MX_x2_idxs, utils.MX_y2_idxs)
        is_pos_y_result = smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_y, utils.MY_x1_idxs, utils.MY_y1_idxs, utils.MY_x2_idxs, utils.MY_y2_idxs)
        is_pos_z_result = smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y_pos_z, utils.MZ_x1_idxs, utils.MZ_y1_idxs, utils.MZ_x2_idxs, utils.MZ_y2_idxs)

    result = is_rot_result == is_pos_x_result == is_pos_y_result == is_pos_z_result

    if not result and (prev_bf.frame >= now_bf.frame or now_bf.frame >= next_bf.frame):
        # 隣接の場合、そのまま登録して終了

        frames_by_bone[prev_bf.frame] = prev_bf
        frames_by_bone[now_bf.frame] = now_bf
        frames_by_bone[next_bf.frame] = next_bf

        return True

    return result

# 滑らかに繋ぐベジェ曲線
def smooth_bezier(frames_by_bone, prev_bf, now_bf, next_bf, get_smooth_bezier_y, x1_idxs, y1_idxs, x2_idxs, y2_idxs):
    if not (prev_bf.frame < now_bf.frame < next_bf.frame):
        # フレーム範囲外はNG
        return False
    
    # 前後に分けて登録する

    x1 = prev_bf.frame
    x2 = now_bf.frame
    x3 = next_bf.frame

    y1 = get_smooth_bezier_y(prev_bf, prev_bf)
    y2 = get_smooth_bezier_y(prev_bf, now_bf)
    y3 = get_smooth_bezier_y(prev_bf, next_bf)

    is_smooth, bresult, aresult, before_bz, after_bz = utils.calc_smooth_bezier(x1, y1, x2, y2, x3, y3)

    if not is_smooth:
        # ベジェ曲線計算対象外の場合、とりあえずTRUEで終了
        return True

    if bresult == aresult == True:
        # # オフセットを設けているので、その分調整する
        # utils.fit_bezier_split_mmd(bz)

        # # 前半の始点を、前bfに設定する
        # prev_bf.complement[x1_idxs[0]] = prev_bf.complement[x1_idxs[1]] = \
        #     prev_bf.complement[x1_idxs[2]] = prev_bf.complement[x1_idxs[3]] = before_bz[1].x()
        # prev_bf.complement[y1_idxs[0]] = prev_bf.complement[y1_idxs[1]] = \
        #     prev_bf.complement[y1_idxs[2]] = prev_bf.complement[y1_idxs[3]] = before_bz[1].y()

        # # 前半の終点を、前bfに設定する
        # prev_bf.complement[x2_idxs[0]] = prev_bf.complement[x2_idxs[1]] = \
        #     prev_bf.complement[x2_idxs[2]] = prev_bf.complement[x2_idxs[3]] = before_bz[2].x()
        # prev_bf.complement[y2_idxs[0]] = prev_bf.complement[y2_idxs[1]] = \
        #     prev_bf.complement[y2_idxs[2]] = prev_bf.complement[y2_idxs[3]] = before_bz[2].y()

        # 中間の始点を、中bfに設定する
        now_bf.complement[x1_idxs[0]] = now_bf.complement[x1_idxs[1]] = \
            now_bf.complement[x1_idxs[2]] = now_bf.complement[x1_idxs[3]] = before_bz[1].x()
        now_bf.complement[y1_idxs[0]] = now_bf.complement[y1_idxs[1]] = \
            now_bf.complement[y1_idxs[2]] = now_bf.complement[y1_idxs[3]] = before_bz[1].y()

        # 中間の終点を、中bfに設定する
        now_bf.complement[x2_idxs[0]] = now_bf.complement[x2_idxs[1]] = \
            now_bf.complement[x2_idxs[2]] = now_bf.complement[x2_idxs[3]] = before_bz[2].x()
        now_bf.complement[y2_idxs[0]] = now_bf.complement[y2_idxs[1]] = \
            now_bf.complement[y2_idxs[2]] = now_bf.complement[y2_idxs[3]] = before_bz[2].y()

        # 中間の始点を、中bfに設定する
        next_bf.complement[x1_idxs[0]] = next_bf.complement[x1_idxs[1]] = \
            next_bf.complement[x1_idxs[2]] = next_bf.complement[x1_idxs[3]] = after_bz[1].x()
        next_bf.complement[y1_idxs[0]] = next_bf.complement[y1_idxs[1]] = \
            next_bf.complement[y1_idxs[2]] = next_bf.complement[y1_idxs[3]] = after_bz[1].y()

        # 中間の終点を、中bfに設定する
        next_bf.complement[x2_idxs[0]] = next_bf.complement[x2_idxs[1]] = \
            next_bf.complement[x2_idxs[2]] = next_bf.complement[x2_idxs[3]] = after_bz[2].x()
        next_bf.complement[y2_idxs[0]] = next_bf.complement[y2_idxs[1]] = \
            next_bf.complement[y2_idxs[2]] = next_bf.complement[y2_idxs[3]] = after_bz[2].y()

        # prev_bf.key = True
        # frames_by_bone[prev_bf.frame] = prev_bf

        now_bf.key = True
        frames_by_bone[now_bf.frame] = now_bf

        next_bf.key = True
        frames_by_bone[next_bf.frame] = next_bf

        return True

    return False

def get_smooth_bezier_y_rot(before_bf, after_bf):
    # 現在の回転と角度の中間地点との差(離れているほど値を大きくする)
    return 1 - abs(QQuaternion.dotProduct(before_bf.rotation, after_bf.rotation))

def get_smooth_bezier_y_pos_x(before_bf, after_bf):
    return after_bf.position.x() # - before_bf.position.x()

def get_smooth_bezier_y_pos_y(before_bf, after_bf):
    return after_bf.position.y() # - before_bf.position.y()

def get_smooth_bezier_y_pos_z(before_bf, after_bf):
    return after_bf.position.z() # - before_bf.position.z()

# 滑らかにした移動
def get_smooth_middle_pos(prev_bf, now_bf, next_bf, target_bf):
    p = prev_bf.position
    w = now_bf.position
    n = next_bf.position
    t = target_bf.position

    # 半径は3点間の距離の最長の半分
    r = max(p.distanceToPoint(w), p.distanceToPoint(n),  w.distanceToPoint(n)) / 2

    if r == 0:
        # 半径が0の場合、そのまま返す
        return target_bf.position, 0

    # 3点を通る球体の原点を求める
    c, radius = utils.calc_sphere_center(p, w, n, r)

    # 変化量
    t = (target_bf.frame - prev_bf.frame) / ( now_bf.frame - prev_bf.frame)

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

    # 円周上の座標とデフォルト値の内積（差分）
    diff = abs(QVector3D.dotProduct(target_bf.position.normalized(), out.normalized()))

    # 計算結果と実際の変化量を返す
    return out, diff

# 滑らかにした回転
def get_smooth_middle_rot(prev_bf, now_bf, next_bf, target_bf):
    # # 回転を取り直す
    # default_rot = calc_bone_by_complement_rot(prev_bf, next_bf, now_bf)

    t = (target_bf.frame - prev_bf.frame) / ( next_bf.frame - prev_bf.frame)

    # 角度をeulerに変換した際の中間値
    prev_euler = prev_bf.rotation.toEulerAngles()
    next_euler = next_bf.rotation.toEulerAngles()
    
    test_euler = prev_euler + ((next_euler - prev_euler) * t)

    test_qq = QQuaternion.fromEulerAngles(test_euler)

    # 現在の回転と角度の中間地点との差(離れているほど値を大きくする)
    dot_diff = 1 - abs(QQuaternion.dotProduct(test_qq, target_bf.rotation))

    return test_qq, dot_diff

# 補間曲線を考慮した指定フレーム番号の位置
# https://www55.atwiki.jp/kumiho_k/pages/15.html
# https://harigane.at.webry.info/201103/article_1.html
def calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, frameno, is_only, is_exist):
    fill_bf = VmdBoneFrame()
    fill_bf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
    fill_bf.format_name = bone_name
    fill_bf.frame = frameno

    now_framenos = [x for x in sorted(frames_by_bone.keys()) if x == frameno]
    
    if len(now_framenos) == 1:
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
    
    if is_exist == True:
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

def smooth_filter(model, bone_name, frames_by_bone, is_pos_filter, is_rot_filter, config):
    # 移動用フィルタ
    pxfilter = OneEuroFilter(**config)
    pyfilter = OneEuroFilter(**config)
    pzfilter = OneEuroFilter(**config)

    # 回転用フィルタ
    rxfilter = OneEuroFilter(**config)
    ryfilter = OneEuroFilter(**config)
    rzfilter = OneEuroFilter(**config)
    rwfilter = OneEuroFilter(**config)

    for frameno in sorted(frames_by_bone.keys()):
        bf = frames_by_bone[frameno]

        # 2回目以降なので、一旦キーを落とす
        bf.key = False

        next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, frameno + 1, is_only=False, is_exist=True)

        if not next_bf:
            break

        if is_pos_filter and model.bones[bone_name].getTranslatable() and QVector3D.dotProduct(bf.position, next_bf.position) < 0.99:
            # XYZそれぞれにフィルターをかける
            px = pxfilter(bf.position.x(), bf.frame)
            py = pyfilter(bf.position.y(), bf.frame)
            pz = pzfilter(bf.position.z(), bf.frame)
            bf.position = QVector3D(px, py, pz)
        else:
            # 移動のフィルタ許容してない場合、スルー
            pxfilter.skip(bf.position.x(), bf.frame)
            pyfilter.skip(bf.position.y(), bf.frame)
            pzfilter.skip(bf.position.z(), bf.frame)

        # 同じ回転を表すクォータニオンが正負2通りあるので、wの符号が正のほうに統一する
        # if rotation.scalar() < 0:
        #     rotation.setX(rotation.x() * -1)
        #     rotation.setY(rotation.y() * -1)
        #     rotation.setZ(rotation.z() * -1)
        #     rotation.setScalar(rotation.scalar() * -1)
        
        if is_rot_filter and model.bones[bone_name].getRotatable() and QQuaternion.dotProduct(bf.rotation, next_bf.rotation) > 0.99:
            # XYZそれぞれにフィルターをかける(オイラー角)
            r = bf.rotation.toEulerAngles()
            rx = rxfilter(r.x(), bf.frame)
            ry = ryfilter(r.y(), bf.frame)
            rz = rzfilter(r.z(), bf.frame)
            # rw = rwfilter(rotation.scalar(), bf.frame)

            # クォータニオンに戻して保持
            bf.rotation = QQuaternion.fromEulerAngles(rx, ry, rz)
        else:
            # 回転のフィルタ許容してない場合、スルー
            rxfilter.skip(bf.rotation.x(), bf.frame)
            ryfilter.skip(bf.rotation.y(), bf.frame)
            rzfilter.skip(bf.rotation.z(), bf.frame)
            rwfilter.skip(bf.rotation.scalar(), bf.frame)

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



# # 移動と回転を滑らかにする
# def smooth_pos_rot(model, frames_by_bone, bone_name):
#     for e, frameno in enumerate(sorted(frames_by_bone.keys())):
#         if e < 2:
#             continue

#         now_bf = frames_by_bone[frameno]
#         prev1_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, frameno - 1, True, True, True, False)
#         if not prev1_bf:
#             continue

#         prev2_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev1_bf.frame - 1, True, True, True, False)

#         if not prev2_bf:
#             continue

#         t = ((prev1_bf.frame - prev2_bf.frame) / (now_bf.frame - prev2_bf.frame))

#         # if (model.bones[bone_name].getRotatable() and QQuaternion.dotProduct(now_bf.rotation, prev2_bf.rotation) < 0.99):
#         if model.bones[bone_name].getRotatable():
#             # 角度が違っていたら、球形補正開始
#             euler = QQuaternion.slerp(prev2_bf.rotation, now_bf.rotation, t).toEulerAngles()
#             utils.set_effective_value_vec3(euler)
#             prev1_bf.rotation = QQuaternion.fromEulerAngles(euler)

#         # if (model.bones[bone_name].getTranslatable() and QVector3D.dotProduct(now_bf.position, prev2_bf.position) < 0.99):
#         if model.bones[bone_name].getTranslatable():
#             # 位置が違っていたら、円形補正
#             x = define_get_bezier_get_test_val_pos_x(prev1_bf, prev2_bf, now_bf, t)
#             y = define_get_bezier_get_test_val_pos_y(prev1_bf, prev2_bf, now_bf, t)
#             z = define_get_bezier_get_test_val_pos_z(prev1_bf, prev2_bf, now_bf, t)
#             prev1_bf.position = QVector3D(x, y, z)

# def smooth_pose(frames_by_bone, smooth_times):
#     for e, frameno in enumerate(sorted(frames_by_bone.keys())):
#         if e < 1:
#             continue

#         now_bf = frames_by_bone[frameno]
#         prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, frameno - 1, True, True, False)
#         prev2_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame - 1, True, True, False)

#         if prev2_bf.position != now_bf.rotation:
#             # 角度が違っていたら、球形補正開始
#             euler = QQuaternion.slerp(prev2_bf.rotation, now_bf.rotation, ((prev_bf.frame - prev2_bf.frame) / (now_bf.frame - prev2_bf.frame))).toEulerAngles()
#             utils.set_effective_value_vec3(euler)
#             prev1_bf.rotation = QQuaternion.fromEulerAngles(euler)


#     # 移動の位置円滑化
#     for n in range(smooth_times):
#         for frame in range(len(frames_by_bone)):
#             if 2 <= frame <= len(frames_by_bone) - 1:
#                 prev2_bf = frames_by_bone[frame - 2]
#                 prev1_bf = frames_by_bone[frame - 1]
#                 now_bf = frames_by_bone[frame]

#                 # 移動ボーンのどこかが動いていたら
#                 if now_bf != prev2_bf:
#                     if 3 <= frame <= len(frames_by_bone) - 2:
#                         # 5F取れるようであれば、5F
#                         prev3_bf = frames_by_bone[frame - 3]
#                         next_bf = frames_by_bone[frame + 1]
#                     else:
#                         # 取れないようであれば、3Fで採用
#                         prev3_bf = prev2_bf
#                         next_bf = now_bf

#                     # 線形補正(prev1自身は含めず、突飛な値を落とす)
#                     new_prev1_pos = prev2_bf.position + now_bf.position + prev3_bf.position + next_bf.position
#                     new_prev1_pos /= 4
#                     prev1_bf.position = new_prev1_pos


# def define_get_bezier_get_default_by_rot(motion, bone_name, prev_bf, now_bf, next_bf):
#     start = prev_bf.frame
#     end = next_bf.frame
#     step = end - start + 1

#     max_dot_diff = 0
#     far_frameno = end

#     # 普通の球形補間で求めた回転量
#     default_rotation = QQuaternion.slerp(prev_bf.rotation, next_bf.rotation, 0.5)

#     for n in range(start, end - 1):
#         # 開始から終了までで、普通の球形補間で求めた回転量と最も近い回転量を探す

#         # 現在の補間曲線で求めたbf
#         testbf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, n)
#         # 現在のbfとt地点のbfの差
#         dot_diff = QQuaternion.dotProduct(testbf.rotation, default_rotation)

#         if max_dot_diff <= dot_diff:
#             # これまでの最大内積より大きい値だった場合、保持
#             max_dot_diff = dot_diff
#             far_frameno = n
    
#     if far_frameno == prev_bf.frame or far_frameno == next_bf.frame or far_frameno == now_bf.frame:
#         return False, None, None

#     return False, far_frameno, (1 - max_dot_diff)


# def define_get_bezier_get_default_by_rot(frames_by_bone, bone_name, prev_bf, now_bf, next_bf):
#     start = prev_bf.frame
#     end = next_bf.frame
#     step = end - start + 1

#     max_dot_diff = 0
#     far_frameno = int((start + end) / 2)
    
#     # 現在の線形補間で求めた移動量
#     default_rot_diff = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, (start + end) / 2, False, False).rotation

#     for n in range(start + 1, now_bf.frame):
#         # 開始から終了までで、普通の球形補間で求めた回転量と最も近い回転量を探す

#         # 現在の補間曲線で求めたbf
#         test_rot = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, n, False, False).rotation

#         # 現在のbfとt地点のbfの差
#         dot_diff = QQuaternion.dotProduct(test_rot, default_rot_diff)

#         if max_dot_diff > dot_diff:
#             # これまでの内積より小さい値（外れている）だった場合、保持
#             max_dot_diff = dot_diff
#             far_frameno = n

#     # 最も遠いフレームの値を取得する
#     far_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, far_frameno, False, False)
#     t = (far_frameno - prev_bf.frame) / (next_bf.frame - prev_bf.frame)

#     x1 = prev_bf.frame + 1
#     x2 = far_bf.frame
#     x3 = now_bf.frame
#     x4 = next_bf.frame

#     if x1 >= x2 or x2 >= x3 or x1 >= x3:
#         # キーが超過していたら分割対象外
#         return False, far_frameno, None, None, None, None

#     y1 = QQuaternion.dotProduct(prev_bf.rotation, prev_bf.rotation)
#     y2 = QQuaternion.dotProduct(prev_bf.rotation, far_bf.rotation)
#     y3 = QQuaternion.dotProduct(prev_bf.rotation, now_bf.rotation)
#     y4 = QQuaternion.dotProduct(prev_bf.rotation, next_bf.rotation)

#     is_target, near_before_bz, near_after_bz = utils.calc_smooth_bezier(x1, y1, x2, y2, x3, y3, t)

#     is_target, far_before_bz, far_after_bz = utils.calc_smooth_bezier(x2, y2, x3, y3, x4, y4, 1 - t)

#     return is_target, far_frameno, near_before_bz, near_after_bz, far_before_bz, far_after_bz



                # # 補間曲線を分割する
                # for bf_idx, bf in enumerate(frames_by_bone):
                #     # キー名で補間曲線を分割
                #     split_frame(motion, bone_name, bf, utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs)

                # test_complement_idxs = [
                #     ([utils.R_x1_idxs, utils.R_y1_idxs], [utils.R_x2_idxs, utils.R_y2_idxs])
                #     , ([utils.MX_x1_idxs, utils.MX_y1_idxs], [utils.MX_x2_idxs, utils.MX_y2_idxs])
                #     , ([utils.MY_x1_idxs, utils.MY_y1_idxs], [utils.MY_x2_idxs, utils.MY_y2_idxs])
                #     , ([utils.MZ_x1_idxs, utils.MZ_y1_idxs], [utils.MZ_x2_idxs, utils.MZ_y2_idxs])
                # ]

                # for bf_idx, bf in enumerate(frames_by_bone):

                #     # 最初は無視
                #     if bf_idx <= 0:
                #         continue
                    
                #     # 最後は終了
                #     if bf_idx == len(frames_by_bone) - 1:
                #         break
                    
                #     # 補間曲線がほぼまっすぐなキーは無効化する
                #     is_no_complement = True
                #     for (start_xy_idxs, end_xy_idxs) in test_complement_idxs:
                #         for (start_idxs, end_idxs) in zip(start_xy_idxs, end_xy_idxs):
                #             if abs(bf.complement[start_xy_idxs[0][3]] - bf.complement[start_xy_idxs[1][3]]) > 20:
                #                 is_no_complement = False
                #                 break
                #             if abs(bf.complement[end_xy_idxs[0][3]] - bf.complement[end_xy_idxs[1][3]]) > 20:
                #                 is_no_complement = False
                #                 break

                #         if not is_no_complement:
                #             break

                #     if is_no_complement:
                #         # 最終的に補間曲線がほとんど変化していない場合、キーを落とす

                #         # 次のフレームがある場合、ベジェ曲線再設定
                #         if bf_idx < len(frames_by_bone) - 2:
                #             for (start_xy_idxs, end_xy_idxs) in test_complement_idxs:
                #                 x1v = bf.complement[start_xy_idxs[0][3]]
                #                 y1v = bf.complement[start_xy_idxs[1][3]]
                #                 x2v = bf.complement[end_xy_idxs[0][3]]
                #                 y2v = bf.complement[end_xy_idxs[1][3]]
                            
                #             prev_bf = frames_by_bone[bf_idx - 1]
                #             next_bf = frames_by_bone[bf_idx + 1]
                #             start = prev_bf.frame + 1
                #             end = next_bf.frame
                #             # できるだけ中間地点を基準に補間曲線を考える
                #             now = int(start + ((end - start) / 2))
                #             # 補間曲線を分割すると考える
                #             t, x, y, [bA2, bE2, bH2, bJ2], [aJ2, aI2, aG2, aD2] = utils.calc_bezier_split_offset(x1v, y1v, x2v, y2v, start, end, now, "")

                #             x1, y1 = utils.fit_bezier_mmd(bA2)
                #             if x1 == y1:
                #                 x1 = 20
                #                 y1 = 20
                #             prev_bf.complement[start_xy_idxs[0][0]] = prev_bf.complement[start_xy_idxs[0][1]] = \
                #                 prev_bf.complement[start_xy_idxs[0][2]] = prev_bf.complement[start_xy_idxs[0][3]] = x1
                #             prev_bf.complement[start_xy_idxs[1][0]] = prev_bf.complement[start_xy_idxs[1][1]] = \
                #                 prev_bf.complement[start_xy_idxs[1][2]] = prev_bf.complement[start_xy_idxs[1][3]] = y1

                #             x2, y2 = utils.fit_bezier_mmd(aD2)
                #             if x2 == y2:
                #                 x1 = 107
                #                 y1 = 107
                #             next_bf.complement[end_xy_idxs[0][0]] = next_bf.complement[end_xy_idxs[0][1]] = \
                #                 next_bf.complement[end_xy_idxs[0][2]] = next_bf.complement[end_xy_idxs[0][3]] = x2
                #             next_bf.complement[end_xy_idxs[1][0]] = next_bf.complement[end_xy_idxs[1][1]] = \
                #                 next_bf.complement[end_xy_idxs[1][2]] = next_bf.complement[end_xy_idxs[1][3]] = y2
                #     else:
                #         bf.key = True

# def split_frame(frames_by_bone, bone_name, now_bf, x1_idxs, y1_idxs, x2_idxs, y2_idxs):
#     # 有効な直前のフレーム
#     prev_bfs = [x for x in frames_by_bone if x.frame < now_bf.frame]
#     # 有効な直後のフレーム
#     next_bfs = [x for x in frames_by_bone if x.frame > now_bf.frame]

#     # 有効な前のフレームがない場合、終了
#     if len(prev_bfs) == 0:
#         return
    
#     # 有効な後のフレームがない場合、終了
#     if len(next_bfs) == 0:
#         return
    
#     prev_bf = prev_bfs[-1]
#     next_bf = next_bfs[0]

#     next_x1v = next_bf.complement[x1_idxs[3]]
#     next_y1v = next_bf.complement[y1_idxs[3]]
#     next_x2v = next_bf.complement[x2_idxs[3]]
#     next_y2v = next_bf.complement[y2_idxs[3]]

#     sub_arm_ik.split_complement(frames_by_bone, next_x1v, next_y1v, next_x2v, next_y2v, prev_bf, next_bf, now_bf, x1_idxs, y1_idxs, x2_idxs, y2_idxs, bone_name, ",")


                        # max_dot_diff = 0
                        # near_frameno = start + 1
                        
                        # # 普通の球形補間で求めた回転量
                        # default_rotation = QQuaternion.slerp(prev_bf.rotation, next_bf.rotation, t)

                        # for n in range(start + 1, end):
                        #     # 開始から終了までで、普通の球形補間で求めた回転量と最も近い回転量を探す

                        #     # 現在の補間曲線で求めたbf
                        #     testbf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, n)
                        #     # 現在のbfとt地点のbfの差
                        #     dot_diff = QQuaternion.dotProduct(testbf.rotation, default_rotation)

                        #     if max_dot_diff < dot_diff:
                        #         # これまでの最大内積より大きい値だった場合、保持
                        #         max_dot_diff = dot_diff
                        #         near_frameno = n

                        # x1v = next_bf.complement[utils.R_x1_idxs[3]]
                        # y1v = next_bf.complement[utils.R_y1_idxs[3]]
                        # x2v = next_bf.complement[utils.R_x2_idxs[3]]
                        # y2v = next_bf.complement[utils.R_y2_idxs[3]]

                        # # 最も近い回転量のベジェ曲線係数取得
                        # near_t, near_x, near_y = utils.calc_interpolate_bezier(x1v, y1v, x2v, y2v, start, end, near_frameno)
                        # logger.debug("b: %s, f: %s, [rot] near t: %s, x: %s, y: %s", bf.format_name, near_frameno, near_t, near_x, near_y)

                        # # 最も近いところのbf
                        # near_bfs = [x for x in frames_by_bone if x.frame == near_frameno]

                        # if len(near_bfs) > 0:
                        #     # 既にキーが登録されている場合、補間曲線だけ設定して次に移動

                        #     if near_frameno > bf.frame:
                        #         # 現在フレームより後のフレームに補間曲線を設定する場合
                        #         target_bfs = {"start": bf, "end": near_bfs[0]}
                        #     else:
                        #         # 現在フレームより前のフレームに補間曲線を設定する場合
                        #         target_bfs = {"start": near_bfs[0], "end": bf}

                        #     for n in utils.R_y2_idxs:
                        #         # startの終点の変化量を近いYで設定する
                        #         target_bfs["start"].complement[n] = utils.COMPLEMENT_MMD_MAX - (near_y * utils.COMPLEMENT_MMD_MAX)
                        #     for n in utils.R_y1_idxs:
                        #         # endの始点の変化量を近いYで設定する
                        #         target_bf.complement[n] = utils.COMPLEMENT_MMD_MAX - (near_y * utils.COMPLEMENT_MMD_MAX)

                        #     logger.debug("b: %s, f: %s, [rot] comp existed: %s", bf.format_name, near_frameno, near_bfs[0].complement)
                        # else:
                        #     # まだキーがない場合、追加
                        #     fill_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, near_frameno)
                        #     fill_bf.key = True
                        #     fill_bf.split_complement = True

                        #     if near_frameno > bf.frame:
                        #         # 現在フレームより後のフレームに補間曲線を設定する場合
                        #         target_bfs = {"start": bf, "end": fill_bf}
                        #     else:
                        #         # 現在フレームより前のフレームに補間曲線を設定する場合
                        #         target_bfs = {"start": fill_bf, "end": bf}

                        #     for n in utils.R_y2_idxs:
                        #         # startの終点の変化量を近いYで設定する
                        #         target_bfs["start"].complement[n] = utils.COMPLEMENT_MMD_MAX - (near_y * utils.COMPLEMENT_MMD_MAX)
                        #     for n in utils.R_y1_idxs:
                        #         # endの始点の変化量を近いYで設定する
                        #         target_bf.complement[n] = utils.COMPLEMENT_MMD_MAX - (near_y * utils.COMPLEMENT_MMD_MAX)

                        #     if near_frameno > bf.frame:
                        #         # 現在フレームより後のフレームにキーを追加する場合、INDEX等加算
                        #         insert_idx = bf_idx + 1
                        #         bf_idx += 1
                        #     else:
                        #         # 前の場合、前のINDEX指定
                        #         insert_idx = bf_idx

                        #     # まだそのフレーム番号のキーがない場合は、追加
                        #     frames_by_bone.insert(insert_idx, fill_bf)

                        #     logger.debug("b: %s, f: %s, [rot] comp insert: %s", bf.format_name, near_frameno, fill_bf.complement)
                                                
                        # dot_max_diff = 1
                        # far_t = 0
                        # step_start = int(step / 4) * 1
                        # step_end = int(step / 4) * 3
                        # for n in range(step_start, step_end):
                        #     # 区間を4分割に区切って、球形補間の移動量で最も近い回転量を求める
                        #     t = n / step

                        #     # 普通の球形補間で求めた回転量
                        #     default_rotation = QQuaternion.slerp(prev_bf.rotation, bf.rotation, t)
                        #     # 実際に設定されている回転量との差
                        #     dot_diff = QQuaternion.dotProduct(bf.rotation, default_rotation)
                        #     if dot_max_diff > dot_diff:
                        #         # より普通の球形補間から遠い場合、保持
                        #         far_t = t
                        #         dot_max_diff = dot_diff

                        # x1v = bf.complement[utils.R_x1_idxs[3]]
                        # y1v = bf.complement[utils.R_y1_idxs[3]]
                        # x2v = bf.complement[utils.R_x2_idxs[3]]
                        # y2v = bf.complement[utils.R_y2_idxs[3]]

                        # # 最も遠いtに基づく変化量を求める
                        # far_x3, far_x, far_y = utils.calc_interpolate_bezier_by_t(x1v, y1v, x2v, y2v, start, end, far_t)
                        # logger.debug("b: %s, f: %s, [rot] far t: %s, x: %s, y: %s", bf.format_name, bf.frame, far_t, far_x, far_y)

                        # far_bf = [x for x in frames_by_bone if x.frame == far_x3]

                        # if far_bf:
                        #     # 既にキーが登録されている場合、次に移動
                        #     bf_idx += 1
                        #     continue

                        # # 最も遠いtの実際の変化量を求める
                        # now_t, now_x, now_y = utils.calc_interpolate_bezier(x1v, y1v, x2v, y2v, start, end, far_x3)
                        # logger.debug("b: %s, f: %s, [rot] now t: %s, x: %s, y: %s", bf.format_name, far_x3, now_t, now_x, now_y)

                        # # 最も遠いところのbf
                        # fill_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, far_x3)
                        # fill_bf.key = True
                        # for n in utils.R_y2_idxs:
                        #     # 終点の変化量を遠いYで設定する
                        #     fill_bf.complement[n] = utils.COMPLEMENT_MMD_MAX - (far_y * utils.COMPLEMENT_MMD_MAX)
                            
                        # logger.debug("b: %s, f: %s, [rot] comp: %s", bf.format_name, far_x3, fill_bf.complement)

                        # if far_x3 > bf.frame:
                        #     # 現在フレームより後のフレームにキーを追加する場合、INDEX等加算
                        #     insert_idx = bf_idx
                        #     bf_idx += 1
                        # else:
                        #     # 前の場合、前のINDEX指定
                        #     insert_idx = bf_idx - 1

                        # # まだそのフレーム番号のキーがない場合は、追加
                        # frames_by_bone.insert(insert_idx, fill_bf)

                        # logger.debug("fill_bf.complement: %s", fill_bf.complement)

                    # # デフォルトスタンス位置
                    # _, _, _, _, default_global_3ds = utils.create_matrix_global(model, links, {}, bf)
                    # default_pos = default_global_3ds[-1]

                    # # 指定ボーンのグローバル位置ALL
                    # _, _, _, _, prev_global_3ds = utils.create_matrix_global(model, links, frames_by_bone, prev_bf)                        
                    # _, _, _, _, now_global_3ds = utils.create_matrix_global(model, links, frames_by_bone, bf)
                    # prev_pos = prev_global_3ds[-1]
                    # now_pos = now_global_3ds[-1]

                    # # 指定ボーンの回転量
                    # prev_direction_qq = utils.calc_upper_direction_qq(model, links, frames_by_bone, prev_bf)
                    # now_direction_qq = utils.calc_upper_direction_qq(model, links, frames_by_bone, bf)

                    # # 指定ボーンの正面向きグローバル位置ALL
                    # front_prev_global_3ds = utils.create_direction_pos_all(prev_direction_qq.inverted(), prev_global_3ds)
                    # front_now_global_3ds = utils.create_direction_pos_all(now_direction_qq.inverted(), now_global_3ds)

                    # # 指定ボーンの正面向きグローバル位置
                    # front_prev_pos = front_prev_global_3ds[-1]
                    # front_now_pos = front_now_global_3ds[-1]
                    # utils.output_message("b: %s, f: %s, front_now_pos: %s" % (bf.format_name, bf.frame, front_now_pos))

                    # for idx, fill_bf_fno in enumerate(range(prev_bf.frame + 1, bf.frame)):
                    #     # 前回と今回の間のキーを埋める
                    #     fill_bf = VmdBoneFrame()
                    #     fill_bf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
                    #     fill_bf.format_name = bone_name
                    #     fill_bf.frame = fill_bf_fno
                    #     fill_bf.key = True
                        
                    #     # グローバル位置の増分を求める
                    #     step = bf.frame - prev_bf.frame + 1

                    #     if model.bones[bone_name].getTranslatable():
                    #         # 移動が許可されている場合、移動から求める
                    #         fill_pos = ((bf.position - prev_bf.position) / step * (idx + 1))
                    #         fill_bf.position = prev_bf.position + fill_pos
                    #         utils.output_message("b: %s, f: %s, mov fill_pos: %s" % (fill_bf.format_name, fill_bf.frame, fill_bf.position), is_print)
                    #     else:
                    #         # 球形補間で移動量を求める
                    #         fill_bf.rotation = QQuaternion.slerp(prev_bf.rotation, bf.rotation, idx / step)
                    #         # front_fill_global_pos = front_prev_pos + ((front_now_pos - front_prev_pos) / step * (idx + 1))
                    #         # # utils.output_message("b: %s, f: %s, rot fill_pos: %s" % (fill_bf.format_name, fill_bf.frame, front_fill_global_pos), is_print)

                    #         # fill_global_3ds = copy.deepcopy(prev_global_3ds)
                    #         # fill_global_3ds[-1] = front_fill_global_pos

                    #         # # グローバル位置に辿り着く為のクォータニオンを求める
                    #         # fill_global_3ds = utils.create_direction_pos_all(prev_direction_qq, fill_global_3ds)
                    #         # fill_pos = fill_global_3ds[-1]
                    #         # fill_qq = QQuaternion.rotationTo(front_prev_pos.normalized(), front_fill_global_pos.normalized())
                    #         # fill_bf.rotation = (prev_bf.rotation * fill_qq.inverted())
                    #         # utils.output_message("f: %s, fill_bf.rotation: %s" % (fill_bf_fno, fill_bf.rotation.toEulerAngles()), is_print)
                    #         utils.output_message("b: %s, f: %s, rot fill_rot: %s" % (fill_bf.format_name, fill_bf.frame, fill_bf.rotation.toEulerAngles()), is_print)

                        # frames_by_bone.insert(fill_bf_fno, fill_bf)


                # split_frames = {"rot_x": {k: []}, "rot_y": {k: []}, "rot_z": {k: []}, "pos_x": {k: []}, "pos_y": {k: []}, "pos_z": {k: []}}

                # # 移動と回転を滑らかに
                # smooth_rotation(frames_by_bone[k], 3)
                # smooth_pose(frames_by_bone[k], 3)
                # smooth_filter(k, frames_by_bone[k], {"freq": 30, "mincutoff": 0.1, "beta": 0.5, "dcutoff": 0.8})

                # # 間引き（必要なキーだけONにする）
                # reduce_frames(frames_by_bone[k], 0.5, 5)

            # with open(camera_fpath, encoding='cp932', mode='w') as f:
                
            #     # s = "フレーム,位置X,位置Y,位置Z,回転X,回転Y,回転Z,距離,視野角,パース,X_x1,Y_x1,Z_x1,R_x1,L_x1,VA_x1, X_y1,Y_y1,Z_y1,R_y1,L_y1,VA_y1,X_x2,Y_x2,Z_x2,R_x2,L_x2,VA_x2, X_y2,Y_y2,Z_y2,R_y2,L_y2,VA_y2"
            #     f.write(s)
            #     f.write("\n")

            #     for cf in frames_by_bone.cameras:
            #         s = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9},{10}".format(cf.frame, cf.position.x(), cf.position.y(), cf.position.z(), cf.euler.x(), cf.euler.y(), cf.euler.z(), -cf.length, cf.angle, cf.perspective,','.join([str(i) for i in cf.complement]))
            #         f.write(s)
            #         f.write("\n")


# def reduce_frames(frames, threshold_pos, threshold_rot):
#     reduced_frames = reduce_bone_frame(frames, frames, 0, len(frames) - 1, threshold_pos, threshold_rot, False)
    
#     for rf in reduced_frames:
#         active_bf_idx = [e for e, x in enumerate(frames) if x.frame == rf.frame]
#         if active_bf_idx:
#             logger.debug("active: %s, name: %s", frames[active_bf_idx[0]].frame, frames[active_bf_idx[0]].format_name)
#             frames[active_bf_idx[0]].key = True

# # キーフレームを間引く
# # オリジナル：https://github.com/errno-mmd/smoothvmd/blob/master/reducevmd.cc
# def reduce_bone_frame(total_frames, v, head, tail, threshold_pos, threshold_rot, bezier):
#     # 移動のエラー最大値
#     max_pos_err = float(0.0)
#     # 回転のエラー最大値
#     max_rot_err = float(0.0)
#     # 移動：エラー最大値のindex
#     max_idx_pos = 0
#     # 回転：エラー最大値のindex
#     max_idx_rot = 0
#     # 最初から最後までのフレーム数
#     total = tail - head
#     head_frame = v[head]
#     tail_frame = v[tail]
#     bezier_interpolation_limit = 60

#     # if bezier and tail - head < bezier_interpolation_limit:
#     #     optimize_bezier_parameter(tail_frame, v, head, tail)

#     for i in range(head + 1, tail , 1):
#         # 移動
#         f = [x for x in total_frames if x.frame == i][0]
#         pos_err = (f.position - v[i].position).length()

#         if pos_err > max_pos_err:
#             max_idx_pos = i
#             max_pos_err = pos_err

#         t = float(i - head) / total

#         # 回転
#         ip_rot = QQuaternion.slerp(v[head].rotation, v[tail].rotation, t)
#         q_err = (ip_rot * v[i].rotation.inverted()).normalized()

#         # フィルタではなく、ここで正負反転させてプラスに寄せる
#         if q_err.scalar() < 0:
#             q_err.setX(q_err.x() * -1)
#             q_err.setY(q_err.y() * -1)
#             q_err.setX(q_err.z() * -1)
#             q_err.setScalar(q_err.scalar() * -1)
            
#         #  math.acos(q_err.scalar()) * 2 * 180 / math.pi
#         rot_err = math.degrees(math.acos(q_err.scalar()))
#         # logger.debug("rot_err: %s, %s", rot_err, max_rot_err)
        
#         if rot_err > max_rot_err:
#             max_idx_rot = i
#             max_rot_err = rot_err

#     v1 = []
#     if max_pos_err > threshold_pos:
#         v1 = reduce_bone_frame(total_frames, v, head, max_idx_pos, threshold_pos, threshold_rot, bezier)
#         v2 = reduce_bone_frame(total_frames, v, max_idx_pos, tail, threshold_pos, threshold_rot, bezier)
        
#         v1.extend(v2)
#     else:
#         if max_rot_err > threshold_rot:
#             v1 = reduce_bone_frame(total_frames, v, head, max_idx_rot, threshold_pos, threshold_rot, bezier)
#             v2 = reduce_bone_frame(total_frames, v, max_idx_rot, tail, threshold_pos, threshold_rot, bezier)

#             v1.extend(v2)
#         else:
#             v1.append(v[head])

#     return v1

                        # if cnt < rot_repeat and axis == "角度" and model.bones[bone_name].getRotatable()\
                        #         and ((model.bones[bone_name].getTranslatable() and cnt < pos_repeat) or (not model.bones[bone_name].getTranslatable())):
                        #     # now_bf.key = next_bf.key = False
                        #     # now_bf.key = (cnt >= pos_repeat and model.bones[bone_name].getTranslatable() and now_bf.key )
                        #     is_r_result, near_bf, far_bf = smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs, (cnt == 0), \
                        #         define_get_bezier_get_default_val_rot, define_get_bezier_get_test_val_rot, define_get_bezier_get_far_target_rot, define_get_bezier_get_y_rot, define_set_target_val_rot, define_set_notarget_val_rot)
                        #     utils.output_message("smooth_bf r finish now: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), is_print)
                        
                        # if cnt < pos_repeat and axis == "X" and model.bones[bone_name].getTranslatable()\
                        #         and ((model.bones[bone_name].getRotatable() and cnt < rot_repeat) or (not model.bones[bone_name].getRotatable())):
                        #     # now_bf.key = next_bf.key = False
                        #     # now_bf.key = (cnt >= rot_repeat and model.bones[bone_name].getRotatable() and now_bf.key )
                        #     is_x_result, near_bf, far_bf = smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, utils.MX_x1_idxs, utils.MX_y1_idxs, utils.MX_x2_idxs, utils.MX_y2_idxs, (cnt == 0), \
                        #         define_get_bezier_get_default_val_pos_x, define_get_bezier_get_test_val_pos_x, define_get_bezier_get_far_target_pos, define_get_bezier_get_y_pos_x, define_set_target_val_pos_x, define_set_notarget_val_pos_y)
                        #     utils.output_message("smooth_bf x finish now: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), is_print)

                        # if cnt < pos_repeat and axis == "Y" and model.bones[bone_name].getTranslatable()\
                        #         and ((model.bones[bone_name].getRotatable() and cnt < rot_repeat) or (not model.bones[bone_name].getRotatable())):
                        #     # now_bf.key = next_bf.key = False
                        #     # now_bf.key = (cnt >= rot_repeat and ( model.bones[bone_name].getRotatable() and now_bf.key ))
                        #     is_y_result, near_bf, far_bf = smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, utils.MY_x1_idxs, utils.MY_y1_idxs, utils.MY_x2_idxs, utils.MY_y2_idxs, (cnt == 0), \
                        #         define_get_bezier_get_default_val_pos_y, define_get_bezier_get_test_val_pos_y, define_get_bezier_get_far_target_pos, define_get_bezier_get_y_pos_y, define_set_target_val_pos_y, define_set_notarget_val_pos_y)
                        #     utils.output_message("smooth_bf y finish now: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), is_print)

                        # if cnt < pos_repeat and axis == "Z" and model.bones[bone_name].getTranslatable()\
                        #         and ((model.bones[bone_name].getRotatable() and cnt < rot_repeat) or (not model.bones[bone_name].getRotatable())):
                        #     # now_bf.key = next_bf.key = False
                        #     # now_bf.key = (cnt >= rot_repeat and ( model.bones[bone_name].getRotatable() and now_bf.key ))
                        #     is_z_result, near_bf, far_bf = smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, utils.MZ_x1_idxs, utils.MZ_y1_idxs, utils.MZ_x2_idxs, utils.MZ_y2_idxs, (cnt == 0), \
                        #         define_get_bezier_get_default_val_pos_z, define_get_bezier_get_test_val_pos_z, define_get_bezier_get_far_target_pos, define_get_bezier_get_y_pos_z, define_set_target_val_pos_z, define_set_notarget_val_pos_z)
                        #     utils.output_message("smooth_bf z finish now: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), is_print)
                        

                    # target_axises = []
                    # if model.bones[bone_name].getTranslatable():
                    #     target_axises.extend(["X"]) # ," Y", "Z"

                    # if model.bones[bone_name].getRotatable():
                    #     target_axises.extend(["角度"])

                    # for e, axis in enumerate(target_axises):

                        # is_r_result = is_x_result = is_y_result = is_z_result = False
                        # near_bf = far_bf = None

                        # is_r_result, near_bf, far_bf = smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, (cnt == 0))

                        # # farを登録する
                        # frames_by_bone[near_bf.frame] = near_bf
                        # frames_by_bone[far_bf.frame] = far_bf
                    # while now_bf.frame < last_frameno:

                    #     # 次のを処理してたら終了
                    #     if next_bf.frame > last_frameno: break

                    #     # if cnt == 0 and e == 0:
                    #     #     # 初回は、読み込んだキーの間を埋めていく
                    #     #     next_now_frameno = near_bf.frame + 1

                    #     #     # 現在フレームは、初回は前回と次回の間で計算して繋ぐ
                    #     #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, next_now_frameno, False, False, False, False)
                    #     #     # 一度通常通り次のキーを読み込んで、フレーム番号が同じ場合、埋まったと見なし、次に行く
                    #     #     # if now_bf.frame == next_next_frameno:
                    #     #     #     # 次キーと等しい場合、次の区間
                    #     #     #     next_prev_frameno = next_bf.frame
                    #     #     #     next_now_frameno = next_bf.frame + 1
                    #     #     #     next_next_frameno = next_bf.frame + 1
                    #     #     if now_bf.frame == next_now_frameno:
                    #     #         # 現在キーと等しい場合、次の区間
                    #     #         next_prev_frameno = now_bf.frame
                    #     #         next_now_frameno = now_bf.frame + 1
                    #     #         next_next_frameno = now_bf.frame + 1
                    #     #     else:
                    #     #         # まだ違う場合、間を埋めていく
                    #     #         next_prev_frameno = prev_bf.frame
                    #     #         next_next_frameno = next_bf.frame
                    #     # else:
                    #     # 2回目以降はあるキーをそのまま埋めていく
                    #     # next_now_frameno = next_prev_frameno + 1

                    #     # 前は、初回は前回と次回の間で計算して繋ぐ
                    #     next_prev_frameno = near_bf.frame if near_bf.frame != far_bf.frame else prev_bf.frame + 1
                    #     prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, next_prev_frameno, is_only=False, is_exist=(cnt == 0 and e == 0))
                    #     if not prev_bf: break
                    #     # prev_bf.position = frames_by_bone[prev_bf.frame].position
                    #     # prev_bf.rotation = frames_by_bone[prev_bf.frame].rotation
                        
                    #     # 現在フレームは、初回は前回と次回の間で計算して繋ぐ
                    #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=(cnt == 0 and e == 0))
                    #     if not now_bf: break
                    #     # if now_bf.frame in frames_by_bone:
                    #     #     now_bf.position = frames_by_bone[now_bf.frame].position
                    #     #     now_bf.rotation = frames_by_bone[now_bf.frame].rotation
                        
                    #     # 次は、あるのを取得
                    #     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
                    #     if not next_bf:
                    #         if now_bf.frame == last_frameno:
                    #             # 一度最終キーの次を登録したと見なして処理する
                    #             next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=False)
                    #         else:
                    #             break
                    #     else:
                    #         if now_bf.frame >= last_frameno:
                    #             break
                    #         # next_bf.position = frames_by_bone[next_bf.frame].position
                    #         # next_bf.rotation = frames_by_bone[next_bf.frame].rotation
                            
                    #         # 実際のフレーム番号を保持
                    #         next_prev_frameno = prev_bf.frame
                    #         next_next_frameno = next_bf.frame

                    #             # # 最終キーを有効にする
                    #             # next_bf.key = True

                    #         # if now_bf.frame == next_bf.frame == last_frameno:
                    #         #     # 一度最終キーの次を登録したと見なして処理する
                    #         #     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, next_bf.frame + 1, False, False, False, True)
                    #         #     # 最終キーを有効にする
                    #         #     next_bf.key = True
                    #         # if cnt == 0:
                    #         #     # 初回で現在と次が被ったら、次にいく
                    #         #     prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame, True, True, False, False)
                    #         #     if not prev_bf:
                    #         #         break

                    #         #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, False, False, False, False)
                    #         #     if not now_bf:
                    #         #         break
                                
                    #         #     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, False, False, False, False)
                    #         #     if not next_bf:
                    #         #         break
                                
                    #         #     # 初回は次の範囲を続ける
                    #         #     continue
                    #         # now_bf.key = True

                    #         # # 最終キーを有効にする
                    #         # next_bf.key = True

                    #         # if next_bf.frame == last_frameno:
                    #         #     # 一度最終キーの次を登録したと見なして処理する
                    #         #     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, next_bf.frame + 1, False, False, False, True)
                    #         # else:
                    #         #     # 次のキーも処理し終わってたら終了
                    #         #     break

# def define_get_bezier_get_y_rot(model, frames_by_bone, bone_name, prev_bf, bf, t):
#     # 線形補間と球形補間のdotで回転量の大きさをはかる
#     nlerp_rot = QQuaternion.nlerp(prev_bf.rotation, bf.rotation, t)
#     slerp_rot = QQuaternion.slerp(prev_bf.rotation, bf.rotation, t)

#     return QQuaternion.dotProduct(nlerp_rot, slerp_rot)

# def define_get_bezier_get_y_pos_x(model, bframes_by_bone, bone_name, prev_bf, bf, t):
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(VmdBoneFrame(), prev_bf, bf, t)
#     return tx

# def define_get_bezier_get_y_pos_y(model, frames_by_bone, bone_name, prev_bf, bf, t):
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(VmdBoneFrame(), prev_bf, bf, t)
#     return ty

# def define_get_bezier_get_y_pos_z(model, frames_by_bone, bone_name, prev_bf, bf, t):
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(VmdBoneFrame(), prev_bf, bf, t)
#     return tz

# def define_get_bezier_get_default_val_rot(bf):
#     # 前の1つ後の回転と次の回転の球形補間
#     # return  QQuaternion.slerp(prev_bf.rotation, next_bf.rotation, t)
#     return bf.rotation

# def define_get_bezier_get_default_val_pos_x(bf):
#     return bf.position.x()

# def define_get_bezier_get_default_val_pos_y(bf):
#     return bf.position.y()

# def define_get_bezier_get_default_val_pos_z(bf):
#     return bf.position.z()

# def define_get_bezier_get_test_val_rot(prev_bf, now_bf, next_bf, t):
#     # 前の1つ後の回転と次の回転の線形補間
#     # return  QQuaternion.nlerp(prev_bf.rotation, next_bf.rotation, t)

#     # 角度をeulerに変換した際の中間値
#     prev_euler = prev_bf.rotation.toEulerAngles()
#     next_euler = next_bf.rotation.toEulerAngles()
    
#     test_euler = prev_euler + ((next_euler - prev_euler) * t)

#     test_qq = QQuaternion.fromEulerAngles(test_euler)

#     if abs(QQuaternion.dotProduct(test_qq, now_bf.rotation)) < 0.96:
#         # 大きく離れている場合、現在の値をそのまま採用
#         return now_bf.rotation

#     # オイラー角に戻した時に離れている場合も現在の値    
#     if abs(test_qq.toEulerAngles().x()) - abs(now_bf.rotation.x()) > 90:
#         return now_bf.rotation
#     if abs(test_qq.toEulerAngles().y()) - abs(now_bf.rotation.y()) > 90:
#         return now_bf.rotation
#     if abs(test_qq.toEulerAngles().z()) - abs(now_bf.rotation.z()) > 90:
#         return now_bf.rotation

#     return test_qq, t

# # http://marupeke296.com/DXG_No57_SheareLinearInterWithoutQu.html
# def get_bezier_get_test_val_pos(prev_bf, now_bf, next_bf, t):
    
#     p = prev_bf.position
#     n = next_bf.position

#     # if p == n or now_bf.frame == prev_bf.frame or t == 0:
#     #     # 固定で前F該当
#     #     return p, 0, 0, 0
    
#     # if prev_bf.frame + 1 == next_bf.frame or t == 1:
#     #     # 固定で後F該当
#     #     return n, 1, 1, 1

#     # 本来の距離（再計算する）
#     d = calc_bone_by_complement_pos(prev_bf, next_bf, copy.deepcopy(now_bf))

#     # 2ベクトルのｔによる中点
#     mid = (p + n) * t

#     # 中点を原点とみなした半径
#     radius = math.sqrt((mid.x()**2) + (mid.y()**2) + (mid.z()**2))

#     # 各角度の向き
#     x_sign = -1 if (n.x() > p.x()) else 1 if (n.x() < p.x()) else 0
#     y_sign = -1 if (n.y() > p.y()) else 1 if (n.y() < p.y()) else 0
#     z_sign = -1 if (n.z() > p.z()) else 1 if (n.z() < p.z()) else 0

#     s1 = (1 - t)
#     s2 = t

#     # 比率による増減
#     xr = 1 if t == 1 else math.asin(s1) if n.x() >= p.x() else  math.asin(s2)
#     yr = 1 if t == 1 else math.atan(s1) if n.y() >= p.y() else  math.atan(s2)
#     zr = 1 if t == 1 else math.asin(s2) if n.z() >= p.z() else  math.asin(s1)

#     # 実際の値
#     x = p.x() + ((d.x() + (p.x() * x_sign)) * xr) if n.x() != p.x() else 0
#     y = p.y() + ((d.y() + (p.y() * y_sign)) * yr) if n.y() != p.y() else 0
#     z = p.z() + ((d.z() + (p.z() * z_sign)) * zr) if n.z() != p.z() else 0

#     # 計算結果と実際の変化量を返す
#     return QVector3D(x, y, z), abs(xr), abs(yr), abs(zr)


    # s1 = max(1, min(-1, 1 / ((1 - t) * radius)))
    # s2 = max(1, min(-1, 1 / ((t) * radius)))


    # # 本来の距離（再計算する）
    # d = calc_bone_by_complement_pos(prev_bf, next_bf, copy.deepcopy(now_bf))

    # 原点に加算して、位置を求める

    # xt = 1 - t if (n.x() >= p.x()) else t
    # yt = 1 - t if (n.y() >= p.y()) else t
    # zt = 1 - t if (n.z() >= p.z()) else t

    # out_pos = p + (n * QVector3D(x, y, z) * t)

    # diff = out_pos / d2_pos
    # utils.set_effective_value_vec3(diff)

    # x = 0 if (t == 0) else 1 if (t == 1) else math.asin(1 - t)
    # y = 0 if (t == 0) else 1 if (t == 1) else math.atan(1 - t)
    # z = 0 if (t == 0) else 1 if (t == 1) else math.acos(1 - t)
    
    # if t == 0:
    #     return prev_bf.position, 0, 0, 0

    # if t == 1:
    #     return next_bf.position, 1, 1, 1

    # # 各角度の向き
    # x_sign = 1 if (n.x() > p.x()) else -1 if (n.x() < p.x()) else 0
    # y_sign = 1 if (n.y() > p.y()) else -1 if (n.y() < p.y()) else 0
    # z_sign = 1 if (n.z() > p.z()) else -1 if (n.z() < p.z()) else 0
    # sign = QVector3D(x_sign, y_sign, z_sign)

    # # 2ベクトルの中点
    # mid = (p + n) * 0.5

    # # 中点を原点とみなした半径
    # radius = math.sqrt((mid.x()**2) + (mid.y()**2) + (mid.z()**2))


    # # 内積（念のため-1～1に収める）
    # dot = max(1, min(-1, QVector3D.dotProduct(p.normalized(), d.normalized())))
    # # 2ベクトル間の角度（鋭角側）
    # angle = math.acos(dot)

    # # 極座標による媒介変数表示（とりあえず変化量だけ知りたいので、半径1）
    # x = math.cos(t) * math.cos(1 - t)
    # y = math.cos(t) * math.sin(1 - t)
    # z = math.sin(t)

    # # 内積を求める
    # dot = QVector3D.dotProduct(d2_pos.normalized(), out_pos.normalized())

    # # 本来の距離
    # d2_bf = copy.deepcopy(now_bf)
    # calc_bone_by_complement_pos(prev_bf, now_bf, d2_bf, prev_bf.position, now_bf.position, now_bf.complement)
    # d2_pos = d2_bf.position

    # diff = out_pos / d2_pos
    # utils.set_effective_value_vec3(diff)

    # m2 = (m / l)

    # p = prev_bf.position
    # n = now_bf.position
    # d = now_bf.position

    # # 2ベクトル間の角度（鋭角側）
    # a =  math.acos(QVector3D.dotProduct(p.normalized(), n.normalized()))

    # # 結果
    # ox = (( (math.sin( a * (1 - t) ) * p.x()) + (math.sin( a * t ) * n.x()) ) / math.sin(a))
    # oy = (( (math.sin( a * (1 - t) ) * p.y()) + (math.sin( a * t ) * n.y()) ) / math.sin(a))
    # oz = (( (math.sin( a * (1 - t) ) * p.z()) + (math.sin( a * t ) * n.z()) ) / math.sin(a))

    # out_pos = QVector3D(ox, oy, oz)

    # mx = max(a.x(), b.x())
    # my = max(a.y(), b.y())
    # mz = max(a.z(), b.z())

    # nx = min(a.x(), b.x())
    # ny = min(a.y(), b.y())
    # nz = min(a.z(), b.z())

    # if ((b.x() >= a.x())) and ((b.z() >= a.z())):
    #     # X増加、Z増加
    #     tx = math.sin(1 - t)
    #     tz = math.cos(t)
    # elif ((b.x() < a.x())) and ((b.z() >= a.z())):
    #     # X減少、Z増加
    #     tx = (math.sin(1 - t)) * -1
    #     tz = (math.cos(t))
    # elif ((b.x() >= a.x())) and ((b.z() < a.z())):
    #     # X増加、Z減少
    #     tx = math.sin(t)
    #     tz = (math.cos(1 - t)) * -1
    # else:
    #     # X減少、Z減少
    #     tx = (math.sin(1 - t)) * -1
    #     tz = (math.cos(t)) * -1

    # if (b.y() >= a.y()):
    #     # Y増加
    #     ty = math.tan(1 - t)
    # else:
    #     # Y減少
    #     ty = (math.tan(t)) * -1

    # # 直線移動した場合の値
    # # tによって、移動量を変える
    # test_pos = a + ((QVector3D(mx, my, mz) - QVector3D(nx, ny, nz)) * QVector3D(tx, ty, tz))

    # return test_pos, tx, ty, tz


        # bx = math.asin(1 - t)
        # by = math.atan(1 - t)
        # bz = math.acos(1 - t)

        # tx = bx * by
        # ty = by * bz
        # tz = bz * bx
            
    # # prevとnowを移動させて原点からずらす
    # p = prev_bf.position
    # n = now_bf.position

    # # 原点を通る場合のオフセット
    # if p == QVector3D():
    #     if (n - p).x() >= 0:
    #         p2 = QVector3D(1, 0, 0)
    #     else:
    #         p2 = QVector3D(-1, 0, 0)
    # else:
    #     p2 = p

    # if n == QVector3D():
    #     if (n - n).x() >= 0:
    #         n2 = QVector3D(1, 0, 0)
    #     else:
    #         n2 = QVector3D(-1, 0, 0)
    # else:
    #     n2 = n

    # # 2ベクトル間の角度（鋭角側）
    # a =  math.acos(QVector3D.dotProduct(p2.normalized(), n2.normalized()))

    # # aが0という事は同じ向きなので、1とみなす
    # a = 1 if a == 0 else a

    # # 結果
    # ox = (( (math.cos( a * (1 - t) ) * p.x()) + (math.cos( a * t ) * n.x()) ) / math.cos(a))
    # oy = (( (math.tan( a * (1 - t) ) * p.y()) + (math.tan( a * t ) * n.y()) ) / math.tan(a))
    # oz = (( (math.sin( a * (1 - t) ) * p.z()) + (math.sin( a * t ) * n.z()) ) / math.sin(a))

    # out_pos = QVector3D(ox, oy, oz)

    # # 本来の距離
    # d2_bf = copy.deepcopy(now_bf)
    # calc_bone_by_complement_pos(prev_bf, now_bf, d2_bf, prev_bf.position, now_bf.position, now_bf.complement)
    # d2_pos = d2_bf.position

    # diff = out_pos / d2_pos
    # utils.set_effective_value_vec3(diff)

    # # 計算結果と実際の変化量を返す
    # return out_pos, diff.x(), diff.y(), diff.z()



    # # 結果
    # ox = (( (math.cos( a * (1 - t) ) * p.x()) + (math.cos( a * t ) * n.x()) ) / math.cos(a))
    # oy = (( (math.tan( a * (1 - t) ) * p.y()) + (math.tan( a * t ) * n.y()) ) / math.tan(a))
    # oz = (( (math.sin( a * (1 - t) ) * p.z()) + (math.sin( a * t ) * n.z()) ) / math.sin(a))

    # # 補間係数
    # pp = math.sin( d * (1 - t) )
    # pn = math.sin( d * t )

    # p2 = QVector3D.crossProduct(QVector3D(1, 0, 0), p)
    # n2 = QVector3D.crossProduct(QVector3D(0, 0, 1), n)

    # # 2ベクトルの中点
    # m = (p + n) * 0.5

    # # 中点から距離
    # l = (m.x()-p.x()**2) + (m.y()-p.y()**2) +  (m.z()-p.z()**2)

    # m2 = (m / l)

    # # 2ベクトル間の角度（鋭角側）
    # angle = math.acos(QVector3D.dotProduct(p.normalized(), n.normalized()))

    # # sinθ
    # sin_th = math.sin(angle)

    # # 補間係数
    # pp = math.sin( angle * (1 - t) )
    # pn = math.sin( angle * t )

    # # 結果
    # out = ( (pp * p) + (pn * n) ) / sin_th

    # # 元々の移動量との差
    # diff = out.normalized() / now_bf.position.normalized()
    # utils.set_effective_value_vec3(diff)

    # 計算結果と実際の変化量を返す
    # return out, diff.x(), diff.y(), diff.z()






    # a = QVector3D(1, 0, 0) if p == QVector3D() else p
    # b = QVector3D(1, 0, 0) if n == QVector3D() else n

    # # 2ベクトル間の角度（鋭角側）
    # d = QVector3D.dotProduct(a.normalized(), b.normalized())
    # c = math.acos(d)

    # # XYZの移動比率
    # x = math.cos(c)
    # y = math.tan(c)
    # z = math.sin(c)

    # # 実際の位置
    # out = p + ( (n - p) * QVector3D(x, y, z) * t )

    # 計算結果と実際の変化量を返す
    # return out, x, y, z



# public Vector3 GetPosition(float angle, float radius) {
# 2
# 	    float x = Mathf.Cos(angle * Mathf.Deg2Rad) * radius;
# 3
# 	    float y = Mathf.Sin(angle * Mathf.Deg2Rad) * radius;
# 4
# 	    return new Vector3 (x, y, 0);
# 5
# 	}

# public Vector3 GetPosition(float angle1, float angle2, float radius) {
# 2
# 	        float x = radius * Mathf.Sin(angle1 * Mathf.Deg2Rad) * Mathf.Cos(angle2 * Mathf.Deg2Rad);
# 3
# 	        float y = radius * Mathf.Sin(angle1 * Mathf.Deg2Rad) * Mathf.Sin(angle2 * Mathf.Deg2Rad);
# 4
# 	        float z = radius * Mathf.Cos(angle1 * Mathf.Deg2Rad);
# 5
# 	        return new Vector3(x, y, z);
# 6
# 	}
    # # 原点にあった場合、回転量が求められないので、オフセットする
    # if p == QVector3D() or n == QVector3D():
    #     p += QVector3D(1, 0, 0)
    #     n += QVector3D(1, 0, 0)

    # # prevとnowのそれぞれの回転量（同じ位置から測る）
    # p_qq = QQuaternion.rotationTo(QVector3D(1, 0, 0), p.normalized())
    # n_qq = QQuaternion.rotationTo(QVector3D(1, 0, 0), n.normalized())

    # # 球形補間の変化量
    # pns_qq = QQuaternion.slerp(p_qq, n_qq, t)

    # # 変化量の逆から移動位置を求める
    # out = pns_qq.inverted().rotatedVector(now_bf.position)

    # # 元々の移動量との差
    # diff = out.normalized() / now_bf.position.normalized()
    # utils.set_effective_value_vec3(diff)

    # # 計算結果と実際の変化量を返す
    # return out, diff.x(), diff.y(), diff.z()

    # # 移動させて球形補間の位置を求める
    # mat = QMatrix4x4()
    # # 移動する
    # mat.translate(p)
    # # 変化量分回転
    # mat.rotate(pns_qq)
    # # オフセット分を戻して位置を算出
    # out = mat * total_offset

    # # 原点から1移動した角度を回転させた場合の
    # mat = QMatrix4x4()
    # mat.translate(p)
    # mat.rotate(pns_qq)
    # test_pos = mat * n

    # # 2ベクトル間の角度（鋭角側）
    # angle = math.acos(QVector3D.dotProduct(s, e))

    # # sinθ
    # sin_th = math.sin(math.radians(angle))

    # # 補間係数
    # ps = math.sin( angle * (1 - t) )
    # pe = math.sin( angle * t )

    # # 結果
    # out = ( (ps * s) + (pe * e) ) / sin_th

    # # 元々の移動量との差
    # diff = out.normalized() / now_bf.position.normalized()
    # utils.set_effective_value_vec3(diff)

    # # 計算結果と実際の変化量を返す
    # return out, diff.x(), diff.y(), diff.z()

    # mx = max(abs(a.x()), abs(b.x()))
    # my = max(abs(a.y()), abs(b.y()))
    # mz = max(abs(a.z()), abs(b.z()))

    # nx = min(abs(a.x()), abs(b.x()))
    # ny = min(abs(a.y()), abs(b.y()))
    # nz = min(abs(a.z()), abs(b.z()))

    # # prevとnowのそれぞれの回転量（同じ位置から測る）
    # a_qq = QQuaternion.rotationTo(QVector3D(1, 0, 0), a.normalized())
    # b_qq = QQuaternion.rotationTo(QVector3D(1, 0, 0), b.normalized())

    # # 球形補間の変化量
    # abs_qq = QQuaternion.slerp(a_qq, b_qq, t)

    # # 原点から1移動した角度を回転させた場合の
    # mat = QMatrix4x4()
    # mat.translate(QVector3D(1, 0, 0))
    # mat.rotate(abs_qq)
    # test_pos = mat * QVector3D(1, 0, 0)

    # # 元々の移動量との差
    # diff = (test_pos + a) / now_bf.position
    # utils.set_effective_value_vec3(diff)

# def define_get_bezier_get_test_val_pos_x(prev_bf, now_bf, next_bf, t):
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(prev_bf, now_bf, next_bf, t)
#     return test_pos.x(), tx

# def define_get_bezier_get_test_val_pos_y(prev_bf, now_bf, next_bf, t):
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(prev_bf, now_bf, next_bf, t)
#     return test_pos.y(), ty

# def define_get_bezier_get_test_val_pos_z(prev_bf, now_bf, next_bf, t):
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(prev_bf, now_bf, next_bf, t)
#     return test_pos.z(), tz

# def define_get_bezier_get_far_target_rot(prev_bf, now_bf, next_bf, t, get_bezier_get_test_val):
#     # テストとして本来あるべき値
#     test_val, t = get_bezier_get_test_val(prev_bf, now_bf, next_bf, t)
#     # 現在の値
#     default_val = now_bf.rotation

#     # 現在の回転と角度の中間地点との差(離れているほど値を大きくする)
#     dot_diff = 1 - abs(QQuaternion.dotProduct(test_val, default_val))

#     # # これまでの内積より小さい値（外れている）だった場合、保持
#     # if max_dot_diff > dot_diff:
#     #     return True, dot_diff

#     # # 回転が反転しそうな場合は1を返して必ず対象とする
#     # if abs(test_val.toEulerAngles().x()) - abs(default_val.toEulerAngles().x()) > 90:
#     #     return True, -1
#     # if abs(test_val.toEulerAngles().y()) - abs(default_val.toEulerAngles().y()) > 90:
#     #     return True, -1
#     # if abs(test_val.toEulerAngles().z()) - abs(default_val.toEulerAngles().z()) > 90:
#     #     return True, -1

#     return dot_diff

# def define_get_bezier_get_far_target_pos(prev_bf, now_bf, next_bf, t, get_bezier_get_test_val):
#     # テストとして本来あるべき値とその変化量
#     test_val, at = get_bezier_get_test_val(prev_bf, now_bf, next_bf, t)
#     return abs(at)

# def define_set_target_val_rot(far_bf, prev_bf, now_bf, t):
#     test_val, t = define_get_bezier_get_test_val_rot(far_bf, prev_bf, now_bf, t)
#     far_bf.rotation = test_val

# def define_set_target_val_pos_x(far_bf, prev_bf, now_bf, t):
#     # x, tx = define_get_bezier_get_test_val_pos_x(far_bf, prev_bf, now_bf, t)
#     # y, ty = define_get_bezier_get_test_val_pos_y(far_bf, prev_bf, now_bf, t)
#     # z, tz = define_get_bezier_get_test_val_pos_z(far_bf, prev_bf, now_bf, t)
#     # far_bf.postion = QVector3D(x, y, z)
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(far_bf, prev_bf, now_bf, t)
#     # far_bf.position = test_pos
#     # d2_pos = calc_bone_by_complement_pos(prev_bf, now_bf, copy.deepcopy(far_bf))

#     far_bf.position.setX(test_pos.x())
#     # far_bf.position.setY(d2_pos.y())
#     # far_bf.position.setZ(d2_pos.z())

#     # x, xt = define_get_bezier_get_test_val_pos_x(far_bf, prev_bf, now_bf, t)
#     # far_bf.position.setX(x)

# def define_set_target_val_pos_y(far_bf, prev_bf, now_bf, t):
#     # x, tx = define_get_bezier_get_test_val_pos_x(far_bf, prev_bf, now_bf, t)
#     # y, ty = define_get_bezier_get_test_val_pos_y(far_bf, prev_bf, now_bf, t)
#     # z, tz = define_get_bezier_get_test_val_pos_z(far_bf, prev_bf, now_bf, t)
#     # far_bf.postion = QVector3D(x, y, z)
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(far_bf, prev_bf, now_bf, t)
#     # far_bf.position = test_pos

#     # d2_pos = calc_bone_by_complement_pos(prev_bf, now_bf, copy.deepcopy(far_bf))

#     # far_bf.position.setX(d2_pos.x())
#     far_bf.position.setY(test_pos.y())
#     # far_bf.position.setZ(d2_pos.z())
#     # far_bf.position.setY(test_pos.y())
#     # y, yt = define_get_bezier_get_test_val_pos_y(far_bf, prev_bf, now_bf, t)
#     # far_bf.position.setY(y)

# def define_set_target_val_pos_z(far_bf, prev_bf, now_bf, t):
#     # x, tx = define_get_bezier_get_test_val_pos_x(far_bf, prev_bf, now_bf, t)
#     # y, ty = define_get_bezier_get_test_val_pos_y(far_bf, prev_bf, now_bf, t)
#     # z, tz = define_get_bezier_get_test_val_pos_z(far_bf, prev_bf, now_bf, t)
#     # far_bf.postion = QVector3D(x, y, z)
#     test_pos, tx, ty, tz = get_bezier_get_test_val_pos(far_bf, prev_bf, now_bf, t)
#     # far_bf.position = test_pos

#     # d2_pos = calc_bone_by_complement_pos(prev_bf, now_bf, copy.deepcopy(far_bf))

#     # far_bf.position.setX(d2_pos.x())
#     # far_bf.position.setY(d2_pos.y())
#     far_bf.position.setZ(test_pos.z())
#     # far_bf.position.setZ(test_pos.z())
#     # z, zt = define_get_bezier_get_test_val_pos_z(far_bf, prev_bf, now_bf, t)
#     # far_bf.position.setZ(z)

# def define_set_notarget_val_rot(far_bf, far_nocalc_bf):
#     far_bf.position = far_nocalc_bf.position

# def define_set_notarget_val_pos_x(far_bf, far_nocalc_bf):
#     far_bf.rotation = far_nocalc_bf.rotation

# def define_set_notarget_val_pos_y(far_bf, far_nocalc_bf):
#     far_bf.rotation = far_nocalc_bf.rotation

# def define_set_notarget_val_pos_z(far_bf, far_nocalc_bf):
#     far_bf.rotation = far_nocalc_bf.rotation

# def get_bezier(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, \
#     get_bezier_get_default_val, get_bezier_get_test_val, get_bezier_get_far_target, get_bezier_get_y, set_target_val, set_notarget_val):

#     max_at = 0
#     target_frameno = prev_bf.frame + 1 # int(( now_bf.frame - prev_bf.frame ) / 2)

#     # # 補間曲線の開始する、prevの次のフレーム
#     # prev_next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=False)

#     for n in range(prev_bf.frame + 1, next_bf.frame - 1):
#         # 開始から終了までで、差がもっとも大きい箇所を探す（farの可能性があるので、最大でもnextの2つ手前まで）
#         t = (n - prev_bf.frame) / ( next_bf.frame - prev_bf.frame)
        
#         # 現在のそのままの中間で求めた変化量
#         now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, n, is_only=False, is_exist=False)
#         # default_val = get_bezier_get_default_val(now_bf)

#         # 現在のそのままの値と、テスト値を比較して、どのくらい離れているかを返す
#         at = get_bezier_get_far_target(prev_bf, now_bf, next_bf, t, get_bezier_get_test_val)

#         if max_at < at:
#             # これまでより遠い値だった場合、保持
#             max_at = at
#             target_frameno = n
    
#     # if not is_target:
#     #     # 最後まで対象が見つからなかった場合、nowを対象とする
#     #     far_frameno = now_bf.frame

#     # if now_bf.frame == far_frameno:
#     #     # 現在と遠いのが同じ場合、遠いのをずらす
#     #     far_frameno = now_bf.frame + 1

#     # 最も遠い追加対象フレームの値を取得する
#     target_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, target_frameno, is_only=False, is_exist=False)

#     if target_bf.frame == now_bf.frame:
#         # 同じフレームが対象の場合、計算しなおしたのを両方に適用する
#         t = (target_bf.frame - prev_bf.frame) / ( next_bf.frame - prev_bf.frame)
#         set_target_val(target_bf, prev_bf, next_bf, t)

#         near_bf = target_bf
#         far_bf = target_bf
        
#     elif target_bf.frame < now_bf.frame:
#         # # prev < target < now < next
#         # # 一度値を計算し直す
#         # target_bf.rotation = calc_bone_by_complement_rot(prev_next_bf, next_bf, target_bf)
#         # target_bf.position = calc_bone_by_complement_pos(prev_next_bf, next_bf, target_bf)

#         # 必要な値だけ設定し直す
#         t = (target_bf.frame - prev_bf.frame) / ( next_bf.frame - prev_bf.frame)
#         set_target_val(target_bf, prev_bf, next_bf, t)

#         near_bf = target_bf
#         far_bf = now_bf

#         # nowの方を計算し直す        
#         now_bf.rotation = calc_bone_by_complement_rot(target_bf, next_bf, now_bf)
#         now_bf.position = calc_bone_by_complement_pos(target_bf, next_bf, now_bf)
        
#         # t = (now_bf.frame - target_bf.frame ) / ( next_bf.frame - target_bf.frame )
#         # set_target_val(now_bf, prev_bf, target_bf, 1 - t)
#     else:
#         # # 補間曲線の開始する、prevの次のフレーム
#         # now_next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=False)

#         # 一度値を計算し直す
#         target_bf.rotation = calc_bone_by_complement_rot(now_bf, next_bf, target_bf)
#         target_bf.position = calc_bone_by_complement_pos(now_bf, next_bf, target_bf)

#         # 必要な値だけ設定し直す
#         t = (target_bf.frame - now_bf.frame ) / ( next_bf.frame - now_bf.frame )
#         set_target_val(target_bf, now_bf, next_bf, t)

#         near_bf = now_bf
#         far_bf = target_bf

#         # nowの再計算は行わない（次の次が必要なため）

#         # # nowの方を計算し直す        
#         # now_bf.rotation = calc_bone_by_complement_rot(target_bf, next_bf, now_bf)
#         # now_bf.position = calc_bone_by_complement_pos(target_bf, next_bf, now_bf)
        
#         # pass
#         # # prev < now < target < next
#         # # 一度値を計算し直す
#         # calc_bone_by_complement_rot(now_bf, next_bf, target_bf, now_bf.rotation, next_bf.rotation, next_bf.complement)
#         # calc_bone_by_complement_pos(now_bf, next_bf, target_bf, now_bf.position, next_bf.position, next_bf.complement)

#         # # 必要な値だけ設定し直す
#         # t = (target_bf.frame - now_bf.frame ) / ( next_bf.frame - now_bf.frame )
#         # set_target_val(target_bf, now_bf, next_bf, t)
#         # t = (now_bf.frame - prev_bf.frame ) / ( target_bf.frame - prev_bf.frame )
#         # set_target_val(now_bf, prev_bf, target_bf, t)

#     # # 遠いのがフレーム番号違う場合だけ、その時になってて欲しい値を設定
#     # if far_bf.frame > now_bf.frame:
#     #     t = (far_frameno - now_bf.frame) / ( next_bf.frame - now_bf.frame )
#     #     set_target_val(now_bf, far_nocalc_bf, next_bf, t)
#     #     now_bf.key = now_bf.split_complement = True
#     #     # nowを追加する場合、こっちは元に戻す
#     #     far_bf = copy.deepcopy(far_nocalc_bf)
#     # else:

#     # # nearとfar は取り直す
#     # near_bf = target_bf if target_bf.frame <= now_bf.frame else now_bf
#     # far_bf = target_bf if target_bf.frame > now_bf.frame else now_bf

#     # キーをONにする
#     near_bf.key = far_bf.key = True

#     # if prev_bf.frame == far_bf.frame or now_bf.frame == far_bf.frame:
#     #     return False, near_bf, far_bf, None, None 

#     # # 必要な値だけ設定し直す
#     # t = (near_bf.frame - prev_bf.frame ) / ( next_bf.frame - prev_bf.frame )
#     # set_target_val(near_bf, prev_bf, next_bf, t)
#     # t = (far_bf.frame - prev_bf.frame ) / ( next_bf.frame - prev_bf.frame )
#     # set_target_val(far_bf, prev_bf, next_bf, t)
#     # set_target_val(far_bf, prev_bf, now_bf, (far_bf.frame - prev_bf.frame ) / ( now_bf.frame - prev_bf.frame ))
#     # set_target_val(far_bf, near_bf, next_bf, t)
#     # # その他の値を設定し直す
#     # set_notarget_val(near_bf, far_nocalc_bf)

#     x1 = prev_bf.frame
#     x2 = near_bf.frame
#     x3 = far_bf.frame

#     if not (x1 < x2 < x3):
#         return False, near_bf, far_bf, None, None
    
#     t = (x2 - x1) / (x3 - x1)
#     y1 = get_bezier_get_y(model, frames_by_bone, bone_name, prev_bf, prev_bf, 0)
#     y2 = get_bezier_get_y(model, frames_by_bone, bone_name, prev_bf, near_bf, ((x2 - x1) / (x3 - x1)))
#     y3 = get_bezier_get_y(model, frames_by_bone, bone_name, prev_bf, far_bf, 1)

#     is_near_target, near_before_bz, near_after_bz = utils.calc_smooth_bezier(x1, y1, x2, y2, x3, y3, t)

#     if not utils.is_fit_bezier_mmd(near_before_bz, 10) or not utils.is_fit_bezier_mmd(near_after_bz, 10):
#         # 補間曲線の分割に合わない場合、登録しない（位置か角度の値だけ変えるので、bfは返す)
#         return False, near_bf, far_bf, None, None

#     # is_far_target, far_before_bz, far_after_bz = utils.calc_smooth_bezier(x2, y2, x3, y3, x4, y4, 1 - t)
#     # else:
#     #     is_far_target = False
#     #     # far_before_bz = [QVector2D(0, 0), \
#     #     #     QVector2D(20, 20), \
#     #     #     QVector2D(107, 107), \
#     #     #     QVector2D(utils.COMPLEMENT_MMD_MAX, utils.COMPLEMENT_MMD_MAX)]
#     #     # far_after_bz = [QVector2D(0, 0), \
#     #     #     QVector2D(20, 20), \
#     #     #     QVector2D(107, 107), \
#     #     #     QVector2D(utils.COMPLEMENT_MMD_MAX, utils.COMPLEMENT_MMD_MAX)]
#     #     far_before_bz = None
#     #     far_after_bz = None

#     return is_near_target, near_bf, far_bf, near_before_bz, near_after_bz

# # bfのスムース化
# def smooth_bf2(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, x1_idxs, y1_idxs, x2_idxs, y2_idxs, is_add, \
#     get_bezier_get_default_val, get_bezier_get_test_val, get_bezier_get_far_target, get_bezier_get_y, set_target_val, set_notarget_val):
    
#     # 開始から終了までで、普通の球形補間で求めた値と最も遠い値を持つフレーム番号を返す
#     is_target, near_bf, far_bf, near_before_bz, near_after_bz = get_bezier(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, \
#         get_bezier_get_default_val, get_bezier_get_test_val, get_bezier_get_far_target, get_bezier_get_y, set_target_val, set_notarget_val)
#     utils.output_message("smooth_bf get_bezier now: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), is_print)
    
#     if not is_target:
#         return False, near_bf, far_bf

#     # # 登録はとりあえずしないとこから開始する
#     # is_insert = False

#     # if far_bf.frame in frames_by_bone:
#     #     fill_bf = frames_by_bone[far_bf.frame]
#     # else:
#     #     is_insert = True
#     #     # まだキーがない場合、追加
#     # fill_bf = far_bf
#     # fill_bf.key = True

#     # near_before_bz = utils.fit_bezier_split_mmd(near_before_bz)
#     # near_after_bz = utils.fit_bezier_split_mmd(near_after_bz)
#     # # far_before_bz = utils.fit_bezier_split_mmd(far_before_bz)
#     # # far_after_bz = utils.fit_bezier_split_mmd(far_after_bz)

#     # # if is_add:
#     # #     prev_bf.key = True
#     #     # fill_after_bf.key = True
#     #     # next_bf.key = True

#     for (bz, front_bf, back_bf) in [(near_before_bz, near_bf, near_bf), (near_after_bz, far_bf, far_bf)]:
#         # ベジェ曲線の配置
#         set_split_complement(bz, front_bf, back_bf, x1_idxs, y1_idxs, x2_idxs, y2_idxs)
#         # logger.debug("b: %s, f: %s, [rot] start comp: %s", target_bf.format_name, target_bf.frame, target_bf.complement)

#     utils.output_message("smooth_bf set_split_complement now: %s" % datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'), is_print)

#     # --------------------

#     return True, near_bf, far_bf

# def set_split_complement(bz, front_bf, back_bf, x1_idxs, y1_idxs, x2_idxs, y2_idxs):
#     # ベジェ曲線をMMDの範囲内に収める
#     bz = utils.fit_bezier_split_mmd(bz)
    
#     if front_bf:
#         # キーの登録が確定したら改めてON
#         front_bf.key  = True
#         front_bf.split_complement = True
        
#         # 始点を設定する
#         front_bf.complement[x1_idxs[0]] = front_bf.complement[x1_idxs[1]] = \
#             front_bf.complement[x1_idxs[2]] = front_bf.complement[x1_idxs[3]] = bz[1].x()
#         front_bf.complement[y1_idxs[0]] = front_bf.complement[y1_idxs[1]] = \
#             front_bf.complement[y1_idxs[2]] = front_bf.complement[y1_idxs[3]] = bz[1].y()

#     if back_bf:
#         # キーの登録が確定したら改めてON
#         back_bf.key  = True
#         back_bf.split_complement = True
        
#         # 終点を設定する
#         back_bf.complement[x2_idxs[0]] = back_bf.complement[x2_idxs[1]] = \
#             back_bf.complement[x2_idxs[2]] = back_bf.complement[x2_idxs[3]] = bz[2].x()
#         back_bf.complement[y2_idxs[0]] = back_bf.complement[y2_idxs[1]] = \
#             back_bf.complement[y2_idxs[2]] = back_bf.complement[y2_idxs[3]] = bz[2].y()

#     # if x1 == y1:
#     #     x1 = y1 = 20

#     # if x2 == y2:
#     #     x2 = y2 = 107

#     # prev_bxy2_diff = round(abs(target_bf.complement[x2_idxs[3]] - target_bf.complement[y2_idxs[3]]))

#         # prev_bxy1_diff = round(abs(target_bf.complement[x1_idxs[3]] - target_bf.complement[y1_idxs[3]]))
#     # if prev_bxy1_diff - 5 < round(abs(x1 - y1)) < prev_bxy1_diff + 5 and prev_bxy2_diff - 5 < round(abs(x2 - y2)) < prev_bxy2_diff + 5:
#     #     # 既存の補間曲線とほぼ同じであれば、追加しない(すでにある場合はOK)
#     #     is_insert = is_insert or False
#     #     # 一旦キーを落とす
#     #     target_bf.key = target_bf.key or False
#     # else:
#     # is_insert = True

#     # return (before_bz or after_bz)


    # if len(now_framenos) > 0 and frames_by_bone[now_framenos[0]].read == True and model.bones[bone_name].getTranslatable():
    #     # 指定フレームのキーがあり、かつ、readで移動ボーンの場合、コピーせずに自身を返す
    #     return frames_by_bone[now_framenos[0]]



#     # ベジェ曲線をMMDの範囲内に収める
#     bz = utils.fit_bezier_split_mmd(bz)
    
#     if front_bf:
#         # キーの登録が確定したら改めてON
#         front_bf.key  = True
#         front_bf.split_complement = True
        
#         # 始点を設定する
#         front_bf.complement[x1_idxs[0]] = front_bf.complement[x1_idxs[1]] = \
#             front_bf.complement[x1_idxs[2]] = front_bf.complement[x1_idxs[3]] = bz[1].x()
#         front_bf.complement[y1_idxs[0]] = front_bf.complement[y1_idxs[1]] = \
#             front_bf.complement[y1_idxs[2]] = front_bf.complement[y1_idxs[3]] = bz[1].y()

#     if back_bf:
#         # キーの登録が確定したら改めてON
#         back_bf.key  = True
#         back_bf.split_complement = True
        
#         # 終点を設定する
#         back_bf.complement[x2_idxs[0]] = back_bf.complement[x2_idxs[1]] = \
#             back_bf.complement[x2_idxs[2]] = back_bf.complement[x2_idxs[3]] = bz[2].x()
#         back_bf.complement[y2_idxs[0]] = back_bf.complement[y2_idxs[1]] = \
#             back_bf.complement[y2_idxs[2]] = back_bf.complement[y2_idxs[3]] = bz[2].y()

    # # 中点を原点とみなした半径
    # radius = math.sqrt((mid.x()**2) + (mid.y()**2) + (mid.z()**2))




    # # 各角度の向き
    # x_sign = 1 if (n.x() > p.x()) else 1
    # y_sign = 1 if (n.y() > p.y()) else 1
    # z_sign = 1 if (n.z() > p.z()) else 1

    # s1 = t
    # s2 = (1 - t)

    # 比率による増減
    # xr = 1 if t == 1 else math.asin(s1) if n.x() >= p.x() else math.acos(s1)
    # yr = 1 if t == 1 else math.atan(s1) if n.y() >= p.y() else math.atan(s2)
    # zr = 1 if t == 1 else math.asin(s2) if n.z() >= p.z() else math.acos(s2)

    # # 極座標による媒介変数表示
    # # https://mathtrain.jp/kyumenequ
    # xr = math.cos(t) * math.cos(2 * t)  if n.x() - p.x() != 0 else 0
    # yr = math.cos(t) * math.sin(2 * t)  if n.y() - p.y() != 0 else 0
    # zr = math.sin(t)                    if n.z() - p.z() != 0 else 0

    # if n == p == QVector3D():
    #     # 原点にある場合、midに加算
    #     # 実際の値
    #     x = mid.x() * xr
    #     y = mid.y() * yr
    #     z = mid.z() * zr
    # else:
    # 実際の値
    # x = mid.x() + ((n.x() - (p.x() * x_sign)) * xr * t)
    # y = mid.y() + ((n.y() - (p.y() * y_sign)) * yr * t)
    # z = mid.z() + ((n.z() - (p.z() * z_sign)) * zr * t)
    # x = radius * xr + (n.x() - p.x())
    # y = radius * yr + (n.y() - p.y())
    # z = radius * zr + (n.z() - p.x())

    # x = radius * xr + p.x()
    # y = radius * yr + p.y()
    # z = radius * zr + p.z()

    # x = (min(n.x(),p.x()) + (max(n.x(),p.x()) - min(n.x(),p.x())) * xr) * t
    # y = (min(n.y(),p.y()) + (max(n.y(),p.y()) - min(n.y(),p.y())) * yr) * t
    # z = (min(n.z(),p.z()) + (max(n.z(),p.z()) - min(n.z(),p.z())) * zr) * t

    # x = p.x() + ((n.x() - p.x()) * xr)
    # y = p.y() + ((n.y() - p.y()) * yr)
    # z = p.z() + ((n.z() - p.z()) * zr)

    # x = mid.x() + ((n.x() - p.x()) * xr * t)
    # y = mid.y() + ((n.y() - p.y()) * yr * t)
    # z = mid.z() + ((n.z() - p.z()) * zr * t)

    # out = QVector3D(x, y, z)



#     # if prev_bf.frame + 1 >= now_bf.frame or now_bf.frame >= next_bf.frame - 1:
#     #     prev_bf.frame += 1

#     #     # prevとnextの値を再取得する
#     #     prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame, is_only=False, is_exist=True)
#     #     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
#     #     if not prev_bf or not next_bf:
#     #         # 前後がなければ終了
#     #         return

#     #     # nowは両者の中間
#     #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, int((prev_bf.frame + next_bf.frame) / 2), is_only=False, is_exist=False)

#     # if prev_bf.frame >= now_bf.frame or now_bf.frame >= next_bf.frame:
#     #     # prevとnextの値を再取得する
#     #     prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, next_bf.frame, is_only=False, is_exist=True)
#     #     if not prev_bf: return

#     #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=False)
#     #     if not now_bf: return

#     #     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
#     #     if not next_bf: return

#     max_at = 0

#     fill_bf = VmdBoneFrame()
#     fill_bf.frame = prev_bf.frame + 1 # int((prev_bf.frame + next_bf.frame) / 2)
#     fill_bf.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
#     fill_bf.format_name = bone_name

#     for n in range(prev_bf.frame + 1, next_bf.frame):
#         # 開始から終了までで、差がもっとも大きい箇所を探す
        
#         # 現在のそのままの中間で求めた変化量
#         now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, n, is_only=False, is_exist=False)

#         # 現在のそのままの値と、テスト値を比較して、どのくらい離れているかを返す
#         test_rot = QQuaternion()
#         if model.bones[bone_name].getRotatable():
#             # if prev_bf.rotation != next_bf.rotation:
#             #     # 回転量を計算し直す
#             #     now_bf.rotation = calc_bone_by_complement_rot(prev_bf, next_bf, now_bf)
#             test_rot, rt = get_smooth_middle_rot(prev_bf, now_bf, next_bf)
#         else:
#             rt = 0
        
#         test_pos = QVector3D()
#         if model.bones[bone_name].getTranslatable():
#             # if prev_bf.position != next_bf.position:
#             #     # 移動量を計算し直す
#             #     now_bf.position = calc_bone_by_complement_pos(prev_bf, next_bf, now_bf)
#             test_pos, mt = get_smooth_middle_pos(prev_bf, now_bf, next_bf)
#         else:
#             mt = 0

#         if max_at < max(rt, mt):
#             # これまでより遠い値だった場合、保持
#             max_at = max(rt, mt)
#             fill_bf.frame = n
#             fill_bf.rotation = test_rot
#             fill_bf.position = test_pos
        
#         # if max_at >= 0.8:
#         #     # 変化量が一定以上の場合、とりあえず分割
#         #     # fill_bf.frame = n
#         #     # fill_bf.rotation = test_rot
#         #     # fill_bf.position = test_pos
#         #     break
    
#     # if prev_bf.frame + 1 >= next_bf.frame:
#     #     # 最後までいったら自身を登録して終了

#     #     # if prev_bf.frame not in  frames_by_bone:
#     #     #     frames_by_bone[prev_bf.frame] = prev_bf

#     #     # frames_by_bone[prev_bf.frame].key = True

#     #     # next_bf.key = True

#     #     # if next_bf.frame not in  frames_by_bone:
#     #     #     frames_by_bone[next_bf.frame] = next_bf

#     #     # frames_by_bone[now_bf.frame].key = True

#     #     # if model.bones[bone_name].getRotatable():
#     #     #     test_rot, rt = get_smooth_middle_rot(fill_bf, prev_bf, next_bf)
#     #     #     fill_bf.rotation = test_rot
        
#     #     # if model.bones[bone_name].getTranslatable():
#     #     #     test_pos, mt = get_smooth_middle_pos(fill_bf, prev_bf, next_bf)
#     #     #     fill_bf.position = test_pos
    
#     #     # now_bf.key = True
#     #     # frames_by_bone[now_bf.frame] = now_bf

#     #     return

#     # if prev_bf.frame < fill_bf.frame < now_bf.frame:
#     #     # if model.bones[bone_name].getRotatable():
#     #     #     test_rot, rt = get_smooth_middle_rot(fill_bf, prev_bf, now_bf)
#     #     #     fill_bf.rotation = test_rot
        
#     #     # test_pos = QVector3D()
#     #     # if model.bones[bone_name].getTranslatable():
#     #     #     test_pos, mt = get_smooth_middle_pos(fill_bf, prev_bf, now_bf)
#     #     #     fill_bf.position = test_pos

#     #     # 前半を分割する
#     #     split_bf(model, frames_by_bone, bone_name, prev_bf, fill_bf, now_bf, next_bf, is_add)

#     # frames_by_bone[fill_bf.frame] = copy.deepcopy(fill_bf)

#     # if fill_bf.frame not in  frames_by_bone:
#     # frames_by_bone[fill_bf.frame] = fill_bf
    
#     # is_filled = False

#     # if fill_bf.frame <= now_bf.frame:

#     #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=False)
#     #     if not now_bf: return

#     #     # 同じ範囲内を再選択した場合、次へ
#     #     smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, is_add)

#     # if prev_bf.frame < fill_bf.frame < now_bf.frame:
#     #     # 現在のそのままの中間で求めた変化量
#     #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, fill_bf.frame, is_only=False, is_exist=False)

#     #     if model.bones[bone_name].getRotatable():
#     #         test_rot, rt = get_smooth_middle_rot(now_bf, prev_bf, now_bf)
#     #         fill_bf.rotation = test_rot
        
#     #     if model.bones[bone_name].getTranslatable():
#     #         test_pos, mt = get_smooth_middle_pos(now_bf, prev_bf, now_bf)
#     #         fill_bf.position = test_pos

#     #     frames_by_bone[fill_bf.frame] = fill_bf

#     #     # 前半を分割する
#     #     split_bf(model, frames_by_bone, bone_name, prev_bf, fill_bf, now_bf, next_bf, is_add)

#     # if model.bones[bone_name].getRotatable():
#     #     test_rot, rt = get_smooth_middle_rot(fill_bf, prev_bf, next_bf)
#     #     fill_bf.rotation = test_rot
    
#     # if model.bones[bone_name].getTranslatable():
#     #     test_pos, mt = get_smooth_middle_pos(fill_bf, prev_bf, next_bf)
#     #     fill_bf.position = test_pos

#     # if now_bf.frame < fill_bf.frame and fill_bf.frame not in frames_by_bone:
#     #     frames_by_bone[fill_bf.frame] = fill_bf
#     #     pass

#         # if model.bones[bone_name].getRotatable():
#         #     test_rot, rt = get_smooth_middle_rot(prev_bf, now_bf, next_bf)
#         #     now_bf.rotation = test_rot
        
#         # if model.bones[bone_name].getTranslatable():
#         #     test_pos, mt = get_smooth_middle_pos(prev_bf, now_bf, next_bf)
#         #     now_bf.position = test_pos
#     # else:

#     # 分割出来なかった場合、次に進む
#     prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
#     if not prev_bf: return

#     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
#     if not now_bf: return

#     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
#     if not next_bf: return

#     smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, is_add)

#     # smooth_bf(model, frames_by_bone, bone_name, prev_bf, fill_bf, now_bf, is_add)

#     # smooth_bf(model, frames_by_bone, bone_name, now_bf, fill_bf, next_bf, is_add)

#     # if now_bf.frame <= fill_bf.frame < next_bf.frame:
#     #     # if model.bones[bone_name].getRotatable():
#     #     #     test_rot, rt = get_smooth_middle_rot(fill_bf, now_bf, next_bf)
#     #     #     fill_bf.rotation = test_rot
        
#     #     # test_pos = QVector3D()
#     #     # if model.bones[bone_name].getTranslatable():
#     #     #     test_pos, mt = get_smooth_middle_pos(fill_bf, now_bf, next_bf)
#     #     #     fill_bf.position = test_pos
        
#     #     # 後半を分割する
#     # #     split_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, fill_bf, next_bf, is_add)
    
#     # smooth_bf(model, frames_by_bone, bone_name, prev_bf, fill_bf, now_bf, is_add)
#     # smooth_bf(model, frames_by_bone, bone_name, now_bf, fill_bf, next_bf, is_add)
#     # if prev_bf.frame + 1 >= now_bf.frame or now_bf.frame >= next_bf.frame - 1:
    
#     # prev_bf.frame += 1

#     # frames_by_bone[now_bf.frame] = now_bf

#     # smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, is_add)


# def split_bf(model, frames_by_bone, bone_name, prev_bf, near_bf, far_bf, next_bf, is_add):

#     is_rot_result = True
#     if model.bones[bone_name].getRotatable():
#         is_rot_result = smooth_bezier(frames_by_bone, prev_bf, near_bf, far_bf, next_bf, get_smooth_bezier_y_rot, utils.R_x1_idxs, utils.R_y1_idxs, utils.R_x2_idxs, utils.R_y2_idxs)

#     is_pos_x_result = True
#     is_pos_y_result = True
#     is_pos_z_result = True
#     if model.bones[bone_name].getTranslatable():
#         is_pos_x_result = smooth_bezier(frames_by_bone, prev_bf, near_bf, far_bf, next_bf, get_smooth_bezier_y_pos_x, utils.MX_x1_idxs, utils.MX_y1_idxs, utils.MX_x2_idxs, utils.MX_y2_idxs)
#         is_pos_y_result = smooth_bezier(frames_by_bone, prev_bf, near_bf, far_bf, next_bf, get_smooth_bezier_y_pos_y, utils.MY_x1_idxs, utils.MY_y1_idxs, utils.MY_x2_idxs, utils.MY_y2_idxs)
#         is_pos_z_result = smooth_bezier(frames_by_bone, prev_bf, near_bf, far_bf, next_bf, get_smooth_bezier_y_pos_z, utils.MZ_x1_idxs, utils.MZ_y1_idxs, utils.MZ_x2_idxs, utils.MZ_y2_idxs)

#     if is_rot_result == is_pos_x_result == is_pos_y_result == is_pos_z_result == True:
#         # # 全部の補間曲線がOKなら設定して終了
#         # prev_bf.key = near_bf.key = far_bf.key = next_bf.key = True

#         # キーをONにする
#         # 念のためコピーして辞書データ置き換え
#         # prev_bf.key = True
#         # frames_by_bone[prev_bf.frame] = copy.deepcopy(prev_bf)
        
#         # near_bf.key = True
#         # frames_by_bone[near_bf.frame] = copy.deepcopy(near_bf)
        
#         # far_bf.key = True
#         # frames_by_bone[far_bf.frame] = copy.deepcopy(far_bf)
        
#         # if next_bf.frame == False:
#         #     next_bf.key = True
#         #     frames_by_bone[next_bf.frame] = copy.deepcopy(next_bf)
        
#         return True
#     # else:
#     #     # # どれかが駄目な場合、前半と後半に分けて分割し直す
#     #     # smooth_bf(model, frames_by_bone, bone_name, prev_bf, near_bf, next_bf, is_add)
#     #     # smooth_bf(model, frames_by_bone, bone_name, prev_bf, far_bf, next_bf, is_add)
#     #     pass

#     return False

# # 滑らかに繋ぐベジェ曲線
# def smooth_bezier(frames_by_bone, prev_bf, near_bf, far_bf, next_bf, get_smooth_bezier_y, x1_idxs, y1_idxs, x2_idxs, y2_idxs):
#     if not (prev_bf.frame < near_bf.frame < far_bf.frame < next_bf.frame):
#         # フレーム範囲外はNG
#         return False
    
#     # 前後に分けて登録する

#     # 前半 ----------------
#     x1 = prev_bf.frame
#     x2 = near_bf.frame
#     x3 = far_bf.frame

#     y1 = get_smooth_bezier_y(prev_bf, prev_bf)
#     y2 = get_smooth_bezier_y(prev_bf, near_bf)
#     y3 = get_smooth_bezier_y(prev_bf, far_bf)

#     t = (x2 - x1) / (x3 - x1)
#     before_front_bz, before_back_bz = utils.calc_smooth_bezier(x1, y1, x2, y2, x3, y3, t)

#     # 後半 ----------------
#     x1 = near_bf.frame
#     x2 = far_bf.frame
#     x3 = next_bf.frame

#     y1 = get_smooth_bezier_y(near_bf, near_bf)
#     y2 = get_smooth_bezier_y(near_bf, far_bf)
#     y3 = get_smooth_bezier_y(near_bf, next_bf)

#     t = (x2 - x1) / (x3 - x1)
#     after_front_bz, after_back_bz = utils.calc_smooth_bezier(x1, y1, x2, y2, x3, y3, t)

#     # if not utils.is_fit_bezier_mmd([before_front_bz[2], before_back_bz[1], after_front_bz[2], after_back_bz[1]], 10) :
#     #     # 必要な補間曲線が範囲外ならばNG
#     #     return False

#     is_all_fit = False

#     if utils.is_fit_bezier_mmd([before_front_bz[2]], 10) == True:
#         # 範囲内に収める
#         utils.fit_bezier_split(before_front_bz[2])

#         # 前半-後半の終点前bfの後ろ側に設定する
#         prev_bf.complement[x2_idxs[0]] = prev_bf.complement[x2_idxs[1]] = \
#             prev_bf.complement[x2_idxs[2]] = prev_bf.complement[x2_idxs[3]] = before_front_bz[2].x()
#         prev_bf.complement[y2_idxs[0]] = prev_bf.complement[y2_idxs[1]] = \
#             prev_bf.complement[y2_idxs[2]] = prev_bf.complement[y2_idxs[3]] = before_front_bz[2].y()
#         prev_bf.key = True
    
#         if not prev_bf.frame in frames_by_bone:
#             frames_by_bone[prev_bf.frame] = prev_bf

#         frames_by_bone[prev_bf.frame] = prev_bf

#         is_all_fit = True
            
#     if utils.is_fit_bezier_mmd([before_back_bz[1]], 10) == True:
#         # 範囲内に収める
#         utils.fit_bezier_split(before_back_bz[1])

#         # 前半-後半の始点を、中間の前に設定する
#         # 始点を設定する
#         near_bf.complement[x1_idxs[0]] = near_bf.complement[x1_idxs[1]] = \
#             near_bf.complement[x1_idxs[2]] = near_bf.complement[x1_idxs[3]] = before_back_bz[1].x()
#         near_bf.complement[y1_idxs[0]] = near_bf.complement[y1_idxs[1]] = \
#             near_bf.complement[y1_idxs[2]] = near_bf.complement[y1_idxs[3]] = before_back_bz[1].y()
#         near_bf.key = True

#         if not near_bf.frame in frames_by_bone:
#             frames_by_bone[near_bf.frame] = near_bf

#         frames_by_bone[near_bf.frame].complement = near_bf.complement

#         is_all_fit = True

#     if utils.is_fit_bezier_mmd([after_front_bz[2]], 10) == True:
#         utils.fit_bezier_split(after_front_bz[2])

#         # 後半-前半の終点、中間の後に設定する（間の補間曲線はなくても繋がるはず）
#         near_bf.complement[x2_idxs[0]] = near_bf.complement[x2_idxs[1]] = \
#             near_bf.complement[x2_idxs[2]] = near_bf.complement[x2_idxs[3]] = after_front_bz[2].x()
#         near_bf.complement[y2_idxs[0]] = near_bf.complement[y2_idxs[1]] = \
#             near_bf.complement[y2_idxs[2]] = near_bf.complement[y2_idxs[3]] = after_front_bz[2].y()
#         near_bf.key = True

#         if not near_bf.frame in frames_by_bone:
#             frames_by_bone[near_bf.frame] = near_bf

#         frames_by_bone[near_bf.frame].complement = near_bf.complement

#         is_all_fit = True

#     if utils.is_fit_bezier_mmd([after_back_bz[1]], 10) == True:
#         utils.fit_bezier_split(after_back_bz[1])

#         # 後半-後半の始点を、後半の前に設定する
#         far_bf.complement[x1_idxs[0]] = far_bf.complement[x1_idxs[1]] = \
#             far_bf.complement[x1_idxs[2]] = far_bf.complement[x1_idxs[3]] = after_back_bz[1].x()
#         far_bf.complement[y1_idxs[0]] = far_bf.complement[y1_idxs[1]] = \
#             far_bf.complement[y1_idxs[2]] = far_bf.complement[y1_idxs[3]] = after_back_bz[1].y()
#         far_bf.key = True

#         if not far_bf.frame in frames_by_bone:
#             frames_by_bone[far_bf.frame] = far_bf

#         frames_by_bone[far_bf.frame].complement = far_bf.complement

#         is_all_fit = True

#     if utils.is_fit_bezier_mmd([after_back_bz[2]], 10) == True:
#         utils.fit_bezier_split(after_back_bz[2])

#         # 後半-後半の始点を、後半の前に設定する
#         far_bf.complement[x2_idxs[0]] = far_bf.complement[x2_idxs[1]] = \
#             far_bf.complement[x2_idxs[2]] = far_bf.complement[x2_idxs[3]] = after_back_bz[2].x()
#         far_bf.complement[y2_idxs[0]] = far_bf.complement[y2_idxs[1]] = \
#             far_bf.complement[y2_idxs[2]] = far_bf.complement[y2_idxs[3]] = after_back_bz[2].y()
#         far_bf.key = True

#         if not far_bf.frame in frames_by_bone:
#             frames_by_bone[far_bf.frame] = far_bf

#         frames_by_bone[far_bf.frame].complement = far_bf.complement

#         is_all_fit = True

#     return is_all_fit

                    # prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, start_frameno, is_only=True, is_exist=True)
                    # if not prev_bf: break

                    # next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
                    # if not next_bf: break

                    # now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, int((prev_bf.frame + next_bf.frame) / 2), is_only=False, is_exist=False)
                    # if not now_bf: break

                    # # 現在の補間曲線ではなく、なめらかに繋いだ場合の角度を設定する
                    # now_rot, rt = get_smooth_middle_rot(prev_bf, now_bf, next_bf)
                    # now_bf.rotation = now_rot
                    
                    # # 現在の補間曲線ではなく、なめらかに繋いだ場合の位置を設定する
                    # now_pos, mt = get_smooth_middle_pos(prev_bf, now_bf, next_bf)
                    # now_bf.position = now_pos

                    # while next_bf.frame <= last_frameno:
                    #     # とりあえずベジェ曲線で繋ぐ
                    #     smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, (cnt == 0))

                    #     prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, next_bf.frame, is_only=True, is_exist=True)
                    #     if not prev_bf: break

                    #     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
                    #     if not next_bf: break

                    #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, int((prev_bf.frame + next_bf.frame) / 2), is_only=False, is_exist=False)
                    #     if not now_bf: break

                    #     # 現在の補間曲線ではなく、なめらかに繋いだ場合の角度を設定する
                    #     now_rot, rt = get_smooth_middle_rot(prev_bf, now_bf, next_bf)
                    #     now_bf.rotation = now_rot
                        
                    #     # 現在の補間曲線ではなく、なめらかに繋いだ場合の位置を設定する
                    #     now_pos, mt = get_smooth_middle_pos(prev_bf, now_bf, next_bf)
                    #     now_bf.position = now_pos

    # # 座標比率
    # xr = 0 if n.x() == p.x() == 0 else math.cos(dot)
    # yr = 0 if n.y() == p.y() == 0 else math.tan(dot)
    # zr = 0 if n.z() == p.z() == 0 else math.sin(dot)

    # # 各角度の向き
    # x_sign = 1 if (n.x() >= p.x()) else -1
    # y_sign = 1 if (n.y() >= p.y()) else -1
    # z_sign = 1 if (n.z() >= p.z()) else -1


                    # prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, start_frameno, is_only=True, is_exist=True)
                    # if not prev_bf: break

                    # now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
                    # if not now_bf: break

                    # next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
                    # if not next_bf: break

                    # while next_bf.frame <= last_frameno:
                    #     # とりあえずベジェ曲線で繋ぐ
                    #     smooth_bf(model, frames_by_bone, bone_name, prev_bf, now_bf, next_bf, (cnt == 0))

                    #     prev_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, next_bf.frame, is_only=True, is_exist=True)
                    #     if not prev_bf: break

                    #     now_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, prev_bf.frame + 1, is_only=False, is_exist=True)
                    #     if not now_bf: break

                    #     next_bf = calc_bone_by_complement_by_bone(model, frames_by_bone, bone_name, now_bf.frame + 1, is_only=False, is_exist=True)
                    #     if not next_bf: break

    # # nとpの差で、基準点を求める
    # s = QVector3D.crossProduct(p.normalized(), n.normalized())
    
    # if p == QVector3D():
    #     p = QVector3D(1, 0, 0)

    # if n == QVector3D():
    #     n = QVector3D(1, 0, 0)

    # 基準点からの内積
    # xdot = QVector3D.dotProduct(QVector3D(1, 0, 0), mid.normalized())
    # ydot = QVector3D.dotProduct(QVector3D(0, 1, 0), mid.normalized())
    # zdot = QVector3D.dotProduct(QVector3D(0, 0, 1), mid.normalized())
    # dot = QVector3D.dotProduct(p.normalized(), n.normalized())

    # xt = t - (t * (math.pi / 2))
    # yt = math.pi/2 - t
    # zt = (t * (math.pi / 2))

    # xt = t #* math.pi / 2
    # yt = t / 2
    # zt = t
    # xt = (t - 0.5) #* math.pi / 2
    # yt = (t - 0.5) #* math.pi / 2
    # zt = (t - 0.5) #* math.pi / 2

    # # 極座標による媒介変数表示
    # xr = math.cos(dot) * math.cos(1 - dot)
    # yr = math.cos(dot) * math.sin(1 - dot)
    # zr = math.sin(dot)

    # 円周上の座標
    # out = prev_bf.position + ((next_bf.position - prev_bf.position) * t * QVector3D(xr, yr, zr))
    # t2 = 1 if t <= 0.5 else 1 - t
    # out = p + ((mid + (radius * QVector3D(xr, yr, zr))) * QVector3D(x_sign, y_sign, z_sign))

    # # 値の変化がない場合、上書き
    # if p.x() == n.x():
    #     out.setX(n.x())
    # if p.y() == n.y():
    #     out.setY(n.y())
    # if p.z() == n.z():
    #     out.setZ(n.z())

    # # 値の変化がない場合、上書き
    # if p.x() == n.x():
    #     out.setX(n.x())
    # if p.y() == n.y():
    #     out.setY(n.y())
    # if p.z() == n.z():
    #     out.setZ(n.z())

    # # if n == QVector3D():
    # #     n = QVector3D(1, 0, 0)

    # # # 中点からtoの内積
    # # dot = QVector3D.dotProduct(d.normalized(), mid.normalized())

    # # xt = (1 - t)
    # # yt = (1 - t)
    # # zt = (1 - t)

    # # xr = math.sin((1 - t) * math.pi / 2) if (n.x() >= p.x()) else math.sin((1 - t) - math.pi/2)
    # # yr = math.tan((1 - t) * math.pi / 4) if (n.y() >= p.y()) else math.tan(-(1 - t) * math.pi / 4)
    # # zr = math.cos((1 - t) * math.pi / 2) if (n.z() >= p.z()) else math.cos((1 - t) + math.pi/2)

    # # t1 = t #* math.pi / 2
    # # t2 = (1 - t) #* math.pi / 2
    # xr = math.cos(t) if (n.x() >= p.x()) else math.cos(1 - t) #math.acos(t)       if (n.x() >= p.x()) else 1 - math.acos(-t)
    # yr = t #math.atan(1 - t)   if (n.y() >= p.y()) else math.atan(-t)
    # zr = t # math.sin(t) if (n.z() >= p.z()) else math.sin(1 - t) #math.asin(t)       if (n.z() >= p.z()) else math.asin(-t)

    # # xr = math.sin((1 - t) * math.pi / 2)  if (n.x() >= p.x()) else math.cos((1 - t) * math.pi / 2)
    # # yr = math.tan((1 - t) * math.pi / 4)  if (n.y() >= p.y()) else math.tan((1 - t) * math.pi / 4)
    # # zr = math.cos((1 - t) * math.pi / 2)  if (n.z() >= p.z()) else math.sin((1 - t) * math.pi / 2)

    # xr = math.cos((math.pi - (t - 0.5)) * xs) #if t > 0.5 else math.cos(t) #* xs * zs #if (n.x() >= p.x()) else -math.sin(t) #math.acos(t)       if (n.x() >= p.x()) else 1 - math.acos(-t)
    # yr = math.atan2(math.cos(t), math.sin(t)) if ys else math.atan2(math.cos(1 - t), math.sin(1 - t)) #if t > 0.5 else math.tan(t) #* ys * xs #if (n.y() >= p.y()) else -math.tan(1 - t) #math.atan(1 - t)   if (n.y() >= p.y()) else math.atan(-t)
    # zr = math.sin((math.pi * t) * zs) #if t > 0.5 else math.sin(t) #* zs * ys #if (n.z() >= p.z()) else -math.cos(t) # math.sin(t) if (n.z() >= p.z()) else math.sin(1 - t) #math.asin(t)       if (n.z() >= p.z()) else math.asin(-t)

    # xr = math.cos(0.5 - t) / 2 #if t > 0.5 else math.cos(t) #* xs * zs #if (n.x() >= p.x()) else -math.sin(t) #math.acos(t)       if (n.x() >= p.x()) else 1 - math.acos(-t)
    # yr = math.atan2(math.cos(t), math.sin(t)) / 2 #if t > 0.5 else math.tan(t) #* ys * xs #if (n.y() >= p.y()) else -math.tan(1 - t) #math.atan(1 - t)   if (n.y() >= p.y()) else math.atan(-t)
    # zr = math.sin(0.5 + t) / 2 #if t > 0.5 else math.sin(t) #* zs * ys #if (n.z() >= p.z()) else -math.cos(t) # math.sin(t) if (n.z() >= p.z()) else math.sin(1 - t) #math.asin(t)       if (n.z() >= p.z()) else math.asin(-t)

    # 増減
    # # if t <= 0.5:
    # xm = xr if (n.x() >= p.x()) else (xr - 1) #if (n.x() > p.x()) else -(1 - t) if (n.x() < p.x()) else 0
    # ym = yr if (n.y() >= p.y()) else (yr - 1) #if (n.y() > p.y()) else -(1 - t) if (n.y() < p.y()) else 0
    # zm = zr if (n.z() >= p.z()) else (zr - 1) #if (n.z() > p.z()) else -(1 - t) if (n.z() < p.z()) else 0
    # else:
    #     xm = (1 - t) if (n.x() >= p.x()) else (t - 1) #if (n.x() > p.x()) else -(1 - t) if (n.x() < p.x()) else 0
    #     ym = (1 - t) if (n.y() >= p.y()) else (t - 1) #if (n.y() > p.y()) else -(1 - t) if (n.y() < p.y()) else 0
    #     zm = (1 - t) if (n.z() >= p.z()) else (t - 1) #if (n.z() > p.z()) else -(1 - t) if (n.z() < p.z()) else 0

    # mid = QVector3D()
    # mid2 = QVector3D()
    # t3 = 0.5 - t if t <= 0.5 else t - 0.5

    # if n.x() >= p.x():
    #     mid.setX( (n.x() - p.x()) * t3 )
    #     mid2.setX( (n.x() - p.x()) * t )
    # else:
    #     mid.setX( (n.x() - p.x()) * t3 )
    #     mid2.setX( (n.x() - p.x()) * t )

    # if n.y() >= p.y():
    #     mid.setY( (n.y() - p.y()) * t3 )
    #     mid2.setY( (n.y() - p.y()) * t )
    # else:
    #     mid.setY( (n.y() - p.y()) * t3 )
    #     mid2.setY( (n.y() - p.y()) * t )

    # if n.z() >= p.z():
    #     mid.setZ( (n.z() - p.z()) * t3 )
    #     mid2.setZ( (n.z() - p.z()) * t )
    # else:
    #     mid.setZ( (n.z() - p.z()) * t3 )
    #     mid2.setZ( (n.z() - p.z()) * t )

    # # 中点を原点とみなした半径
    # radius = math.sqrt(((mid2.x())**2) + ((mid2.y())**2) + ((mid2.z())**2))

    # xr = math.cos(t*math.pi/2)       if t <= 0.5 else math.cos(t)   #if n.z() >= p.z() else math.cos(t - t2) #if t > 0.5 else math.sin(t) #* zs * ys #if (n.z() >= p.z()) else -math.cos(t) # math.sin(t) if (n.z() >= p.z()) else math.sin(1 - t) #math.asin(t)       if (n.z() >= p.z()) else math.asin(-t)
    # yr = math.tan((1 - t)*math.pi/4) if t <= 0.5 else math.tan(t)    #if n.y() >= p.y() else math.tan(t)  #if t > 0.5 else math.tan(t) #* ys * xs #if (n.y() >= p.y()) else -math.tan(1 - t) #math.atan(1 - t)   if (n.y() >= p.y()) else math.atan(-t)
    # zr = math.sin(t - math.pi)       if t <= 0.5 else math.sin(t)         #if n.x() >= p.x() else math.sin(t) #if t > 0.5 else math.cos(t) #* xs * zs #if (n.x() >= p.x()) else -math.sin(t) #math.acos(t)       if (n.x() >= p.x()) else 1 - math.acos(-t)

    # xr = math.sin(math.pi/2 - (1 - t)) #      if t <= 0.5 else math.cos(t)   #if n.z() >= p.z() else math.cos(t - t2) #if t > 0.5 else math.sin(t) #* zs * ys #if (n.z() >= p.z()) else -math.cos(t) # math.sin(t) if (n.z() >= p.z()) else math.sin(1 - t) #math.asin(t)       if (n.z() >= p.z()) else math.asin(-t)
    # yr = math.tan(math.pi/4 - (1 - t)) #if t <= 0.5 else math.tan(t)    #if n.y() >= p.y() else math.tan(t)  #if t > 0.5 else math.tan(t) #* ys * xs #if (n.y() >= p.y()) else -math.tan(1 - t) #math.atan(1 - t)   if (n.y() >= p.y()) else math.atan(-t)
    # zr = math.cos(math.pi/2 - (1 - t)) #      if t <= 0.5 else math.sin(t)         #if n.x() >= p.x() else math.sin(t) #if t > 0.5 else math.cos(t) #* xs * zs #if (n.x() >= p.x()) else -math.sin(t) #math.acos(t)       if (n.x() >= p.x()) else 1 - math.acos(-t)
    # xr = math.cos(t*math.pi/2)  #if n.x() >= p.x() else math.sin(t/math.pi/2)
    # yr = math.tan(1 - t)        #if n.y() >= p.y() else math.tan(t)
    # zr = math.sin(t/math.pi/2)  #if n.z() >= p.z() else math.cos(t*math.pi/2)

    # out = (n - p) * t * (n - p).normalized() * QVector3D(xr, yr, zr)

    # xm = xr if (n.x() >= p.x()) else xr - 1  #if xs == zs else zr*xs #if xs != ys else zr*xs
    # ym = yr if (n.y() >= p.y()) else yr - 1 #if xs == ys else xr*ys #if ys != zs else xr*ys
    # zm = zr if (n.z() >= p.z()) else zr - 1 #if ys == zs else yr*zs #if zs != xs else yr*zs

    # 実際の変化量
    # out = mid2 * (radius * QVector3D(xm, ym, zm))
    # if t <= 0.5:
    # else:
    #     out = p + (mid2 + QVector3D(xm, ym, zm))

    # # # 3点を通る円の中心座標x, y, 半径
    # # xys, xyh, xyk, xyr = utils.calc_circle(p.x(), p.y(), mid.x(), mid.y(), n.x(), n.y())
    # # xzs, xzh, xzk, xzr = utils.calc_circle(p.x(), p.z(), mid.x(), mid.z(), n.x(), n.z())
    # # yzs, yzh, yzk, yzr = utils.calc_circle(p.y(), p.z(), mid.y(), mid.z(), n.y(), n.z())



    # # xr = math.cos(t)
    # # yr = math.tan(1 - t)
    # # zr = math.sin(t)
    # # asinr = math.asin(1 - t)  #if n.z() >= p.z() else math.cos(t*math.pi/2)
    # # acosr = math.acos(1 - t)  #if n.x() >= p.x() else math.sin(t/math.pi/2)
    # # atanr = math.atan2(math.cos(t), math.sin(t))        #if n.y() >= p.y() else math.tan(t)

    # # msinr = math.sin(t * math.pi)  #if n.z() >= p.z() else math.cos(t*math.pi/2)
    # # mcosr = math.cos(t - 0.5)  #if n.x() >= p.x() else math.sin(t/math.pi/2)
    # # mtanr = math.tan(t * math.pi / 2)       #if n.y() >= p.y() else math.tan(t)

    # # 0～1
    # msinr = math.sin(math.pi/2-t*math.pi/2)
    # mcosr = math.cos(math.pi/2-t*math.pi/2)
    # mtanr = math.tan(math.pi/4-t*math.pi/4)

    # pxt = mcosr*xs # *  #if xs == ys == zs else zr*zs * yr
    # pyt = mtanr*ys # *  #if xs == ys == zs else yr*ys * xr
    # pzt = msinr*zs # *  #if xs == ys == zs else xr*xs * zr

    # mxt = (1 - msinr)*xs # *  #if xs == ys == zs else zr*zs * yr
    # myt = (1 - mtanr)*ys # *  #if xs == ys == zs else yr*ys * xr
    # mzt = (1 - mcosr)*zs # *  #if xs == ys == zs else xr*xs * zr

    # # mxt = mcosr*ys
    # # myt = mtanr*zs
    # # mzt = msinr*xs

    # # m1 = (n - p) * (1 - t) * QVector3D(xt, yt, zt)
    # # m2 = (n - p) * (1 - t) * QVector3D(xt, yt, zt)
    # #m2 = ((n - p) * t).length() * QVector3D(1, 1, 1) #* QVector3D(xt, yt, zt)
    # #m2 = (n - p) * t #* QVector3D(mxt, myt, mzt)

    # m1 = (n - p) * t
    # m2 = ((n - p).length() / 2) * t * QVector3D(pxt, pyt, pzt)

    # out = p + m1 + m2

    # # 値の変化がない場合、上書き
    # if p.x() == n.x():
    #     out.setX(n.x())
    # if p.y() == n.y():
    #     out.setY(n.y())
    # if p.z() == n.z():
    #     out.setZ(n.z())


    # # 符号
    # xs = 1 if (n.x() > p.x()) else -1 if (n.x() < p.x()) else 0
    # ys = 1 if (n.y() > p.y()) else -1 if (n.y() < p.y()) else 0
    # zs = 1 if (n.z() > p.z()) else -1 if (n.z() < p.z()) else 0



# # 始点からの変化量
# dot = QQuaternion.dotProduct(t_qq, cp_qq)

# theta = t * math.pi
# phi = t * math.pi * 2

# x = p.x() + radius*math.sin(theta)*math.cos(phi)
# y = p.y() + radius*math.sin(theta)*math.sin(phi)
# z = p.z() + radius*math.cos(theta)

# r2 = (w - p).length() / 2
# mat = QMatrix4x4()
# # 開始地点分移動する
# mat.translate(p - c)
# # t分回す
# mat.rotate(t_qq)
# # 原点分の移動量を戻して、pの移動を求める
# out = mat * (w + c)

# # 極座標の係数
# theta = math.pi/2 - t_rad
# phi = theta * 2

# # prev -> now の半径
# x = c.x() + radius * math.sin(theta) * math.cos(phi)
# y = c.y() + radius * math.sin(theta) * math.sin(phi)
# z = c.z() + radius * math.cos(theta)

# mat = QMatrix4x4()
# mat.translate(c)
# mat.rotate(QQuaternion.fromEulerAngles(0, t_qq.toEulerAngles().y(),0))
# mat.translate(QVector3D(0, radius, 0))
# mat.rotate(QQuaternion.fromEulerAngles(0, 0, t_qq.toEulerAngles().z()))
# mat.translate(QVector3D(0, 0, radius))
# mat.rotate(QQuaternion.fromEulerAngles(t_qq.toEulerAngles().x(), 0, 0))
# mat.translate(QVector3D(radius, 0, 0))
# out = mat * (p - c)


# mat = QMatrix4x4()
# mat.translate(p - c)
# mat.rotate(t_qq)
# out = mat * (p + c)

    # # 回転角度
    # t_rad = 2 * math.acos(t_qq.scalar())
    
    # mcp = (p - c)

    # x = mcp.x() * math.cos(t_rad) - mcp.y()
    # # prev -> now の半径
    # x = c.x() + radius * math.cos(t_rad)
    # y = c.y() + radius * math.atan2(math.cos(t_rad), math.sin(t_rad))
    # z = c.z() + radius * math.sin(t_rad)


    # # x = math.sin(t_rad)
    # # z = math.cos(math.pi - t_rad)
    # # y = math.atan2(z, x)

    # x = math.sin(t_rad)
    # z = math.cos(t_rad)
    # y = math.atan2(z, x)

    # out = (c + p) + radius * QVector3D(x, y, z)

# # 変化量
# t = (target_bf.frame - prev_bf.frame) / ( next_bf.frame - prev_bf.frame)

# # prev -> now の t分の回転量
# cp_qq = QQuaternion.rotationTo((p - c), (c - c))
# pn_qq = QQuaternion.rotationTo((p - c), (n - c))
# # 球形補間の移動量
# t_qq = QQuaternion.slerp(cp_qq, pn_qq, t)

# # 回転角度
# t_deg = math.degrees(2 * math.acos(t_qq.scalar()))

# t2_qq = QQuaternion.fromAxisAndAngle(c, t_deg)

# mat = QMatrix4x4()
# mat.translate(p - c)
# mat.rotate(t_qq)
# mat.translate(c)
# out = mat * c

# # 変化量
# t = (target_bf.frame - prev_bf.frame) / ( now_bf.frame - prev_bf.frame)

# # prev -> now の t分の回転量
# pc_qq = QQuaternion.rotationTo((p - c), (c - c))
# pw_qq = QQuaternion.rotationTo((p - c), (w - c))
# # 球形補間の移動量
# t_qq = QQuaternion.slerp(pc_qq, pw_qq, t)

# # 回転角度
# t_deg = math.degrees(2 * math.acos(t_qq.scalar()))

# p2 = p if p != QVector3D() else QVector3D(-1, 0, 0) if n.x() - p.x() >= 0 else QVector3D(1, 0, 0)
# w2 = w if w != QVector3D() else QVector3D(-1, 0, 0) if n.x() - p.x() >= 0 else QVector3D(1, 0, 0)
# pw_cross = QVector3D.crossProduct(p2, w2).normalized()

# mat = QMatrix4x4()
# mat.translate(p - c)
# mat.rotate(t_deg, pw_cross)
# mat.translate(c)
# out = mat * (w - p)



# x_qq = QQuaternion.fromEulerAngles(0, 0, -90)
# tx_qq = t_qq.inverted() * x_qq

# z_qq = QQuaternion.fromEulerAngles(-90, 0, 0)
# tz_qq = t_qq.inverted() * z_qq

# theta = 2 * math.acos(tx_qq.scalar())
# phi = 2 * math.acos(tz_qq.scalar())

# # prev -> now の半径
# x = c.x() + radius * math.sin(theta) * math.cos(phi)
# y = c.y() + radius * math.cos(theta)
# z = c.z() + radius * math.sin(theta) * math.sin(phi)

# p2 = p if p != QVector3D() else QVector3D(-1, 0, 0) if n.x() - p.x() >= 0 else QVector3D(1, 0, 0)
# w2 = w if w != QVector3D() else QVector3D(-1, 0, 0) if n.x() - p.x() >= 0 else QVector3D(1, 0, 0)
# pw_cross = QVector3D.crossProduct(p2, w2).normalized()

    # x = math.sin(t_rad)
    # z = math.cos(math.pi - t_rad)
    # y = math.atan2(z, x)

    # x = math.sin((1 - t_rad) * math.pi / 2)
    # y = math.tan((1 - t_rad) * math.pi / 4)
    # z = math.cos((1 - t_rad) * math.pi / 2)

    # # p2 = QVector3D(1, 0, 0) if p == QVector3D() else p
    # # w2 = QVector3D(1, 0, 0) if n == QVector3D() else n

    # # 回転角度
    # t_rad = math.acos(t_qq.scalar()) * 2

    # x = math.cos(t_rad)
    # z = math.sin(t_rad)
    # y = math.tan(t_rad)

    # out = c + radius * QVector3D(x, y, z)

# t_euler = t_qq.toEulerAngles()

# xr = math.radians(t_euler.x())
# yr = math.radians(t_euler.y())
# zr = math.radians(t_euler.z())

# # http://www.kodama-lab.com/seminar/clang/23th/ex155.html
# # http://www.f.waseda.jp/moriya/PUBLIC_HTML/education/classes/infomath6/applet/fractal/coord/
# x1 = (p + c).x()
# y1 = (p + c).y()
# z1 = (p + c).z()

# x2 = math.cos(zr) * x1 + math.sin(zr) * y1
# y2 = -math.sin(zr) * x1 + math.cos(zr) * y1
# z2 = z1

# x3 = x2
# y3 = math.cos(xr) * y2 + math.sin(xr) * z2
# z3 = -math.sin(xr) * y2 + math.cos(xr) * z2

# x4 = math.cos(yr) * x3 + -math.sin(yr) * z3
# y4 = y3
# z4 = math.sin(yr) * x3 + math.cos(yr) * z3

# out = QVector3D(x4, y4, z4)

# # 回転角度
# t_rad = math.acos(t_qq.scalar()) * 2

# x_sign = 1 if wpn.x() >= 0 else -1
# y_sign = 1 if wpn.y() >= 0 else -1
# z_sign = 1 if wpn.z() >= 0 else -1

# x = math.cos(t_rad * x_sign)
# z = math.sin(t_rad * z_sign)
# y = math.tan(t_rad * y_sign)

# out = c + radius * QVector3D(x, y, z)

if __name__=="__main__":
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--vmd_path', dest='vmd_path', help='input vmd', type=str)
    parser.add_argument('--pmx_path', dest='pmx_path', help='input pmx', type=str)
    parser.add_argument('--pos_repeat', dest='pos_repeat', help='pos_repeat', type=int)
    parser.add_argument('--rot_repeat', dest='rot_repeat', help='rot_repeat', type=int)

    args = parser.parse_args()

    if wrapperutils.is_valid_file(args.vmd_path, "VMDファイル", ".vmd", True) == False:
        sys.exit(-1)

    if wrapperutils.is_valid_file(args.pmx_path, "PMXファイル", ".pmx", True) == False:
        sys.exit(-1)

    main(args.vmd_path, args.pmx_path, args.pos_repeat, args.rot_repeat)