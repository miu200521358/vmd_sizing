# -*- coding: utf-8 -*-
#
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MLogger import MLogger # noqa
import numpy as np
import bezier

logger = MLogger(__name__, level=1)

# MMDでの補間曲線の最大値
INTERPOLATION_MMD_MAX = 127

# 回転補間曲線のインデックス
R_x1_idxs = [3, 18, 33, 48]
R_y1_idxs = [7, 22, 37, 52]
R_x2_idxs = [11, 26, 41, 56]
R_y2_idxs = [15, 30, 45, 60]

# X移動補間曲線のインデックス
MX_x1_idxs = [0, 0, 0, 0]
MX_y1_idxs = [19, 34, 49, 4]
MX_x2_idxs = [23, 38, 53, 8]
MX_y2_idxs = [27, 42, 57, 12]

# Y移動補間曲線のインデックス
MY_x1_idxs = [1, 16, 16, 16]
MY_y1_idxs = [5, 35, 50, 20]
MY_x2_idxs = [9, 39, 54, 24]
MY_y2_idxs = [13, 43, 58, 28]

# Z移動補間曲線のインデックス
MZ_x1_idxs = [2, 17, 32, 32]
MZ_y1_idxs = [6, 21, 51, 36]
MZ_x2_idxs = [10, 25, 55, 40]
MZ_y2_idxs = [14, 29, 59, 44]


# 補間曲線を求める
# http://d.hatena.ne.jp/edvakf/20111016/1318716097
# https://pomax.github.io/bezierinfo
# https://shspage.hatenadiary.org/entry/20140625/1403702735
# https://bezier.readthedocs.io/en/stable/python/reference/bezier.curve.html#bezier.curve.Curve.evaluate
def evaluate(x1v: int, y1v: int, x2v: int, y2v: int, start: int, now: int, end: int):
    if (now - start) == 0 or (end - start) == 0:
        return 0, 0, 0
        
    x = (now - start) / (end - start)
    x1 = x1v / INTERPOLATION_MMD_MAX
    x2 = x2v / INTERPOLATION_MMD_MAX
    y1 = y1v / INTERPOLATION_MMD_MAX
    y2 = y2v / INTERPOLATION_MMD_MAX

    # 補間曲線ベジェ曲線
    curve1 = bezier.Curve(np.asfortranarray([[0, x1, x2, 1], [0, y1, y2, 1]]), degree=3)
    # 交点を求める為のX線上の直線
    curve2 = bezier.Curve(np.asfortranarray([[x, x], [0, 1]]), degree=1)

    # 交点を求める
    intersections = curve1.intersect(curve2)

    # tからyを求め直す
    s_vals = np.asfortranarray(intersections[0, :])
    es = curve1.evaluate_multi(s_vals)

    # >>> curve1.evaluate_multi(s_vals)
    # array([[0.25 , 0.75 ],
    #        [0.375, 0.375]])
    # x: x          横軸
    # y: es[1, 0]   縦軸
    # t: s_vals[0]  実際の変化量
    return x, es[1, 0], s_vals[0]




























# 回転による補間曲線の再設定
def reset_interpolation_by_rot(motion, bone_name, prev_bf, now_bf, next_bf):
    x1_idxs = R_x1_idxs
    y1_idxs = R_y1_idxs
    x2_idxs = R_x2_idxs
    y2_idxs = R_y2_idxs
    next_x1v = now_bf.complement[x1_idxs[3]]
    next_y1v = now_bf.complement[y1_idxs[3]]
    next_x2v = now_bf.complement[x2_idxs[3]]
    next_y2v = now_bf.complement[y2_idxs[3]]

    reset_interpolation(motion, bone_name, prev_bf, now_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)


def reset_interpolation(motion, bone_name, prev_bf, now_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs):
    # 区切りキー位置
    before_fill_bf = after_fill_bf = None
    
    # ベジェ曲線を分割して新しい制御点を求める
    t, x, y, bresult, aresult, before_bz, after_bz = calc_bezier_split(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, now_bf.frame, next_bf.frame)

    # 分割（今回キー）の始点は、前半のB
    now_bf.complement[x1_idxs[0]] = now_bf.complement[x1_idxs[1]] = now_bf.complement[x1_idxs[2]] = now_bf.complement[x1_idxs[3]] = int(before_bz[1].x())
    now_bf.complement[y1_idxs[0]] = now_bf.complement[y1_idxs[1]] = now_bf.complement[y1_idxs[2]] = now_bf.complement[y1_idxs[3]] = int(before_bz[1].y())

    # 分割（今回キー）の終点は、後半のC
    now_bf.complement[x2_idxs[0]] = now_bf.complement[x2_idxs[1]] = now_bf.complement[x2_idxs[2]] = now_bf.complement[x2_idxs[3]] = int(before_bz[2].x())
    now_bf.complement[y2_idxs[0]] = now_bf.complement[y2_idxs[1]] = now_bf.complement[y2_idxs[2]] = now_bf.complement[y2_idxs[3]] = int(before_bz[2].y())

    # 次回読み込みキーの始点は、後半のB
    next_bf.complement[x1_idxs[0]] = next_bf.complement[x1_idxs[1]] = next_bf.complement[x1_idxs[2]] = next_bf.complement[x1_idxs[3]] = int(after_bz[1].x())
    next_bf.complement[y1_idxs[0]] = next_bf.complement[y1_idxs[1]] = next_bf.complement[y1_idxs[2]] = next_bf.complement[y1_idxs[3]] = int(after_bz[1].y())

    # 次回読み込みキーの終点は、後半のC
    next_bf.complement[x2_idxs[0]] = next_bf.complement[x2_idxs[1]] = next_bf.complement[x2_idxs[2]] = next_bf.complement[x2_idxs[3]] = int(after_bz[2].x())
    next_bf.complement[y2_idxs[0]] = next_bf.complement[y2_idxs[1]] = next_bf.complement[y2_idxs[2]] = next_bf.complement[y2_idxs[3]] = int(after_bz[2].y())

    if bresult and aresult:
        # logger.test("%s, 【分割成功】: , %s,prev: %s, now: %s, next: %s", indent, link_name, prev_bf.frame, now_bf.frame, next_bf.frame)
        return
    else:
        # 分割に失敗している場合、さらに分割する

        if not bresult:
            # logger.test("%s, 【分割前半失敗開始】: ,%s, prev: %s, now: %s, next: %s", indent, link_name, prev_bf.frame, now_bf.frame, next_bf.frame)

            # 前半用補間曲線
            next_x1v = now_bf.complement[x1_idxs[3]]
            next_y1v = now_bf.complement[y1_idxs[3]]
            next_x2v = now_bf.complement[x2_idxs[3]]
            next_y2v = now_bf.complement[y2_idxs[3]]

            # 前半を区切る位置を求める(t=0.5で曲線を半分に分割する位置)
            new_fill_fno, _, _ = calc_interpolate_bezier_by_t(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.frame, now_bf.frame, 0.5)
            # logger.test("%s, 【前半】, now: %s", indent, now)

            if new_fill_fno > prev_bf.frame:
                # ちゃんとキーが打てるような状態の場合、前半を再分割
                before_fill_bf = motion.calc_bone_by_interpolation(bone_name, new_fill_fno, is_only=False, is_exist=False)

            if before_fill_bf:
                # 分割キーが取得できた場合、前半の補間曲線を分割して求めなおす
                reset_interpolation(motion, bone_name, prev_bf, before_fill_bf, now_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)
            else:
                # 分割キーが取得できなかった場合、既にキーがあるので、さらに分割する

                # 分割キーが取得できなかった場合、念のため補間曲線を0-127の間に収め直す
                # 分割（今回キー）の始点は、前半のB
                r_x1 = 0 if 0 > before_bz[1].x() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < before_bz[1].x() else int(before_bz[1].x())
                now_bf.complement[x1_idxs[0]] = now_bf.complement[x1_idxs[1]] = now_bf.complement[x1_idxs[2]] = now_bf.complement[x1_idxs[3]] = r_x1
                r_y1 = 0 if 0 > before_bz[1].y() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < before_bz[1].y() else int(before_bz[1].y())
                now_bf.complement[y1_idxs[0]] = now_bf.complement[y1_idxs[1]] = now_bf.complement[y1_idxs[2]] = now_bf.complement[y1_idxs[3]] = r_y1

                # 分割（今回キー）の終点は、後半のC
                r_x2 = now_bf.complement[x2_idxs[3]] = 0 if 0 > before_bz[2].x() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < before_bz[2].x() else int(before_bz[2].x())
                now_bf.complement[x2_idxs[0]] = now_bf.complement[x2_idxs[1]] = now_bf.complement[x2_idxs[2]] = now_bf.complement[x2_idxs[3]] = r_x2
                r_y2 = 0 if 0 > before_bz[2].y() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < before_bz[2].y() else int(before_bz[2].y())
                now_bf.complement[y2_idxs[0]] = now_bf.complement[y2_idxs[1]] = now_bf.complement[y2_idxs[2]] = now_bf.complement[y2_idxs[3]] = r_y2

                # logger.test("%s,前半分割キー取得失敗,R_x1_idxs,%s,R_y1_idxs,%s,R_x2_idxs,%s,R_y2_idxs,%s,before_bz,%s", indent, now_bf.complement[x1_idxs[3]], now_bf.complement[y1_idxs[3]], now_bf.complement[x2_idxs[3]], now_bf.complement[x2_idxs[3]],before_bz)

        if not aresult:
            # logger.test("%s, 【分割後半失敗開始】: ,%s, prev: %s, now: %s, next: %s", indent, link_name, prev_bf.frame, now_bf.frame, next_bf.frame)

            # 後半用補間曲線
            next_x1v = next_bf.complement[x1_idxs[3]]
            next_y1v = next_bf.complement[y1_idxs[3]]
            next_x2v = next_bf.complement[x2_idxs[3]]
            next_y2v = next_bf.complement[y2_idxs[3]]

            # 後半を区切る位置を求める
            new_fill_fno, _, _ = calc_interpolate_bezier_by_t(next_x1v, next_y1v, next_x2v, next_y2v, now_bf.frame, next_bf.frame, 0.5)
            # logger.test("%s, 【後半】, now: %s", indent, now)

            if new_fill_fno > now_bf.frame:
                # ちゃんとキーが打てるような状態の場合、後半を再分割
                after_fill_bf = motion.calc_bone_by_interpolation(bone_name, new_fill_fno, is_only=False, is_exist=False)

            if after_fill_bf:
                # 分割キーが取得できた場合、後半の補間曲線を分割して求めなおす
                reset_interpolation(motion, bone_name, now_bf, after_fill_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)
            else:
                # 分割キーが取得できなかった場合、念のため補間曲線を0-127の間に収め直す

                # 次回読み込みキーの始点は、後半のB
                r_x1 = 0 if 0 > after_bz[1].x() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < after_bz[1].x() else int(after_bz[1].x())
                next_bf.complement[x1_idxs[0]] = next_bf.complement[x1_idxs[1]] = next_bf.complement[x1_idxs[2]] = next_bf.complement[x1_idxs[3]] = r_x1
                r_y1 = 0 if 0 > after_bz[1].y() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < after_bz[1].y() else int(after_bz[1].y())
                next_bf.complement[y1_idxs[0]] = next_bf.complement[y1_idxs[1]] = next_bf.complement[y1_idxs[2]] = next_bf.complement[y1_idxs[3]] = r_y1

                # 次回読み込みキーの終点は、後半のC
                r_x2 = 0 if 0 > after_bz[2].x() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < after_bz[2].x() else int(after_bz[2].x())
                next_bf.complement[x2_idxs[0]] = next_bf.complement[x2_idxs[1]] = next_bf.complement[x2_idxs[2]] = next_bf.complement[x2_idxs[3]] = r_x2
                r_y2 = 0 if 0 > after_bz[2].y() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < after_bz[2].y() else int(after_bz[2].y())
                next_bf.complement[y2_idxs[0]] = next_bf.complement[y2_idxs[1]] = next_bf.complement[y2_idxs[2]] = next_bf.complement[y2_idxs[3]] = r_y2

                # logger.test("%s,後半分割キー取得失敗,R_x1_idxs,%s,R_y1_idxs,%s,R_x2_idxs,%s,R_y2_idxs,%s,after_bz,%s", indent, next_bf.complement[x1_idxs[3]], next_bf.complement[y1_idxs[3]], next_bf.complement[x2_idxs[3]], next_bf.complement[x2_idxs[3]],after_bz)

        # logger.test("%s, 【分割失敗終了】: ,%s, prev: %s, now: %s, next: %s", indent, link_name, prev_bf.frame, now_bf.frame, next_bf.frame)
        return

    # logger.test("%s, 【分割終了】: ,%s, prev: %s, now: %s, next: %s, next_x1v: %s, next_y1v: %s, next_x2v: %s, next_y2v: %s", indent, link_name, prev_bf.frame, now_bf.frame, next_bf.frame, next_x1v, next_y1v, next_x2v, next_y2v)
    return


# 3次ベジェ曲線の分割
# http://geom.web.fc2.com/geometry/bezier/cut-cb.html
def calc_bezier_split(x1v, y1v, x2v, y2v, start, end, now):
    if (now - start) == 0 or (end - start) == 0:
        return 0, 0, 0, False, False, [MVector2D(), MVector2D(), MVector2D(), MVector2D()], [MVector2D(), MVector2D(), MVector2D(), MVector2D()]

    # 3次ベジェ曲線を分割する
    t, x, y, beforebz, afterbz = calc_bezier_split_offset(x1v, y1v, x2v, y2v, start, end, now)

    # ベジェ曲線の値がMMD用に合っているかを加味して返す
    return t, x, y, is_fit_bezier_mmd(beforebz), is_fit_bezier_mmd(afterbz), beforebz, afterbz


# ベジェ曲線の値がMMD用に合っているか
def is_fit_bezier_mmd(bz, offset=0):
    for b in bz:
        # # 1割以下は誤差として吸収してしまう
        # b.setX( 0 if INTERPOLATION_MMD_MAX-1 <= b.x() < 0 else b.x() )
        # b.setY( INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < b.x() <= INTERPOLATION_MMD_MAX+1 else b.y() )

        if not (0 - offset <= b.x() <= INTERPOLATION_MMD_MAX + offset) or not (0 - offset <= b.y() <= INTERPOLATION_MMD_MAX + offset):
            # MMD用の範囲内でなければNG
            return False

    return True


def fit_bezier_mmd(b):
    if not (0 <= b.x() <= INTERPOLATION_MMD_MAX) or not (0 <= b.y() <= INTERPOLATION_MMD_MAX):
        x = 0 if 0 > b.x() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < b.x() else int(b.x())
        y = 0 if 0 > b.y() else INTERPOLATION_MMD_MAX if INTERPOLATION_MMD_MAX < b.y() else int(b.y())

        return int(x), int(y)

    return int(b.x()), int(b.y())


# オフセット込みの3次ベジェ曲線の分割
def calc_bezier_split_offset(x1v, y1v, x2v, y2v, start, end, now):
    # 補間曲線の進んだ時間分を求める
    t, x, y = calc_interpolate_bezier(x1v, y1v, x2v, y2v, start, end, now)

    A = MVector2D(0.0, 0.0)
    B = MVector2D(x1v / INTERPOLATION_MMD_MAX, y1v / INTERPOLATION_MMD_MAX)
    C = MVector2D(x2v / INTERPOLATION_MMD_MAX, y2v / INTERPOLATION_MMD_MAX)
    D = MVector2D(1.0, 1.0)

    E = (1 - t) * A + t * B
    F = (1 - t) * B + t * C
    G = (1 - t) * C + t * D
    H = (1 - t) * E + t * F
    I = (1 - t) * F + t * G # noqa
    J = (1 - t) * H + t * I

    # 新たな4つのベジェ曲線の制御点は、A側がAEHJ、C側がJIGDとなる。

    # スケーリング
    bA, bE, bH, bJ = scale_bezier(A, E, H, J)
    aJ, aI, aG, aD = scale_bezier(J, I, G, D)

    bA2 = round_bezier_mmd(bA)
    bE2 = round_bezier_mmd(bE)
    bH2 = round_bezier_mmd(bH)
    bJ2 = round_bezier_mmd(bJ)
    aJ2 = round_bezier_mmd(aJ)
    aI2 = round_bezier_mmd(aI)
    aG2 = round_bezier_mmd(aG)
    aD2 = round_bezier_mmd(aD)

    return t, x, y, [bA2, bE2, bH2, bJ2], [aJ2, aI2, aG2, aD2]


# 分割したベジェのスケーリング
def scale_bezier(p1, p2, p3, p4):
    diff = p4 - p1

    # nan対策
    s1 = scale_bezier_point(p1, p1, diff)
    s2 = scale_bezier_point(p2, p1, diff)
    s3 = scale_bezier_point(p3, p1, diff)
    s4 = scale_bezier_point(p4, p1, diff)

    return s1, s2, s3, s4


# nan対策を加味したベジェ曲線の点算出
def scale_bezier_point(pn, p1, diff):
    s = (pn - p1) / diff

    # logger.test("diff: %s", diff)
    # logger.test("(pn-p1): %s", (pn-p1))
    # logger.test("s: %s", s)

    # nanになったら0決め打ち
    s.effective()

    return s


# ベジェ曲線をMMD用の数値に丸める
def round_bezier_mmd(target):
    t2 = MVector2D()

    # XとYをそれぞれ整数(0-127)に丸める
    t2.setX(round_integer(target.x() * INTERPOLATION_MMD_MAX))
    t2.setY(round_integer(target.y() * INTERPOLATION_MMD_MAX))

    return t2


# 指定されたtに相当するx(フレーム番号)とy(0-1)を返す
def calc_interpolate_bezier_by_t(x1v, y1v, x2v, y2v, start, end, t):
    x1 = x1v / INTERPOLATION_MMD_MAX
    x2 = x2v / INTERPOLATION_MMD_MAX
    y1 = y1v / INTERPOLATION_MMD_MAX
    y2 = y2v / INTERPOLATION_MMD_MAX

    s = 1 - t

    x = (3 * (s * s) * t * x1) + (3 * s * (t * t) * x2) + (t * t * t)
    y = (3 * (s * s) * t * y1) + (3 * s * (t * t) * y2) + (t * t * t)

    # 開始から終了までの区間に広げる(yは広げない？)
    x2 = start + ((end - start) * x)

    # 整数に丸める
    x3 = round_integer(x2)

    # 開始と被ってたらずらす
    x3 = start + 1 if x3 == start else x3

    # 終了と被ってたらずらす
    x3 = end - 1 if x3 == end else x3

    return x3, x, y


def round_integer(t):
    # 一旦整数部にまで持ち上げる
    t2 = t * 1000000
    
    # pythonは偶数丸めなので、整数部で丸めた後、元に戻す
    return round(round(t2, -6) / 1000000)

