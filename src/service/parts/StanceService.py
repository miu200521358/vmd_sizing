# -*- coding: utf-8 -*-
#
import numpy as np
import math
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from mmd.PmxData import PmxModel # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions, MOptionsDataSet
from module.MParams import BoneLinks
from utils import MUtils, MServiceUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException

logger = MLogger(__name__, level=MLogger.DEBUG)

RADIANS_1 = math.cos(math.radians(1))
RADIANS_2 = math.cos(math.radians(2))
RADIANS_5 = math.cos(math.radians(5))
RADIANS_8 = math.cos(math.radians(8))


class StanceService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        futures = []
        with ThreadPoolExecutor(thread_name_prefix="stance", max_workers=min(5, self.options.max_workers)) as executor:
            for data_set_idx, data_set in enumerate(self.options.data_set_list):
                if data_set.motion.motion_cnt <= 0:
                    # モーションデータが無い場合、処理スキップ
                    continue

                futures.append(executor.submit(self.execute_pool, data_set_idx))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        return True
    
    def execute_pool(self, data_set_idx: int):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            # スタンス追加補正をする場合
            if data_set.detail_stance_flg:
                if "センターXZ補正" in data_set.selected_stance_details:
                    # センターXZ補正
                    self.adjust_center_stance(data_set_idx, data_set)

                if "上半身補正" in data_set.selected_stance_details:
                    # 上半身補正
                    self.adjust_upper_stance(data_set_idx, data_set)

                if "下半身補正" in data_set.selected_stance_details:
                    # 下半身補正
                    self.adjust_lower_stance(data_set_idx, data_set)

                if "足ＩＫ補正" in data_set.selected_stance_details:
                    # 足ＩＫ補正
                    self.adjust_leg_ik_stance(data_set_idx, data_set)

                if "つま先補正" in data_set.selected_stance_details:
                    # つま先補正
                    self.adjust_toe_stance(data_set_idx, data_set)

                if "つま先ＩＫ補正" in data_set.selected_stance_details:
                    # つま先ＩＫ補正
                    self.adjust_toe_ik_stance(data_set_idx, data_set)

            # 腕系サイジング可能（もしくはチェックスキップ）であれば、腕スタンス補正
            if (data_set.org_model.can_arm_sizing and data_set.rep_model.can_arm_sizing) or self.options.arm_options.arm_check_skip_flg:
                if data_set.detail_stance_flg:
                    if "肩補正" in data_set.selected_stance_details:
                        # 肩補正
                        self.adjust_shoulder_stance(data_set_idx, data_set)

                if data_set.twist_flg:
                    # 捩り分散あり
                    self.spread_twist(data_set_idx, data_set)
                
                # 腕スタンス補正
                self.adjust_arm_stance(data_set_idx, data_set)

                if data_set.detail_stance_flg:
                    # センターY補正
                    if "センターY補正" in data_set.selected_stance_details:
                        # センターY補正
                        self.adjust_center_arm_stance(data_set_idx, data_set)
            else:
                target_model_type = ""

                if not data_set.org_model.can_arm_sizing:
                    target_model_type = "作成元"

                if not data_set.rep_model.can_arm_sizing:
                    if len(target_model_type) > 0:
                        target_model_type = target_model_type + "/"
                    
                    target_model_type = target_model_type + "変換先"

                logger.warning("No.%sの%sモデルの腕構造にサイジングが対応していない為、腕系処理をスキップします。", (data_set_idx + 1), target_model_type, decoration=MLogger.DECORATION_BOX)

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 捩り分散
    def spread_twist(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("捩り分散　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)
        
        futures = []
        with ThreadPoolExecutor(thread_name_prefix="twist{0}".format(data_set_idx), max_workers=min(5, self.options.max_workers)) as executor:
            for direction in ["左", "右"]:
                futures.append(executor.submit(self.spread_twist_lr, data_set_idx, direction))
        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        return True

    # 捩り分散左右
    def spread_twist_lr(self, data_set_idx: int, direction: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            # 捩り分散に必要なボーン群
            arm_bone_name = "{0}腕".format(direction)
            arm_twist_bone_name = "{0}腕捩".format(direction)
            elbow_bone_name = "{0}ひじ".format(direction)
            wrist_twist_bone_name = "{0}手捩".format(direction)
            wrist_bone_name = "{0}手首".format(direction)

            twist_target_bones = [arm_bone_name, arm_twist_bone_name, elbow_bone_name, wrist_twist_bone_name, wrist_bone_name]

            if set(twist_target_bones).issubset(data_set.rep_model.bones):
                # 先モデルにボーンが揃ってる場合、捩り分散
                
                # フラグON
                data_set.full_arms = True

                # 各ボーンのローカル軸
                local_z_axis = MVector3D(0, 0, -1)
                arm_local_x_axis = data_set.rep_model.get_local_x_axis(arm_bone_name)
                arm_twist_local_x_axis = data_set.rep_model.get_local_x_axis(arm_twist_bone_name)
                elbow_local_x_axis = data_set.rep_model.get_local_x_axis(elbow_bone_name)
                elbow_local_y_axis = MVector3D.crossProduct(elbow_local_x_axis, local_z_axis).normalized()
                wrist_twist_local_x_axis = data_set.rep_model.get_local_x_axis(wrist_twist_bone_name)
                wrist_local_x_axis = data_set.rep_model.get_local_x_axis(wrist_bone_name)
                wrist_local_y_axis = MVector3D.crossProduct(wrist_local_x_axis, local_z_axis).normalized()

                logger.test("%s: axis: %s", arm_bone_name, arm_local_x_axis)
                logger.test("%s: axis: %s", arm_twist_bone_name, arm_twist_local_x_axis)
                logger.test("%s: axis: %s", elbow_bone_name, elbow_local_x_axis)
                logger.test("%s: axis: %s", elbow_bone_name, elbow_local_y_axis)
                logger.test("%s: axis: %s", wrist_twist_bone_name, wrist_twist_local_x_axis)
                logger.test("%s: axis: %s", wrist_bone_name, wrist_local_x_axis)

                # 内積差分に基づきキー追加
                logger.info("%s捩り分散準備開始【No.%s】", direction, (data_set_idx + 1))
                fnos = data_set.motion.get_differ_fnos((data_set_idx + 1), [arm_bone_name, arm_twist_bone_name, elbow_bone_name, wrist_twist_bone_name, wrist_bone_name], \
                                                       limit_degrees=20, limit_length=0)

                futures = []
                with ThreadPoolExecutor(thread_name_prefix="twist_smooth{0}".format(data_set_idx), max_workers=self.options.max_workers) as executor:
                    for bone_name in [arm_bone_name, arm_twist_bone_name, elbow_bone_name, wrist_twist_bone_name, wrist_bone_name]:
                        futures.append(executor.submit(self.regist_twist_bf, data_set_idx, bone_name, fnos))

                concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)
                for f in futures:
                    if not f.result():
                        return False

                logger.info("-- %s捩り分散準備:終了【No.%s】", direction, (data_set_idx + 1))

                logger.info("%s捩り分散準備:終了【No.%s】", direction, (data_set_idx + 1))
                logger.info("%s捩り分散開始【No.%s】", direction, (data_set_idx + 1))

                # 腕系ボーンのfnos
                fnos = data_set.motion.get_bone_fnos(arm_bone_name, arm_twist_bone_name, elbow_bone_name, wrist_twist_bone_name, wrist_bone_name)

                prev_sep_fno = 0
                log_target_idxs = []
                for fno_idx, fno in enumerate(fnos):
                    if fno // 200 > prev_sep_fno:
                        log_target_idxs.append(fno)
                        prev_sep_fno = fno // 200
                log_target_idxs.append(fnos[-1])

                futures = []
                with ThreadPoolExecutor(thread_name_prefix="twist_exec{0}".format(data_set_idx), max_workers=min(5, self.options.max_workers)) as executor:
                    for fno_idx, fno in enumerate(fnos):
                        futures.append(executor.submit(self.spread_twist_pool, data_set_idx, fno_idx, fno, fnos[-1], \
                                                       arm_bone_name, arm_twist_bone_name, elbow_bone_name, wrist_twist_bone_name, wrist_bone_name, \
                                                       arm_local_x_axis, arm_twist_local_x_axis, elbow_local_x_axis, elbow_local_y_axis, \
                                                       wrist_twist_local_x_axis, wrist_local_x_axis, wrist_local_y_axis, log_target_idxs))
                concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

                for f in futures:
                    if not f.result():
                        return False

                # logger.info("%s捩り分散後処理 - 円滑化【No.%s】", arm_bone_name, (data_set_idx + 1))

                # # 各ボーンのbfを円滑化
                # futures = []
                # with ThreadPoolExecutor(thread_name_prefix="twist_smooth{0}".format(data_set_idx), max_workers=self.options.max_workers) as executor:
                #     for bone_name in [arm_bone_name, arm_twist_bone_name, elbow_bone_name, wrist_twist_bone_name, wrist_bone_name]:
                #         futures.append(executor.submit(self.smooth_twist, data_set_idx, bone_name))

                # concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)
                # for f in futures:
                #     if not f.result():
                #         return False

                logger.info("%s捩り分散後処理 - フィルタリング【No.%s】", arm_bone_name, (data_set_idx + 1))

                # 捩りボーンのbfにフィルターをかける
                futures = []
                with ThreadPoolExecutor(thread_name_prefix="twist_smooth_twist{0}".format(data_set_idx), max_workers=self.options.max_workers) as executor:
                    for bone_name in [arm_twist_bone_name, wrist_twist_bone_name]:
                        futures.append(executor.submit(self.smooth_filter_twist, data_set_idx, bone_name, \
                                       config={"freq": 30, "mincutoff": 0.01, "beta": 0.05, "dcutoff": 0.5}))

                concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)
                for f in futures:
                    if not f.result():
                        return False

                # 各ボーンのbfにフィルターをかける
                futures = []
                with ThreadPoolExecutor(thread_name_prefix="twist_smooth{0}".format(data_set_idx), max_workers=self.options.max_workers) as executor:
                    for bone_name in [arm_bone_name, elbow_bone_name, wrist_bone_name, arm_twist_bone_name, wrist_twist_bone_name]:
                        futures.append(executor.submit(self.smooth_filter_twist, data_set_idx, bone_name, \
                                       config={"freq": 30, "mincutoff": 0.03, "beta": 0.1, "dcutoff": 1}))

                concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)
                for f in futures:
                    if not f.result():
                        return False

                logger.info("%s捩り分散:終了【No.%s】", direction, (data_set_idx + 1))
            else:
                logger.info("%s捩り分散: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", direction, (data_set_idx + 1), ", ".join(twist_target_bones))

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e
    
    def remove_unnecessary_bf_pool_parts(self, data_set_idx: int, bone_name: str, offset: int):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]
            data_set.motion.remove_unnecessary_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
                                                  data_set.rep_model.bones[bone_name].getTranslatable(), offset=offset)

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    def regist_twist_bf(self, data_set_idx: int, bone_name: str, fnos: list):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]
            
            prev_sep_fno = 0
            for fno in fnos:
                bf = data_set.motion.calc_bf(bone_name, fno)
                data_set.motion.regist_bf(bf, bone_name, fno)

                if fno // 500 > prev_sep_fno and fnos[-1] > 0:
                    logger.info("-- %sフレーム目:終了(%s％)【No.%s - キーフレ追加 - %s】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, bone_name)
                    prev_sep_fno = fno // 500

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e
    
    def smooth_twist(self, data_set_idx: int, bone_name: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]
            
            data_set.motion.smooth_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
                                      data_set.rep_model.bones[bone_name].getTranslatable(), limit_degrees=1)

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    def smooth_filter_twist(self, data_set_idx: int, bone_name: str, config: dict):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            data_set.motion.smooth_filter_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
                                             data_set.rep_model.bones[bone_name].getTranslatable(), config=config, loop=1)

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 捩り分散後のチェック処理
    def check_twist_pool(self, data_set_idx: int, fno_idx: int, fno: int, last_fno: int, arm_bone_name: str, arm_twist_bone_name: str, elbow_bone_name: str, \
                         wrist_twist_bone_name: str, wrist_bone_name: str, arm_local_x_axis: str, arm_twist_local_x_axis: MVector3D, elbow_local_x_axis: MVector3D, \
                         elbow_local_y_axis: MVector3D, wrist_twist_local_x_axis: MVector3D, wrist_local_x_axis: MVector3D, wrist_local_y_axis: MVector3D, log_target_idxs: list):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            # 削除後（強制補間曲線再計算後）の値
            arm_twist_bf = data_set.motion.calc_bf(arm_twist_bone_name, fno)
            if not arm_twist_bf.key:
                # 有効な前後のキー
                prev_arm_twist_fno, next_arm_twist_fno = data_set.motion.get_bone_prev_next_fno(arm_twist_bone_name, fno, is_key=True)
                # 前後のキーフレ
                prev_arm_twist_bf = data_set.motion.calc_bf(arm_twist_bone_name, prev_arm_twist_fno)
                next_arm_twist_bf = data_set.motion.calc_bf(arm_twist_bone_name, next_arm_twist_fno)
                # 補間曲線を元に間を埋める
                now_arm_twist_qq = data_set.motion.calc_bf_rot(prev_arm_twist_bf, arm_twist_bf, next_arm_twist_bf)
            else:
                now_arm_twist_qq = arm_twist_bf.rotation

            # 削除前後の差
            arm_twist_cancel_qq = now_arm_twist_qq.inverted() * arm_twist_bf.org_rotation

            # 手捩りの削除後（強制補間曲線再計算後）の値
            wrist_twist_bf = data_set.motion.calc_bf(wrist_twist_bone_name, fno)
            if not wrist_twist_bf.key:
                # 有効な前後のキー
                prev_wrist_twist_fno, next_wrist_twist_fno = data_set.motion.get_bone_prev_next_fno(wrist_twist_bone_name, fno, is_key=True)
                # 前後のキーフレ
                prev_wrist_twist_bf = data_set.motion.calc_bf(wrist_twist_bone_name, prev_wrist_twist_fno)
                next_wrist_twist_bf = data_set.motion.calc_bf(wrist_twist_bone_name, next_wrist_twist_fno)
                # 補間曲線を元に間を埋める
                now_wrist_twist_qq = data_set.motion.calc_bf_rot(prev_wrist_twist_bf, wrist_twist_bf, next_wrist_twist_bf)
            else:
                now_wrist_twist_qq = wrist_twist_bf.rotation

            # 腕捩りのキャンセルを行った手捩りの回転
            wrist_recancel_qq = arm_twist_cancel_qq * now_wrist_twist_qq

            logger.debug("再チェック f: %s, %s: 腕捩: 前: %s, 後: %s, 差: %s, 手捩: 前: %s, 後: %s, %s", fno, arm_twist_bone_name, arm_twist_bf.org_rotation.toDegree(), \
                         now_arm_twist_qq.toDegree(), arm_twist_cancel_qq.toDegree(), now_wrist_twist_qq.toDegree(), wrist_recancel_qq.toDegree(), wrist_recancel_qq)

            # 軸に基いた角度で再計算
            wrist_twist_bf.rotation = MQuaternion.fromAxisAndAngle(wrist_twist_local_x_axis, wrist_recancel_qq.toDegree() * (np.sign(wrist_recancel_qq.x() * -1)))
            wrist_twist_bf.key = True
            data_set.motion.bones[wrist_twist_bone_name][fno] = wrist_twist_bf

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 捩り分散のPool内処理
    def spread_twist_pool(self, data_set_idx: int, fno_idx: int, fno: int, last_fno: int, arm_bone_name: str, arm_twist_bone_name: str, elbow_bone_name: str, \
                          wrist_twist_bone_name: str, wrist_bone_name: str, arm_local_x_axis: str, arm_twist_local_x_axis: MVector3D, elbow_local_x_axis: MVector3D, \
                          elbow_local_y_axis: MVector3D, wrist_twist_local_x_axis: MVector3D, wrist_local_x_axis: MVector3D, wrist_local_y_axis: MVector3D, log_target_idxs: list):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            logger.test("f: %s start -------------", fno)

            # 各ボーンのbf（補間曲線リセットなし）
            arm_bf = data_set.motion.calc_bf(arm_bone_name, fno)
            arm_twist_bf = data_set.motion.calc_bf(arm_twist_bone_name, fno)
            elbow_bf = data_set.motion.calc_bf(elbow_bone_name, fno)
            wrist_twist_bf = data_set.motion.calc_bf(wrist_twist_bone_name, fno)
            wrist_bf = data_set.motion.calc_bf(wrist_bone_name, fno)

            # 回転をローカル軸で分離
            arm_x_qq, arm_y_qq, arm_z_qq, arm_yz_qq = MServiceUtils.separate_local_qq(fno, arm_bone_name, arm_bf.rotation, arm_local_x_axis)
            elbow_x_qq, elbow_y_qq, elbow_z_qq, elbow_yz_qq = MServiceUtils.separate_local_qq(fno, elbow_bone_name, elbow_bf.rotation, elbow_local_x_axis)
            wrist_x_qq, wrist_y_qq, wrist_z_qq, wrist_yz_qq = MServiceUtils.separate_local_qq(fno, wrist_bone_name, wrist_bf.rotation, wrist_local_x_axis)

            logger.test("f: %s, %s: total: %s", fno, arm_bone_name, arm_bf.rotation.toEulerAngles())
            logger.test("f: %s, %s: x: %s", fno, arm_bone_name, arm_x_qq.toEulerAngles())
            logger.test("f: %s, %s: y: %s", fno, arm_bone_name, arm_y_qq.toEulerAngles())
            logger.test("f: %s, %s: z: %s", fno, arm_bone_name, arm_z_qq.toEulerAngles())
            logger.test("f: %s, %s: yz: %s", fno, arm_bone_name, arm_yz_qq.toEulerAngles())
            logger.test("f: %s, %s: total: %s", fno, elbow_bone_name, elbow_bf.rotation.toEulerAngles())
            logger.test("f: %s, %s: x: %s", fno, elbow_bone_name, elbow_x_qq.toEulerAngles())
            logger.test("f: %s, %s: y: %s", fno, elbow_bone_name, elbow_y_qq.toEulerAngles())
            logger.test("f: %s, %s: z: %s", fno, elbow_bone_name, elbow_z_qq.toEulerAngles())
            logger.test("f: %s, %s: yz: %s", fno, elbow_bone_name, elbow_yz_qq.toEulerAngles())
            logger.test("f: %s, %s: total: %s", fno, wrist_bone_name, wrist_bf.rotation.toEulerAngles())
            logger.test("f: %s, %s: x: %s", fno, wrist_bone_name, wrist_x_qq.toEulerAngles())
            logger.test("f: %s, %s: y: %s", fno, wrist_bone_name, wrist_y_qq.toEulerAngles())
            logger.test("f: %s, %s: z: %s", fno, wrist_bone_name, wrist_z_qq.toEulerAngles())
            logger.test("f: %s, %s: yz: %s", fno, wrist_bone_name, wrist_yz_qq.toEulerAngles())

            # 腕YZを腕に
            arm_result_qq = arm_yz_qq

            # 通常はひじYZ回転をひじボーンの順回転として扱う
            # FIXME 逆肘考慮
            elbow_result_qq = MQuaternion.fromAxisAndQuaternion(elbow_local_y_axis, elbow_yz_qq)
            
            # 腕捩り -------------------------

            # 腕Xを腕捩りに適用させる
            arm_x_twisted_qq = MQuaternion.fromAxisAndQuaternion(arm_twist_local_x_axis, arm_x_qq)

            # 腕捩りの回転量を取得する
            arm_twist_result_dot, arm_twist_result_qq = self.calc_twist_qq(data_set_idx, fno, arm_twist_bone_name, None, None, None, None, None, \
                                                                           arm_local_x_axis, arm_bf.rotation, arm_result_qq, \
                                                                           arm_twist_local_x_axis, arm_twist_bf.rotation, arm_x_twisted_qq, \
                                                                           elbow_local_x_axis, elbow_local_y_axis, elbow_bf.rotation, elbow_result_qq)
            logger.debug("f: %s, %s: 腕捩り: dot: %s, degree: %s, %s", fno, arm_twist_bone_name, arm_twist_result_dot, arm_twist_result_qq.toDegree(), arm_twist_result_qq)

            # 手首YZ回転を手首に
            wrist_result_qq = wrist_bf.rotation

            # ひじXを手捻りに
            wrist_x_twisted_qq = MQuaternion.fromAxisAndQuaternion(wrist_twist_local_x_axis, elbow_x_qq)
            logger.test("f: %s, %s: ひじX: %s", fno, wrist_twist_bone_name, wrist_x_twisted_qq)

            # 手首Xを手捻りに
            wrist_x_twisted_qq *= MQuaternion.fromAxisAndQuaternion(wrist_twist_local_x_axis, wrist_x_qq)
            logger.test("f: %s, %s: 手首X: %s", fno, wrist_twist_bone_name, wrist_x_twisted_qq)

            # 手捩りの回転量を取得する
            wrist_twist_result_dot, wrist_twist_result_qq = self.calc_twist_qq(data_set_idx, fno, wrist_twist_bone_name, arm_local_x_axis, arm_bf.rotation, arm_result_qq, \
                                                                               arm_twist_bf.rotation, arm_twist_result_qq, \
                                                                               elbow_local_x_axis, elbow_bf.rotation, elbow_result_qq, \
                                                                               wrist_twist_local_x_axis, wrist_twist_bf.rotation, wrist_x_twisted_qq, \
                                                                               wrist_local_x_axis, wrist_local_y_axis, wrist_bf.rotation, wrist_result_qq)
            logger.debug("f: %s, %s: 手捩り: dot: %s, degree: %s, %s", fno, wrist_twist_bone_name, wrist_twist_result_dot, wrist_twist_result_qq.toDegree(), wrist_twist_result_qq)

            # 全て登録
            arm_bf.rotation = arm_result_qq
            arm_bf.key = True
            data_set.motion.bones[arm_bone_name][fno] = arm_bf

            arm_twist_bf.rotation = arm_twist_result_qq
            # 腕捩りの元の回転量として別保持
            arm_twist_bf.org_rotation = arm_twist_result_qq.copy()
            arm_twist_bf.key = True
            data_set.motion.bones[arm_twist_bone_name][fno] = arm_twist_bf

            elbow_bf.rotation = elbow_result_qq
            elbow_bf.key = True
            data_set.motion.bones[elbow_bone_name][fno] = elbow_bf

            wrist_twist_bf.rotation = wrist_twist_result_qq
            wrist_twist_bf.key = True
            data_set.motion.bones[wrist_twist_bone_name][fno] = wrist_twist_bf

            wrist_bf.rotation = wrist_result_qq
            wrist_bf.key = True
            data_set.motion.bones[wrist_bone_name][fno] = wrist_bf

            if fno in log_target_idxs and last_fno > 0:
                logger.info("-- %sフレーム目:終了(%s％)【No.%s - 捩り分散 - %s】", fno, round((fno / last_fno) * 100, 3), data_set_idx + 1, arm_twist_bone_name)

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 捩りの回転量を計算する
    def calc_twist_qq(self, data_set_idx: int, fno: int, bone_name: str, grand_parent_x_axis: MVector3D, original_grand_parent_qq: MQuaternion, \
                      grand_parent_qq: MQuaternion, original_grand_parent_twist_qq: MQuaternion, grand_parent_twist_qq: MQuaternion, \
                      parent_x_axis: MVector3D, original_parent_qq: MQuaternion, parent_qq: MQuaternion, \
                      twist_x_axis: MVector3D, original_twist_qq: MQuaternion, twist_qq: MQuaternion, \
                      child_x_axis: MVector3D, child_y_axis: MVector3D, original_child_qq: MQuaternion, child_qq: MQuaternion):

        # ローカル座標系（ボーンベクトルが（1，0，0）になる空間）の向き
        local_x_axis = MVector3D(1, 0, 0)

        # グローバル座標系（Ａスタンス）からローカル座標系（ボーンベクトルが（1，0，0）になる空間）への変換
        child_global2local_qq = MQuaternion.rotationTo(child_x_axis, local_x_axis)

        # 軸制限のローカル座標に変換
        original_mat = MMatrix4x4()                     # オリジナルの回転量に基づく移動量
        original_mat.setToIdentity()                    # 初期化
        original_mat.rotate(original_child_qq)          # 元々のひじ・手首の回転量
        original_mat.rotate(child_global2local_qq)      # グローバルからローカルへ
        original_mat.translate(local_x_axis)            # ローカルX軸方向の移動量
        original_vec = original_mat * MVector3D()       # ベクトル算出
        original_vec.setX(0)                            # Xの捩りは潰す

        separated_mat = MMatrix4x4()                    # 分散後の回転量に基づく移動量
        separated_mat.setToIdentity()                   # 初期化
        separated_mat.rotate(child_qq)                  # ひじ・手首の回転量
        separated_mat.rotate(child_global2local_qq)     # グローバルからローカルへ
        separated_mat.translate(local_x_axis)           # ローカルX軸方向の移動量
        separated_vec = separated_mat * MVector3D()     # ベクトル算出
        separated_vec.setX(0)                           # Xの捩りは潰す

        # 分散後の回転量からオリジナルの回転量に戻すだけの回転量
        local_qq = MQuaternion.rotationTo(separated_vec.normalized(), original_vec.normalized())
        
        # グローバル軸に戻す
        # global_qq = original_twist_qq * twist_qq * local_qq
        total_degree = twist_qq.toDegree() + local_qq.toDegree()    # original_twist_qq.toDegree()
        total_qq = MQuaternion.fromAxisAndAngle(twist_x_axis, total_degree)
        logger.debug("f: %s, 生成: %s, total_degree: %s", fno, bone_name, total_degree)

        logger.test("fno: %s, original_twist_qq: %s, %s", fno, original_twist_qq.toDegree(), original_twist_qq)
        logger.test("fno: %s, twist_qq: %s, %s", fno, twist_qq.toDegree(), twist_qq)
        logger.test("fno: %s, local_qq: %s, %s", fno, local_qq.toDegree(), local_qq)
        # logger.test("fno: %s, global_qq: %s, %s", fno, global_qq.toDegree(), global_qq)
        logger.test("fno: %s, total_qq: %s, %s", fno, total_qq.toDegree(), total_qq)

        original_mat = MMatrix4x4()                     # オリジナルの回転量に基づく移動量
        original_mat.setToIdentity()                    # 初期化

        # 手捩りの場合、腕まで見る
        if grand_parent_x_axis:
            original_mat.rotate(original_grand_parent_qq)           # 元々の腕の回転量
            original_mat.rotate(original_grand_parent_twist_qq)     # 元々の腕捩りの回転量
            original_mat.translate(grand_parent_x_axis)             # 腕のX軸方向

        original_mat.rotate(original_parent_qq)         # 元々の腕・ひじの回転量
        original_mat.rotate(original_twist_qq)          # 元々の腕捩り・手捩りの回転量
        original_mat.translate(parent_x_axis)           # 腕・ひじのX軸方向
        original_mat.rotate(original_child_qq)          # 元々のひじ・手首の回転量
        
        # 手捩りの場合、Y軸でチェック
        if grand_parent_x_axis:
            original_vec = original_mat * child_y_axis      # 手首のY軸方向
        else:
            original_vec = original_mat * child_x_axis      # ひじのX軸方向

        max_dot = 0
        max_degree = 0

        # 捩りの計算が取れなかった場合、再計算してひじ・手首の位置を確認する
        # 1度単位
        max_dot, max_degree = self.test_twist_qq(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                 parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, \
                                                 child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec, \
                                                 total_degree, max_dot, max_degree, np.asarray([(x, -x) for x in range(0, 31, 1)]).flatten())

        if max_dot > RADIANS_2:
            return max_dot, MQuaternion.fromAxisAndAngle(twist_x_axis, max_degree)

        # 30度範囲でチェック(前のチェックは破棄)
        max_dot, max_degree = self.test_twist_qq(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                 parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, \
                                                 child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec, \
                                                 total_degree, max_dot, max_degree, np.asarray([(x, -x) for x in range(0, 181, 10)]).flatten())

        if max_dot > RADIANS_2:
            return max_dot, MQuaternion.fromAxisAndAngle(twist_x_axis, max_degree)

        # 1度単位
        total_degree = max_degree
        max_dot, max_degree = self.test_twist_qq(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                 parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, \
                                                 child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec, \
                                                 total_degree, max_dot, max_degree, np.asarray([(x, -x) for x in range(1, 21, 1)]).flatten())

        if max_dot > RADIANS_2:
            return max_dot, MQuaternion.fromAxisAndAngle(twist_x_axis, max_degree)

        # 整数で取れなかった場合、小数まで割って調べる
        total_degree = max_degree
        max_dot, max_degree = self.test_twist_qq(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                 parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, \
                                                 child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec, \
                                                 total_degree, max_dot, max_degree, np.asarray([(x * 0.1, -x * 0.1) for x in range(1, 11)]).flatten())

        if max_dot > RADIANS_8:
            return max_dot, MQuaternion.fromAxisAndAngle(twist_x_axis, max_degree)

        # 最後まで近似が取れなかった場合最も近いの
        logger.warning("【No.%s】%sフレーム目:%s捩り分散失敗: 角度: %s 近似度: %s", (data_set_idx + 1), fno, bone_name, round(max_degree, 3), round(max_dot, 5))
        return max_dot, MQuaternion.fromAxisAndAngle(twist_x_axis, max_degree)

    def test_twist_qq(self, fno: int, bone_name: str, grand_parent_x_axis: MVector3D, grand_parent_qq: MQuaternion, grand_parent_twist_qq: MQuaternion, \
                      parent_x_axis: MVector3D, parent_qq: MQuaternion, twist_x_axis: MVector3D, original_twist_qq: MQuaternion, \
                      child_x_axis: MVector3D, child_y_axis: MVector3D, original_child_qq: MQuaternion, child_qq: MQuaternion, original_vec: MVector3D, \
                      total_degree: float, max_dot: float, max_degree: float, degree_range: list):
        
        for n, append_degree in enumerate(degree_range):
            # 正＋方向の捩り角度
            max_dot, max_degree = self.test_twist_qq_inner(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                           parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, \
                                                           child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec, \
                                                           0, max_dot, max_degree, total_degree + append_degree)

            if max_dot > RADIANS_2:
                # 充分に近似している場合、このまま終了
                logger.debug("f: %s, %s, 確定 max_dot: %s, total_degree: %s, append_degree: %s, test_degree: %s, (正＋)", fno, bone_name, max_dot, total_degree, append_degree, max_degree)
                return max_dot, max_degree

            # 正－方向の捩り角度
            max_dot, max_degree = self.test_twist_qq_inner(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                           parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, \
                                                           child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec, \
                                                           0, max_dot, max_degree, total_degree - append_degree)

            if max_dot > RADIANS_2:
                # 充分に近似している場合、このまま終了
                logger.debug("f: %s, %s, 確定 max_dot: %s, total_degree: %s, append_degree: %s, test_degree: %s, (正－)", fno, bone_name, max_dot, total_degree, append_degree, max_degree)
                return max_dot, max_degree

            # 逆＋方向の捩り角度
            max_dot, max_degree = self.test_twist_qq_inner(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                           parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, \
                                                           child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec, \
                                                           0, max_dot, max_degree, -total_degree + append_degree)

            if max_dot > RADIANS_2:
                # 充分に近似している場合、このまま終了
                logger.debug("f: %s, %s, 確定 max_dot: %s, total_degree: %s, append_degree: %s, test_degree: %s, (逆＋)", fno, bone_name, max_dot, total_degree, append_degree, max_degree)
                return max_dot, max_degree

            # 逆－方向の捩り角度
            max_dot, max_degree = self.test_twist_qq_inner(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                           parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, \
                                                           child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec, \
                                                           0, max_dot, max_degree, -total_degree - append_degree)

            if max_dot > RADIANS_2:
                # 充分に近似している場合、このまま終了
                logger.debug("f: %s, %s, 確定 max_dot: %s, total_degree: %s, append_degree: %s, test_degree: %s, (逆－)", fno, bone_name, max_dot, total_degree, append_degree, max_degree)
                return max_dot, max_degree

        # 最後まで取れなければ、最大近似のを返す
        return max_dot, max_degree
        
    # 捩りの精査内部処理
    def test_twist_qq_inner(self, fno: int, bone_name: str, grand_parent_x_axis: MVector3D, grand_parent_qq: MQuaternion, grand_parent_twist_qq: MQuaternion, \
                            parent_x_axis: MVector3D, parent_qq: MQuaternion, twist_x_axis: MVector3D, original_twist_qq: MQuaternion, \
                            child_x_axis: MVector3D, child_y_axis: MVector3D, original_child_qq: MQuaternion, child_qq: MQuaternion, original_vec: MVector3D, \
                            total_degree: float, max_dot: float, max_degree: float, test_degree: float):
        
        twisted_dot, twist_degree, result_twist_qq = self.confirm_twist_qq(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                                           parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, test_degree, \
                                                                           child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec)
        logger.test("f: %s, %s, twisted_dot: %s, twist_degree: %s, result_twist_qq: %s", fno, bone_name, twisted_dot, twist_degree, result_twist_qq.toEulerAngles().to_log())
        
        if twisted_dot > RADIANS_2:
            # 充分に近似している場合、このまま終了
            return twisted_dot, twist_degree

        # 内積が近付いていたら上書き
        if max_dot < twisted_dot:
            max_dot = twisted_dot
            max_degree = twist_degree
        
        # 絶対値内積が近付いてたら反転
        if max_dot < abs(twisted_dot):
            test_degree = -test_degree
            twisted_dot, twist_degree, result_twist_qq = self.confirm_twist_qq(fno, bone_name, grand_parent_x_axis, grand_parent_qq, grand_parent_twist_qq, \
                                                                               parent_x_axis, parent_qq, twist_x_axis, original_twist_qq, test_degree, \
                                                                               child_x_axis, child_y_axis, original_child_qq, child_qq, original_vec)
            # logger.test("fno: %s, 正＋ append_degree: %s, twisted_dot: %s, result_twist_qq: %s, result_twist_qq: %s", \
            #             fno, append_degree, twisted_dot, result_twist_qq.toDegree(), result_twist_qq)
            
            if twisted_dot > RADIANS_2:
                # 充分に近似している場合、このまま終了
                return twisted_dot, twist_degree

            # 内積が近付いていたら上書き
            if max_dot < twisted_dot:
                max_dot = twisted_dot
                max_degree = twist_degree

        return max_dot, max_degree

    def confirm_twist_qq(self, fno: int, bone_name: str, grand_parent_x_axis: MVector3D, grand_parent_qq: MQuaternion, grand_parent_twist_qq: MQuaternion, \
                         parent_x_axis: MVector3D, parent_qq: MQuaternion, twist_x_axis: MVector3D, original_twist_qq: MQuaternion, twist_degree: float, \
                         child_x_axis: MVector3D, child_y_axis: MVector3D, original_child_qq: MQuaternion, child_qq: MQuaternion, original_vec: MVector3D):
        # twist_degree = twist_degree % (180 if np.sign(twist_x_axis.x()) == 1 else -180)
        
        result_twist_qq = MQuaternion.fromAxisAndAngle(twist_x_axis, twist_degree)
        # logger.test("fno: %s, total: %s, %s", fno, result_twist_qq.toDegree(), result_twist_qq)

        twisted_mat = MMatrix4x4()                      # 捩り分散後の回転量に基づく移動量
        twisted_mat.setToIdentity()                     # 初期化

        # 手捩りの場合、腕まで見る
        if grand_parent_x_axis:
            twisted_mat.rotate(grand_parent_qq)             # 腕の回転量
            twisted_mat.rotate(grand_parent_twist_qq)       # 腕捩りの回転量
            twisted_mat.translate(grand_parent_x_axis)      # 腕のX軸方向

        twisted_mat.rotate(parent_qq)                   # 腕・ひじの回転量
        twisted_mat.rotate(result_twist_qq)             # 腕捩り・手捩りの回転量
        twisted_mat.translate(parent_x_axis)            # 腕・ひじのX軸方向
        twisted_mat.rotate(child_qq)                    # 元々のひじ・手首の回転量

        # 手捩りの場合、Y軸でチェック
        if grand_parent_x_axis:
            twisted_vec = twisted_mat * child_y_axis        # 手首のY軸方向
        else:
            twisted_vec = twisted_mat * child_x_axis        # ひじのX軸方向

        # 捩り分散後との差
        twisted_dot = MVector3D.dotProduct(original_vec.normalized(), twisted_vec.normalized())

        return twisted_dot, twist_degree, result_twist_qq

    # 足ＩＫ補正
    def adjust_leg_ik_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("足ＩＫ補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="leg_ik{0}".format(data_set_idx), max_workers=min(2, self.options.max_workers)) as executor:
            for direction in ["左", "右"]:
                futures.append(executor.submit(self.adjust_leg_ik_stance_lr, data_set_idx, direction))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        return True
                 
    # 足ＩＫ補正
    def adjust_leg_ik_stance_lr(self, data_set_idx: int, direction: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            # 足ＩＫ調整に必要なボーン群(足IK親は必須としない)
            leg_ik_target_bones = ["{0}足ＩＫ".format(direction), "{0}足".format(direction), "下半身"]

            if set(leg_ik_target_bones).issubset(data_set.org_model.bones) and set(leg_ik_target_bones).issubset(data_set.rep_model.bones):
                prev_sep_fno = 0
                # 足ＩＫのそれぞれでフレーム番号をチェックする
                for target_bone_name in ["{0}足ＩＫ".format(direction)]:
                    if target_bone_name in data_set.org_model.bones and target_bone_name in data_set.rep_model.bones and target_bone_name in data_set.motion.bones:
                        # ボーンとモーションが揃ってある場合のみ補正

                        logger.info("%s補正【No.%s】", target_bone_name, (data_set_idx + 1))

                        org_ik_root_bone_name = data_set.org_model.bone_indexes[data_set.org_model.bones[target_bone_name].ik.link[-1].bone_index]
                        rep_ik_root_bone_name = data_set.rep_model.bone_indexes[data_set.rep_model.bones[target_bone_name].ik.link[-1].bone_index]
                    
                        # 足IKの長さ比率
                        leg_ratio = MVector3D(data_set.original_xz_ratio, data_set.original_y_ratio, data_set.original_xz_ratio)
                        
                        # # 足から見た、足IKの位置差異
                        # org_leg_diff = ((data_set.org_model.bones["下半身"].position - data_set.org_model.bones[org_ik_root_bone_name].position) * leg_ratio)
                        # rep_leg_diff = data_set.rep_model.bones["下半身"].position - data_set.rep_model.bones[rep_ik_root_bone_name].position
                        # # 足IKの差分
                        # leg_diff = rep_leg_diff - org_leg_diff
                        
                        org_ik_root_links = data_set.org_model.create_link_2_top_one(org_ik_root_bone_name)
                        rep_ik_root_links = data_set.rep_model.create_link_2_top_one(rep_ik_root_bone_name)
                                        
                        org_leg_ik_links = data_set.org_model.create_link_2_top_one(target_bone_name)
                        rep_leg_ik_links = data_set.rep_model.create_link_2_top_one(target_bone_name)

                        # 初期立ち位置の足IKのグローバル位置と行列
                        _, rep_initial_leg_ik_matrixs = MServiceUtils.calc_global_pos(data_set.rep_model, rep_leg_ik_links, VmdMotion(), 0, return_matrix=True)

                        fnos = data_set.motion.get_bone_fnos(target_bone_name)
                        for fno_idx, fno in enumerate(fnos):
                            # 足ＩＫのbf
                            ik_bf = data_set.motion.calc_bf(target_bone_name, fno)
                            
                            # 処理対象ボーンまでの位置とグローバル座標
                            org_ik_root_global_3ds = MServiceUtils.calc_global_pos(data_set.org_model, org_ik_root_links, data_set.org_motion, fno)
                            org_leg_ik_global_3ds = MServiceUtils.calc_global_pos(data_set.org_model, org_leg_ik_links, data_set.org_motion, fno)

                            # 先リンク元（足ボーン）
                            rep_ik_root_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, rep_ik_root_links, data_set.motion, fno)
                            rep_leg_ik_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, rep_leg_ik_links, data_set.motion, fno)

                            # 足ボーンから見た、処理対象足IKボーンの親のローカル位置

                            # 元モデル
                            # 足IKのグローバル位置
                            org_global_leg_ik_pos = org_leg_ik_global_3ds[target_bone_name]
                            
                            # 足ボーンのローカル座標系
                            org_leg_matrix = MMatrix4x4()
                            org_leg_matrix.setToIdentity()
                            org_leg_matrix.translate(org_ik_root_global_3ds[org_ik_root_bone_name])

                            # 足ボーンから見た足IKのローカル位置
                            org_local_leg_ik_pos = org_leg_matrix.inverted() * org_global_leg_ik_pos

                            logger.debug("f: %s, %s, org_global_leg_ik_pos: %s, org_ik_root_pos: %s, org_local_leg_ik_pos: %s", fno, target_bone_name, \
                                         org_global_leg_ik_pos.to_log(), org_ik_root_global_3ds[org_ik_root_bone_name].to_log(), org_local_leg_ik_pos.to_log())

                            # 先モデル
                            # 足IKのグローバル位置
                            rep_global_leg_ik_pos = rep_leg_ik_global_3ds[target_bone_name]

                            # 足ボーンのローカル座標系
                            rep_leg_matrix = MMatrix4x4()
                            rep_leg_matrix.setToIdentity()
                            rep_leg_matrix.translate(rep_ik_root_global_3ds[rep_ik_root_bone_name])
                            # 足IKの起点位置を、元に合わせた感じで計算する
                            # rep_leg_matrix.translate(leg_diff)

                            # # 足ボーンから見た足IKの本来のローカル位置
                            # original_rep_local_leg_ik_pos = rep_leg_matrix.inverted() * rep_global_leg_ik_pos

                            # 先モデルの足IKのローカル位置は、足の長さの縮尺
                            rep_local_leg_ik_pos = org_local_leg_ik_pos * leg_ratio
                            # # Yは元の位置そのまま
                            # rep_local_leg_ik_pos.setY(original_rep_local_leg_ik_pos.y())
                            # 先モデルの再計算した足IKグローバル座標
                            recalc_rep_global_leg_ik_pos = rep_leg_matrix * rep_local_leg_ik_pos

                            logger.debug("f: %s, %s, rep_global_leg_ik_pos: %s, rep_ik_root_pos: %s, rep_local_leg_ik_pos: %s", fno, target_bone_name, \
                                         rep_global_leg_ik_pos.to_log(), rep_ik_root_global_3ds[rep_ik_root_bone_name].to_log(), rep_local_leg_ik_pos.to_log())

                            # 足IKのローカル座標系
                            rep_leg_ik_matrix = rep_initial_leg_ik_matrixs[target_bone_name]
                            # IKの親から見た、計算後IKのローカル位置
                            rep_leg_ik_recalc_local_pos = rep_leg_ik_matrix.inverted() * recalc_rep_global_leg_ik_pos
                            rep_leg_ik_recalc_local_pos.setY(ik_bf.position.y())

                            logger.debug("f: %s, %s, 先IKローカル(計算前): %s, 先IKローカル(計算後): %s, 変更後IK: %s", fno, target_bone_name, \
                                         rep_local_leg_ik_pos.to_log(), rep_leg_ik_recalc_local_pos.to_log(), ik_bf.position.to_log())

                            # 計算後IKのローカル位置を加算
                            ik_bf.position = rep_leg_ik_recalc_local_pos

                            data_set.motion.regist_bf(ik_bf, target_bone_name, fno)
                            
                            if fno // 500 > prev_sep_fno and fnos[-1] > 0:
                                logger.info("-- %sフレーム目:終了(%s％)【No.%s - %s補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, target_bone_name)
                                prev_sep_fno = fno // 500

                logger.info("%s足ＩＫ補正:終了【No.%s】", direction, (data_set_idx + 1))
            else:
                logger.info("%s足ＩＫ補正: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", direction, (data_set_idx + 1), ", ".join(leg_ik_target_bones))

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # つま先ＩＫ補正
    def adjust_toe_ik_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("つま先ＩＫ補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="toe_ik{0}".format(data_set_idx), max_workers=min(2, self.options.max_workers)) as executor:
            for direction in ["左", "右"]:
                futures.append(executor.submit(self.adjust_toe_ik_stance_lr, data_set_idx, direction))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        return True
                 
    # つま先ＩＫ補正
    def adjust_toe_ik_stance_lr(self, data_set_idx: int, direction: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            toe_ik_bone_name = "{0}つま先ＩＫ".format(direction)
            leg_ik_bone_name = "{0}足ＩＫ".format(direction)
            ankle_bone_name = "{0}足首".format(direction)
            leg_bone_name = "{0}足".format(direction)

            # つま先ＩＫ調整に必要なボーン群
            toe_ik_target_bones = [toe_ik_bone_name, leg_ik_bone_name, ankle_bone_name, leg_bone_name]

            if set(toe_ik_target_bones).issubset(data_set.org_model.bones) and set(toe_ik_target_bones).issubset(data_set.rep_model.bones):
                prev_sep_fno = 0

                if toe_ik_bone_name in data_set.org_model.bones and toe_ik_bone_name in data_set.rep_model.bones \
                        and toe_ik_bone_name in data_set.motion.bones and data_set.motion.is_active_bones(toe_ik_bone_name):
                    # ボーンとモーションが揃ってある場合のみ補正

                    logger.info("%s補正【No.%s】", toe_ik_bone_name, (data_set_idx + 1))

                    org_toe_ik_links = data_set.org_model.create_link_2_top_one(toe_ik_bone_name)
                    org_leg_links = data_set.org_model.create_link_2_top_one(leg_bone_name)
                    leg_ik_parent_name = org_toe_ik_links.get(leg_ik_bone_name, offset=-1).name

                    # つま先と足IKのあるキーフレ
                    fnos = data_set.motion.get_bone_fnos(toe_ik_bone_name, leg_ik_bone_name)
                    fnos.extend(data_set.motion.get_differ_fnos((data_set_idx + 1), [toe_ik_bone_name], limit_degrees=10, limit_length=1))
                    fnos = sorted(list(set(fnos)))

                    for fno_idx, fno in enumerate(fnos):
                        # 足ＩＫのキーを追加しておく
                        leg_ik_bf = data_set.motion.calc_bf(leg_ik_bone_name, fno)
                        data_set.motion.regist_bf(leg_ik_bf, leg_ik_bone_name, fno)

                    for fno_idx, fno in enumerate(fnos):
                        # つま先ＩＫのbf
                        toe_ik_bf = data_set.motion.calc_bf(toe_ik_bone_name, fno)
                        # 足ＩＫのbf
                        leg_ik_bf = data_set.motion.calc_bf(leg_ik_bone_name, fno)
                        logger.debug("f: %s, %s, toe_ik_bf.rot: %s, leg_ik_bf.rot: %s", fno, toe_ik_bone_name, \
                                     toe_ik_bf.rotation.toEulerAngles().to_log(), leg_ik_bf.rotation.toEulerAngles().to_log())

                        if round(toe_ik_bf.position.x(), 2) == 0 and round(toe_ik_bf.position.y(), 2) == 0 and round(toe_ik_bf.position.z(), 2) == 0:
                            # つま先IKにキーがあっても値がなければスルー
                            continue

                        # 元モデルデータ --------

                        # 足ボーンまでの回転量
                        org_leg_direction_qq = MServiceUtils.calc_direction_qq(data_set.org_model, org_leg_links, data_set.org_motion, fno)

                        # 足ＩＫまでのグローバル座標と行列
                        org_target_global_3ds, org_target_toe_ik_matrixs \
                            = MServiceUtils.calc_global_pos(data_set.org_model, org_toe_ik_links, data_set.org_motion, fno, return_matrix=True)
                        # 足IKの親までのグローバル座標と行列
                        _, org_initial_toe_ik_matrixs \
                            = MServiceUtils.calc_global_pos(data_set.org_model, org_toe_ik_links, data_set.org_motion, fno, \
                                                            limit_links=org_toe_ik_links.from_links(leg_ik_parent_name), return_matrix=True)
                        # つま先IKまでの初期相対位置
                        org_initial_toe_trans_vs = MServiceUtils.calc_relative_position(data_set.org_model, org_toe_ik_links, data_set.org_motion, fno, \
                                                                                        limit_links=org_toe_ik_links.from_links(leg_ik_bone_name))

                        # つま先ＩＫのグローバル位置
                        org_target_global_toe_ik_pos = org_target_global_3ds[toe_ik_bone_name]

                        # 足IKまでの行列
                        org_initial_leg_ik_matrix = org_initial_toe_ik_matrixs[leg_ik_parent_name].copy()
                        # 足IKの回転を殺して、移動量のみで移動させる（足IKの回転を見ないことで、つま先IKのニュートラルな初期位置取得）
                        org_initial_leg_ik_matrix.translate(org_initial_toe_trans_vs[org_toe_ik_links.index(leg_ik_bone_name)])
                        # 足ボーンの向きを加味する
                        org_initial_leg_ik_matrix.rotate(org_leg_direction_qq)

                        # さらにつま先IKの移動量をかけて、つま先IKの初期グローバル位置を求める
                        org_initial_global_toe_ik_pos = org_initial_leg_ik_matrix * org_initial_toe_trans_vs[org_toe_ik_links.index(toe_ik_bone_name)]

                        # 足IKからみた初期つま先IKローカル位置
                        initial_local_toe_ik_pos = org_initial_leg_ik_matrix.inverted() * org_initial_global_toe_ik_pos
                        # 足IKからみた目標つま先IKローカル位置
                        target_local_toe_ik_pos = org_initial_leg_ik_matrix.inverted() * org_target_global_toe_ik_pos

                        toe_qq = MQuaternion.rotationTo(initial_local_toe_ik_pos, target_local_toe_ik_pos)
                        toe_qq.normalize()

                        logger.debug("f: %s, %s, org_initial_global_toe_ik_pos: %s, org_target_global_toe_ik_pos: %s, initial_local_toe_ik_pos: %s, target_local_toe_ik_pos: %s", fno, \
                                     toe_ik_bone_name, org_initial_global_toe_ik_pos.to_log(), org_target_global_toe_ik_pos.to_log(), \
                                     initial_local_toe_ik_pos.to_log(), target_local_toe_ik_pos.to_log())

                        logger.debug("f: %s, %s, leg_ik_bf.rotation: [%s], org_leg_direction_qq: [%s], toe_qq: [%s]", fno, \
                                     toe_ik_bone_name, leg_ik_bf.rotation.toEulerAngles().to_log(), org_leg_direction_qq.toEulerAngles().to_log(), toe_qq.toEulerAngles().to_log())

                        # つま先の向きを足ＩＫの回転に置き換え
                        leg_ik_bf.rotation = org_leg_direction_qq * toe_qq

                        # 計算後つま先ＩＫの移動をクリア
                        toe_ik_bf.position = MVector3D()

                        # 登録
                        data_set.motion.regist_bf(toe_ik_bf, toe_ik_bone_name, fno)
                        data_set.motion.regist_bf(leg_ik_bf, leg_ik_bone_name, fno)
                        
                        if fno // 500 > prev_sep_fno and fnos[-1] > 0:
                            logger.info("-- %sフレーム目:終了(%s％)【No.%s - %s補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, toe_ik_bone_name)
                            prev_sep_fno = fno // 500

                self.remove_unnecessary_bf_pool_parts(data_set_idx, leg_ik_bone_name, 0)
                self.remove_unnecessary_bf_pool_parts(data_set_idx, toe_ik_bone_name, 0)

                logger.info("%sつま先ＩＫ補正:終了【No.%s】", direction, (data_set_idx + 1))
            else:
                logger.info("%sつま先ＩＫ補正: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", direction, (data_set_idx + 1), ", ".join(toe_ik_target_bones))

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # つま先補正
    def adjust_toe_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("つま先補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="toe{0}".format(data_set_idx), max_workers=min(2, self.options.max_workers)) as executor:
            for direction in ["左", "右"]:
                futures.append(executor.submit(self.adjust_toe_stance_lr, data_set_idx, direction))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        return True
                 
    # つま先補正
    def adjust_toe_stance_lr(self, data_set_idx: int, direction: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            # つま先調整に必要なボーン群
            toe_target_bones = ["{0}足ＩＫ".format(direction), "{0}つま先ＩＫ".format(direction), "{0}足首".format(direction), "{0}つま先実体".format(direction), "{0}足底実体".format(direction)]

            if set(toe_target_bones).issubset(data_set.org_model.bones) and set(toe_target_bones).issubset(data_set.rep_model.bones):
                org_toe_links = data_set.org_model.create_link_2_top_one("{0}つま先実体".format(direction))
                rep_toe_links = data_set.rep_model.create_link_2_top_one("{0}つま先実体".format(direction))

                if direction == "左":
                    logger.debug("元：左つま先：%s", data_set.org_model.left_toe_vertex)
                    logger.debug("先：左つま先：%s", data_set.rep_model.left_toe_vertex)
                    logger.debug("元：左足底：%s", data_set.org_model.left_sole_vertex)
                    logger.debug("先：左足底：%s", data_set.rep_model.left_sole_vertex)
                else:
                    logger.debug("元：右つま先：%s", data_set.org_model.right_toe_vertex)
                    logger.debug("先：右つま先：%s", data_set.rep_model.right_toe_vertex)
                    logger.debug("元：右足底：%s", data_set.org_model.right_sole_vertex)
                    logger.debug("先：右足底：%s", data_set.rep_model.right_sole_vertex)

                org_toe_limit = data_set.org_model.bones["{0}足首".format(direction)].position.distanceToPoint(data_set.org_model.bones["{0}つま先実体".format(direction)].position)
                rep_toe_limit = data_set.rep_model.bones["{0}足首".format(direction)].position.distanceToPoint(data_set.rep_model.bones["{0}つま先実体".format(direction)].position)

                toe_limit_ratio = rep_toe_limit / org_toe_limit

                logger.info("%sつま先補正【No.%s】", direction, (data_set_idx + 1))
            
                prev_sep_fno = 0
                # 足ＩＫと足IK親の両方でフレーム番号をチェックする
                ik_bone_name = "{0}足ＩＫ".format(direction)
                fnos = data_set.motion.get_bone_fnos(ik_bone_name, "{0}足IK親".format(direction))
                for fno_idx, fno in enumerate(fnos):
                    # 足ＩＫのbf(この時点では登録するか分からないので、補間曲線リセットなし)
                    ik_bf = data_set.motion.calc_bf(ik_bone_name, fno)

                    # つま先と足底の位置
                    org_toe_pos, org_sole_pos = self.get_toe_entity(data_set_idx, data_set, data_set.org_model, data_set.org_motion, org_toe_links, ik_bone_name, fno)
                    rep_toe_pos, rep_sole_pos = self.get_toe_entity(data_set_idx, data_set, data_set.rep_model, data_set.motion, rep_toe_links, ik_bone_name, fno)

                    # つま先が元モデルの上にある場合、つま先を合わせて下に下ろす（実体を考慮する）
                    toe_diff = ((org_toe_pos.y() - data_set.org_model.bones["{0}つま先実体".format(ik_bone_name[0])].position.y()) * toe_limit_ratio) \
                        - (rep_toe_pos.y() - data_set.rep_model.bones["{0}つま先実体".format(ik_bone_name[0])].position.y()) \
                        + (data_set.rep_model.bones["{0}つま先実体".format(ik_bone_name[0])].position.y() - (data_set.org_model.bones["{0}つま先実体".format(ik_bone_name[0])].position.y() * toe_limit_ratio))
                    logger.test("f: %s, %s - toe_diff: %s", fno, ik_bone_name[0], toe_diff)
                    
                    # 足底が元モデルの上にある場合、足底を合わせて下に下ろす（実体を考慮する）
                    sole_diff = (rep_sole_pos.y() - data_set.rep_model.bones["{0}足底実体".format(ik_bone_name[0])].position.y()) \
                        - ((org_sole_pos.y() - data_set.org_model.bones["{0}足底実体".format(ik_bone_name[0])].position.y()) * toe_limit_ratio) \
                        + (data_set.rep_model.bones["{0}足底実体".format(ik_bone_name[0])].position.y() - (data_set.org_model.bones["{0}足底実体".format(ik_bone_name[0])].position.y() * toe_limit_ratio))
                    logger.test("f: %s, %s - sole_diff: %s", fno, ik_bone_name[0], sole_diff)

                    if rep_toe_pos.y() <= rep_sole_pos.y() and org_toe_pos.y() < org_toe_limit:
                        # 足底よりつま先のが下の場合（つま先立ち）
                        org_toe_diff = org_toe_pos.y() * toe_limit_ratio
                        rep_toe_diff = rep_toe_pos.y()
                        
                        # 足ＩＫを動かして、つま先の位置を合わせる
                        adjust_toe_y = ik_bf.position.y() + (org_toe_diff - rep_toe_diff)
                        ik_bf.position.setY(adjust_toe_y)
                        logger.debug("f: %s, %sつま先床補正: つま先合わせ つま先実体: %s, 足底実体: %s, 足IK: %s", ik_bf.fno, direction, rep_toe_pos.y(), rep_sole_pos.y(), adjust_toe_y)
                        # 登録対象
                        data_set.motion.regist_bf(ik_bf, "{0}足ＩＫ".format(direction), fno)
                    elif rep_sole_pos.y() < rep_toe_pos.y() and org_sole_pos.y() < org_toe_limit:
                        # 足先のがつま先より下の場合（接地）
                        org_sole_diff = (org_sole_pos.y() - data_set.org_model.bones["{0}足底実体".format(ik_bone_name[0])].position.y()) * toe_limit_ratio
                        rep_sole_diff = rep_sole_pos.y() - data_set.rep_model.bones["{0}足底実体".format(ik_bone_name[0])].position.y()
                        
                        # 足ＩＫを動かして、足底の位置を合わせる
                        adjust_sole_y = ik_bf.position.y() + (org_sole_diff - rep_sole_diff)
                        ik_bf.position.setY(adjust_sole_y)
                        logger.debug("f: %s, %s足底床補正: 足底合わせ 足底実体: %s, 足底実体: %s, 足IK: %s", ik_bf.fno, direction, rep_sole_pos.y(), rep_sole_pos.y(), adjust_sole_y)
                        # 登録対象
                        data_set.motion.regist_bf(ik_bf, "{0}足ＩＫ".format(direction), fno)
                    else:
                        # つま先補正なし
                        pass
                
                    if fno // 500 > prev_sep_fno and fnos[-1] > 0:
                        logger.info("-- %sフレーム目:終了(%s％)【No.%s - %sつま先補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, direction)
                        prev_sep_fno = fno // 500

                logger.info("%sつま先補正:終了【No.%s】", direction, (data_set_idx + 1))
            else:
                logger.info("%sつま先補正: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", direction, (data_set_idx + 1), ", ".join(toe_target_bones))

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # つま先実体のグローバル位置を取得する
    def get_toe_entity(self, data_set_idx: int, data_set: MOptionsDataSet, model: PmxModel, motion: VmdMotion, toe_links: BoneLinks, ik_bone_name: str, fno: int):
        toe_3ds = MServiceUtils.calc_global_pos(model, toe_links, motion, fno)

        logger.test(model.name)
        [logger.test("-- %s: %s", k, v) for k, v in toe_3ds.items()]

        toe_pos = toe_3ds["{0}つま先実体".format(ik_bone_name[0])]
        sole_pos = toe_3ds["{0}足底実体".format(ik_bone_name[0])]

        return toe_pos, sole_pos

    # センターXZ補正
    def adjust_center_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("センターXZ補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        # センター調整に必要なボーン群
        center_target_bones = ["センター", "上半身", "下半身", "左足ＩＫ", "右足ＩＫ", "左足", "右足"]

        if set(center_target_bones).issubset(data_set.org_model.bones) and set(center_target_bones).issubset(data_set.rep_model.bones) and "センター" in data_set.motion.bones:
            # 判定用のセンターボーン名（グルーブがある場合、グルーブまでを対象とする）
            org_center_bone_name = "グルーブ" if "グルーブ" in data_set.org_model.bones else "センター"
            rep_center_bone_name = "グルーブ" if "グルーブ" in data_set.rep_model.bones else "センター"

            # 元モデルのリンク生成
            org_center_links = data_set.org_model.create_link_2_top_one(org_center_bone_name)
            org_leg_ik_links = data_set.org_model.create_link_2_top_lr("足ＩＫ")
            org_upper_links = data_set.org_model.create_link_2_top_one("上半身")
            org_lower_links = data_set.org_model.create_link_2_top_one("下半身")
            org_leg_links = data_set.org_model.create_link_2_top_lr("足")

            # 変換先モデルのリンク生成
            rep_center_links = data_set.rep_model.create_link_2_top_one(rep_center_bone_name)
            rep_leg_ik_links = data_set.rep_model.create_link_2_top_lr("足ＩＫ")
            rep_upper_links = data_set.rep_model.create_link_2_top_one("上半身")
            rep_lower_links = data_set.rep_model.create_link_2_top_one("下半身")
            rep_leg_links = data_set.rep_model.create_link_2_top_lr("足")

            # 準備（細分化）
            self.prepare_split_stance(data_set_idx, data_set, "センター")

            logger.info("センターXZ補正: 準備終了【No.%s】", (data_set_idx + 1))

            prev_fno = 0
            fnos = data_set.motion.get_bone_fnos("センター")
            for fno in fnos:
                bf = data_set.motion.bones["センター"][fno]
                if bf.key:
                    logger.debug("f: %s, 調整前: %s", bf.fno, bf.position)
                    bf.position += self.calc_center_offset_by_leg_ik(bf, data_set_idx, data_set, \
                                                                     org_center_links, org_leg_ik_links, rep_center_links, rep_leg_ik_links, \
                                                                     org_center_bone_name, rep_center_bone_name)
                    logger.debug("f: %s, 足IKオフセット後: %s", bf.fno, bf.position)
                    bf.position += self.calc_center_offset_by_trunk(bf, data_set_idx, data_set, \
                                                                    org_center_links, org_upper_links, org_lower_links, org_leg_links, \
                                                                    rep_center_links, rep_upper_links, rep_lower_links, rep_leg_links, \
                                                                    org_center_bone_name, rep_center_bone_name)
                    logger.debug("f: %s, 体幹オフセット後: %s", bf.fno, bf.position)

                if fno // 500 > prev_fno and fnos[-1] > 0:
                    logger.info("-- %sフレーム目:終了(%s％)【No.%s - センターXZ補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1)
                    prev_fno = fno // 500

            logger.info("センターXZ補正: 終了【No.%s】", (data_set_idx + 1))
        else:
            logger.info("センターXZ補正: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", (data_set_idx + 1), ", ".join(center_target_bones))

    # センターY補正
    def adjust_center_arm_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("センターY補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        # センター調整に必要なボーン群（腕チェック済み）
        center_target_bones = ["センター", "上半身", "首根元"]

        if set(center_target_bones).issubset(data_set.org_model.bones) and set(center_target_bones).issubset(data_set.rep_model.bones) and "センター" in data_set.motion.bones:
            # 判定用のセンターボーン名（グルーブがある場合、グルーブまでを対象とする）
            org_center_bone_name = "グルーブ" if "グルーブ" in data_set.org_model.bones else "センター"
            rep_center_bone_name = "グルーブ" if "グルーブ" in data_set.rep_model.bones else "センター"

            # 元モデルのリンク生成
            org_center_links = data_set.org_model.create_link_2_top_one(org_center_bone_name)
            org_arm_links = data_set.org_model.create_link_2_top_lr("手首")

            # 変換先モデルのリンク生成
            rep_center_links = data_set.rep_model.create_link_2_top_one(rep_center_bone_name)
            rep_arm_links = data_set.rep_model.create_link_2_top_lr("手首")

            # 準備（細分化）
            self.prepare_split_stance(data_set_idx, data_set, "センター")

            logger.info("センターY補正: 準備終了【No.%s】", (data_set_idx + 1))

            prev_fno = 0
            fnos = data_set.motion.get_bone_fnos("センター")
            for fno in fnos:
                bf = data_set.motion.bones["センター"][fno]
                if bf.key:
                    logger.debug("f: %s, 調整前: %s", bf.fno, bf.position)
                    bf.position += self.calc_center_offset_by_arm(bf, data_set_idx, data_set, org_center_links, org_arm_links, \
                                                                  rep_center_links, rep_arm_links, org_center_bone_name, rep_center_bone_name)
                    logger.debug("f: %s, 腕オフセット後: %s", bf.fno, bf.position)

                if fno // 500 > prev_fno and fnos[-1] > 0:
                    logger.info("-- %sフレーム目:終了(%s％)【No.%s - センターY補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1)
                    prev_fno = fno // 500

            logger.info("センターY補正: 終了【No.%s】", (data_set_idx + 1))
        else:
            logger.info("センターY補正: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", (data_set_idx + 1), ", ".join(center_target_bones))

    # 足IKによるセンターオフセット値
    def calc_center_offset_by_arm(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                  org_center_links: BoneLinks, org_arm_links: BoneLinks, \
                                  rep_center_links: BoneLinks, rep_arm_links: BoneLinks, \
                                  org_center_bone_name: str, rep_center_bone_name: str):

        # 元モデルのセンターオフセット
        org_left_wrist_pos, org_right_wrist_pos, org_upper_pos, org_neck_base_pos = \
            self.calc_center_offset_by_arm_model(bf, data_set_idx, data_set, data_set.org_model, data_set.org_motion, \
                                                 org_center_links, org_arm_links, org_center_bone_name)
        logger.test("f: %s, org_left_wrist_pos: %s, org_right_wrist_pos: %s", bf.fno, org_left_wrist_pos, org_right_wrist_pos)

        # 先モデルのセンターオフセット
        rep_left_wrist_pos, rep_right_wrist_pos, rep_upper_pos, rep_neck_base_pos = \
            self.calc_center_offset_by_arm_model(bf, data_set_idx, data_set, data_set.rep_model, data_set.motion, \
                                                 rep_center_links, rep_arm_links, rep_center_bone_name)
        logger.test("f: %s, rep_left_wrist_pos: %s, rep_right_wrist_pos: %s", bf.fno, rep_left_wrist_pos, rep_right_wrist_pos)
        
        rep_center_arm_offset = MVector3D()

        # # 首が上半身よりも大体上の場合、座ってる可能性があるので調整しない
        # is_sit = org_neck_base_pos.y() * 1.2 > org_upper_pos.y()
        # # 腰が浮いている（上半身がちょっと上）の場合、
        # logger.debug("f: %s, org_neck_base_pos: %s, org_upper_pos: %s, is_sit: %s", bf.fno, org_neck_base_pos, org_upper_pos, is_sit)

        # 元モデルの床に近い方（Yが小さい方）が先モデルで床に潜ってる場合、センターの位置を元モデルも合わせる
        if org_left_wrist_pos.y() < org_right_wrist_pos.y() and rep_left_wrist_pos.y() < 0 < org_left_wrist_pos.y() * data_set.original_xz_ratio:
            rep_center_arm_offset.setY(org_left_wrist_pos.y() * data_set.original_xz_ratio - rep_left_wrist_pos.y())

        elif org_right_wrist_pos.y() < org_left_wrist_pos.y() and rep_right_wrist_pos.y() < 0 < org_right_wrist_pos.y() * data_set.original_xz_ratio:
            rep_center_arm_offset.setY(org_right_wrist_pos.y() * data_set.original_xz_ratio - rep_right_wrist_pos.y())

        return rep_center_arm_offset

    # モデル別足IKによるセンターオフセット値
    def calc_center_offset_by_arm_model(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                        model: PmxModel, motion: VmdMotion, \
                                        center_links: BoneLinks, arm_links: BoneLinks, center_bone_name: str):

        # 左手首までの位置
        left_arm_global_3ds, front_left_arm_global_3ds, left_arm_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, arm_links["左"], motion, bf.fno)

        # 右手首までの位置
        right_arm_global_3ds, front_right_arm_global_3ds, right_arm_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, arm_links["右"], motion, bf.fno)

        return left_arm_global_3ds["左手首"], right_arm_global_3ds["右手首"], right_arm_global_3ds["上半身"], right_arm_global_3ds["首根元"]

    # 足IKによるセンターオフセット値
    def calc_center_offset_by_leg_ik(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                     org_center_links: BoneLinks, org_leg_ik_links: BoneLinks, \
                                     rep_center_links: BoneLinks, rep_leg_ik_links: BoneLinks, \
                                     org_center_bone_name: str, rep_center_bone_name: str):

        # 元モデルのセンターオフセット
        org_front_center_ik_offset, org_center_direction_qq = \
            self.calc_center_offset_by_leg_ik_model(bf, data_set_idx, data_set, data_set.org_model, data_set.org_motion, \
                                                    org_center_links, org_leg_ik_links, org_center_bone_name)
        logger.test("f: %s, org_front_center_ik_offset: %s", bf.fno, org_front_center_ik_offset)

        # 先モデルのセンターオフセット
        rep_front_center_ik_offset, rep_center_direction_qq = \
            self.calc_center_offset_by_leg_ik_model(bf, data_set_idx, data_set, data_set.rep_model, data_set.motion, \
                                                    rep_center_links, rep_leg_ik_links, rep_center_bone_name)
        logger.test("f: %s, rep_front_center_ik_offset: %s", bf.fno, rep_front_center_ik_offset)
        
        # 元モデルに本来のXZ比率をかけて、それと先モデルの差をオフセットとする
        front_center_ik_offset = rep_front_center_ik_offset - (org_front_center_ik_offset * data_set.original_xz_ratio)
        logger.debug("f: %s, front_center_ik_offset: %s", bf.fno, front_center_ik_offset)

        # 回転を元に戻した位置
        rotated_center_3ds = MServiceUtils.calc_global_pos_by_direction(rep_center_direction_qq, {rep_center_bone_name: front_center_ik_offset})

        return rotated_center_3ds[rep_center_bone_name]

    # モデル別足IKによるセンターオフセット値
    def calc_center_offset_by_leg_ik_model(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                           model: PmxModel, motion: VmdMotion, \
                                           center_links: BoneLinks, leg_ik_links: BoneLinks, center_bone_name: str):

        # センターまでの位置
        center_global_3ds, front_center_global_3ds, center_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, center_links, motion, bf.fno)

        # 左足IKまでの位置
        left_leg_ik_global_3ds, front_left_leg_ik_global_3ds, left_leg_ik_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, leg_ik_links["左"], motion, bf.fno)

        # 右足IKまでの位置
        right_leg_ik_global_3ds, front_right_leg_ik_global_3ds, right_leg_ik_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, leg_ik_links["右"], motion, bf.fno)
        
        front_center_pos = front_center_global_3ds[center_bone_name]
        front_left_ik_pos = front_left_leg_ik_global_3ds["左足ＩＫ"]
        front_right_ik_pos = front_right_leg_ik_global_3ds["右足ＩＫ"]

        # 足IKの中間とセンターの差分をオフセットとする
        front_center_ik_offset = ((front_left_ik_pos + front_right_ik_pos) / 2 - front_center_pos)
        front_center_ik_offset.effective()
        front_center_ik_offset.setY(0)

        return front_center_ik_offset, center_direction_qq

    # 体幹によるセンターオフセット値
    def calc_center_offset_by_trunk(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                    org_center_links: BoneLinks, org_upper_links: BoneLinks, org_lower_links: BoneLinks, org_leg_links: BoneLinks, \
                                    rep_center_links: BoneLinks, rep_upper_links: BoneLinks, rep_lower_links: BoneLinks, rep_leg_links: BoneLinks, \
                                    org_center_bone_name: str, rep_center_bone_name: str):
        
        # 元モデルのセンター差分
        org_front_upper_center_diff, org_front_lower_center_diff, org_upper_direction_qq, org_lower_direction_qq = \
            self.calc_center_offset_by_trunk_model(bf, data_set_idx, data_set, data_set.org_model, data_set.org_motion, \
                                                   org_center_links, org_upper_links, org_lower_links, org_center_bone_name)
    
        # 先モデルのセンター差分
        rep_front_upper_center_diff, rep_front_lower_center_diff, rep_upper_direction_qq, rep_lower_direction_qq = \
            self.calc_center_offset_by_trunk_model(bf, data_set_idx, data_set, data_set.rep_model, data_set.motion, \
                                                   rep_center_links, rep_upper_links, rep_lower_links, rep_center_bone_name)
    
        # 上半身差分
        front_upper_center_diff = rep_front_upper_center_diff - (org_front_upper_center_diff * data_set.original_xz_ratio)
        logger.debug("f: %s, front_upper_center_diff: %s", bf.fno, front_upper_center_diff)
    
        # 下半身差分
        front_lower_center_diff = rep_front_lower_center_diff - (org_front_lower_center_diff * data_set.original_xz_ratio)
        logger.debug("f: %s, front_lower_center_diff: %s", bf.fno, front_lower_center_diff)

        # 元々の方向に向かせる
        rotated_upper_center_3ds = MServiceUtils.calc_global_pos_by_direction(rep_upper_direction_qq, {rep_center_bone_name: front_upper_center_diff})
        rotated_lower_center_3ds = MServiceUtils.calc_global_pos_by_direction(rep_lower_direction_qq, {rep_center_bone_name: front_lower_center_diff})

        # 差分の平均
        center_trunk_diff = (rotated_upper_center_3ds[rep_center_bone_name] + rotated_lower_center_3ds[rep_center_bone_name]) / 2
        center_trunk_diff.effective()
        center_trunk_diff.setY(0)
        logger.debug("f: %s, center_trunk_diff: %s", bf.fno, center_trunk_diff)

        return center_trunk_diff

    def calc_center_offset_by_trunk_model(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                          model: PmxModel, motion: VmdMotion, \
                                          center_links: BoneLinks, upper_links: BoneLinks, lower_links: BoneLinks, \
                                          center_bone_name: str):

        # センターまでの位置
        center_global_3ds, front_center_global_3ds, center_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, center_links, motion, bf.fno)
        
        # 上半身を原点として回った場合のモーション
        upper_motion = VmdMotion()
        for lidx, lname in enumerate(upper_links.all().keys()):
            calc_bf = motion.calc_bf(lname, bf.fno).copy()
            
            if lidx == 0:
                # SIZING_ROOTに上半身とセンターとのズレを加算する
                calc_bf.position += (model.bones["上半身"].position - model.bones["センター"].position)
                calc_bf.position.setY(0)
            
            upper_motion.bones[lname] = {bf.fno: calc_bf}

        # 上半身までの位置(センターを含む)
        upper_global_3ds, front_upper_global_3ds, upper_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, upper_links, upper_motion, bf.fno)

        # 上半身起点に基づくセンター差分
        front_upper_center_diff = front_center_global_3ds[center_bone_name] - front_upper_global_3ds[center_bone_name]

        # ---------------
        
        # 下半身を原点として回った場合のモーション
        lower_motion = VmdMotion()
        for lidx, lname in enumerate(lower_links.all().keys()):
            calc_bf = motion.calc_bf(lname, bf.fno).copy()
            
            if lidx == 0:
                # SIZING_ROOTに下半身とセンターとのズレを加算する
                calc_bf.position += (model.bones["下半身"].position - model.bones["センター"].position)
                calc_bf.position.setY(0)
            
            lower_motion.bones[lname] = {bf.fno: calc_bf}

        # 下半身までの位置(センターを含む)
        lower_global_3ds, front_lower_global_3ds, lower_direction_qq = \
            MServiceUtils.calc_front_global_pos(model, lower_links, lower_motion, bf.fno)

        # 下半身起点に基づくセンター差分
        front_lower_center_diff = front_center_global_3ds[center_bone_name] - front_lower_global_3ds[center_bone_name]

        return front_upper_center_diff, front_lower_center_diff, upper_direction_qq, lower_direction_qq

    # 上半身補正
    def adjust_upper_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("上半身補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        # 上半身調整に必要なボーン群
        upper_target_bones = ["上半身", "頭", "首", "左腕", "右腕"]

        # 上半身2調整に必要なボーン群
        upper2_target_bones = ["上半身", "上半身2", "頭", "首", "左腕", "右腕"]

        # モデルとモーション全部に上半身2がある場合、TRUE
        is_upper2_existed = set(upper2_target_bones).issubset(data_set.org_model.bones) and set(upper2_target_bones).issubset(data_set.rep_model.bones) \
            and "上半身2" in data_set.motion.bones and len(data_set.motion.bones["上半身2"]) > 1

        if set(upper_target_bones).issubset(data_set.org_model.bones) and set(upper_target_bones).issubset(data_set.rep_model.bones) and "上半身" in data_set.motion.bones:
            # 元モデルのリンク生成
            org_head_links = data_set.org_model.create_link_2_top_one("頭")
            org_upper_links = data_set.org_model.create_link_2_top_one("上半身")
            org_arm_links = data_set.org_model.create_link_2_top_lr("腕")

            # 変換先モデルのリンク生成
            rep_head_links = data_set.rep_model.create_link_2_top_one("頭")
            rep_upper_links = data_set.rep_model.create_link_2_top_one("上半身")
            rep_arm_links = data_set.rep_model.create_link_2_top_lr("腕")

            # 元モデルの上半身の傾き
            org_upper_slope = (data_set.org_model.bones["頭"].position - data_set.org_model.bones["上半身"].position).normalized()

            # 上半身からTO_BONEへの傾き
            rep_upper_slope = (data_set.rep_model.bones["頭"].position - data_set.rep_model.bones["上半身"].position).normalized()
            rep_upper_slope_up = MVector3D(-1, 0, 0)
            rep_upper_slope_cross = MVector3D.crossProduct(rep_upper_slope, rep_upper_slope_up).normalized()
            
            logger.test("上半身 slope: %s", rep_upper_slope)
            logger.test("上半身 cross: %s", rep_upper_slope_cross)

            # 上半身の傾き度合い - 0.1 を変化量の上限とする
            dot_limit = MVector3D.dotProduct(org_upper_slope.normalized(), rep_upper_slope.normalized()) - 0.1
            logger.debug("dot_limit: %s", dot_limit)

            # 初期傾き
            rep_upper_initial_slope_qq = MQuaternion.fromDirection(rep_upper_slope, rep_upper_slope_cross)

            # TOの長さ比率

            # 肩幅比率
            org_arm_diff = (org_arm_links["左"].get("左腕").position - org_arm_links["右"].get("右腕").position)
            rep_arm_diff = (rep_arm_links["左"].get("左腕").position - rep_arm_links["右"].get("右腕").position)
            arm_diff_ratio = rep_arm_diff / org_arm_diff
            arm_diff_ratio.one()    # 比率なので、0は1に変換する

            # TOの長さ比率
            org_to_diff = (org_head_links.get("頭").position - org_head_links.get("上半身").position)
            org_to_diff.one()
            rep_to_diff = (rep_head_links.get("頭").position - rep_head_links.get("上半身").position)
            rep_to_diff.one()
            to_diff_ratio = rep_to_diff / org_to_diff
            
            logger.test("arm_diff_ratio: %s", arm_diff_ratio)
            logger.test("to_diff_ratio: %s", to_diff_ratio)

            ratio = MVector3D(arm_diff_ratio.x(), to_diff_ratio.y(), arm_diff_ratio.x())

            # 初期状態の上半身2の傾き
            initial_bf = VmdBoneFrame(fno=0)
            initial_bf.set_name("上半身")
            initial_dataset = MOptionsDataSet(VmdMotion(), data_set.org_model, data_set.rep_model, data_set.output_vmd_path, data_set.detail_stance_flg, data_set.twist_flg, [], None, 0, [])

            self.calc_rotation_stance_trunk(initial_bf, data_set_idx, initial_dataset, \
                                            org_upper_links, org_head_links, org_arm_links, \
                                            rep_upper_links, rep_head_links, rep_arm_links, \
                                            "上半身", "頭", rep_upper_links.get("上半身", offset=-1).name, ratio, \
                                            rep_upper_initial_slope_qq, MQuaternion(), 0, "腕")

            # 内積
            dot = MVector3D.dotProduct(org_upper_slope.normalized(), rep_upper_slope.normalized())

            logger.info("【No.%s】上半身 - 向きの近似度: %s", (data_set_idx + 1), round(dot, 5))

            if dot >= 0.8:
                upper_initial_qq = initial_bf.rotation
                dot_limit = 0.9
            else:
                # 初期姿勢が違いすぎてる場合、初期姿勢を維持しない（四つ足等）
                upper_initial_qq = MQuaternion()
                dot_limit = 0

            logger.debug("dot: %s", dot)
            logger.debug("upper_initial_qq: %s", upper_initial_qq)
            logger.debug("dot_limit: %s", dot_limit)

            # 準備（細分化）
            self.prepare_split_stance(data_set_idx, data_set, "上半身")

            logger.info("上半身補正: 準備終了【No.%s】", (data_set_idx + 1))

            prev_fno = 0
            fnos = data_set.motion.get_bone_fnos("上半身")
            for fno_idx, fno in enumerate(fnos):
                upper_bf = data_set.motion.calc_bf("上半身", fno)

                self.calc_rotation_stance_trunk(upper_bf, data_set_idx, data_set, \
                                                org_upper_links, org_head_links, org_arm_links, \
                                                rep_upper_links, rep_head_links, rep_arm_links, \
                                                "上半身", "頭", rep_upper_links.get("上半身", offset=-1).name, ratio, \
                                                rep_upper_initial_slope_qq, upper_initial_qq, dot_limit, "腕")

                # bf登録
                data_set.motion.regist_bf(upper_bf, "上半身", fno)
                    
                if fno // 500 > prev_fno and fnos[-1] > 0:
                    logger.info("-- %sフレーム目:終了(%s％)【No.%s - 上半身補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1)
                    prev_fno = fno // 500

            # 子の角度調整
            self.adjust_rotation_by_parent(data_set_idx, data_set, "首", "上半身")
            self.adjust_rotation_by_parent(data_set_idx, data_set, "左腕", "上半身")
            self.adjust_rotation_by_parent(data_set_idx, data_set, "右腕", "上半身")

            logger.info("上半身補正: 終了【No.%s】", (data_set_idx + 1))

            if is_upper2_existed:
                # 上半身2がある場合
                # 元モデルのリンク生成
                org_head_links = data_set.org_model.create_link_2_top_one("頭")
                org_upper2_links = data_set.org_model.create_link_2_top_one("上半身2")

                # 変換先モデルのリンク生成
                rep_head_links = data_set.rep_model.create_link_2_top_one("頭")
                rep_upper2_links = data_set.rep_model.create_link_2_top_one("上半身2")

                # 元モデルの上半身2の傾き
                org_upper2_slope = (data_set.org_model.bones["頭"].position - data_set.org_model.bones["上半身2"].position).normalized()

                # 上半身からTO_BONEへの傾き
                rep_upper2_slope = (data_set.rep_model.bones["頭"].position - data_set.rep_model.bones["上半身2"].position).normalized()
                rep_upper2_slope_up = MVector3D(-1, 0, 0)
                rep_upper2_slope_cross = MVector3D.crossProduct(rep_upper2_slope, rep_upper2_slope_up).normalized()
                
                logger.test("上半身 slope: %s", rep_upper2_slope)
                logger.test("上半身 cross: %s", rep_upper2_slope_cross)

                rep_upper2_initial_slope_qq = MQuaternion.fromDirection(rep_upper2_slope, rep_upper2_slope_cross)

                # TOの長さ比率
                org_to_diff = (org_head_links.get("頭").position - org_head_links.get("上半身2").position)
                org_to_diff.one()
                rep_to_diff = (rep_head_links.get("頭").position - rep_head_links.get("上半身2").position)
                rep_to_diff.one()
                to_diff_ratio = rep_to_diff / org_to_diff
                
                logger.test("arm_diff_ratio: %s", arm_diff_ratio)
                logger.test("to_diff_ratio: %s", to_diff_ratio)

                ratio = MVector3D(arm_diff_ratio.x(), to_diff_ratio.y(), arm_diff_ratio.x())

                # 初期状態の上半身2の傾き
                initial_bf = VmdBoneFrame(fno=0)
                initial_bf.set_name("上半身2")
                initial_dataset = MOptionsDataSet(VmdMotion(), data_set.org_model, data_set.rep_model, data_set.output_vmd_path, data_set.detail_stance_flg, data_set.twist_flg, [], None, 0, [])

                self.calc_rotation_stance_trunk(initial_bf, data_set_idx, initial_dataset, \
                                                org_upper2_links, org_head_links, org_arm_links, \
                                                rep_upper2_links, rep_head_links, rep_arm_links, \
                                                "上半身2", "頭", rep_upper2_links.get("上半身2", offset=-1).name, ratio, \
                                                rep_upper2_initial_slope_qq, MQuaternion(), 0, "腕")

                # 内積
                dot = MVector3D.dotProduct(org_upper2_slope.normalized(), rep_upper2_slope.normalized())
                logger.info("【No.%s】上半身2 - 向きの近似度: %s", (data_set_idx + 1), round(dot, 5))

                if dot >= 0.8:
                    upper2_initial_qq = initial_bf.rotation
                    dot2_limit = 0.9
                else:
                    # 初期姿勢が違いすぎてる場合、初期姿勢を維持しない（四つ足等）
                    upper2_initial_qq = MQuaternion()
                    dot2_limit = 0

                logger.debug("dot: %s", dot)
                logger.debug("upper2_initial_qq: %s", upper2_initial_qq)
                logger.debug("dot2_limit: %s", dot2_limit)

                # 準備（細分化）
                self.prepare_split_stance(data_set_idx, data_set, "上半身2")

                logger.info("上半身2補正: 準備終了【No.%s】", (data_set_idx + 1))

                prev_fno = 0
                fnos = data_set.motion.get_bone_fnos("上半身2")
                for fno_idx, fno in enumerate(fnos):
                    upper2_bf = data_set.motion.calc_bf("上半身2", fno)

                    self.calc_rotation_stance_trunk(upper2_bf, data_set_idx, data_set, \
                                                    org_upper2_links, org_head_links, org_arm_links, \
                                                    rep_upper2_links, rep_head_links, rep_arm_links, \
                                                    "上半身2", "頭", rep_upper2_links.get("上半身2", offset=-1).name, ratio, \
                                                    rep_upper2_initial_slope_qq, upper2_initial_qq, dot2_limit, "腕")
                    # bf登録
                    data_set.motion.regist_bf(upper2_bf, "上半身2", fno)

                    if fno // 500 > prev_fno and fnos[-1] > 0:
                        logger.info("-- %sフレーム目:終了(%s％)【No.%s - 上半身2補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1)
                        prev_fno = fno // 500

                # 子の角度調整
                self.adjust_rotation_by_parent(data_set_idx, data_set, "首", "上半身2")
                self.adjust_rotation_by_parent(data_set_idx, data_set, "左腕", "上半身2")
                self.adjust_rotation_by_parent(data_set_idx, data_set, "右腕", "上半身2")

                logger.info("上半身2補正: 終了【No.%s】", (data_set_idx + 1))
        else:
            logger.info("上半身補正: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", (data_set_idx + 1), ", ".join(upper_target_bones))

    # 下半身補正
    def adjust_lower_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("下半身補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        # 下半身調整に必要なボーン群
        lower_target_bones = ["下半身", "足中間", "左足", "右足"]

        if set(lower_target_bones).issubset(data_set.org_model.bones) and set(lower_target_bones).issubset(data_set.rep_model.bones) and "下半身" in data_set.motion.bones:
            # 元モデルのリンク生成
            org_leg_center_links = data_set.org_model.create_link_2_top_one("足中間")
            org_lower_links = data_set.org_model.create_link_2_top_one("下半身")
            org_leg_links = data_set.org_model.create_link_2_top_lr("足")

            # 変換先モデルのリンク生成
            rep_leg_center_links = data_set.rep_model.create_link_2_top_one("足中間")
            rep_lower_links = data_set.rep_model.create_link_2_top_one("下半身")
            rep_leg_links = data_set.rep_model.create_link_2_top_lr("足")

            # 元モデルの下半身の傾き
            org_lower_slope = (data_set.org_model.bones["足中間"].position - data_set.org_model.bones["下半身"].position).normalized()

            # 下半身からTO_BONEへの傾き
            rep_lower_slope = (data_set.rep_model.bones["足中間"].position - data_set.rep_model.bones["下半身"].position).normalized()
            rep_lower_slope_up = MVector3D(-1, 0, 0)
            rep_lower_slope_cross = MVector3D.crossProduct(rep_lower_slope, rep_lower_slope_up).normalized()
            
            logger.test("下半身 slope: %s", rep_lower_slope)
            logger.test("下半身 cross: %s", rep_lower_slope_cross)

            # 下半身の傾き度合い - 0.1 を変化量の上限とする
            dot_limit = MVector3D.dotProduct(org_lower_slope.normalized(), rep_lower_slope.normalized()) - 0.1
            logger.debug("dot_limit: %s", dot_limit)

            # 初期傾き
            rep_lower_initial_slope_qq = MQuaternion.fromDirection(rep_lower_slope, rep_lower_slope_cross)

            # TOの長さ比率

            # 肩幅比率
            org_leg_diff = (org_leg_links["左"].get("左足").position - org_leg_links["右"].get("右足").position)
            rep_leg_diff = (rep_leg_links["左"].get("左足").position - rep_leg_links["右"].get("右足").position)
            leg_diff_ratio = rep_leg_diff / org_leg_diff
            leg_diff_ratio.non_zero()    # 比率なので、0は1に変換する

            # TOの長さ比率
            org_to_diff = (org_leg_center_links.get("足中間").position - org_leg_center_links.get("下半身").position)
            org_to_diff.non_zero()
            rep_to_diff = (rep_leg_center_links.get("足中間").position - rep_leg_center_links.get("下半身").position)
            rep_to_diff.non_zero()
            to_diff_ratio = rep_to_diff / org_to_diff
            
            logger.test("leg_diff_ratio: %s", leg_diff_ratio)
            logger.test("to_diff_ratio: %s", to_diff_ratio)

            ratio = MVector3D(leg_diff_ratio.x(), to_diff_ratio.y(), leg_diff_ratio.x())

            # 初期状態の下半身の傾き
            initial_bf = VmdBoneFrame(fno=0)
            initial_bf.set_name("下半身")
            initial_dataset = MOptionsDataSet(VmdMotion(), data_set.org_model, data_set.rep_model, data_set.output_vmd_path, data_set.detail_stance_flg, data_set.twist_flg, [], None, 0, [])

            self.calc_rotation_stance_trunk(initial_bf, data_set_idx, initial_dataset, \
                                            org_lower_links, org_leg_center_links, org_leg_links, \
                                            rep_lower_links, rep_leg_center_links, rep_leg_links, \
                                            "下半身", "足中間", rep_lower_links.get("下半身", offset=-1).name, ratio, \
                                            rep_lower_initial_slope_qq, MQuaternion(), 0, "足")

            # 内積
            dot = MVector3D.dotProduct(org_lower_slope.normalized(), rep_lower_slope.normalized())
            logger.info("【No.%s】下半身 - 向きの近似度: %s", (data_set_idx + 1), round(dot, 5))

            if dot >= 0.8:
                lower_initial_qq = initial_bf.rotation
                dot_limit = 0.9
            else:
                # 初期姿勢が違いすぎてる場合、初期姿勢を維持しない（四つ足等）
                lower_initial_qq = MQuaternion()
                dot_limit = 0

            logger.debug("dot: %s", dot)
            logger.debug("lower_initial_qq: %s", lower_initial_qq.toEulerAngles())
            logger.debug("dot_limit: %s", dot_limit)

            # 準備（細分化）
            self.prepare_split_stance(data_set_idx, data_set, "下半身")

            logger.info("下半身補正: 準備終了【No.%s】", (data_set_idx + 1))

            prev_fno = 0
            fnos = data_set.motion.get_bone_fnos("下半身")
            for fno_idx, fno in enumerate(fnos):
                lower_bf = data_set.motion.bones["下半身"][fno]

                self.calc_rotation_stance_trunk(lower_bf, data_set_idx, data_set, \
                                                org_lower_links, org_leg_center_links, org_leg_links, \
                                                rep_lower_links, rep_leg_center_links, rep_leg_links, \
                                                "下半身", "足中間", rep_lower_links.get("下半身", offset=-1).name, ratio, \
                                                rep_lower_initial_slope_qq, lower_initial_qq, dot_limit, "足")
                # bf登録
                data_set.motion.regist_bf(lower_bf, "下半身", fno)

                if fno // 500 > prev_fno and fnos[-1] > 0:
                    logger.info("-- %sフレーム目:終了(%s％)【No.%s - 下半身補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1)
                    prev_fno = fno // 500

            # 子の角度調整
            self.adjust_rotation_by_parent_ik(data_set_idx, data_set, "左足", "下半身", "左足ＩＫ")
            self.adjust_rotation_by_parent_ik(data_set_idx, data_set, "右足", "下半身", "右足ＩＫ")

            logger.info("下半身補正: 終了【No.%s】", (data_set_idx + 1))
        else:
            logger.info("下半身補正: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", (data_set_idx + 1), ", ".join(lower_target_bones))

    # 体幹スタンス補正
    def calc_rotation_stance_trunk(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                   org_from_links: BoneLinks, org_to_links: BoneLinks, org_arm_links: BoneLinks, \
                                   rep_from_links: BoneLinks, rep_to_links: BoneLinks, rep_arm_links: BoneLinks, \
                                   from_bone_name: str, to_bone_name: str, rep_parent_bone_name: str, ratio: MVector3D, \
                                   rep_initial_slope_qq: MQuaternion, cancel_qq: MQuaternion, dot_limit: float, up_name: str):
        logger.test("f: %s -----------------------------", bf.fno)

        # 基準より親の回転量
        parent_qq = MServiceUtils.calc_direction_qq(data_set.rep_model, rep_to_links.from_links(rep_parent_bone_name), data_set.motion, bf.fno)

        # -------------
        # TO位置の再計算

        # FROMボーンまでの位置
        org_from_global_3ds, org_front_from_global_3ds, org_from_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.org_model, org_from_links, data_set.org_motion, bf.fno, limit_links=org_from_links)
        rep_from_global_3ds, rep_front_from_global_3ds, rep_from_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.rep_model, rep_from_links, data_set.motion, bf.fno, limit_links=rep_from_links)

        # 正面向きのFROMボーンの位置
        org_front_from_pos = org_front_from_global_3ds[from_bone_name]
        rep_front_from_pos = rep_front_from_global_3ds[from_bone_name]

        # -------------

        # TOボーンまでの位置（フレームはFROMまでで、TO自身は初期値として求める）
        org_to_global_3ds, org_front_to_global_3ds, org_to_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.org_model, org_to_links, data_set.org_motion, bf.fno, limit_links=org_from_links)
        rep_to_global_3ds, rep_front_to_global_3ds, rep_to_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.rep_model, rep_to_links, data_set.motion, bf.fno, limit_links=rep_from_links)

        # TOボーンの正面位置
        org_front_to_pos = org_front_to_global_3ds[to_bone_name]
        rep_front_to_pos = rep_front_to_global_3ds[to_bone_name]

        # ---------------

        rep_front_to_x = rep_front_from_pos.x() + ((org_front_to_pos.x() - org_front_from_pos.x()) * ratio.x())
        rep_front_to_y = rep_front_from_pos.y() + ((org_front_to_pos.y() - org_front_from_pos.y()) * ratio.y())
        rep_front_to_z = rep_front_from_pos.z() + ((org_front_to_pos.z() - org_front_from_pos.z()) * ratio.z())

        logger.test("f: %s, re rep_front: x: %s, y: %s, z: %s", bf.fno, rep_front_to_x, rep_front_to_y, rep_front_to_z)

        logger.test("f: %s, rep_front_from_pos: %s", bf.fno, rep_front_from_pos)
        logger.test("f: %s, org_front_to_pos: %s", bf.fno, org_front_to_pos)
        logger.test("f: %s, org_front_from_pos: %s", bf.fno, org_front_from_pos)

        new_rep_front_to_pos = MVector3D(rep_front_to_x, rep_front_to_y, rep_front_to_z)
        logger.test("f: %s, 計算new_rep_front_to_pos: %s", bf.fno, new_rep_front_to_pos)
        logger.test("f: %s, 元rep_front_to_pos: %s", bf.fno, rep_front_to_pos)

        # 正面向きの新しいTO位置
        new_rep_front_to_global_3ds = {}
        new_rep_front_to_global_3ds[to_bone_name] = new_rep_front_to_pos

        # 回転を元に戻した位置
        rotated_to_3ds = MServiceUtils.calc_global_pos_by_direction(rep_to_direction_qq, new_rep_front_to_global_3ds)

        new_rep_to_pos = rotated_to_3ds[to_bone_name]
        rep_to_pos = rep_to_global_3ds[to_bone_name]
        rep_from_pos = rep_to_global_3ds[from_bone_name]

        # UP計算 ---------------

        # 左腕ボーンまでの位置
        org_left_arm_global_3ds = MServiceUtils.calc_global_pos(data_set.org_model, org_arm_links["左"], data_set.org_motion, bf.fno, org_from_links)
        org_left_arm_pos = org_left_arm_global_3ds["左{0}".format(up_name)]
        logger.test("f: %s, org_left_arm_pos: %s", bf.fno, org_left_arm_pos)

        # 右腕ボーンまでの位置
        org_right_arm_global_3ds = MServiceUtils.calc_global_pos(data_set.org_model, org_arm_links["右"], data_set.org_motion, bf.fno, org_from_links)
        org_right_arm_pos = org_right_arm_global_3ds["右{0}".format(up_name)]
        logger.test("f: %s, org_right_arm_pos: %s", bf.fno, org_right_arm_pos)
        
        up_pos = org_right_arm_pos - org_left_arm_pos

        # ---------------
        # FROMの回転量を再計算する
        direction = new_rep_to_pos - rep_from_pos
        up = MVector3D.crossProduct(direction, up_pos)
        from_orientation = MQuaternion.fromDirection(direction.normalized(), up.normalized())
        initial = rep_initial_slope_qq
        from_rotation = parent_qq.inverted() * from_orientation * initial.inverted() * cancel_qq.inverted()
        from_rotation.normalize()
        logger.test("f: %s, rep_from_pos(%s): %s", bf.fno, from_bone_name, rep_from_pos)
        logger.test("f: %s, rep_to_pos(%s): %s, 元: %s", bf.fno, to_bone_name, new_rep_to_pos, rep_to_pos)
        logger.test("f: %s, up_pos: %s", bf.fno, up_pos)
        logger.test("f: %s, direction(%s): %s", bf.fno, to_bone_name, direction)
        logger.test("f: %s, up: %s", bf.fno, up)
        logger.test("f: %s, parent(%s): %s", bf.fno, rep_parent_bone_name, parent_qq.toEulerAngles())
        logger.test("f: %s, initial: %s", bf.fno, initial.toEulerAngles())
        logger.test("f: %s, orientation: %s", bf.fno, from_orientation.toEulerAngles())

        logger.debug("f: %s, 補正回転: %s", bf.fno, from_rotation.toEulerAngles4MMD())

        org_bf = data_set.org_motion.calc_bf(from_bone_name, bf.fno)
        logger.debug("f: %s, 元の回転: %s", bf.fno, org_bf.rotation.toEulerAngles4MMD())

        if org_bf:
            # 元にもあるキーである場合、内積チェック
            uad = abs(MQuaternion.dotProduct(from_rotation.normalized(), org_bf.rotation.normalized()))
            logger.test("f: %s, 近似度: %s", bf.fno, uad)
            if uad < dot_limit:
                # 内積が離れすぎてたらNG
                logger.warning("【No.%s】%sフレーム目:%sスタンス補正失敗: 角度:%s, 近似度: %s", \
                               (data_set_idx + 1), bf.fno, from_bone_name, from_rotation.toEulerAngles4MMD().to_log(), round(uad, 5))
            else:
                # 内積の差が小さい場合、回転適用
                bf.rotation = from_rotation
        else:
            # 元にもない場合（ないはず）、はそのまま設定
            bf.rotation = from_rotation

    # 肩補正
    def adjust_shoulder_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("肩補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="shoulder{0}".format(data_set_idx), max_workers=min(2, self.options.max_workers)) as executor:
            for direction in ["左", "右"]:
                futures.append(executor.submit(self.adjust_shoulder_stance_lr, data_set_idx, "{0}肩P".format(direction), "{0}肩".format(direction), "{0}腕".format(direction)))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        return True

    # 肩補正左右
    def adjust_shoulder_stance_lr(self, data_set_idx: int, shoulder_p_name: str, shoulder_name: str, arm_name: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            # 肩調整に必要なボーン群(肩Pは含めない)
            shoulder_target_bones = ["頭", "首", "首根元", shoulder_name, arm_name, "{0}下延長".format(shoulder_name), "上半身"]

            if set(shoulder_target_bones).issubset(data_set.org_model.bones) and set(shoulder_target_bones).issubset(data_set.rep_model.bones) and shoulder_name in data_set.motion.bones:
                # 肩Pを使うかどうか
                is_shoulder_p = True if shoulder_p_name in data_set.motion.bones and shoulder_p_name in data_set.rep_model.bones and shoulder_p_name in data_set.org_model.bones else False

                # 元モデルの肩の傾き
                org_shoulder_slope = (data_set.org_model.bones[arm_name].position - data_set.org_model.bones[shoulder_name].position).normalized()

                # 肩から腕への傾き
                rep_shoulder_slope = (data_set.rep_model.bones[arm_name].position - data_set.rep_model.bones[shoulder_name].position).normalized()

                # 内積
                dot = MVector3D.dotProduct(org_shoulder_slope.normalized(), rep_shoulder_slope.normalized())
                logger.info("【No.%s】%s - 向きの近似度: %s", (data_set_idx + 1), shoulder_name, round(dot, 5))

                org_shoulder_diff = (data_set.org_model.bones[arm_name].position - data_set.org_model.bones[shoulder_name].position)
                rep_shoulder_diff = (data_set.rep_model.bones[arm_name].position - data_set.rep_model.bones[shoulder_name].position)
                shoulder_diff_ratio = rep_shoulder_diff / org_shoulder_diff

                logger.info("【No.%s】%s - 長さ比率: %s", (data_set_idx + 1), shoulder_name, shoulder_diff_ratio.to_log())

                if dot >= 0.8:
                    self.adjust_shoulder_stance_near(data_set_idx, shoulder_p_name, shoulder_name, arm_name, 0.9, is_shoulder_p)
                elif 0.5 <= dot:
                    # 肩の傾きが遠い場合
                    self.adjust_shoulder_stance_far(data_set_idx, shoulder_p_name, shoulder_name, arm_name, 0.4, is_shoulder_p)
                else:
                    logger.warning("%sの初期スタンスの角度が大きく違うため、肩補正の結果がおかしくなる可能性があります【No.%s】", shoulder_name, (data_set_idx + 1))
                    self.adjust_shoulder_stance_far(data_set_idx, shoulder_p_name, shoulder_name, arm_name, 0, is_shoulder_p)
            else:
                logger.info("%s補正: 【No.%s】[%s]のボーン群が、作成元もしくは変換先のいずれかで足りないため、処理をスキップします。", shoulder_name, (data_set_idx + 1), ", ".join(shoulder_target_bones))

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e
    
    # 肩の傾きが離れている場合のスタンス補正
    def adjust_shoulder_stance_far(self, data_set_idx: int, shoulder_p_name: str, shoulder_name: str, arm_name: str, dot_limit: float, is_shoulder_p: bool):
        logger.copy(self.options)
        data_set = self.options.data_set_list[data_set_idx]

        # 肩から腕への傾き
        rep_shoulder_slope = (data_set.rep_model.bones[arm_name].position - data_set.rep_model.bones[shoulder_name].position).normalized()

        # 元モデルのリンク生成
        org_arm_links = data_set.org_model.create_link_2_top_lr("腕")

        # 変換先モデルのリンク生成
        rep_arm_links = data_set.rep_model.create_link_2_top_lr("腕")

        logger.test("%s: %s", arm_name, data_set.org_model.bones[arm_name].position)
        logger.test("%s: %s", shoulder_name, data_set.org_model.bones[shoulder_name].position)
        
        logger.test("肩 slope: %s", rep_shoulder_slope)

        # 肩幅比率
        org_arm_diff = (org_arm_links["左"].get("左腕").position - org_arm_links["右"].get("右腕").position)
        rep_arm_diff = (rep_arm_links["左"].get("左腕").position - rep_arm_links["右"].get("右腕").position)
        arm_diff_ratio = rep_arm_diff / org_arm_diff
        arm_diff_ratio.non_zero()

        # TOの長さ比率（いかり肩ボーンとかあるので、絶対値はとらない）
        org_to_diff = (org_arm_links[shoulder_name[0]].get(arm_name).position - org_arm_links[shoulder_name[0]].get("首根元2").position)
        org_to_diff.non_zero()
        rep_to_diff = (rep_arm_links[shoulder_name[0]].get(arm_name).position - rep_arm_links[shoulder_name[0]].get("首根元2").position)
        rep_to_diff.non_zero()
        to_diff_ratio = rep_to_diff / org_to_diff
        
        logger.test("arm_diff_ratio: %s", arm_diff_ratio)
        logger.test("to_diff_ratio: %s", to_diff_ratio)

        ratio = MVector3D(arm_diff_ratio.x(), to_diff_ratio.y(), arm_diff_ratio.x())

        # 準備（細分化）
        self.prepare_split_stance(data_set_idx, data_set, shoulder_name)

        if is_shoulder_p:
            # 肩Pがある場合、肩Pも細分化
            self.prepare_split_stance(data_set_idx, data_set, shoulder_p_name)

        # 肩Pクリアして再登録
        for fno in data_set.motion.get_bone_fnos(shoulder_p_name):
            shoulder_p_bf = data_set.motion.calc_bf(shoulder_p_name, fno)
            shoulder_p_bf.rotation = MQuaternion()
            data_set.motion.regist_bf(shoulder_p_bf, shoulder_p_name, fno)

        # 子として肩の角度調整
        self.adjust_rotation_by_parent(data_set_idx, data_set, shoulder_name, shoulder_p_name)

        logger.info("%sスタンス補正: 準備終了【No.%s】", shoulder_name, (data_set_idx + 1))

        prev_fno = 0
        # 肩P、肩、腕の全てのキーフレリスト
        fnos = data_set.motion.get_bone_fnos(shoulder_name, shoulder_p_name)
        for fno_idx, fno in enumerate(fnos):
            # 肩のbf
            bf = data_set.motion.calc_bf(shoulder_name, fno)
            
            # 腕までのグローバル位置と行列
            org_arm_global_3ds, org_arm_matrixs = MServiceUtils.calc_global_pos(data_set.org_model, org_arm_links[shoulder_name[0]], data_set.org_motion, fno, return_matrix=True)
            rep_arm_global_3ds, rep_arm_matrixs = MServiceUtils.calc_global_pos(data_set.rep_model, rep_arm_links[shoulder_name[0]], data_set.motion, fno, return_matrix=True, \
                                                                                limit_links=rep_arm_links[shoulder_name[0]].from_links("首根元2"))

            # 元モデル
            # 肩のグローバル位置
            org_global_neck_base_pos = org_arm_global_3ds["首根元2"]
            # 腕のグローバル位置
            org_global_arm_pos = org_arm_global_3ds[arm_name]
            
            # 首根元2ボーンのローカル座標系
            org_neck_base_matrix = MMatrix4x4()
            org_neck_base_matrix.setToIdentity()
            org_neck_base_matrix.translate(org_global_neck_base_pos)

            # 首根元2ボーンから見た腕のローカル位置
            org_local_arm_pos = org_neck_base_matrix.inverted() * org_global_arm_pos

            logger.debug("f: %s, %s, org_global_arm_pos: %s, org_global_neck_base_pos: %s, org_local_arm_pos: %s", fno, shoulder_name, \
                         org_global_arm_pos.to_log(), org_global_neck_base_pos.to_log(), org_local_arm_pos.to_log())
            
            # 先モデル
            # 肩のグローバル位置
            rep_global_neck_base_pos = rep_arm_global_3ds["首根元2"]
            # 肩のグローバル位置
            rep_global_shoulder_pos = rep_arm_global_3ds[shoulder_name]
            # 腕のグローバル位置(肩の角度がないので初期位置)
            rep_global_arm_pos = rep_arm_global_3ds[arm_name]
            
            logger.debug("f: %s, %s, rep_global_arm_pos: %s, rep_global_neck_base_pos: %s", fno, shoulder_name, \
                         rep_global_arm_pos.to_log(), rep_global_neck_base_pos.to_log())
            
            # 首根元2ボーンのローカル座標系
            rep_neck_base_matrix = MMatrix4x4()
            rep_neck_base_matrix.setToIdentity()
            rep_neck_base_matrix.translate(rep_global_neck_base_pos)

            # 先モデルの現在の腕のローカル位置
            rep_local_arm_pos = rep_neck_base_matrix.inverted() * rep_global_arm_pos

            # 先モデルの腕のローカル位置は、肩の縮尺
            recalc_rep_local_arm_pos = org_local_arm_pos * ratio
            # 先モデルの再計算した腕グローバル座標
            recalc_rep_global_arm_pos = rep_neck_base_matrix * recalc_rep_local_arm_pos

            logger.debug("f: %s, %s, rep_local_arm_pos: %s, recalc_rep_local_arm_pos: %s, recalc_rep_global_arm_pos: %s", fno, shoulder_name, \
                         rep_local_arm_pos.to_log(), recalc_rep_local_arm_pos.to_log(), recalc_rep_global_arm_pos.to_log())
            
            # 肩からの補正角度
            new_shoulder_qq = MQuaternion.rotationTo(rep_global_arm_pos - rep_global_shoulder_pos, recalc_rep_global_arm_pos - rep_global_shoulder_pos)
            
            org_bf = data_set.org_motion.calc_bf(shoulder_name, bf.fno)
            logger.debug("f: %s, %s, 補正回転: %s, 元の回転: %s", bf.fno, bf.name, new_shoulder_qq.toEulerAngles4MMD().to_log(), bf.rotation.toEulerAngles4MMD().to_log())

            if org_bf:
                # 元にもあるキーである場合、内積チェック
                uad = abs(MQuaternion.dotProduct(new_shoulder_qq.normalized(), org_bf.rotation.normalized()))
                logger.test("f: %s, uad: %s, org: %s, result: %s", bf.fno, uad, org_bf.rotation.toEulerAngles4MMD(), new_shoulder_qq.toEulerAngles4MMD())
                if uad < dot_limit:
                    # 内積が離れすぎてたらNG
                    logger.warning("【No.%s】%sフレーム目:%sスタンス補正失敗: 角度:%s, 近似度: %s", \
                                   (data_set_idx + 1), bf.fno, shoulder_name, new_shoulder_qq.toEulerAngles4MMD().to_log(), round(uad, 5))
                    bf.rotation = org_bf.rotation
                else:
                    # 内積の差が小さい場合、回転適用
                    bf.rotation = new_shoulder_qq
            else:
                # 元にもない場合（ないはず）、はそのまま設定
                bf.rotation = new_shoulder_qq

            # bf登録
            data_set.motion.regist_bf(bf, shoulder_name, bf.fno)
                
            if fno // 500 > prev_fno and fnos[-1] > 0:
                logger.info("-- %sフレーム目:終了(%s％)【No.%s - %sスタンス補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, shoulder_name)
                prev_fno = fno // 500

        # 子の角度調整
        self.adjust_rotation_by_parent(data_set_idx, data_set, arm_name, shoulder_name)

        logger.info("%sスタンス補正: 終了【No.%s】", shoulder_name, (data_set_idx + 1))

    # 肩の傾きが近い場合の肩補正
    def adjust_shoulder_stance_near(self, data_set_idx: int, shoulder_p_name: str, shoulder_name: str, arm_name: str, dot_limit: float, is_shoulder_p: bool):
        logger.copy(self.options)
        data_set = self.options.data_set_list[data_set_idx]

        # 肩から腕への傾き
        rep_shoulder_slope = (data_set.rep_model.bones[arm_name].position - data_set.rep_model.bones[shoulder_name].position).normalized()

        # 元モデルのリンク生成
        org_shoulder_links = data_set.org_model.create_link_2_top_one(shoulder_name)
        org_arm_links = data_set.org_model.create_link_2_top_lr("腕")
        org_shoulder_under_links = data_set.org_model.create_link_2_top_one("{0}下延長".format(shoulder_name))

        # 変換先モデルのリンク生成
        rep_shoulder_links = data_set.rep_model.create_link_2_top_one(shoulder_name)
        rep_arm_links = data_set.rep_model.create_link_2_top_lr("腕")
        # rep_shoulder_under_links = data_set.rep_model.create_link_2_top_one("{0}下延長".format(shoulder_name))

        logger.test("%s: %s", arm_name, data_set.org_model.bones[arm_name].position)
        logger.test("%s: %s", shoulder_name, data_set.org_model.bones[shoulder_name].position)

        rep_shoulder_slope_up = MVector3D(1, -1, 0)
        rep_shoulder_slope_cross = MVector3D.crossProduct(rep_shoulder_slope, rep_shoulder_slope_up).normalized()
        
        rep_shoulder_initial_slope_qq = MQuaternion.fromDirection(rep_shoulder_slope, rep_shoulder_slope_cross)

        logger.test("肩 slope: %s", rep_shoulder_slope)
        logger.test("肩 cross: %s", rep_shoulder_slope_cross)

        # 肩幅比率
        org_arm_diff = (org_arm_links["左"].get("左腕").position - org_arm_links["右"].get("右腕").position)
        rep_arm_diff = (rep_arm_links["左"].get("左腕").position - rep_arm_links["右"].get("右腕").position)
        arm_diff_ratio = rep_arm_diff / org_arm_diff
        arm_diff_ratio.one()    # 比率なので、0は1に変換する

        # TOの長さ比率（いかり肩ボーンとかあるので、絶対値はとらない）
        org_to_diff = (org_arm_links[shoulder_name[0]].get(arm_name).position - org_arm_links[shoulder_name[0]].get("首根元").position)
        org_to_diff.one()
        rep_to_diff = (rep_arm_links[shoulder_name[0]].get(arm_name).position - rep_arm_links[shoulder_name[0]].get("首根元").position)
        rep_to_diff.one()
        to_diff_ratio = rep_to_diff / org_to_diff
        
        logger.test("arm_diff_ratio: %s", arm_diff_ratio)
        logger.test("to_diff_ratio: %s", to_diff_ratio)

        ratio = MVector3D(arm_diff_ratio.x(), to_diff_ratio.y(), arm_diff_ratio.x())

        # 初期状態の肩の傾き
        initial_bf = VmdBoneFrame(fno=0)
        initial_bf.set_name(shoulder_name)
        initial_dataset = MOptionsDataSet(VmdMotion(), data_set.org_model, data_set.rep_model, data_set.output_vmd_path, data_set.detail_stance_flg, data_set.twist_flg, [], None, 0, [])

        self.calc_rotation_stance_shoulder(initial_bf, data_set_idx, initial_dataset, \
                                           org_shoulder_links, org_arm_links[shoulder_name[0]], rep_shoulder_links, \
                                           rep_arm_links[shoulder_name[0]], org_shoulder_under_links, \
                                           shoulder_name, arm_name, ratio, rep_shoulder_initial_slope_qq, MQuaternion(), 0)
        shoulder_initial_qq = initial_bf.rotation
        
        logger.debug("shoulder_initial_qq: %s", shoulder_initial_qq)
        logger.debug("dot_limit: %s", dot_limit)

        # 準備（細分化）
        self.prepare_split_stance(data_set_idx, data_set, shoulder_name)

        if is_shoulder_p:
            # 肩Pがある場合、肩Pも細分化
            self.prepare_split_stance(data_set_idx, data_set, shoulder_p_name)

        # 肩Pクリアして再登録
        for fno in data_set.motion.get_bone_fnos(shoulder_p_name):
            shoulder_p_bf = data_set.motion.calc_bf(shoulder_p_name, fno)
            shoulder_p_bf.rotation = MQuaternion()
            data_set.motion.regist_bf(shoulder_p_bf, shoulder_p_name, fno)

        # 子として肩の角度調整
        self.adjust_rotation_by_parent(data_set_idx, data_set, shoulder_name, shoulder_p_name)

        logger.info("%sスタンス補正: 準備終了【No.%s】", shoulder_name, (data_set_idx + 1))

        prev_fno = 0
        # 肩P、肩、腕の全てのキーフレリスト
        fnos = data_set.motion.get_bone_fnos(shoulder_name, shoulder_p_name)
        for fno_idx, fno in enumerate(fnos):
            # 肩補正
            shoulder_bf = data_set.motion.calc_bf(shoulder_name, fno)

            self.calc_rotation_stance_shoulder(shoulder_bf, data_set_idx, data_set, \
                                               org_shoulder_links, org_arm_links[shoulder_name[0]], rep_shoulder_links, \
                                               rep_arm_links[shoulder_name[0]], org_shoulder_under_links, \
                                               shoulder_name, arm_name, ratio, rep_shoulder_initial_slope_qq, shoulder_initial_qq, dot_limit)
                
            # bf登録
            data_set.motion.regist_bf(shoulder_bf, shoulder_name, fno)
                
            if fno // 500 > prev_fno and fnos[-1] > 0:
                logger.info("-- %sフレーム目:終了(%s％)【No.%s - %sスタンス補正】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, shoulder_name)
                prev_fno = fno // 500

        # 子の角度調整
        self.adjust_rotation_by_parent(data_set_idx, data_set, arm_name, shoulder_name)

        logger.info("%sスタンス補正: 終了【No.%s】", shoulder_name, (data_set_idx + 1))

    # 肩補正
    def calc_rotation_stance_shoulder(self, bf: VmdBoneFrame, data_set_idx: int, data_set: MOptionsDataSet, \
                                      org_from_links: BoneLinks, org_to_links: BoneLinks, rep_from_links: BoneLinks, \
                                      rep_to_links: BoneLinks, org_shoulder_under_links: BoneLinks, \
                                      from_bone_name: str, to_bone_name: str, ratio: MVector3D, \
                                      rep_initial_slope_qq: MQuaternion, cancel_qq: MQuaternion, dot_limit):
        logger.test("f: %s -----------------------------", bf.fno)

        base_bone_name = "首根元"
        # 首根元以降のボーンのみを対象とする（体幹の動きは無視）
        org_limit_links = org_to_links.to_links("首根元")
        rep_limit_links = rep_to_links.to_links("首根元")

        # -------------
        # TO位置の再計算

        # TOボーンまでの位置
        org_to_global_3ds, org_front_to_global_3ds, org_to_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.org_model, org_to_links, data_set.org_motion, bf.fno, limit_links=org_limit_links)
        rep_to_global_3ds, rep_front_to_global_3ds, rep_to_direction_qq = \
            MServiceUtils.calc_front_global_pos(data_set.rep_model, rep_to_links, data_set.motion, bf.fno, limit_links=rep_limit_links)

        # 正面向きの基準ボーンの位置
        org_front_base_pos = org_front_to_global_3ds[base_bone_name]
        rep_front_base_pos = rep_front_to_global_3ds[base_bone_name]

        # TOボーンの正面位置
        org_front_to_pos = org_front_to_global_3ds[to_bone_name]
        rep_front_to_pos = rep_front_to_global_3ds[to_bone_name]

        # ---------------

        rep_front_to_x = rep_front_base_pos.x() + ((org_front_to_pos.x() - org_front_base_pos.x()) * ratio.x())
        rep_front_to_y = rep_front_base_pos.y() + ((org_front_to_pos.y() - org_front_base_pos.y()) * ratio.y())
        rep_front_to_z = rep_front_base_pos.z() + ((org_front_to_pos.z() - org_front_base_pos.z()) * ratio.x())

        logger.test("f: %s, re rep_front: x: %s, y: %s, z: %s", bf.fno, rep_front_to_x, rep_front_to_y, rep_front_to_z)

        logger.test("f: %s, rep_front_base_pos: %s", bf.fno, rep_front_base_pos)
        logger.test("f: %s, org_front_to_pos: %s", bf.fno, org_front_to_pos)
        logger.test("f: %s, org_front_base_pos: %s", bf.fno, org_front_base_pos)

        new_rep_front_to_pos = MVector3D(rep_front_to_x, rep_front_to_y, rep_front_to_z)
        logger.test("f: %s, 計算new_rep_front_to_pos: %s", bf.fno, new_rep_front_to_pos)
        logger.test("f: %s, 元rep_front_to_pos: %s", bf.fno, rep_front_to_pos)

        # 正面向きの新しいTO位置
        new_rep_front_to_global_3ds = {}
        new_rep_front_to_global_3ds[to_bone_name] = new_rep_front_to_pos

        # 回転を元に戻した位置
        rotated_to_3ds = MServiceUtils.calc_global_pos_by_direction(rep_to_direction_qq, new_rep_front_to_global_3ds)

        new_rep_to_pos = rotated_to_3ds[to_bone_name]
        rep_to_pos = rep_to_global_3ds[to_bone_name]
        rep_from_pos = rep_to_global_3ds[from_bone_name]

        # UP計算 ---------------
        
        # 肩下延長ボーンまでの位置
        org_shoulder_under_global_3ds = MServiceUtils.calc_global_pos(data_set.org_model, org_shoulder_under_links, \
                                                                      data_set.org_motion, bf.fno, org_limit_links)
        org_shoulder_under_pos = org_shoulder_under_global_3ds["{0}下延長".format(from_bone_name)]
        logger.test("f: %s, org_shoulder_under_pos: %s", bf.fno, org_shoulder_under_pos)

        # 肩ボーンまでの位置
        org_shoulder_pos = org_shoulder_under_global_3ds[from_bone_name]
        logger.test("f: %s, org_shoulder_pos: %s", bf.fno, org_shoulder_pos)

        up_pos = org_shoulder_under_pos - org_shoulder_pos

        # ---------------
        # FROMの回転量を再計算する
        direction = new_rep_to_pos - rep_from_pos
        up = MVector3D.crossProduct(direction, up_pos)
        from_orientation = MQuaternion.fromDirection(direction.normalized(), up.normalized())
        initial = rep_initial_slope_qq
        from_rotation = cancel_qq.inverted() * from_orientation * initial.inverted()
        from_rotation.normalize()
        logger.test("f: %s, rep_from_pos(%s): %s", bf.fno, from_bone_name, rep_from_pos)
        logger.test("f: %s, rep_to_pos(%s): %s, 元: %s", bf.fno, to_bone_name, new_rep_to_pos, rep_to_pos)
        logger.test("f: %s, up_pos: %s", bf.fno, up_pos)
        logger.test("f: %s, direction(%s): %s", bf.fno, to_bone_name, direction)
        logger.test("f: %s, up: %s", bf.fno, up)
        # logger.test("f: %s, parent(%s): %s", bf.fno, base_bone_name, parent_qq.toEulerAngles())
        logger.test("f: %s, initial: %s", bf.fno, initial.toEulerAngles())
        logger.test("f: %s, orientation: %s", bf.fno, from_orientation.toEulerAngles())

        logger.debug("f: %s, 補正回転: %s", bf.fno, from_rotation.toEulerAngles4MMD())

        org_bf = data_set.org_motion.calc_bf(from_bone_name, bf.fno)
        logger.debug("f: %s, 元の回転: %s", bf.fno, org_bf.rotation.toEulerAngles4MMD())

        if org_bf:
            # 元にもあるキーである場合、内積チェック
            uad = abs(MQuaternion.dotProduct(from_rotation.normalized(), org_bf.rotation.normalized()))
            logger.test("f: %s, uad: %s, org: %s, result: %s", bf.fno, uad, org_bf.rotation.toEulerAngles4MMD(), from_rotation.toEulerAngles4MMD())
            if uad < dot_limit:
                # 内積が離れすぎてたらNG
                logger.warning("【No.%s】%sフレーム目:%sスタンス補正失敗: 角度:%s, 近似度: %s", \
                               (data_set_idx + 1), bf.fno, from_bone_name, from_rotation.toEulerAngles4MMD().to_log(), round(uad, 5))
            else:
                # 内積の差が小さい場合、回転適用
                bf.rotation = from_rotation
        else:
            # 元にもない場合（ないはず）、はそのまま設定
            bf.rotation = from_rotation

    # 指定したボーンを親ボーンの調整量に合わせてキャンセル
    def adjust_rotation_by_parent(self, data_set_idx: int, data_set: MOptionsDataSet, target_bone_name: str, target_parent_name: str):
        for fno in data_set.motion.get_bone_fnos(target_bone_name):
            bf = data_set.motion.bones[target_bone_name][fno]

            # 元々の親bf
            org_parent_bf = data_set.org_motion.calc_bf(target_parent_name, fno)
            # 調整後の親bf
            rep_parent_bf = data_set.motion.calc_bf(target_parent_name, fno)

            # 元々の親bfのdeformed回転量
            org_deformed_qq = MServiceUtils.deform_rotation(data_set.org_model, data_set.org_motion, org_parent_bf)
            # 調整後の親bfのdeformed回転量
            rep_deformed_qq = MServiceUtils.deform_rotation(data_set.rep_model, data_set.motion, rep_parent_bf)

            logger.test("f: %s, b: %s, org: %s, rep: %s, diff: %s", fno, target_bone_name, org_deformed_qq.toEulerAngles4MMD(), \
                        rep_deformed_qq.toEulerAngles4MMD(), (rep_deformed_qq.inverted() * org_deformed_qq).toEulerAngles4MMD())

            bf.rotation = rep_parent_bf.rotation.inverted() * org_parent_bf.rotation * bf.rotation

    # 指定したボーンを親ボーンの調整量に合わせてキャンセル
    def adjust_rotation_by_parent_ik(self, data_set_idx: int, data_set: MOptionsDataSet, target_bone_name: str, target_parent_name: str, target_ik_name: str):
        fnos = data_set.motion.get_bone_fnos(target_bone_name)
        ik_on_fnos = []

        if len(fnos) == 0:
            # 処理対象が1件もなければ終了
            return

        is_ik_on = True
        for fno in range(fnos[-1]):
            for showik in data_set.motion.showiks:
                if showik.fno == fno and target_ik_name in showik.ik and showik.ik[target_ik_name].onoff == 0:
                    # IKOFFになったら、フラグOFF
                    is_ik_on = False
                    break
            
            if is_ik_on:
                # フラグONの場合のみ、キーフレ保持
                ik_on_fnos.append(fno)

        for fno in fnos:
            if fno in ik_on_fnos:
                # IKONの場合、計算不要
                continue

            bf = data_set.motion.bones[target_bone_name][fno]

            # 元々の親bf
            org_parent_bf = data_set.org_motion.calc_bf(target_parent_name, fno)
            # 調整後の親bf
            rep_parent_bf = data_set.motion.calc_bf(target_parent_name, fno)

            # 元々の親bfのdeformed回転量
            org_deformed_qq = MServiceUtils.deform_rotation(data_set.org_model, data_set.org_motion, org_parent_bf)
            # 調整後の親bfのdeformed回転量
            rep_deformed_qq = MServiceUtils.deform_rotation(data_set.rep_model, data_set.motion, rep_parent_bf)

            logger.test("f: %s, b: %s, org: %s, rep: %s, diff: %s", fno, target_bone_name, org_deformed_qq.toEulerAngles4MMD(), \
                        rep_deformed_qq.toEulerAngles4MMD(), (rep_deformed_qq.inverted() * org_deformed_qq).toEulerAngles4MMD())

            bf.rotation = rep_parent_bf.rotation.inverted() * org_parent_bf.rotation * bf.rotation

    # スタンス用細分化
    def prepare_split_stance(self, data_set_idx: int, data_set: MOptionsDataSet, target_bone_name: str):
        fnos = data_set.motion.get_bone_fnos(target_bone_name)

        for fidx, fno in enumerate(fnos):
            if fidx == 0:
                continue

            prev_bf = data_set.motion.bones[target_bone_name][fnos[fidx - 1]]
            bf = data_set.motion.bones[target_bone_name][fno]
            diff_degree = abs(prev_bf.rotation.toDegree() - bf.rotation.toDegree())

            if diff_degree >= 150:
                # 回転量が約150度以上の場合、半分に分割しておく
                half_fno = prev_bf.fno + round((bf.fno - prev_bf.fno) / 2)

                if prev_bf.fno < half_fno < bf.fno:
                    # キーが追加できる状態であれば、追加
                    half_bf = data_set.motion.calc_bf(target_bone_name, half_fno)
                    data_set.motion.regist_bf(half_bf, target_bone_name, half_fno)

    # 腕スタンス補正
    def adjust_arm_stance(self, data_set_idx: int, data_set: MOptionsDataSet):
        logger.info("腕スタンス補正　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)
        
        # 腕のスタンス差
        arm_diff_qq_dic = self.calc_arm_stance(data_set)

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="arm{0}".format(data_set_idx), max_workers=self.options.max_workers) as executor:
            for bone_name in ["左腕", "左ひじ", "左手首", "右腕", "右ひじ", "右手首"]:
                futures.append(executor.submit(self.adjust_arm_stance_pool, data_set_idx, arm_diff_qq_dic, bone_name))
            for bone_name in ["左腕捩", "左手捩", "右腕捩", "右手捩"]:
                futures.append(executor.submit(self.adjust_arm_stance_twist_pool, data_set_idx, bone_name))
        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        return True

    def adjust_arm_stance_twist_pool(self, data_set_idx: int, bone_name: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            if bone_name in data_set.motion.bones and bone_name in data_set.org_model.bones and bone_name in data_set.rep_model.bones:
                axis = data_set.rep_model.get_local_x_axis(bone_name)

                for bf in data_set.motion.bones[bone_name].values():
                    if bf.key:
                        # 元モデルのモーションの回転量
                        degree = bf.rotation.toDegree()

                        # 先モデルの軸に合わせる（変換先の軸と回転の軸が逆なら逆回転）
                        rep_qq = MQuaternion.fromAxisAndAngle(axis, degree * (np.sign(bf.rotation.x()) * np.sign(axis.x())))

                        logger.test("f: %s, %s, prev: %s, degree: %s, after: %s", bf.fno, bone_name, bf.rotation, degree, rep_qq)

                        bf.rotation = rep_qq
                
                logger.info("腕スタンス補正【No.%s - %s】", (data_set_idx + 1), bone_name)

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 腕スタンス補正左右
    def adjust_arm_stance_pool(self, data_set_idx: int, arm_diff_qq_dic: dict, bone_name: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]

            if bone_name in arm_diff_qq_dic and bone_name in data_set.motion.bones:
                # スタンス補正値がある場合
                for bf in data_set.motion.bones[bone_name].values():
                    if bf.key:
                        if arm_diff_qq_dic[bone_name]["from"] == MQuaternion():
                            bf.rotation = bf.rotation * arm_diff_qq_dic[bone_name]["to"]
                        else:
                            bf.rotation = arm_diff_qq_dic[bone_name]["from"].inverted() * bf.rotation * arm_diff_qq_dic[bone_name]["to"]
                
                logger.info("腕スタンス補正【No.%s - %s】", (data_set_idx + 1), bone_name)
                logger.test("from: %s", arm_diff_qq_dic[bone_name]["from"].toEulerAngles())
                logger.test("to: %s", arm_diff_qq_dic[bone_name]["to"].toEulerAngles())

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 腕スタンス補正用傾き計算
    def calc_arm_stance(self, data_set: MOptionsDataSet):
        arm_diff_qq_dic = {}

        for direction in ["左", "右"]:
            for from_bone_type, target_bone_type, to_bone_type in [(None, "腕", "ひじ"), ("腕", "ひじ", "手首"), ("ひじ", "手首", "中指１")]:
                from_bone_name = "{0}{1}".format(direction, from_bone_type) if from_bone_type else None
                target_bone_name = "{0}{1}".format(direction, target_bone_type)
                to_bone_name = "{0}{1}".format(direction, to_bone_type)

                if from_bone_name:
                    bone_names = [from_bone_name, target_bone_name, to_bone_name]
                else:
                    bone_names = [target_bone_name, to_bone_name]

                if set(bone_names).issubset(data_set.org_model.bones) and set(bone_names).issubset(data_set.rep_model.bones):
                    # 対象ボーンが揃っている場合（念のためバラバラにチェック）

                    # 揃ってたら辞書登録
                    arm_diff_qq_dic[target_bone_name] = {}

                    if from_bone_name:
                        # FROM-TARGETの傾き
                        _, org_from_qq = data_set.org_model.calc_arm_stance(from_bone_name, target_bone_name)
                        _, rep_from_qq = data_set.rep_model.calc_arm_stance(from_bone_name, target_bone_name)

                        arm_diff_qq_dic[target_bone_name]["from"] = rep_from_qq.inverted() * org_from_qq
                    else:
                        arm_diff_qq_dic[target_bone_name]["from"] = MQuaternion()

                    # TARGET-TOの傾き
                    _, org_to_qq = data_set.org_model.calc_arm_stance(target_bone_name, to_bone_name)
                    _, rep_to_qq = data_set.rep_model.calc_arm_stance(target_bone_name, to_bone_name)

                    arm_diff_qq_dic[target_bone_name]["to"] = rep_to_qq.inverted() * org_to_qq
        
        return arm_diff_qq_dic

        

