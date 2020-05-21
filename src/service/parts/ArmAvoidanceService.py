# -*- coding: utf-8 -*-
#
import math
import numpy as np
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from mmd.PmxData import PmxModel, Bone # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions, MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MUtils, MServiceUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException

logger = MLogger(__name__, level=1)


# 接触回避用オプション
class ArmAvoidanceOption():

    def __init__(self, arm_links: BoneLinks, wrist_links: BoneLinks, ik_links_list: list, ik_count_list: list, avoidance_links: dict, avoidances: dict):
        super().__init__()

        self.arm_links = arm_links
        self.wrist_links = wrist_links
        self.ik_links_list = ik_links_list
        self.ik_count_list = ik_count_list
        self.avoidance_links = avoidance_links
        self.avoidances = avoidances


class ArmAvoidanceService():
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

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="avoidance") as executor:
            for data_set_idx, data_set in enumerate(self.options.data_set_list):
                futures.append(executor.submit(self.execute_avoidance_pool, data_set_idx, "右"))
                futures.append(executor.submit(self.execute_avoidance_pool, data_set_idx, "左"))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        result = True

        for f in futures:
            result = f.result() and result
        
        futures = []
        with ThreadPoolExecutor(thread_name_prefix="avoidance_after") as executor:
            for data_set_idx, data_set in enumerate(self.options.data_set_list):
                futures.append(executor.submit(self.avoidance_after, data_set_idx, "右"))
                futures.append(executor.submit(self.avoidance_after, data_set_idx, "左"))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False
    
        return result
    
    # 接触回避後処理
    def avoidance_after(self, data_set_idx: int, direction: str):
        try:
            logger.info("%s接触回避後処理【No.%s】", direction, (data_set_idx + 1))

            logger.copy(self.options)
            # 処理対象データセット
            data_set = self.options.data_set_list[data_set_idx]

            for bone_name in ["{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction)]:
                # 読み込んだ時のキーフレのみを対象とする
                fnos = data_set.motion.get_bone_fnos(bone_name, is_read=True)
                if len(fnos) < 2:
                    # 前後がない場合、全件キーフレ
                    all_fnos = data_set.motion.get_bone_fnos(bone_name)
                    fnos = [all_fnos[0], all_fnos[-1]]

                prev_sep_fno = 0
                log_target_idxs = []
                for fno_idx, fno in enumerate(data_set.motion.get_bone_fnos(bone_name)):
                    if fno // 500 > prev_sep_fno:
                        log_target_idxs.append(fno)
                        prev_sep_fno = fno // 500
                log_target_idxs.append(fnos[-1])

                for start_fno, end_fno in zip(fnos[:-1], fnos[1:]):
                    # 跳ねたりしてるのを円滑化
                    data_set.motion.smooth_bf(data_set_idx + 1, bone_name, start_fno, end_fno, data_set.rep_model.bones[bone_name].getRotatable(), \
                                              data_set.rep_model.bones[bone_name].getTranslatable(), 5, (end_fno in log_target_idxs))

                # フィルタリング処理
                data_set.motion.smooth_filter_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
                                                 data_set.rep_model.bones[bone_name].getTranslatable(), \
                                                 config={"freq": 30, "mincutoff": 0.5, "beta": 0.1, "dcutoff": 0.5})

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # 接触回避実行（先頭からキーフレ単位で見ていく必要があるので、並列化不可）
    def execute_avoidance_pool(self, data_set_idx: int, direction: str):
        try:
            logger.copy(self.options)
            # 処理対象データセット
            data_set = self.options.data_set_list[data_set_idx]

            # # 一旦登録
            # for fno in data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction)):
            #     for link_name in ["{0}腕".format(direction), "{0}ひじ".format(direction)]:
            #         now_bf = data_set.motion.calc_bf(link_name, fno)
            #         data_set.motion.regist_bf(now_bf, link_name, fno)

            prev_axis = ""
            prev_org_bfs = {}
            prev_correct_qq = {}
            prev_fno = 0
            prev_block_fno = 0
            fnos = data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction))
            while len(fnos) > 0:
                fno = fnos[0]
                
                prev_axis, prev_org_bfs, prev_correct_qq \
                    = self.execute_avoidance_frame(data_set_idx, direction, self.avoidance_options[(data_set_idx, direction)], \
                                                   fno, prev_axis, prev_fno, prev_org_bfs, prev_correct_qq)
                
                # 前回キーフレ保持
                prev_fno = fno

                if fno // 500 > prev_block_fno and fnos[-1] > 0:
                    logger.info("-- %sフレーム目:終了(%s％)【No.%s-%s】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, direction)
                    prev_block_fno = fno // 500
                
                # キーの登録が増えているかもなので、ここで取り直す
                fnos = data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction), start_fno=(fno + 1))

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.print_exc())
            raise e

    # フレーム単位の接触回避処理
    def execute_avoidance_frame(self, data_set_idx: int, direction: str, avoidance_options: ArmAvoidanceOption, fno: int, \
                                prev_axis: str, prev_fno: int, prev_org_bfs: dict, prev_correct_qq: dict):
        # 処理対象データセット
        data_set = self.options.data_set_list[data_set_idx]

        axis = prev_axis
        total_correct_qq = {}
        total_success_cnt = 0

        # キーフレ処理前のデータ
        total_org_bfs = {}
        for ik_links_list in avoidance_options.ik_links_list.values():
            for ik_links in ik_links_list:
                for link_name in ik_links.all().keys():
                    if link_name not in total_org_bfs:
                        total_org_bfs[link_name] = data_set.motion.calc_bf(link_name, fno).copy()

        arm_bone_name = "{0}腕".format(link_name[0])
        elbow_bone_name = "{0}ひじ".format(link_name[0])
        wrist_bone_name = "{0}手首".format(link_name[0])
        elbow_local_x_axis = data_set.rep_model.get_local_x_axis(elbow_bone_name)
        elbow_local_y_axis = MVector3D.crossProduct(elbow_local_x_axis, MVector3D(0, 0, -1)).normalized()
        # 変更前モーションの手首までのグローバル位置
        org_wrist_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, avoidance_options.wrist_links, data_set.motion, fno)

        is_total_success = []
        for ((avoidance_name, avodance_link), avoidance) in zip(avoidance_options.avoidance_links.items(), avoidance_options.avoidances.values()):
            # 剛体の現在位置をチェック
            rep_avbone_global_3ds, rep_avbone_global_mats = \
                MServiceUtils.calc_global_pos(data_set.rep_model, avodance_link, data_set.motion, fno, return_matrix=True)

            obb = avoidance.get_obb(fno, avodance_link.get(avodance_link.last_name()).position, rep_avbone_global_mats, self.options.arm_options.alignment, direction == "左")

            # 剛体の原点 ---------------
            debug_bone_name = "右1"

            debug_bf = VmdBoneFrame(fno)
            debug_bf.key = True
            debug_bf.set_name(debug_bone_name)
            debug_bf.position = obb.origin
            
            if debug_bone_name not in data_set.motion.bones:
                data_set.motion.bones[debug_bone_name] = {}
            
            data_set.motion.bones[debug_bone_name][fno] = debug_bf

            # 変更前のbf（オリジナルモーションではなく、スタンス補正後なので、この時点のを保持）
            org_bfs = {}
            for arm_link in avoidance_options.arm_links:
                for ik_links in avoidance_options.ik_links_list[arm_link.last_display_name()]:
                    for link_name in ik_links.all().keys():
                        if link_name not in org_bfs:
                            org_bfs[link_name] = data_set.motion.calc_bf(link_name, fno).copy()
            if elbow_bone_name not in org_bfs:
                org_bfs[elbow_bone_name] = data_set.motion.calc_bf(elbow_bone_name, fno).copy()
            
            collision = False
            is_success = []
            is_failure_last_names = []
            for arm_link in avoidance_options.arm_links:

                # 先モデルのそれぞれのグローバル位置
                rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, arm_link, data_set.motion, fno)

                # [logger.debug("f: %s, k: %s, v: %s", fno, k, v) for k, v in rep_global_3ds.items()]

                collision, near_collision, axis, rep_collision_vec = obb.get_collistion(rep_global_3ds[arm_link.last_name()], rep_global_3ds["{0}腕".format(arm_link.last_name()[0])], axis)
                logger.test("d: %s-%s, f: %s, col: %s, ret: %s", data_set_idx, direction, fno, collision, rep_collision_vec.to_log())

                if not collision and not near_collision:
                    axis = ""

                # FIXME DEBUG ------------------
                # 元の先端ボーン位置 -------------
                debug_bone_name = "{0}2".format(arm_link.last_name()[0])

                debug_bf = VmdBoneFrame(fno)
                debug_bf.key = True
                debug_bf.set_name(debug_bone_name)
                debug_bf.position = rep_global_3ds[arm_link.last_name()]
                
                if debug_bone_name not in data_set.motion.bones:
                    data_set.motion.bones[debug_bone_name] = {}
                
                data_set.motion.bones[debug_bone_name][fno] = debug_bf
                # ----------
                
                if near_collision:
                    logger.info("－近接あり: f: %s(%s-%s:%s:%s), 元: %s, 回避: %s", fno, \
                                (data_set_idx + 1), arm_link.last_display_name(), avoidance_name, axis, rep_global_3ds[arm_link.last_name()].to_log(), rep_collision_vec.to_log())
                elif collision:
                    logger.info("○接触あり: f: %s(%s-%s:%s:%s), 元: %s, 回避: %s", fno, \
                                (data_set_idx + 1), arm_link.last_display_name(), avoidance_name, axis, rep_global_3ds[arm_link.last_name()].to_log(), rep_collision_vec.to_log())

                # IK処理実行
                for ik_cnt, (ik_links, ik_max_count) in enumerate(zip(avoidance_options.ik_links_list[arm_link.last_display_name()], \
                                                                      avoidance_options.ik_count_list[arm_link.last_display_name()])):
                    is_target = False
                    is_target_names = []

                    if collision or near_collision:
                        # 衝突か近接の場合
                        for link_name in list(ik_links.all().keys())[1:]:
                            correct_qq = MQuaternion()

                            # 前回との差異
                            if link_name in prev_org_bfs:
                                bf = data_set.motion.calc_bf(link_name, fno)
                                prev_dot = MQuaternion.dotProduct(prev_org_bfs[link_name].rotation, bf.rotation)
                                
                                if prev_dot > 1 - math.radians(3) and link_name in prev_correct_qq:
                                    # 差異が一定以内の場合、前回の修正角度を適用するようリンク追加
                                    is_target_names.append(link_name)
                                else:
                                    logger.debug("前回適用なし f: %s(%s-%s:%s), prev[%s], now[%s], prev_dot[%s]", \
                                                 fno, (data_set_idx + 1), link_name, avoidance_name, \
                                                 prev_org_bfs[link_name].rotation.toEulerAngles().to_log(), \
                                                 bf.rotation.toEulerAngles().to_log(), prev_dot)

                                    # 処理対象外の場合False
                                    is_target_names.append(False)
                            else:
                                # 処理対象外の場合False
                                is_target_names.append(False)
                    
                    if len(is_target_names) > 0 and is_target_names.count(False) == 0:
                        for link_name in is_target_names:
                            if link_name in prev_correct_qq:
                                bf = data_set.motion.calc_bf(link_name, fno)
                                correct_qq = prev_correct_qq[link_name]

                                logger.debug("前回適用あり f: %s(%s-%s:%s), prev[%s], now[%s], prev_dot[%s], correct[%s]", \
                                             fno, (data_set_idx + 1), link_name, avoidance_name, \
                                             prev_org_bfs[link_name].rotation.toEulerAngles().to_log(), \
                                             bf.rotation.toEulerAngles().to_log(), prev_dot, correct_qq.toEulerAngles().to_log())

                                # 修正角度がある場合、修正角度適用
                                bf.rotation = bf.rotation * correct_qq
                                # とりあえず登録
                                data_set.motion.regist_bf(bf, link_name, fno)
                                # 過去のは削除
                                del prev_correct_qq[link_name]
                                del prev_org_bfs[link_name]
                                
                                # 回避後の接触状況を再確認
                                collision, near_collision, axis, rep_collision_vec = \
                                    obb.get_collistion(rep_global_3ds[arm_link.last_name()], rep_global_3ds["{0}腕".format(arm_link.last_name()[0])], axis)
                                logger.test("d: %s-%s, f: %s, col: %s, ret: %s", data_set_idx, direction, fno, collision, rep_collision_vec.to_log())

                                if (collision or near_collision) and link_name in org_bfs:
                                    # 回避後にも接触していたら処理対象をクリア
                                    is_target_names = []

                        is_target = True
                    
                    if (collision or near_collision) and (len(is_target_names) == 0 or is_target_names.count(False) > 0):
                        # 衝突していて、かつ前回適用がない場合

                        logger.debug("☆IK計算開始(%s): f: %s(%s:%s:%s), axis: %s, now[%s], new[%s]", ik_cnt, fno, (data_set_idx + 1), \
                                     list(ik_links.all().keys()), avoidance_name, axis, rep_global_3ds[arm_link.last_name()].to_log(), rep_collision_vec.to_log())
                        
                        # 修正角度がない場合、IK計算実行
                        MServiceUtils.calc_IK(data_set.rep_model, arm_link, data_set.motion, fno, rep_collision_vec, ik_links, max_count=ik_max_count)

                        is_target = True
                    
                    if is_target:
                        # 処理対象の場合のみ成功可否チェック

                        # 現在のエフェクタ位置
                        rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, arm_link, data_set.motion, fno)
                        now_rep_effector_pos = rep_global_3ds[arm_link.last_name()]

                        # 現在のエフェクタ位置との差分(エフェクタ位置が指定されている場合のみ)
                        rep_diff = MVector3D() if rep_collision_vec == MVector3D() else rep_collision_vec - now_rep_effector_pos

                        # 回避後の先端ボーン位置 -------------
                        debug_bone_name = "{0}3".format(arm_link.last_name()[0])

                        debug_bf = VmdBoneFrame(fno)
                        debug_bf.key = True
                        debug_bf.set_name(debug_bone_name)
                        debug_bf.position = rep_collision_vec
                        
                        if debug_bone_name not in data_set.motion.bones:
                            data_set.motion.bones[debug_bone_name] = {}
                        
                        data_set.motion.bones[debug_bone_name][fno] = debug_bf
                        # ----------

                        # for link_name, link_bone in ik_links.all().items():
                        #     logger.debug("(%s): f: %s(%s:%s:%s), org: %s, rep: %s", ik_cnt, fno, (data_set_idx + 1), \
                        #                  link_name, avoidance_name, org_bfs[link_name].rotation.toEulerAngles4MMD().to_log(), \
                        #                  data_set.motion.calc_bf(link_name, fno).rotation.toEulerAngles4MMD().to_log())
                        
                        # IKの関連ボーンの内積チェック
                        dot_dict = {}
                        dot_limit_dict = {}
                        for link_name, link_bone in ik_links.all().items():
                            dot_dict[link_name] = MQuaternion.dotProduct(org_bfs[link_name].rotation, data_set.motion.calc_bf(link_name, fno).rotation)
                            dot_limit_dict[link_name] = link_bone.dot_limit

                        if (np.count_nonzero(np.where(np.abs(rep_diff.data()) > 1, 1, 0)) == 0 and \
                                np.count_nonzero(np.where(np.array(list(dot_dict.values())) < np.array(list(dot_limit_dict.values())), 1, 0)) == 0) or \
                                (np.count_nonzero(np.where(np.array(list(dot_dict.values())) < 0.9, 1, 0)) == 0):
                            logger.debug("☆接触回避実行成功(%s): f: %s(%s:%s:%s), axis: %s, new: %s, now: %s, vec: %s, dot: %s", ik_cnt, fno, (data_set_idx + 1), \
                                         list(ik_links.all().keys()), avoidance_name, axis, rep_collision_vec.to_log(), now_rep_effector_pos.to_log(), rep_diff.to_log(), list(dot_dict.values()))

                            # 大体同じ位置にあって、角度もそう大きくズレてない場合、OK
                            is_success.append(True)
                            total_success_cnt += 1

                            for link_name in list(ik_links.all().keys())[1:]:
                                total_correct_qq[link_name] = total_org_bfs[link_name].rotation.inverted() * data_set.motion.calc_bf(link_name, fno).rotation
                                logger.debug("f: %s(%s:%s:%s), total_org[%s], now[%s], diff[%s]", fno, (data_set_idx + 1), link_name, avoidance_name, \
                                             total_org_bfs[link_name].rotation.toEulerAngles().to_log(), data_set.motion.calc_bf(link_name, fno).rotation.toEulerAngles().to_log(), \
                                             total_correct_qq[link_name].toEulerAngles().to_log())

                            # 成功していたら、オリジナルとして再保持
                            for link_name in ik_links.all().keys():
                                org_bfs[link_name] = data_set.motion.calc_bf(link_name, fno).copy()

                            collision, near_collision, axis, rep_collision_vec = \
                                obb.get_collistion(rep_global_3ds[arm_link.last_name()], rep_global_3ds["{0}腕".format(arm_link.last_name()[0])], axis)
                            logger.debug("成功後再チェック d: %s-%s, f: %s, col: %s, nc: %s, axis: %s, ret: %s", data_set_idx, direction, fno, collision, near_collision, axis, rep_collision_vec.to_log())
                            
                            if not collision and not near_collision:
                                # 衝突していなければ終了
                                break
                            else:
                                # 再チェックしてまだ接触してて、かつ最後の場合は失敗とする
                                if ik_cnt == len(avoidance_options.ik_links_list[arm_link.last_display_name()]) - 1:
                                    # 最後が失敗していたら失敗
                                    is_success.append(False)
                                    is_failure_last_names.append(arm_link.last_display_name())
                        else:
                            logger.debug("★接触回避実行失敗(%s): f: %s(%s:%s:%s), axis: %s, new: %s, now: %s, vec: %s, dot: %s", ik_cnt, fno, (data_set_idx + 1), \
                                         list(ik_links.all().keys()), avoidance_name, axis, rep_collision_vec.to_log(), now_rep_effector_pos.to_log(), rep_diff.to_log(), list(dot_dict.values()))

                            # 失敗していたら一旦元に戻す
                            if ik_cnt == len(avoidance_options.ik_links_list[arm_link.last_display_name()]) - 1:
                                # 最後が失敗していたら失敗
                                is_success.append(False)
                                is_failure_last_names.append(arm_link.last_display_name())

                            for link_name in list(ik_links.all().keys())[1:]:
                                data_set.motion.regist_bf(org_bfs[link_name].copy(), link_name, fno)
                                    
            if len(is_success) > 0 and is_success.count(False) > 0:
                # どこかのパターンで失敗してる場合、失敗ログ
                logger.info("×回避失敗: f: %s(%s-%s:%s) %s", fno, (data_set_idx + 1), direction, avoidance_name, ', '.join(list(set(is_failure_last_names))))
            
            # if len(is_success) > 0 and is_success.count(False) == 0:
            #     is_total_success.extend(is_success)
            #     # 全成功であれば、ひじの向きを調整前に合わせる
                
            #     # 元々のひじの角度
            #     org_elbow_x_qq, org_elbow_y_qq, org_elbow_z_qq, org_elbow_yz_qq = \
            #         MServiceUtils.separate_local_qq(fno, elbow_bone_name, org_bfs[elbow_bone_name].rotation, elbow_local_x_axis)
            #     # 現在のひじ
            #     elbow_bf = data_set.motion.calc_bf(elbow_bone_name, fno)
            #     rep_elbow_x_qq, rep_elbow_y_qq, rep_elbow_z_qq, rep_elbow_yz_qq = \
            #         MServiceUtils.separate_local_qq(fno, elbow_bone_name, elbow_bf.rotation, elbow_local_x_axis)

            #     # 回避後手首までのグローバル位置
            #     rep_wrist_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, avoidance_options.wrist_links, data_set.motion, fno)
            #     # 回避後ひじまでのグローバル位置（ひじ角度は初期値）
            #     rep_elbow_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, avoidance_options.wrist_links, data_set.motion, fno, \
            #                                                          limit_links=avoidance_options.wrist_links.from_links(arm_bone_name))

            #     # 初期スタンスから元のグローバル位置までの回転量
            #     correct_elbow_qq = MQuaternion.rotationTo((rep_elbow_global_3ds[wrist_bone_name] - rep_elbow_global_3ds[elbow_bone_name]).normalized(), \
            #                                               (org_wrist_global_3ds[wrist_bone_name] - rep_wrist_global_3ds[elbow_bone_name]).normalized())
            #     correct_elbow_y_qq = MQuaternion.fromAxisAndAngle(elbow_local_y_axis, correct_elbow_qq.toDegree())

            #     # Xの捩りと合わせてひじに登録する
            #     elbow_global_qq = correct_elbow_y_qq * org_elbow_x_qq
            #     logger.debug("ひじ調整(%s): f: %s(%s:%s:%s), axis: %s, org: %s, correct: %s, correcty: %s, rep: %s", ik_cnt, fno, (data_set_idx + 1), \
            #                  list(ik_links.all().keys()), avoidance_name, axis, org_bfs[elbow_bone_name].rotation.toEulerAngles().to_log(), \
            #                  correct_elbow_qq.toEulerAngles().to_log(), correct_elbow_y_qq.toEulerAngles().to_log(), elbow_global_qq.toEulerAngles().to_log())
                
            #     elbow_bf.rotation = elbow_global_qq
            #     data_set.motion.regist_bf(elbow_bf, elbow_bone_name, fno)

        # どっちにしろbf確定
        for arm_link in avoidance_options.arm_links:
            for ik_links in avoidance_options.ik_links_list[arm_link.last_display_name()]:
                for link_name in list(ik_links.all().keys())[1:]:
                    now_bf = data_set.motion.calc_bf(link_name, fno)
                    data_set.motion.regist_bf(now_bf, link_name, fno)
        
        if total_success_cnt == 0:
            # 1件も衝突成功がなければ軸クリア
            axis = ""

        return axis, total_org_bfs, total_correct_qq

    def calc_face_length(self, model: PmxModel):
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
        
        if "頭接触回避" in self.options.arm_options.avoidance_target_list[data_set_idx]:
            # 頭接触回避用剛体取得
            head_rigidbody = data_set.rep_model.get_head_rigidbody()
            head_rigidbody.is_small = (face_length <= 3)

            if head_rigidbody:
                logger.info("【No.%s-%s】頭接触回避用剛体: 半径: %s, 位置: %s", (data_set_idx + 1), direction, head_rigidbody.shape_size.x(), head_rigidbody.shape_position.to_log())
                avoidance_links[head_rigidbody.name] = data_set.rep_model.create_link_2_top_one(data_set.rep_model.bone_indexes[head_rigidbody.bone_index])
                avoidances[head_rigidbody.name] = head_rigidbody
            else:
                logger.info("【No.%s-%s】頭にウェイトが乗っている頂点が見つからなかった為、接触回避用剛体が作れませんでした。", (data_set_idx + 1), direction)

        self.calc_wrist_entity_vertex(data_set_idx, data_set.rep_model, "変換先", direction)
        # self.calc_elbow_entity_vertex(data_set_idx, data_set.rep_model, "変換先", direction)
        # self.calc_elbow_middle_entity_vertex(data_set_idx, data_set.rep_model, "変換先", direction)
        
        logger.debug("list: %s", self.options.arm_options.avoidance_target_list)
        for avoidance_target in self.options.arm_options.avoidance_target_list[data_set_idx]:
            if avoidance_target and len(avoidance_target) > 0:
                for rigidbody_name, rigidbody in data_set.rep_model.rigidbodies.items():
                    # 処理対象剛体：剛体名が指定の文字列であり、かつボーン追従剛体
                    if avoidance_target == rigidbody_name and rigidbody.isModeStatic() and rigidbody.bone_index in data_set.rep_model.bone_indexes:
                        # 追従するボーンINDEXのリンク
                        avoidance_links[rigidbody_name] = data_set.rep_model.create_link_2_top_one(data_set.rep_model.bone_indexes[rigidbody.bone_index])
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

        if "{0}人指先".format(direction) in data_set.rep_model.bones:
            effector_bone_name_list.append("{0}人指先".format(direction))
        effector_bone_name_list.append("{0}手首実体".format(direction))
        effector_bone_name_list.append("{0}ひじ手首中間".format(direction))

        # ひじも動かすパターン
        for effector_entity_bone_name in effector_bone_name_list:
            effector_bone_name = effector_entity_bone_name.replace("実体", "")

            # 末端までのリンク
            arm_link = data_set.rep_model.create_link_2_top_one(effector_entity_bone_name)
            arm_links.append(arm_link)

            ik_links_list[effector_bone_name] = []
            ik_count_list[effector_bone_name] = []

            effector_bone = arm_link.get(effector_bone_name)

            # ひじは角度制限をつける
            elbow_bone = arm_link.get("{0}ひじ".format(direction))
            # elbow_bone.ik_limit_min = MVector3D(-180, -0.5, -10)
            # elbow_bone.ik_limit_max = MVector3D(180, 180, 10)
            elbow_bone.dot_limit = 0.7

            arm_bone = arm_link.get("{0}腕".format(direction))
            arm_bone.dot_limit = 0.7

            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(arm_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(5)

            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(elbow_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(5)
            
            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(elbow_bone)
            ik_links.append(arm_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(10)
        
        effector_bone_name_list = []
        effector_bone_name_list.append("{0}ひじ".format(direction))
        effector_bone_name_list.append("{0}腕ひじ中間".format(direction))

        # 腕を動かすパターン
        for effector_entity_bone_name in effector_bone_name_list:
            effector_bone_name = effector_entity_bone_name.replace("実体", "")

            # 末端までのリンク
            arm_link = data_set.rep_model.create_link_2_top_one(effector_entity_bone_name)
            arm_links.append(arm_link)

            ik_links_list[effector_bone_name] = []
            ik_count_list[effector_bone_name] = []

            effector_bone = arm_link.get(effector_bone_name)

            arm_bone = arm_link.get("{0}腕".format(direction))
            arm_bone.dot_limit = 0.7

            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(arm_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(5)
        
        wrist_links = data_set.rep_model.create_link_2_top_one("{0}手首".format(direction))

        # 手首リンク登録
        return ArmAvoidanceOption(arm_links, wrist_links, ik_links_list, ik_count_list, avoidance_links, avoidances)

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

    # # 指定したモデル・方向の手のひら頂点
    # def calc_elbow_entity_vertex(self, data_set_idx: int, model: PmxModel, target_model_type: str, direction: str):
    #     if "{0}ひじ実体".format(direction) not in model.bones:
    #         elbow_entity_vetex = model.get_elbow_vertex(direction)
    #         # XとZはひじの値（Yだけ頂点値）
    #         elbow_entity_pos = elbow_entity_vetex.position.copy()
    #         elbow_entity_pos.setX(model.bones["{0}ひじ".format(direction)].position.x())
    #         elbow_entity_pos.setZ(model.bones["{0}ひじ".format(direction)].position.z())
    #         elbow_entity_bone = Bone("{0}ひじ実体".format(direction), "", elbow_entity_pos, -1, 0, 0)
    #         elbow_entity_bone.index = len(model.bones.keys())
    #         model.bones[elbow_entity_bone.name] = elbow_entity_bone
    #         model.bone_indexes[elbow_entity_bone.index] = elbow_entity_bone.name
    #         model.elbow_entity_vertex[direction] = elbow_entity_vetex

    #     logger.info("【No.%s】%sモデルの%sひじ頂点INDEX: %s (%s)", (data_set_idx + 1), target_model_type, direction, \
    #                 model.elbow_entity_vertex[direction].index, model.elbow_entity_vertex[direction].position.to_log())

    # # 指定したモデル・方向の手のひら頂点
    # def calc_elbow_middle_entity_vertex(self, data_set_idx: int, model: PmxModel, target_model_type: str, direction: str):
    #     if "{0}ひじ手首中間実体".format(direction) not in model.bones:
    #         elbow_entity_vetex = model.get_elbow_vertex(direction)
    #         # XとZはひじ手首中間の値（Yだけ頂点値）
    #         elbow_middle_entity_pos = elbow_entity_vetex.position.copy()
    #         elbow_middle_entity_pos.setX(model.bones["{0}ひじ手首中間".format(direction)].position.x())
    #         elbow_middle_entity_pos.setY(elbow_middle_entity_pos.y() - model.bones["{0}ひじ".format(direction)].position.y() + model.bones["{0}ひじ手首中間".format(direction)].position.y())
    #         elbow_middle_entity_pos.setZ(model.bones["{0}ひじ手首中間".format(direction)].position.z())
    #         elbow_middle_entity_bone = Bone("{0}ひじ手首中間実体".format(direction), "", elbow_middle_entity_pos, -1, 0, 0)
    #         elbow_middle_entity_bone.index = len(model.bones.keys())
    #         model.bones[elbow_middle_entity_bone.name] = elbow_middle_entity_bone
    #         model.bone_indexes[elbow_middle_entity_bone.index] = elbow_middle_entity_bone.name
    #         model.elbow_middle_entity_vertex[direction] = elbow_entity_vetex

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

