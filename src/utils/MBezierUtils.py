# -*- coding: utf-8 -*-
#
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MLogger import MLogger # noqa
import numpy as np
import bezier

logger = MLogger(__name__)

# MMDでの補間曲線の最大値
INTERPOLATION_MMD_MAX = 127
# MMDの線形補間
LINEAR_MMD_INTERPOLATION = [MVector2D(0, 0), MVector2D(20, 20), MVector2D(107, 107), MVector2D(127, 127)]

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


# 指定したすべての値を通るカトマル曲線からベジェ曲線を計算し、MMD補間曲線範囲内に収められた場合、そのベジェ曲線を返す
def join_value_2_bezier(values: list):
    if np.isclose(np.max(np.array(values)), np.min(np.array(values)), atol=1e-3) or len(values) <= 2:
        # すべてがだいたい同じ値（最小と最大が同じ値)か次数が1の場合、線形補間
        return LINEAR_MMD_INTERPOLATION

    # Xは次数（フレーム数）分移動
    xs = np.linspace(0, len(values) - 2, len(values) - 1)

    # カトマル曲線をベジェ曲線に変換する
    bz_x, bz_y = convert_catmullrom_2_bezier(np.concatenate([[None], xs, [None]]), np.concatenate([[None], values, [None]]))
    logger.test("bz_x: %s", bz_x)
    logger.test("bz_y: %s", bz_y)

    # 次数
    degree = len(bz_x) - 1
    logger.test("degree: %s", degree)

    # すべての制御点を加味したベジェ曲線
    full_curve = bezier.Curve(np.asfortranarray([bz_x, bz_y]), degree=degree)

    if degree < 3:
        # 3次未満の場合、3次まで次数を増やす
        joined_curve = full_curve.elevate()
        for _ in range(1, 3 - degree):
            joined_curve = joined_curve.elevate()
    elif degree == 3:
        # 3次の場合、そのままベジェ曲線をMMD用に補間
        joined_curve = full_curve
    elif degree > 3:
        # 3次より多い場合、次数を減らす

        # 開始から次の開始までのベジェ曲線(次数4から3に減らす)
        fill_curve = bezier.Curve(np.asfortranarray([[bz_x[0], bz_x[1], bz_x[2], bz_x[3], bz_x[4]], [bz_y[0], bz_y[1], bz_y[2], bz_y[3], bz_y[4]]]), degree=4)
        reduced = fill_curve.reduce_()

        for n in range(5, degree + 1):
            # 3次に到達するまでベジェ曲線の次数を減らす
            fill_curve = bezier.Curve(np.asfortranarray([[reduced.nodes[0][0], reduced.nodes[0][1], reduced.nodes[0][2], reduced.nodes[0][3], bz_x[n]], \
                                                        [reduced.nodes[1][0], reduced.nodes[1][1], reduced.nodes[1][2], reduced.nodes[1][3], bz_y[n]]]), degree=4)
            reduced = fill_curve.reduce_()

        joined_curve = reduced

    logger.test("joined_curve: %s", joined_curve.nodes)

    # 全体のキーフレを2倍にしたX（細かく点をチェックする）
    bezier_x = np.linspace(0, len(values), len(values) * 2)

    # 元の2つのベジェ曲線との交点を取得する
    full_ys = intersect_by_x(full_curve, bezier_x)
    logger.debug("full_ys: %s", full_ys)

    # 次数を減らしたベジェ曲線との交点を取得する
    reduced_ys = intersect_by_x(joined_curve, bezier_x)
    logger.debug("reduced_ys: %s", reduced_ys)

    # 交点の差を取得する
    diff_ys = np.asfortranarray(full_ys) - np.asfortranarray(reduced_ys)
    logger.test("diff_ys: %s", diff_ys)

    # 差が大きい箇所をピックアップする
    diff_limit = np.abs(np.diff([np.max(full_ys), np.min(full_ys)])) / len(values) * 2
    diff_large = np.where(np.abs(diff_ys[:-1]) > diff_limit, 1, 0)
    logger.debug("diff_limit: %s, diff_large: %s", diff_limit, diff_large)

    if np.count_nonzero(diff_large) > 0:
        # 差が大きい箇所がある場合、分割不可
        return None
    
    # 差が一定未満である場合、ベジェ曲線をMMD補間曲線に合わせる
    joined_bz = scale_bezier(MVector2D(joined_curve.nodes[0, 0], joined_curve.nodes[1, 0]), MVector2D(joined_curve.nodes[0, 1], joined_curve.nodes[1, 1]), \
                             MVector2D(joined_curve.nodes[0, 2], joined_curve.nodes[1, 2]), MVector2D(joined_curve.nodes[0, 3], joined_curve.nodes[1, 3]))
    logger.debug("joined_bz: %s, %s", joined_bz[1], joined_bz[2])
                        
    if not is_fit_bezier_mmd(joined_bz):
        # 補間曲線がMMD補間曲線内に収まらない場合、NG
        return None
    
    # すべてクリアした場合、補間曲線採用
    return joined_bz


# Catmull-Rom曲線の制御点(通過点)をBezier曲線の制御点に変換する
# http://defghi1977-onblog.blogspot.com/2014/09/catmull-rombezier.html
def convert_catmullrom_2_bezier(xs: list, ys: list):

    bz_x = []
    bz_y = []

    for x0, x1, x2, x3, y0, y1, y2, y3 in zip(xs[:-3], xs[1:-2], xs[2:-1], xs[3:], ys[:-3], ys[1:-2], ys[2:-1], ys[3:]):
        p0 = None if not x0 and not y0 else MVector2D(x0, y0)
        p1 = MVector2D(x1, y1)
        p2 = MVector2D(x2, y2)
        p3 = None if not x3 and not y3 else MVector2D(x3, y3)
        B = None
        C = None

        if not p0 and not p3:
            # 両方ない場合、無視
            continue

        if not p0 and p3:
            # p0が空の場合、始点
            B = (p1 * (1 / 2)) - p2 + (p3 * (1 / 2))
            C = (p1 * (-3 / 2)) + (p2 * 2) - (p3 * (1 / 2))
        
        if p0 and not p3:
            # p3が空の場合、終点
            B = (p0 * (1 / 2)) - p1 + (p2 * (1 / 2))
            C = (p0 * (-1 / 2)) + (p2 * (1 / 2))
        
        if p0 and p3:
            # それ以外は通過点
            B = p0 - (p1 * (5 / 2)) + (p2 * (4 / 2)) - (p3 * (1 / 2))
            C = (p0 * (-1 / 2)) + (p2 * (1 / 2))
        
        if not B or not C:
            logger.warning("p0: %s, p1: %s, p2: %s, p3: %s", p0, p1, p2, p3)

        # ベジェ曲線の制御点
        s1 = (C + (p1 * 3)) / 3
        s2 = (B - (p1 * 3) + (s1 * 6)) / 3
        
        bz_x.append(s1.x())
        bz_x.append(s2.x())

        bz_y.append(s1.y())
        bz_y.append(s2.y())

    return bz_x, bz_y


# 指定された複数のXと交わるそれぞれのYを返す
def intersect_by_x(curve, xs):
    ys = []
    for x in xs:
        # 交点を求める為のX線上の直線
        line1 = bezier.Curve(np.asfortranarray([[x, x], [-99999, 99999]]), degree=1)

        # 交点を求める
        intersections = curve.intersect(line1)

        # tからyを求め直す
        s_vals = np.asfortranarray(intersections[0, :])

        # 評価する
        es = curve.evaluate_multi(s_vals)
        
        # 値が取れている場合、その値を設定する
        if es.shape == (2, 1):
            ys.append(es[1][0])
        # 取れていない場合、無視
        else:
            ys.append(0)
    
    return ys


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

    # 補間曲線
    curve1 = bezier.Curve(np.asfortranarray([[0, x1, x2, 1], [0, y1, y2, 1]]), degree=3)

    # 単一の評価(x, y)
    es = curve1.evaluate(t)

    # xに相当するフレーム番号
    fno = int(round_integer(start + ((end - start) * es[0, 0])))
    
    return fno, es[1, 0], t


# 3次ベジェ曲線の分割
def split_bezier_mmd(x1v: int, y1v: int, x2v: int, y2v: int, start: int, now: int, end: int):
    if (now - start) == 0 or (end - start) == 0:
        return 0, 0, 0, False, False, LINEAR_MMD_INTERPOLATION, LINEAR_MMD_INTERPOLATION

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
    beforeBz = scale_bezier(A, E, H, J)
    afterBz = scale_bezier(J, I, G, D)

    return x, y, t, beforeBz, afterBz


# 分割したベジェのスケーリング
def scale_bezier(p1: MVector2D, p2: MVector2D, p3: MVector2D, p4: MVector2D):
    diff = p4 - p1

    # nan対策
    s1 = scale_bezier_point(p1, p1, diff)
    s2 = scale_bezier_point(p2, p1, diff)
    s3 = scale_bezier_point(p3, p1, diff)
    s4 = scale_bezier_point(p4, p1, diff)

    bs1 = round_bezier_mmd(s1)
    bs2 = round_bezier_mmd(s2)
    bs3 = round_bezier_mmd(s3)
    bs4 = round_bezier_mmd(s4)

    return [bs1, bs2, bs3, bs4]


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

