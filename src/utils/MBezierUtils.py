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
    if (end - start) <= 0:
        return 0, 0, 0
        
    x = (now - start) / (end - start)
    x1 = x1v / INTERPOLATION_MMD_MAX
    x2 = x2v / INTERPOLATION_MMD_MAX
    y1 = y1v / INTERPOLATION_MMD_MAX
    y2 = y2v / INTERPOLATION_MMD_MAX

    # 補間曲線ベジェ曲線
    curve1 = bezier.Curve(np.asfortranarray([[0, x1, x2, 1], [0, y1, y2, 1]]), degree=3)
    # 交点を求める為のX線上の直線
    curve2 = bezier.Curve(np.asfortranarray([[x, x], [-99999, 99999]]), degree=1)

    # 交点を求める
    intersections = curve1.intersect(curve2)

    if intersections.shape[1] == 0:
        # 交点が見つからなかった場合、終了
        return 0, 0, 0

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


# 指定されたtになるフレーム番号を取得する
def evaluate_by_t(x1v: int, y1v: int, x2v: int, y2v: int, start: int, end: int, t: float):
    if (end - start) <= 1:
        # 差が1以内の場合、終了
        return start, 0, t

    x1 = x1v / INTERPOLATION_MMD_MAX
    x2 = x2v / INTERPOLATION_MMD_MAX
    y1 = y1v / INTERPOLATION_MMD_MAX
    y2 = y2v / INTERPOLATION_MMD_MAX

    # 補間曲線ベジェ曲線
    curve1 = bezier.Curve(np.asfortranarray([[0, x1, x2, 1], [0, y1, y2, 1]]), degree=3)

    # 単一の評価(x, y)
    es = curve1.evaluate(t)

    # xに相当するフレーム番号
    fno = int(round_integer(start + ((end - start) * es[0, 0])))
    
    return fno, es[1, 0], t


# 3次ベジェ曲線の分割
def split_bezier_mmd(x1v: int, y1v: int, x2v: int, y2v: int, start: int, now: int, end: int):
    if (now - start) == 0 or (end - start) == 0:
        return 0, 0, 0, False, False, [MVector2D(0, 0), MVector2D(20, 20), MVector2D(107, 107), MVector2D(127, 127)], \
            [MVector2D(0, 0), MVector2D(20, 20), MVector2D(107, 107), MVector2D(127, 127)]

    # 3次ベジェ曲線を分割する
    x, y, t, before_bz, after_bz = split_bezier(x1v, y1v, x2v, y2v, start, now, end)

    # ベジェ曲線の値がMMD用に合っているかを加味して返す
    return x, y, t, is_fit_bezier_mmd(before_bz), is_fit_bezier_mmd(after_bz), before_bz, after_bz


# ベジェ曲線の値がMMD用に合っているか
def is_fit_bezier_mmd(bz: list, offset=0):
    for b in bz:
        if not (0 - offset <= b.x() <= INTERPOLATION_MMD_MAX + offset) or not (0 - offset <= b.y() <= INTERPOLATION_MMD_MAX + offset):
            # MMD用の範囲内でなければNG
            return False

    if bz[1].x() == bz[1].y() == bz[2].x() == bz[2].y() == 0:
        # 全部0なら不整合
        return False

    return True


# 3次ベジェ曲線の分割
# http://geom.web.fc2.com/geometry/bezier/cut-cb.html
def split_bezier(x1v: int, y1v: int, x2v: int, y2v: int, start: int, now: int, end: int):
    # 補間曲線の進んだ時間分を求める
    x, y, t = evaluate(x1v, y1v, x2v, y2v, start, now, end)

    A = MVector2D(0.0, 0.0)
    B = MVector2D(x1v / INTERPOLATION_MMD_MAX, y1v / INTERPOLATION_MMD_MAX)
    C = MVector2D(x2v / INTERPOLATION_MMD_MAX, y2v / INTERPOLATION_MMD_MAX)
    D = MVector2D(1.0, 1.0)

    E = A * (1 - t) + B * t
    F = B * (1 - t) + C * t
    G = C * (1 - t) + D * t
    H = E * (1 - t) + F * t
    I = F * (1 - t) + G * t # noqa
    J = H * (1 - t) + I * t

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

    return x, y, t, [bA2, bE2, bH2, bJ2], [aJ2, aI2, aG2, aD2]


# 分割したベジェのスケーリング
def scale_bezier(p1: MVector2D, p2: MVector2D, p3: MVector2D, p4: MVector2D):
    diff = p4 - p1

    # nan対策
    s1 = scale_bezier_point(p1, p1, diff)
    s2 = scale_bezier_point(p2, p1, diff)
    s3 = scale_bezier_point(p3, p1, diff)
    s4 = scale_bezier_point(p4, p1, diff)

    return s1, s2, s3, s4


# nan対策を加味したベジェ曲線の点算出
def scale_bezier_point(pn: MVector2D, p1: MVector2D, diff: MVector2D):
    s = (pn - p1) / diff

    # logger.test("diff: %s", diff)
    # logger.test("(pn-p1): %s", (pn-p1))
    # logger.test("s: %s", s)

    # nanになったら0決め打ち
    s.effective()

    return s


# ベジェ曲線をMMD用の数値に丸める
def round_bezier_mmd(target: MVector2D):
    t2 = MVector2D()

    # XとYをそれぞれ整数(0-127)に丸める
    t2.setX(round_integer(target.x() * INTERPOLATION_MMD_MAX))
    t2.setY(round_integer(target.y() * INTERPOLATION_MMD_MAX))

    return t2


def round_integer(t: float):
    # 一旦整数部にまで持ち上げる
    t2 = t * 1000000
    
    # pythonは偶数丸めなので、整数部で丸めた後、元に戻す
    return round(round(t2, -6) / 1000000)

