# -*- coding: utf-8 -*-
#
# cython: profile=True
# cython: linetrace=True
# cython: binding=True
# distutils: define_macros=CYTHON_TRACE_NOGIL=1
import numpy as np
cimport numpy as np
import math
cimport libc.math as math
from libcpp cimport  list, str

import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from mmd.PmxData cimport PmxModel, Bone, OBB, RigidBody
from mmd.VmdData cimport VmdMotion, VmdBoneFrame
from module.MParams cimport BoneLinks # noqa
from module.MMath cimport MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions cimport MOptions, MOptionsDataSet # noqa
from utils import MServiceUtils, MBezierUtils
from utils cimport MServiceUtils, MBezierUtils

from mmd.PmxData import Vertex, Material, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException, MKilledException

logger = MLogger(__name__, level=1)

# 接触回避用オプション
cdef class ArmAvoidanceOption():
    cdef public list arm_links
    cdef public dict ik_links_list
    cdef public dict ik_count_list
    cdef public dict avoidance_links
    cdef public dict avoidances
    cdef public float face_length

    def __init__(self, arm_links: list, ik_links_list: dict, ik_count_list: dict, avoidance_links: dict, avoidances: dict, face_length: float):
        super().__init__()

        self.arm_links = arm_links
        self.ik_links_list = ik_links_list
        self.ik_count_list = ik_count_list
        self.avoidance_links = avoidance_links
        self.avoidances = avoidances
        self.face_length = face_length


cdef class ArmAvoidanceService():
    cdef public object options
    cdef public list target_data_set_idxs
    cdef public dict avoidance_options

    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        # 腕処理対象データセットを取得
        self.target_data_set_idxs = self.get_target_set_idxs()
        logger.test("target_data_set_idxs: %s", self.target_data_set_idxs)

        if len(self.target_data_set_idxs) == 0:
            # データセットがない場合、処理スキップ
            logger.warning("接触回避ができるファイルセットが見つからなかったため、処理をスキップします。", decoration=MLogger.DECORATION_BOX)
            return True
        
        self.avoidance_options = {}

        for data_set_idx, data_set in enumerate(self.options.data_set_list):
            logger.info("接触回避　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

            # 接触回避用準備
            self.avoidance_options[(data_set_idx, "左")] = self.prepare_avoidance(data_set_idx, "左")
            self.avoidance_options[(data_set_idx, "右")] = self.prepare_avoidance(data_set_idx, "右")

        for data_set_idx, data_set in enumerate(self.options.data_set_list):
            self.execute_avoidance_pool(data_set_idx, "右")
            self.execute_avoidance_pool(data_set_idx, "左")

        # futures = []
        # with ThreadPoolExecutor(thread_name_prefix="avoidance", max_workers=self.options.max_workers) as executor:
        #     for data_set_idx, data_set in enumerate(self.options.data_set_list):
        #         futures.append(executor.submit(self.execute_avoidance_pool, data_set_idx, "右"))
        #         futures.append(executor.submit(self.execute_avoidance_pool, data_set_idx, "左"))

        # concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        # for f in futures:
        #     if not f.result():
        #         return False
    
        return True
    
    # 接触回避
    cpdef bint execute_avoidance_pool(self, int data_set_idx, str direction):
        try:
            # 接触回避準備
            pfun = profile(self.prepare_avoidance_dataset)
            all_avoidance_axis = pfun(data_set_idx, direction)

            # 接触回避処理
            pfun = profile(self.execute_avoidance)
            pfun(data_set_idx, direction, all_avoidance_axis)

            # # 各ボーンのbfを円滑化
            # futures = []
            # with ThreadPoolExecutor(thread_name_prefix="avoidance_after{0}".format(data_set_idx)) as executor:
            #     for bone_name in ["{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction)]:
            #         futures.append(executor.submit(self.execute_avoidance_after, data_set_idx, bone_name))

            # concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)
            # for f in futures:
            #     if not f.result():
            #         return False

            return True
        except MKilledException as ke:
            raise ke
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 接触回避処理
    def execute_avoidance_after(self, data_set_idx: int, bone_name: str):
        try:
            logger.info("接触回避後処理 - 円滑化【No.%s - %s】", (data_set_idx + 1), bone_name)

            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]
            
            data_set.motion.smooth_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
                                      data_set.rep_model.bones[bone_name].getTranslatable(), limit_degrees=1)

            logger.info("接触回避後処理 - フィルタリング【No.%s - %s】", (data_set_idx + 1), bone_name)

            data_set.motion.smooth_filter_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
                                             data_set.rep_model.bones[bone_name].getTranslatable(), \
                                             config={"freq": 30, "mincutoff": 0.03, "beta": 0.1, "dcutoff": 1}, loop=1)

            # logger.info("接触回避後処理 - 不要キー削除【No.%s - %s】", (data_set_idx + 1), bone_name)

            # data_set.motion.remove_unnecessary_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
            #                                       data_set.rep_model.bones[bone_name].getTranslatable(), offset=15)

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 接触回避処理
    cpdef bint execute_avoidance(self, int data_set_idx, str direction, dict all_avoidance_axis):
        cdef int fno, ik_cnt, ik_max_count, now_ik_max_count, prev_block_fno
        cdef str arm_bone_name, avoidance_name, bone_name, elbow_bone_name, link_name, wrist_bone_name, axis
        cdef list fnos, ik_links_list, target_bone_names, is_success, failured_last_names
        cdef dict dot_dict, dot_limit_dict, now_rep_global_3ds, org_bfs, rep_avbone_global_3ds, rep_avbone_global_mats, rep_global_3ds, avoidance_axis
        cdef bint is_in_elbow
        cdef MVector3D now_rep_effector_pos, rep_collision_vec, rep_diff, prev_rep_diff
        cdef MOptionsDataSet data_set
        cdef BoneLinks arm_link, avodance_link, ik_links
        cdef VmdBoneFrame arm_bf, bf, elbow_bf, now_bf
        cdef RigidBody avoidance
        cdef ArmAvoidanceOption avoidance_options
        cdef MQuaternion  elbow_adjust_qq
        cdef Bone link_bone
        cdef OBB obb
        
        logger.info("接触回避処理【No.%s - %s】", (data_set_idx + 1), direction)

        logger.copy(self.options)
        # 処理対象データセット
        data_set = self.options.data_set_list[data_set_idx]

        # 回避用オプション
        avoidance_options = self.avoidance_options[(data_set_idx, direction)]
        
        arm_bone_name = "{0}腕".format(direction)
        elbow_bone_name = "{0}ひじ".format(direction)
        wrist_bone_name = "{0}手首".format(direction)

        target_bone_names = [arm_bone_name, "{0}腕捩".format(direction), elbow_bone_name, "{0}手捩".format(direction), wrist_bone_name]
        avoidance_axis = {}
        prev_block_fno = 0
        fnos = data_set.motion.get_bone_fnos(*target_bone_names)

        # 一度全部キーを追加する（キー自体は無効化のまま）
        for fno in fnos:
            for bone_name in target_bone_names:
                if bone_name not in data_set.motion.bones:
                    data_set.motion.bones[bone_name] = {}
                data_set.motion.bones[bone_name][fno] = data_set.motion.calc_bf(bone_name, fno)

        while len(fnos) > 0:
            fno = fnos[0]
            
            if fno in all_avoidance_axis:
                # 回避ブロックが始まったら、保持
                avoidance_axis = all_avoidance_axis[fno]

            for ((avoidance_name, avodance_link), avoidance) in zip(avoidance_options.avoidance_links.items(), avoidance_options.avoidances.values()):
                # 剛体の現在位置をチェック
                rep_avbone_global_3ds, rep_avbone_global_mats = \
                    MServiceUtils.calc_global_pos(data_set.rep_model, avodance_link, data_set.motion, fno, return_matrix=True)
                
                obb = avoidance.get_obb(fno, avodance_link.get(avodance_link.last_name()).position, rep_avbone_global_mats, self.options.arm_options.alignment, direction == "左")

                # # 剛体の原点 ---------------
                # debug_bone_name = "原点"

                # debug_bf = VmdBoneFrame(fno)
                # debug_bf.key = True
                # debug_bf.set_name(debug_bone_name)
                # debug_bf.position = obb.origin
                
                # if debug_bone_name not in data_set.motion.bones:
                #     data_set.motion.bones[debug_bone_name] = {}
                
                # data_set.motion.bones[debug_bone_name][fno] = debug_bf
                # # --------------
            
                for arm_link in avoidance_options.arm_links:
                    # 先モデルのそれぞれのグローバル位置
                    rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, arm_link, data_set.motion, fno)
                    # [logger.test("f: %s, k: %s, v: %s", fno, k, v) for k, v in rep_global_3ds.items()]

                    # 衝突情報を取る
                    (collision, near_collision, x_distance, z_distance, rep_x_collision_vec, rep_z_collision_vec) \
                        = obb.get_collistion(rep_global_3ds[arm_link.last_name()], rep_global_3ds[arm_bone_name], \
                                             data_set.rep_model.bones[arm_bone_name].position.distanceToPoint(data_set.rep_model.bones[arm_link.last_name()].position))
                    
                    if collision or near_collision:
                        logger.debug("f: %s(%s-%s:%s), c[%s], nc[%s], xd[%s], zd[%s], xv[%s], zv[%s]", \
                                     fno, (data_set_idx + 1), arm_link.last_name(), avoidance_name, collision, near_collision, \
                                     x_distance, z_distance, rep_x_collision_vec.to_log(), rep_z_collision_vec.to_log())

                        is_success = []
                        failured_last_names = []

                        # 衝突単位のbf情報
                        org_bfs = {}
                        for ik_links_list in avoidance_options.ik_links_list.values():
                            for ik_links in ik_links_list:
                                for link_name in ik_links.all().keys():
                                    if link_name not in org_bfs:
                                        bf = data_set.motion.calc_bf(link_name, fno)
                                        bf.org_rotation = bf.rotation.copy()
                                        data_set.motion.regist_bf(bf, link_name, fno)
                                        org_bfs[link_name] = bf.copy()

                        # 既定の回避方向（なければとりあえずZ）
                        axis = "z" if "axis" not in avoidance_axis else avoidance_axis["axis"]
                        # 回避方向
                        rep_collision_vec = rep_x_collision_vec if axis == "x" else rep_z_collision_vec

                        if collision:
                            logger.info("○接触あり: f: %s(%s-%s:%s:%s), 元: %s, 回避: %s", fno, \
                                        (data_set_idx + 1), arm_link.last_display_name(), avoidance_name, axis, rep_global_3ds[arm_link.last_name()].to_log(), rep_collision_vec.to_log())
                        else:
                            logger.info("－近接あり: f: %s(%s-%s:%s:%s), 元: %s, 回避: %s", fno, \
                                        (data_set_idx + 1), arm_link.last_display_name(), avoidance_name, axis, rep_global_3ds[arm_link.last_name()].to_log(), rep_collision_vec.to_log())

                        # # 回避後の先端ボーン位置 -------------
                        # debug_bone_name = "{0}A".format(arm_link.last_name())

                        # debug_bf = VmdBoneFrame(fno)
                        # debug_bf.key = True
                        # debug_bf.set_name(debug_bone_name)
                        # debug_bf.position = rep_collision_vec
                        
                        # if debug_bone_name not in data_set.motion.bones:
                        #     data_set.motion.bones[debug_bone_name] = {}
                        
                        # data_set.motion.bones[debug_bone_name][fno] = debug_bf
                        # # ----------

                        # IK処理実行
                        for ik_cnt, (ik_links, ik_max_count) in enumerate(zip(avoidance_options.ik_links_list[arm_link.last_name()], \
                                                                              avoidance_options.ik_count_list[arm_link.last_name()])):
                            prev_rep_diff = MVector3D()
                            # ひじを含んでいるか
                            is_in_elbow = elbow_bone_name in list(ik_links.all().keys())
                            
                            for now_ik_max_count in range(1, ik_max_count + 1):
                                logger.debug("IK計算開始(%s): f: %s(%s:%s:%s), axis: %s, now[%s], new[%s]", now_ik_max_count, fno, (data_set_idx + 1), \
                                             list(ik_links.all().keys()), avoidance_name, axis, rep_global_3ds[arm_link.last_name()].to_log(), rep_collision_vec.to_log())
                                
                                # 修正角度がない場合、IK計算実行
                                MServiceUtils.calc_IK(data_set.rep_model, arm_link, data_set.motion, fno, rep_collision_vec, ik_links, max_count=1)

                                # 現在のエフェクタ位置
                                now_rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, arm_link, data_set.motion, fno)
                                now_rep_effector_pos = now_rep_global_3ds[arm_link.last_name()]

                                # 現在のエフェクタ位置との差分(エフェクタ位置が指定されている場合のみ)
                                rep_diff = MVector3D() if rep_collision_vec == MVector3D() else rep_collision_vec - now_rep_effector_pos

                                # IKの関連ボーンの内積チェック
                                dot_dict = {}
                                dot_limit_dict = {}
                                for link_name, link_bone in ik_links.all().items():
                                    dot_dict[link_name] = MQuaternion.dotProduct(org_bfs[link_name].rotation, data_set.motion.calc_bf(link_name, fno).rotation)
                                    dot_limit_dict[link_name] = link_bone.dot_limit

                                # まずは一旦確定
                                for link_name in list(ik_links.all().keys())[1:]:
                                    now_bf = data_set.motion.calc_bf(link_name, fno)
                                    data_set.motion.regist_bf(now_bf, link_name, fno)
                                
                                if np.count_nonzero(np.where(np.array(list(dot_dict.values())) < np.array(list(dot_limit_dict.values())), 1, 0)) == 0:
                                    if (prev_rep_diff == MVector3D() or np.sum(np.abs(rep_diff.data())) < np.sum(np.abs(prev_rep_diff.data()))) and \
                                            np.count_nonzero(np.where(np.abs(rep_diff.data()) > (0.2 if data_set.original_xz_ratio > 0.5 else 0.1), 1, 0)) == 0:
                                        logger.debug("☆接触回避実行成功(%s): f: %s(%s:%s:%s), axis: %s, 指定 [%s], 現在[%s], 差異[%s], dot[%s]", now_ik_max_count, fno, (data_set_idx + 1), \
                                                     list(ik_links.all().keys()), avoidance_name, axis, rep_collision_vec.to_log(), \
                                                     now_rep_effector_pos.to_log(), rep_diff.to_log(), list(dot_dict.values()))

                                        # # 回避後の先端ボーン位置 -------------
                                        # debug_bone_name = "{0}B".format(arm_link.last_name())

                                        # debug_bf = VmdBoneFrame(fno)
                                        # debug_bf.key = True
                                        # debug_bf.set_name(debug_bone_name)
                                        # debug_bf.position = now_rep_effector_pos
                                        
                                        # if debug_bone_name not in data_set.motion.bones:
                                        #     data_set.motion.bones[debug_bone_name] = {}
                                        
                                        # data_set.motion.bones[debug_bone_name][fno] = debug_bf
                                        # # ----------

                                        # org_bfを保持し直し
                                        for link_name in ik_links.all().keys():
                                            org_bfs[link_name] = data_set.motion.calc_bf(link_name, fno).copy()

                                        # 回避方向保持
                                        for link_name in list(ik_links.all().keys())[1:]:
                                            data_set.motion.bones[link_name][fno].avoidance = axis
                                
                                        # 大体同じ位置にあって、角度もそう大きくズレてない場合、OK(全部上書き)
                                        is_success = [True]
                                        
                                        # 衝突を計り直す
                                        (collision, near_collision, x_distance, z_distance, rep_x_collision_vec, rep_z_collision_vec) \
                                            = obb.get_collistion(now_rep_global_3ds[arm_link.last_name()], now_rep_global_3ds[arm_link.first_name()], \
                                                                 data_set.rep_model.bones[arm_bone_name].position.distanceToPoint(data_set.rep_model.bones[arm_link.last_name()].position))

                                        if (not collision and not near_collision) or prev_rep_diff == rep_diff or np.count_nonzero(np.where(np.abs(rep_diff.data()) > 0.05, 1, 0)) == 0:
                                            # 衝突していなければこのIKターンは終了
                                            # 前回とまったく同じ場合か、充分に近い場合、IK的に動きがないので終了
                                            break

                                        prev_rep_diff = rep_diff

                                    elif (prev_rep_diff == MVector3D() or (prev_rep_diff != MVector3D() and np.sum(np.abs(rep_diff.data())) < np.sum(np.abs(prev_rep_diff.data())))) and \
                                            (np.count_nonzero(np.where(np.abs(rep_diff.data()) > (1 if data_set.original_xz_ratio > 0.5 else 0.5), 1, 0)) == 0):
                                        logger.debug("☆接触回避実行ちょっと失敗採用(%s): f: %s(%s:%s:%s), axis: %s, 指定 [%s], 現在[%s], 差異[%s], dot[%s]", now_ik_max_count, fno, (data_set_idx + 1), \
                                                     list(ik_links.all().keys()), avoidance_name, axis, rep_collision_vec.to_log(), \
                                                     now_rep_effector_pos.to_log(), rep_diff.to_log(), list(dot_dict.values()))

                                        # # 回避後の先端ボーン位置 -------------
                                        # debug_bone_name = "{0}B".format(arm_link.last_name())

                                        # debug_bf = VmdBoneFrame(fno)
                                        # debug_bf.key = True
                                        # debug_bf.set_name(debug_bone_name)
                                        # debug_bf.position = now_rep_effector_pos
                                        
                                        # if debug_bone_name not in data_set.motion.bones:
                                        #     data_set.motion.bones[debug_bone_name] = {}
                                        
                                        # data_set.motion.bones[debug_bone_name][fno] = debug_bf
                                        # # ----------

                                        # org_bfを保持し直し
                                        for link_name in ik_links.all().keys():
                                            org_bfs[link_name] = data_set.motion.calc_bf(link_name, fno).copy()

                                        # 回避方向保持
                                        for link_name in list(ik_links.all().keys())[1:]:
                                            data_set.motion.bones[link_name][fno].avoidance = axis

                                        # 採用されたらOK
                                        is_success.append(True)
                                        # 衝突を計り直す
                                        (collision, near_collision, x_distance, z_distance, rep_x_collision_vec, rep_z_collision_vec) \
                                            = obb.get_collistion(now_rep_global_3ds[arm_link.last_name()], now_rep_global_3ds[arm_link.first_name()], \
                                                                 data_set.rep_model.bones[arm_bone_name].position.distanceToPoint(data_set.rep_model.bones[arm_link.last_name()].position))

                                        if (not collision and not near_collision) or prev_rep_diff == rep_diff or np.count_nonzero(np.where(np.abs(rep_diff.data()) > 0.05, 1, 0)) == 0:
                                            # 衝突していなければこのIKターンは終了
                                            # 前回とまったく同じ場合か、充分に近い場合、IK的に動きがないので終了
                                            break

                                        # 再チェックしてまだ接触してて、かつ最後の場合は失敗とする
                                        if now_ik_max_count == len(avoidance_options.ik_links_list[arm_link.last_name()]) - 1:
                                            # 最後が失敗していたら失敗
                                            is_success.append(False)
                                            failured_last_names.append(arm_link.last_name())

                                        prev_rep_diff = rep_diff
                                    else:
                                        logger.debug("★接触回避実行ちょっと失敗不採用(%s): f: %s(%s:%s:%s), axis: %s, 指定 [%s], 現在[%s], 差異[%s], dot[%s]", now_ik_max_count, fno, (data_set_idx + 1), \
                                                     list(ik_links.all().keys()), avoidance_name, axis, rep_collision_vec.to_log(), \
                                                     now_rep_effector_pos.to_log(), rep_diff.to_log(), list(dot_dict.values()))

                                        is_success.append(False)

                                        # 再チェックしてまだ接触してて、かつ最後の場合は失敗とする
                                        if now_ik_max_count == len(avoidance_options.ik_links_list[arm_link.last_name()]) - 1:
                                            # 最後が失敗していたら失敗
                                            failured_last_names.append(arm_link.last_name())

                                        # 前回とまったく同じ場合か、充分に近い場合、IK的に動きがないので終了
                                        if prev_rep_diff == rep_diff or np.count_nonzero(np.where(np.abs(rep_diff.data()) > 0.05, 1, 0)) == 0:
                                            break

                                        if prev_rep_diff == MVector3D():
                                            # 初回失敗の場合、とりあえず設定
                                            prev_rep_diff = rep_diff
                                else:
                                    logger.debug("★接触回避実行失敗(%s): f: %s(%s:%s:%s), axis: %s, 指定 [%s], 現在[%s], 差異[%s], dot[%s]", now_ik_max_count, fno, (data_set_idx + 1), \
                                                 list(ik_links.all().keys()), avoidance_name, axis, rep_collision_vec.to_log(), \
                                                 now_rep_effector_pos.to_log(), rep_diff.to_log(), list(dot_dict.values()))

                                    is_success.append(False)

                                    # 再チェックしてまだ接触してて、かつ最後の場合は失敗とする
                                    if now_ik_max_count == len(avoidance_options.ik_links_list[arm_link.last_name()]) - 1:
                                        # 最後が失敗していたら失敗
                                        failured_last_names.append(arm_link.last_name())

                                    # 前回とまったく同じ場合か、充分に近い場合、IK的に動きがないので終了
                                    if prev_rep_diff == rep_diff or np.count_nonzero(np.where(np.abs(rep_diff.data()) > 0.05, 1, 0)) == 0:
                                        break

                            if is_success == [True]:
                                # 成功していたらそのまま終了
                                break

                        if len(is_success) > 0:
                            if is_success.count(True) == 0:
                                # 全てのパターンで失敗してる場合、失敗ログ
                                logger.info("×接触回避失敗: f: %s(%s-%s)", fno, (data_set_idx + 1), arm_link.last_display_name())
                                
                                # 元々の値に戻す
                                for ik_links in avoidance_options.ik_links_list[arm_link.last_name()]:
                                    for link_name in list(ik_links.all().keys())[1:]:
                                        data_set.motion.regist_bf(org_bfs[link_name].copy(), link_name, fno)
                            else:
                                # どっか成功していたら、最後に成功したトコまで戻す
                                is_in_elbow = False
                                for ik_links in avoidance_options.ik_links_list[arm_link.last_name()]:
                                    is_in_elbow = is_in_elbow or elbow_bone_name in list(ik_links.all().keys())
                                    for link_name in list(ik_links.all().keys())[1:]:
                                        data_set.motion.regist_bf(org_bfs[link_name].copy(), link_name, fno)

                                if not is_in_elbow:
                                    # IKリストの中にひじが含まれていない場合、キャンセル
                                    arm_bf = data_set.motion.calc_bf(arm_bone_name, fno)
                                    elbow_bf = data_set.motion.calc_bf(elbow_bone_name, fno)
                                    # 腕の変化量YZのみをひじに加算
                                    elbow_adjust_qq = arm_bf.rotation.inverted() * arm_bf.org_rotation * elbow_bf.rotation

                                    logger.debug("◆手首調整: f: %s(%s:%s), arm_bf.org_rotation [%s], arm_bf.rotation[%s], elbow_bf.rotation[%s], adjust_qq[%s]", \
                                                 fno, (data_set_idx + 1), avoidance_name, arm_bf.org_rotation.toEulerAngles().to_log(), \
                                                 arm_bf.rotation.toEulerAngles().to_log(), elbow_bf.rotation.toEulerAngles().to_log(), elbow_adjust_qq.toEulerAngles().to_log())

                                    # 再設定
                                    elbow_bf.rotation = elbow_adjust_qq
                                    data_set.motion.regist_bf(elbow_bf, elbow_bone_name, fno)

                                if len(is_success) > 1 and is_success.count(False) > 0:
                                    # どこかのパターンで失敗している場合、一部成功ログ
                                    logger.info("△接触回避一部成功: f: %s(%s-%s)", fno, (data_set_idx + 1), arm_link.last_display_name())
                                else:
                                    # 全部成功している場合、成功ログ
                                    logger.info("○接触回避成功: f: %s(%s-%s)", fno, (data_set_idx + 1), arm_link.last_display_name())

            if fno // 500 > prev_block_fno and fnos[-1] > 0:
                logger.info("-- %sフレーム目:終了(%s％)【No.%s - 接触回避 - %s】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, direction)
                prev_block_fno = fno // 500
            
            # キーの登録が増えているかもなので、ここで取り直す
            fnos = data_set.motion.get_bone_fnos(*target_bone_names, start_fno=(fno + 1))

        for bone_name in target_bone_names:
            # 非活性キー削除
            data_set.motion.remove_unkey_bf(data_set_idx + 1, bone_name)

        return True

    # 接触回避準備
    cpdef dict prepare_avoidance_dataset(self, int data_set_idx, str direction):
        logger.info("接触回避準備【No.%s - %s】", (data_set_idx + 1), direction)

        cdef int aidx, fno, from_fno, prev_block_fno, to_fno
        cdef float block_x_distance, block_z_distance, x_distance, z_distance
        cdef list all_avoidance_list, fnos, prev_collisions
        cdef dict all_avoidance_axis, rep_avbone_global_3ds, rep_avbone_global_mats, rep_global_3ds, rep_matrixs, avoidance_list
        cdef str avoidance_name, bone_name
        cdef bint collision, near_collision
        cdef BoneLinks arm_link, avodance_link
        cdef ArmAvoidanceOption avoidance_options
        cdef MOptionsDataSet data_set
        cdef OBB obb
        cdef RigidBody avoidance
        cdef MVector3D rep_x_collision_vec, rep_z_collision_vec

        logger.copy(self.options)
        # 処理対象データセット
        data_set = self.options.data_set_list[data_set_idx]

        # 回避用オプション
        avoidance_options = self.avoidance_options[(data_set_idx, direction)]

        all_avoidance_list = [{}]
        prev_collisions = []
        prev_block_fno = 0
        fno = 0
        fnos = data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}腕捩".format(direction), "{0}ひじ".format(direction), "{0}手捩".format(direction), "{0}手首".format(direction))
        for fno in fnos:
            
            # 衝突しておらず、かつ前回の衝突情報がある場合、追加
            if prev_collisions.count(True) == 0 and len(all_avoidance_list[-1].keys()) > 0:
                # 前回衝突なしで今回衝突していたら、リスト追加
                all_avoidance_list.append({})
            
            prev_collisions = []

            for ((avoidance_name, avodance_link), avoidance) in zip(avoidance_options.avoidance_links.items(), avoidance_options.avoidances.values()):
                # 剛体の現在位置をチェック
                rep_avbone_global_3ds, rep_avbone_global_mats = \
                    MServiceUtils.calc_global_pos(data_set.rep_model, avodance_link, data_set.motion, fno, return_matrix=True)

                obb = avoidance.get_obb(fno, avodance_link.get(avodance_link.last_name()).position, rep_avbone_global_mats, self.options.arm_options.alignment, direction == "左")
            
                for arm_link in avoidance_options.arm_links:
                    # 先モデルのそれぞれのグローバル位置
                    rep_global_3ds, rep_matrixs = MServiceUtils.calc_global_pos(data_set.rep_model, arm_link, data_set.motion, fno, return_matrix=True)
                    [logger.debug("f: %s, k: %s, v: %s", fno, k, v) for k, v in rep_global_3ds.items()]

                    # 衝突情報を取る
                    (collision, near_collision, x_distance, z_distance, rep_x_collision_vec, rep_z_collision_vec) \
                        = obb.get_collistion(rep_global_3ds[arm_link.last_name()], rep_global_3ds["{0}腕".format(direction)], \
                                             data_set.rep_model.bones["{0}腕".format(direction)].position.distanceToPoint(data_set.rep_model.bones[arm_link.last_name()].position))

                    if collision or near_collision:
                        logger.debug("f: %s(%s-%s:%s), c[%s], nc[%s], xd[%s], zd[%s], xv[%s], zv[%s]", \
                                     fno, (data_set_idx + 1), arm_link.last_name(), avoidance_name, collision, near_collision, \
                                     x_distance, z_distance, rep_x_collision_vec.to_log(), rep_z_collision_vec.to_log())

                        # 衝突していたら、その中にキーフレ/ボーン名で登録
                        all_avoidance_list[-1][(fno, avoidance_name, arm_link.last_name())] = \
                            {"fno": fno, "avoidance_name": avoidance_name, "bone_name": arm_link.last_name(), "collision": collision, "near_collision": near_collision, \
                                "x_distance": x_distance, "z_distance": z_distance, "rep_x_collision_vec": rep_x_collision_vec, "rep_z_collision_vec": rep_z_collision_vec}

                    prev_collisions.append(collision)
                    prev_collisions.append(near_collision)

            if fno // 500 > prev_block_fno and fnos[-1] > 0:
                logger.info("-- %sフレーム目:終了(%s％)【No.%s - 接触回避準備① - %s】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, direction)
                prev_block_fno = fno // 500

        prev_block_fno = 0
        all_avoidance_axis = {}
        for aidx, avoidance_list in enumerate(all_avoidance_list):
            # 衝突ブロック単位で判定
            block_x_distance = 0
            block_z_distance = 0
            for (fno, avoidance_name, bone_name), avf in avoidance_list.items():
                collision = avf["collision"]
                near_collision = avf["near_collision"]
                x_distance = avf["x_distance"]
                z_distance = avf["z_distance"]
                rep_x_collision_vec = avf["rep_x_collision_vec"]
                rep_z_collision_vec = avf["rep_z_collision_vec"]

                # 距離を加算
                block_x_distance += x_distance
                block_z_distance += z_distance
            
            if len(avoidance_list.keys()) > 0:
                # 範囲
                from_fno = min([fno for (fno, avoidance_name, bone_name) in avoidance_list.keys()])
                to_fno = max([fno for (fno, avoidance_name, bone_name) in avoidance_list.keys()])

                # トータルで近い方の軸に移動させる
                all_avoidance_axis[from_fno] = {"from_fno": from_fno, "to_fno": to_fno, "axis": ("x" if block_x_distance * 1.5 < block_z_distance else "z")}
                logger.debug("aidx: %s, d: %s, from: %s, to: %s, axis: %s, xd: %s, zd: %s", aidx, direction, from_fno, to_fno, all_avoidance_axis[from_fno], block_x_distance, block_z_distance)

            if fno // 1000 > prev_block_fno and fnos[-1] > 0:
                logger.info("-- %sフレーム目:終了(%s％)【No.%s - 接触回避準備② - %s】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, direction)
                prev_block_fno = fno // 1000
            
        return all_avoidance_axis

    def calc_face_length(self, model: PmxModel):
        face_length = 1

        if "頭" in model.bones:
            # 顔の大きさ
            face_length = model.bones["頭頂実体"].position.y() - model.bones["頭"].position.y()

            if face_length == 0:
                if "首" in model.bones:
                    # 頭がなくて首がある場合、首までの長さ
                    face_length = model.bones["頭頂実体"].position.y() - model.bones["首"].position.y()
                else:
                    # 首もなければとりあえずよくある6頭身くらい
                    return 6

        # 全身の高さ
        total_height = model.bones["頭頂実体"].position.y()
            
        # 全身の高さ / 顔の大きさ　で頭身算出
        return total_height / face_length

    # 接触回避の準備
    def prepare_avoidance(self, data_set_idx: int, direction: str):
        data_set = self.options.data_set_list[data_set_idx]

        # 頭身計算
        face_length = self.calc_face_length(data_set.rep_model)

        avoidance_links = {}
        avoidances = {}
        
        if data_set_idx in self.options.arm_options.avoidance_target_list and "頭接触回避" in self.options.arm_options.avoidance_target_list[data_set_idx]:
            # 頭接触回避用剛体取得
            head_rigidbody = data_set.rep_model.get_head_rigidbody()
            head_rigidbody.is_small = (face_length <= 3)

            if head_rigidbody:
                logger.info("【No.%s - %s】頭接触回避用剛体: 半径: %s, 位置: %s", (data_set_idx + 1), direction, head_rigidbody.shape_size.x(), head_rigidbody.shape_position.to_log())
                avoidance_links[head_rigidbody.name] = data_set.rep_model.create_link_2_top_one(data_set.rep_model.bone_indexes[head_rigidbody.bone_index])
                avoidances[head_rigidbody.name] = head_rigidbody
            else:
                logger.info("【No.%s - %s】頭にウェイトが乗っている頂点が見つからなかった為、接触回避用剛体が作れませんでした。", (data_set_idx + 1), direction)

        # self.calc_wrist_entity_vertex(data_set_idx, data_set.rep_model, "変換先", direction)
        # self.calc_elbow_entity_vertex(data_set_idx, data_set.rep_model, "変換先", direction)
        # self.calc_elbow_middle_entity_vertex(data_set_idx, data_set.rep_model, "変換先", direction)
        
        logger.debug("list: %s", self.options.arm_options.avoidance_target_list)
        for avoidance_target in self.options.arm_options.avoidance_target_list[data_set_idx]:
            if avoidance_target and len(avoidance_target) > 0:
                for rigidbody_name, rigidbody in data_set.rep_model.rigidbodies.items():
                    # 処理対象剛体：剛体名が指定の文字列であり、かつボーン追従剛体
                    if avoidance_target == rigidbody_name and rigidbody.isModeStatic() and rigidbody.bone_index in data_set.rep_model.bone_indexes:
                        # 追従するボーンINDEXのリンク（ボーンは未定義のものも取得）
                        avoidance_links[rigidbody_name] = data_set.rep_model.create_link_2_top_one(data_set.rep_model.bone_indexes[rigidbody.bone_index], is_defined=False)
                        avoidances[rigidbody_name] = rigidbody
                        rigidbody.bone_name = data_set.rep_model.bone_indexes[rigidbody.bone_index]
                        # 腕より上の剛体か
                        rigidbody.is_arm_upper = rigidbody.shape_position.y() > data_set.rep_model.bones["右腕"].position.y()
                        # 小さい子か
                        rigidbody.is_small = (face_length <= 3)

                        logger.debug("%s-%s, %s: %s", data_set_idx, direction, rigidbody_name, rigidbody)

                        logger.info("【No.%s】判定対象剛体「%s」", (data_set_idx + 1), rigidbody_name)

        # グローバル位置計算用リンク
        arm_links = []
        # IK用リンク（エフェクタから追加していく）
        ik_links_list = {}
        ik_count_list = {}
         
        effector_bone_name_list = []

        effector_bone_name_list.append("{0}腕ひじ中間".format(direction))
        effector_bone_name_list.append("{0}ひじ".format(direction))

        # 腕を動かすパターン
        for effector_bone_name in effector_bone_name_list:
            # 末端までのリンク
            arm_link = data_set.rep_model.create_link_2_top_one(effector_bone_name)
            arm_links.append(arm_link)

            ik_links_list[effector_bone_name] = []
            ik_count_list[effector_bone_name] = []

            effector_bone = arm_link.get(effector_bone_name)

            arm_bone = arm_link.get("{0}腕".format(direction))
            arm_bone.dot_limit = 0.8
            arm_bone.degree_limit = 57.2957

            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(arm_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(30)

        effector_bone_name_list = []
       
        effector_bone_name_list.append("{0}ひじ手首中間".format(direction))
        effector_bone_name_list.append("{0}手首".format(direction))
        if "{0}人指先実体".format(direction) in data_set.rep_model.bones:
            effector_bone_name_list.append("{0}人指先実体".format(direction))

        # ひじも動かすパターン
        for effector_bone_name in effector_bone_name_list:
            # 末端までのリンク
            arm_link = data_set.rep_model.create_link_2_top_one(effector_bone_name)
            arm_links.append(arm_link)

            ik_links_list[effector_bone_name] = []
            ik_count_list[effector_bone_name] = []

            effector_bone = arm_link.get(effector_bone_name)

            elbow_bone = arm_link.get("{0}ひじ".format(direction))
            elbow_bone.dot_limit = 0.7
            elbow_bone.degree_limit = 57.2957

            arm_bone = arm_link.get("{0}腕".format(direction))
            arm_bone.dot_limit = 0.8
            arm_bone.degree_limit = 57.2957

            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(arm_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(30)

            # ik_links = BoneLinks()
            # ik_links.append(effector_bone)
            # ik_links.append(elbow_bone)
            # ik_links_list[effector_bone_name].append(ik_links)
            # ik_count_list[effector_bone_name].append(20)
            
            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(elbow_bone)
            ik_links.append(arm_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(30)

        # 手首リンク登録
        return ArmAvoidanceOption(arm_links, ik_links_list, ik_count_list, avoidance_links, avoidances, face_length)

    # 指定したモデル・方向の手のひら頂点
    def calc_wrist_entity_vertex(self, data_set_idx: int, model: PmxModel, target_model_type: str, direction: str):
        if "{0}手首実体".format(direction) not in model.bones:
            wrist_entity_vetex = model.get_wrist_vertex(direction)
            # XとZは手首の値（Yだけ頂点値）
            wrist_entity_pos = wrist_entity_vetex.position.copy()
            wrist_entity_pos.setX(model.bones["{0}手首".format(direction)].position.x())
            wrist_entity_pos.setZ(model.bones["{0}手首".format(direction)].position.z())
            wrist_entity_bone = Bone("{0}手首実体".format(direction), "", wrist_entity_pos, -1, 0, 0)
            wrist_entity_bone.index = len(model.bones.keys())
            model.bones[wrist_entity_bone.name] = wrist_entity_bone
            model.bone_indexes[wrist_entity_bone.index] = wrist_entity_bone.name
            model.wrist_entity_vertex[direction] = wrist_entity_vetex

        logger.info("【No.%s】%sモデルの%s手のひら頂点INDEX: %s (%s)", (data_set_idx + 1), target_model_type, direction, \
                    model.wrist_entity_vertex[direction].index, model.wrist_entity_vertex[direction].position.to_log())

    # 処理対象データセットINDEX取得
    def get_target_set_idxs(self):
        target_data_set_idxs = []
        for data_set_idx, data_set in enumerate(self.options.data_set_list):
            if data_set.motion.motion_cnt <= 0:
                # モーションデータが無い場合、処理スキップ
                continue
            
            if (self.options.arm_options.arm_check_skip_flg or (data_set.rep_model.can_arm_sizing and data_set.org_model.can_arm_sizing)) \
                    and data_set_idx not in target_data_set_idxs and data_set_idx in self.options.arm_options.avoidance_target_list:
                # ボーンセットがあり、腕系サイジング可能で、かつまだ登録されていない場合
                target_data_set_idxs.append(data_set_idx)
            
        return target_data_set_idxs

