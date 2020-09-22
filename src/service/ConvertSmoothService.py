# -*- coding: utf-8 -*-
#
import math
import numpy as np
import logging
import os
import traceback
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from module.MOptions import MSmoothOptions, MOptionsDataSet
from mmd.PmxData import PmxModel # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from mmd.VmdWriter import VmdWriter
import module.MMath as MMath
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MServiceUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException

logger = MLogger(__name__, level=1)


class ConvertSmoothService():
    def __init__(self, options: MSmoothOptions):
        self.options = options

    def execute(self):
        logging.basicConfig(level=self.options.logging_level, format="%(message)s [%(module_name)s]")

        try:
            service_data_txt = "スムージング処理実行\n------------------------\nexeバージョン: {version_name}\n".format(version_name=self.options.version_name) \

            service_data_txt = "{service_data_txt}　VMD: {vmd}\n".format(service_data_txt=service_data_txt,
                                    vmd=os.path.basename(self.options.motion.path)) # noqa
            service_data_txt = "{service_data_txt}　モデル: {model}({model_name})\n".format(service_data_txt=service_data_txt,
                                    model=os.path.basename(self.options.motion.path), model_name=self.options.model.name) # noqa
            service_data_txt = "{service_data_txt}　処理回数: {loop_cnt}回\n".format(service_data_txt=service_data_txt,
                                    loop_cnt=self.options.loop_cnt) # noqa
            service_data_txt = "{service_data_txt}　補間方法: {interpolation}\n".format(service_data_txt=service_data_txt,
                                    interpolation=("補間曲線に従う" if self.options.interpolation == 0 else "補間曲線無視（円形）" if self.options.interpolation == 1 else "補間曲線無視（曲線）")) # noqa

            logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

            # 処理に成功しているか
            result = self.convert_smooth()

            # 最後に出力
            VmdWriter(MOptionsDataSet(self.options.motion, None, self.options.model, self.options.output_path, False, False, [], None, 0, [])).write()

            logger.info("出力終了: %s", os.path.basename(self.options.output_path), decoration=MLogger.DECORATION_BOX, title="成功")

            return result
        except SizingException as se:
            logger.error("スムージング処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception:
            logger.critical("スムージング処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

    # スムージング処理実行
    def convert_smooth(self):
        # 最初に全打ち

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="prepare", max_workers=self.options.max_workers) as executor:
            for bone_name in self.options.motion.bones.keys():
                if bone_name in self.options.model.bones:
                    if self.options.interpolation == 0 and len(self.options.motion.bones[bone_name].keys()) >= 2:
                        # 線形補間の場合、そのまま全打ち
                        futures.append(executor.submit(self.prepare_linear, bone_name))
                    elif self.options.interpolation == 1:
                        if len(self.options.motion.bones[bone_name].keys()) > 2:
                            # 円形補間の場合、円形全打ち
                            futures.append(executor.submit(self.prepare_circle, bone_name))
                        else:
                            # 円形補間でキー数が足りない場合、線形補間
                            logger.warning("円形補間が指定されましたが、キー数が3つに満たないため、計算出来ません。ボーン名: %s", bone_name)
                            futures.append(executor.submit(self.prepare_linear, bone_name))
                    elif self.options.interpolation == 2:
                        if len(self.options.motion.bones[bone_name].keys()) > 2:
                            # 曲線補間の場合、カトマル曲線全打ち
                            futures.append(executor.submit(self.prepare_curve, bone_name))
                        else:
                            # 曲線補間でキー数が足りない場合、線形補間
                            logger.warning("曲線補間が指定されましたが、キー数が3つに満たないため、計算出来ません。ボーン名: %s", bone_name)
                            futures.append(executor.submit(self.prepare_linear, bone_name))
        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        # 処理回数が3回以上の場合、フィルタをかける
        if self.options.loop_cnt >= 3:
            futures = []
            with ThreadPoolExecutor(thread_name_prefix="filter", max_workers=self.options.max_workers) as executor:
                for bone_name in self.options.motion.bones.keys():
                    if bone_name in self.options.model.bones:
                        futures.append(executor.submit(self.fitering, bone_name))
            concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

            for f in futures:
                if not f.result():
                    return False
        
        # 処理回数が2回以上の場合、不要キー削除
        if self.options.loop_cnt >= 2:
            futures = []
            with ThreadPoolExecutor(thread_name_prefix="remove", max_workers=self.options.max_workers) as executor:
                for bone_name in self.options.motion.bones.keys():
                    if bone_name in self.options.model.bones:
                        futures.append(executor.submit(self.remove_unnecessary_bf, bone_name))
            concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

            for f in futures:
                if not f.result():
                    return False

        return True
    
    # 不要キー削除処理
    def remove_unnecessary_bf(self, bone_name: str):
        try:
            logger.copy(self.options)

            logger.info("【不要キー削除】%s 開始", bone_name)
            self.options.motion.remove_unnecessary_bf(0, bone_name, self.options.model.bones[bone_name].getRotatable(), \
                                                      self.options.model.bones[bone_name].getTranslatable(), offset=(self.options.loop_cnt - 2))
            logger.info("【不要キー削除】%s 終了", bone_name)

            return True
        except SizingException as se:
            logger.error("スムージング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return False
        except Exception as e:
            logger.error("スムージング処理が意図せぬエラーで終了しました。", e)
            return False
    
    # フィルタリング処理
    def fitering(self, bone_name: str):
        try:
            logger.copy(self.options)

            for n in range(1, self.options.loop_cnt - 1):
                logger.info("【フィルタリング%s回目】%s 開始", n, bone_name)
                self.options.motion.smooth_filter_bf(0, bone_name, self.options.model.bones[bone_name].getRotatable(), \
                                                     self.options.model.bones[bone_name].getTranslatable(), \
                                                     config={"freq": 30, "mincutoff": 0.1, "beta": 0.1, "dcutoff": 1})

            logger.info("【フィルタリング】%s 終了", bone_name)

            return True
        except SizingException as se:
            logger.error("スムージング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return False
        except Exception as e:
            logger.error("スムージング処理が意図せぬエラーで終了しました。", e)
            return False
        
    # 線形補間で全打ち
    def prepare_linear(self, bone_name: str):
        try:
            logger.copy(self.options)

            logger.info("【スムージング1回目】%s 開始", bone_name)

            # 各ボーンのbfを全打ち
            self.options.motion.regist_full_bf(1, [bone_name], offset=1)
            
            logger.info("【スムージング1回目】%s 終了", bone_name)

            return True
        except SizingException as se:
            logger.error("スムージング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return False
        except Exception as e:
            logger.error("スムージング処理が意図せぬエラーで終了しました。", e)
            return False
        
    # 曲線補間で全打ち
    def prepare_curve(self, bone_name: str):
        try:
            logger.copy(self.options)

            logger.info("【スムージング1回目】%s 開始", bone_name)

            # 全キーフレを取得
            fnos = self.options.motion.get_bone_fnos(bone_name, is_read=True)

            rx_values = []
            ry_values = []
            rz_values = []
            mx_values = []
            my_values = []
            mz_values = []
            
            for fno in fnos:
                bf = self.options.motion.calc_bf(bone_name, fno)
                
                if self.options.model.bones[bone_name].getRotatable():
                    euler = bf.rotation.toEulerAngles()
                    rx_values.append(euler.x())
                    ry_values.append(euler.y())
                    rz_values.append(euler.z())
                
                if self.options.model.bones[bone_name].getTranslatable():
                    mx_values.append(bf.position.x())
                    my_values.append(bf.position.y())
                    mz_values.append(bf.position.z())
            
            if self.options.model.bones[bone_name].getRotatable():
                rx_all_values = MBezierUtils.calc_value_from_catmullrom(bone_name, fnos, rx_values)
                logger.info("【スムージング1回目】%s - 回転X 終了", bone_name)

                ry_all_values = MBezierUtils.calc_value_from_catmullrom(bone_name, fnos, ry_values)
                logger.info("【スムージング1回目】%s - 回転Y 終了", bone_name)

                rz_all_values = MBezierUtils.calc_value_from_catmullrom(bone_name, fnos, rz_values)
                logger.info("【スムージング1回目】%s - 回転X 終了", bone_name)
            else:
                if len(fnos) > 0:
                    rx_all_values = np.zeros(fnos[-1] + 1)
                    ry_all_values = np.zeros(fnos[-1] + 1)
                    rz_all_values = np.zeros(fnos[-1] + 1)
                else:
                    rx_all_values = [0]
                    ry_all_values = [0]
                    rz_all_values = [0]

            if self.options.model.bones[bone_name].getTranslatable():
                mx_all_values = MBezierUtils.calc_value_from_catmullrom(bone_name, fnos, mx_values)
                logger.info("【スムージング1回目】%s - 移動X 終了", bone_name)

                my_all_values = MBezierUtils.calc_value_from_catmullrom(bone_name, fnos, my_values)
                logger.info("【スムージング1回目】%s - 移動Y 終了", bone_name)

                mz_all_values = MBezierUtils.calc_value_from_catmullrom(bone_name, fnos, mz_values)
                logger.info("【スムージング1回目】%s - 移動Z 終了", bone_name)
            else:
                if len(fnos) > 0:
                    mx_all_values = np.zeros(fnos[-1] + 1)
                    my_all_values = np.zeros(fnos[-1] + 1)
                    mz_all_values = np.zeros(fnos[-1] + 1)
                else:
                    mx_all_values = [0]
                    my_all_values = [0]
                    mz_all_values = [0]

            # カトマル曲線で生成した値を全打ち
            for fno, (rx, ry, rz, mx, my, mz) in enumerate(zip(rx_all_values, ry_all_values, rz_all_values, mx_all_values, my_all_values, mz_all_values)):
                bf = self.options.motion.calc_bf(bone_name, fno)
                bf.rotation = MQuaternion.fromEulerAngles(rx, ry, rz)
                bf.position = MVector3D(mx, my, mz)
                self.options.motion.regist_bf(bf, bone_name, fno)
                
            logger.info("【スムージング1回目】%s 終了", bone_name)

            return True
        except SizingException as se:
            logger.error("スムージング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return False
        except Exception as e:
            logger.error("スムージング処理が意図せぬエラーで終了しました。", e)
            return False

    # 円形補間で全打ち
    def prepare_circle(self, bone_name: str):
        try:
            logger.copy(self.options)

            logger.info("【スムージング1回目】%s 開始", bone_name)

            if self.options.model.bones[bone_name].fixed_axis != MVector3D():
                # 回転は3Dベクトルに直すため、そのボーンのローカル軸の向きを先に計算しておく
                local_axis = calc_local_axis(self.options.model, bone_name)
            else:
                # 通常ボーンはそのまま回す
                local_axis = MVector3D()

            prev_sep_fno = 0
            fnos = self.options.motion.get_bone_fnos(bone_name, is_read=True)
            for prev_fno, now_fno, next_fno in zip(fnos[:-2], fnos[1:-1], fnos[2:]):
                
                prev_bf = self.options.motion.calc_bf(bone_name, prev_fno)
                now_bf = self.options.motion.calc_bf(bone_name, now_fno)
                next_bf = self.options.motion.calc_bf(bone_name, next_fno)

                # 読み込み時のキーで3キーフレで伸ばす
                for fno in range(prev_fno, next_fno):
                    if fno in fnos:
                        # 読み込みキーはスルー
                        continue

                    target_bf = VmdBoneFrame(fno)
                    target_bf.set_name(bone_name)
                    target_bf.key = True

                    if self.options.model.bones[bone_name].getRotatable():
                        # 回転可ボーンの場合、回転円形補間
                        self.interpolate_rot_circle(prev_bf, now_bf, next_bf, target_bf, local_axis)

                    if self.options.model.bones[bone_name].getTranslatable():
                        # 移動可ボーンの場合、移動円形補間
                        self.interpolate_mov_circle(prev_bf, now_bf, next_bf, target_bf)

                    self.options.motion.regist_bf(target_bf, bone_name, fno)

                    if fno // 500 > prev_sep_fno and fnos[-1] > 0:
                        logger.info("-- %sフレーム目:終了(%s％) %s", fno, round((fno / fnos[-1]) * 100, 3), bone_name)
                        prev_sep_fno = fno // 500
                        
            logger.info("【スムージング1回目】%s 終了", bone_name)

            return True
        except SizingException as se:
            logger.error("スムージング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return False
        except Exception as e:
            logger.error("スムージング処理が意図せぬエラーで終了しました。", e)
            return False

    # 移動の円形補間
    def interpolate_mov_circle(self, prev_bf: VmdBoneFrame, now_bf: VmdBoneFrame, next_bf: VmdBoneFrame, target_bf: VmdBoneFrame):
        p = prev_bf.position.copy()
        w = now_bf.position.copy()
        n = next_bf.position.copy()

        if target_bf.fno < now_bf.fno:
            # nowより前の場合
            # 変化量
            t = (target_bf.fno - prev_bf.fno) / (now_bf.fno - prev_bf.fno)

            # デフォルト値
            d = w + (w - p)

            out = interpolate_vec3(p, w, n, d, t, target_bf.fno)
        else:
            # nowより後の場合
            # 変化量
            t = (target_bf.fno - now_bf.fno) / (next_bf.fno - now_bf.fno)

            # デフォルト値
            d = n + (n - w)

            out = interpolate_vec3(w, n, p, d, t, target_bf.fno)

        target_bf.position = out

    # 移動の円形補間
    def interpolate_rot_circle(self, prev_bf: VmdBoneFrame, now_bf: VmdBoneFrame, next_bf: VmdBoneFrame, target_bf: VmdBoneFrame, local_axis: MVector3D):
        if local_axis != MVector3D():
            # 軸がある場合、その方向に回す
            p_qq = MQuaternion.fromAxisAndAngle(local_axis, prev_bf.rotation.toDegree())
            w_qq = MQuaternion.fromAxisAndAngle(local_axis, now_bf.rotation.toDegree())
            n_qq = MQuaternion.fromAxisAndAngle(local_axis, next_bf.rotation.toDegree())

            p = p_qq.toEulerAngles()
            w = w_qq.toEulerAngles()
            n = n_qq.toEulerAngles()
        else:
            p_qq = prev_bf.rotation.copy()
            w_qq = now_bf.rotation.copy()
            n_qq = next_bf.rotation.copy()

            # 軸がない場合、そのまま回転
            p = p_qq.toEulerAngles()
            w = w_qq.toEulerAngles()
            n = n_qq.toEulerAngles()

        if target_bf.fno < now_bf.fno:
            # 変化量
            t = (target_bf.fno - prev_bf.fno) / (now_bf.fno - prev_bf.fno)

            # デフォルト値
            d_qq = MQuaternion.slerp(p_qq, w_qq, t)
            d = d_qq.toEulerAngles()

            out = interpolate_vec3(p, w, n, d, t, target_bf.fno)
        else:
            # 変化量
            t = (target_bf.fno - now_bf.fno) / (next_bf.fno - now_bf.fno)

            # デフォルト値
            d_qq = MQuaternion.slerp(w_qq, n_qq, t)
            d = d_qq.toEulerAngles()

            out = interpolate_vec3(w, n, p, d, t, target_bf.fno)

        out_qq = MQuaternion.fromEulerAngles(out.x(), out.y(), out.z())

        if local_axis != MVector3D():
            # 回転を元に戻す
            if target_bf.fno < now_bf.fno:
                d2_qq = MQuaternion.slerp(prev_bf.rotation, now_bf.rotation, t)
            else:
                d2_qq = MQuaternion.slerp(now_bf.rotation, next_bf.rotation, t)

            result_qq = (d_qq.inverted() * out_qq * d2_qq)
        else:
            result_qq = out_qq

        target_bf.rotation = result_qq


# 指定されたボーンの最終的なローカル軸を求める
def calc_local_axis(model, bone_name):
    # 定義されていないのも含め全ボーンリンクを取得する
    links = model.create_link_2_top_one(bone_name, is_defined=False)

    # 初期スタンスのボーングローバル位置と行列を取得
    global_3ds_dic, total_mats = MServiceUtils.calc_global_pos(model, links, VmdMotion(), 0, return_matrix=True, is_local_x=True)
    
    # target_mat = MMatrix4x4()
    # target_mat.setToIdentity()

    # # 処理対象行列
    # for n, (lname, mat) in enumerate(total_mats.items()):
    #     target_link = links.get(lname)

    #     if n == 0:
    #         # 最初は行列そのもの
    #         target_mat = mat.copy()
    #     else:
    #         # 2番目以降は行列をかける
    #         target_mat *= mat.copy()

    #     if n > 0:
    #         # ボーン自身にローカル軸が設定されているか
    #         local_x_matrix = MMatrix4x4()
    #         local_x_matrix.setToIdentity()

    #         local_axis_qq = MQuaternion()

    #         if target_link.local_x_vector == MVector3D():
    #             # ローカル軸が設定されていない場合、計算

    #             # 自身から親を引いた軸の向き
    #             local_axis = target_link.position - links.get(lname, offset=-1).position
    #             local_axis_qq = MQuaternion.fromDirection(local_axis.normalized(), MVector3D(0, 0, 1))
    #         else:
    #             # ローカル軸が設定されている場合、その値を採用
    #             local_axis_qq = MQuaternion.fromDirection(target_link.local_x_vector.normalized(), MVector3D(0, 0, 1))
            
    #         local_x_matrix.rotate(local_axis_qq)

    #         target_mat *= local_x_matrix

    # ワールド座標系から注目ノードの局所座標系への変換
    inv_coord = total_mats[bone_name].inverted()

    # 自身のボーンからの向き先を取得
    axis = model.get_local_x_axis(bone_name)
    
    # 最終的な対象ボーンのローカル軸の向き
    local_axis = (inv_coord * axis).normalized()

    return local_axis

    
# vec3での滑らかな変化
def interpolate_vec3(op: MVector3D, ow: MVector3D, on: MVector3D, d: MVector3D, t: float, f: int):
    # 念のためコピー
    p = op.copy()
    w = ow.copy()
    n = on.copy()

    # 半径は3点間の距離の最長の半分
    r = max(p.distanceToPoint(w), p.distanceToPoint(n), w.distanceToPoint(n)) / 2

    logger.test("op: %s, ow: %s, on: %s, d: %s, t: %s, f: %s, r: %s", p.to_log(), w.to_log(), n.to_log(), d.to_log(), t, f, r)

    if r == 0:
        # 半径が取れなかった場合、そもそもまったく移動がないので、線分移動
        return (p + n) * t

    if p == w or p == n or w == n:
        # 半径が0の場合か、どれか同じ値の場合、線対称な値を使用する
        n = d

    # 3点を通る球体の原点を求める
    c, radius = calc_sphere_center(p, w, n, r)

    if radius == 0:
        # 半径が取れなかった場合、そもそもまったく移動がないので、線分移動
        return (p + n) * t

    # prev -> now の t分の回転量
    pn_qq = MQuaternion.rotationTo((p - c).normalized(), (c - c).normalized())
    pw_qq = MQuaternion.rotationTo((p - c).normalized(), (w - c).normalized())
    # 球形補間の移動量
    t_qq = MQuaternion.slerp(pn_qq, pw_qq, t)

    logger.test("(p - c): %s, (c - c): %s, (w - c): %s", (p - c).normalized(), (c - c).normalized(), (w - c).normalized())
    logger.test("pn_qq: %s, pw: %s, t: %s", pn_qq, pw_qq, t_qq)

    out = t_qq * (p - c) + c

    # 値の変化がない場合、上書き
    if p.x() == w.x() == n.x():
        out.setX(w.x())
    if p.y() == w.y() == n.y():
        out.setY(w.y())
    if p.z() == w.z() == n.z():
        out.setZ(w.z())

    out.effective()
    
    logger.test(out.to_log())

    return out


# 指定された3点と半径を通る球の中心点を求める
# https://oshiete.goo.ne.jp/qa/195295.html
# https://okwave.jp/qa/q9467739.html
def calc_sphere_center(pv, wv, nv, r):
    # 大体0の場合は代替値で求める
    x1 = pv.x() if not MMath.is_almost_null(pv.x()) else 0.00001
    y1 = pv.y() if not MMath.is_almost_null(pv.y()) else 0.00001
    z1 = pv.z() if not MMath.is_almost_null(pv.z()) else 0.00001
    x2 = wv.x() if not MMath.is_almost_null(wv.x()) else 0.00001
    y2 = wv.y() if not MMath.is_almost_null(wv.y()) else 0.00001
    z2 = wv.z() if not MMath.is_almost_null(wv.z()) else 0.00001
    x3 = nv.x() if not MMath.is_almost_null(nv.x()) else 0.00001
    y3 = nv.y() if not MMath.is_almost_null(nv.y()) else 0.00001
    z3 = nv.z() if not MMath.is_almost_null(nv.z()) else 0.00001

    m = (pv + wv + nv) / 3

    try:
        tm01=x1**2-x2**2+y1**2-y2**2+z1**2-z2**2 # noqa
        tm02=x1**2-x3**2+y1**2-y3**2+z1**2-z3**2 # noqa
        tm11=-2*(x1-x2)*(z1-z3)+2*(x1-x3)*(z1-z2) # noqa
        tm12=-2*(y1-y2)*(z1-z3)+2*(y1-y3)*(z1-z2) # noqa
        tm13=tm01*(z1-z3)-tm02*(z1-z2) # noqa
        tm21=-2*(x1-x2)*(y1-y3)+2*(x1-x3)*(y1-y2) # noqa
        tm22=-2*(z1-z2)*(y1-y3)+2*(z1-z3)*(y1-y2) # noqa
        tm23=tm01*(y1-y3)-tm02*(y1-y2) # noqa
        tma=1+tm11**2/tm12**2+tm21**2/tm22**2 # noqa
        tmb=-2*x1+2*(y1+tm13/tm12)*tm11/tm12+2*(z1+tm23/tm22)*tm21/tm22 # noqa
        tmc=x1**2+(y1+tm13/tm12)**2+(z1+tm23/tm22)**2-r**2 # noqa
        xq1=(-tmb+math.sqrt(abs(tmb**2-4*tma*tmc)))/2/tma # noqa
        xq2=(-tmb-math.sqrt(abs(tmb**2-4*tma*tmc)))/2/tma # noqa
        yq1=-tm13/tm12-tm11/tm12*xq1 # noqa
        yq2=-tm13/tm12-tm11/tm12*xq2 # noqa
        zq1=-tm23/tm22-tm21/tm22*xq1 # noqa
        zq2=-tm23/tm22-tm21/tm22*xq2 # noqa

        c1 = MVector3D(xq1, yq1, zq1)
        c2 = MVector3D(xq2, yq2, zq2)

        if c1.isnan() or c2.isnan():
            # 球体の原点が求められなかった場合、二次元円として求める
            if round(x1, 1) == round(x2, 1) == round(x3, 1):
                # 同じ値の場合、2次元円として求める
                cx, cy, r = calc_circle_center(y1, z1, y2, z2, y3, z3)
                return MVector3D(x1, cx, cy), r
            
            if round(y1, 1) == round(y2, 1) == round(y3, 1):
                cx, cy, r = calc_circle_center(x1, z1, x2, z2, x3, z3)
                return MVector3D(cx, y1, cy), r
            
            if round(z1, 1) == round(z2, 1) == round(z3, 1):
                cx, cy, r = calc_circle_center(x1, y1, x2, y2, x3, y3)
                return MVector3D(cx, cy, z1), r
        
        logger.test("c1: %s(%s), c2: %s(%s)", c1.to_log(), c1.isnan(), c2.to_log(), c2.isnan())

        if c1 == c2:
            # 重解
            return c1, r

        if c1.distanceToPoint(m) < c2.distanceToPoint(m):
            # 3点の中間に近い方を返す
            return c1, r

        return c2, r
    except ZeroDivisionError:

        if round(x1, 1) == round(x2, 1) == round(x3, 1):
            # 同じ値の場合、2次元円として求める
            cx, cy, r = calc_circle_center(y1, z1, y2, z2, y3, z3)
            return MVector3D(x1, cx, cy), r
        
        if round(y1, 1) == round(y2, 1) == round(y3, 1):
            cx, cy, r = calc_circle_center(x1, z1, x2, z2, x3, z3)
            return MVector3D(cx, y1, cy), r
        
        if round(z1, 1) == round(z2, 1) == round(z3, 1):
            cx, cy, r = calc_circle_center(x1, y1, x2, y2, x3, y3)
            return MVector3D(cx, cy, z1), r
    
    return MVector3D(), 0


# http://www.iot-kyoto.com/satoh/2016/01/29/tangent-003/
# http://nobutina.blog86.fc2.com/blog-entry-674.html
def calc_circle_center(x1, y1, x2, y2, x3, y3):

    G=( y2*x1-y1*x2 +y3*x2-y2*x3 +y1*x3-y3*x1 ) # noqa

    try:
        Xc= ((x1*x1+y1*y1)*(y2-y3)+(x2*x2+y2*y2)*(y3-y1)+(x3*x3+y3*y3)*(y1-y2))/(2*G) # noqa
        Yc=-((x1*x1+y1*y1)*(x2-x3)+(x2*x2+y2*y2)*(x3-x1)+(x3*x3+y3*y3)*(x1-x2))/(2*G) # noqa

        Xd=(((x1*x1+y1*y1)-(x2*x2+y2*y2))*(y2-y3)-((x2*x2+y2*y2)-(x3*x3+y3*y3))*(y1-y2))/(2*((x1-x2)*(y2-y3)-(x2-x3)*(y1-y2))) # noqa
        Yd=(((y1*y1+x1*x1)-(y2*y2+x2*x2))*(x2-x3)-((y2*y2+x2*x2)-(y3*y3+x3*x3))*(x1-x2))/(2*((y1-y2)*(x2-x3)-(y2-y3)*(x1-x2))) # noqa

        G = 2 * math.sqrt((x1 - Xc) * (x1 - Xc) + (y1 - Yc) * (y1 - Yc))

        return Xd, Yd, G / 2
    except ZeroDivisionError:

        if round(x1, 1) == round(x2, 1) == round(x3, 1):
            G = math.sqrt((y1 + y2 + y3) ** 2)
            return (x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3, G

        G = math.sqrt((x1 + x2 + x3) ** 2)
        return (x1 + x2 + x3) / 3, (y1 + y2 + y3) / 3, G

    return 0, 0, 0

