# -*- coding: utf-8 -*-
#
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

# 床処理用INDEX
FLOOR_IDX = -1


# 剛体接触回避用オプション
class ArmAvoidanceOption():

    def __init__(self, arm_links: BoneLinks, ik_links_list: list, ik_count_list: list, avoidance_links: dict, avoidances: dict):
        super().__init__()

        self.arm_links = arm_links
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
            logger.warning("剛体接触回避ができるファイルセットが見つからなかったため、処理をスキップします。", decoration=MLogger.DECORATION_BOX)
            return True

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="avoidance", max_workers=2) as executor:
            for data_set_idx, data_set in enumerate(self.options.data_set_list):
                logger.info("剛体接触回避　【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)

                futures.append(executor.submit(self.execute_avoidance_pool, data_set_idx, "左"))
                futures.append(executor.submit(self.execute_avoidance_pool, data_set_idx, "右"))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        result = True

        for f in futures:
            result = f.result() and result
    
        return result

    # 剛体接触回避実行（先頭からキーフレ単位で見ていく必要があるので、並列化不可）
    def execute_avoidance_pool(self, data_set_idx: int, direction: str):
        try:
            logger.copy(self.options)
            # 処理対象データセット
            data_set = self.options.data_set_list[data_set_idx]

            # 剛体接触回避用準備
            avoidance_options = self.prepare_avoidance(data_set_idx, direction)

            prev_fno = 0
            fnos = data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction))
            for fno in fnos:
                self.execute_avoidance_frame(data_set_idx, direction, avoidance_options, fno)

                if fno // 500 > prev_fno and fnos[-1] > 0:
                    logger.info("-- %sフレーム目:終了(%s％)【No.%s-%s】", fno, round((fno / fnos[-1]) * 100, 3), data_set_idx + 1, direction)
                    prev_fno = fno // 500

            return True
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return False
        except Exception as e:
            logger.error("サイジング処理が意図せぬエラーで終了しました。", e)
            return False

    # フレーム単位の剛体接触回避処理
    def execute_avoidance_frame(self, data_set_idx: int, direction: str, avoidance_options: ArmAvoidanceOption, fno: int):
        # 処理対象データセット
        data_set = self.options.data_set_list[data_set_idx]

        for ((avoidance_name, avodance_link), avoidance) in zip(avoidance_options.avoidance_links.items(), avoidance_options.avoidances.values()):
            # 剛体の現在位置をチェック
            rep_avbone_global_3ds, rep_avbone_global_mats = \
                MServiceUtils.calc_global_pos(data_set.rep_model, avodance_link, data_set.motion, fno, return_matrix=True)

            obb = avoidance.get_obb(avodance_link.get(avodance_link.last_name()).position, rep_avbone_global_mats[avodance_link.last_name()])

            for arm_link in avoidance_options.arm_links:
                # 先モデルのそれぞれのグローバル位置
                rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, arm_link, data_set.motion, fno)

                collision, rep_collision_vec = obb.judge_collision(rep_global_3ds[arm_link.last_name()], direction)
                logger.debug("d: %s-%s, f: %s, col: %s, ret: %s", data_set_idx, direction, fno, collision, rep_collision_vec.to_log())

                if collision:
                    logger.info("○回避あり: f: %s(%s-%s), 元: %s, 回避: %s", fno, \
                                (data_set_idx + 1), arm_link.last_name(), rep_global_3ds[arm_link.last_name()].to_log(), rep_collision_vec.to_log())

                    # 変更前のbf（オリジナルモーションではなく、スタンス補正後なので、この時点のを保持）
                    org_bfs = {}
                    for ik_links in avoidance_options.ik_links_list[arm_link.last_name()]:
                        for link_name in ik_links.all().keys():
                            if link_name not in org_bfs:
                                org_bfs[link_name] = data_set.motion.calc_bf(link_name, fno).copy()

                    is_success = False
                    # まだIK処理が成功していない場合、IK処理実行
                    for ik_cnt, (ik_links, ik_max_count) in enumerate(zip(avoidance_options.ik_links_list[arm_link.last_name()], avoidance_options.ik_count_list[arm_link.last_name()])):
                        # IK計算実行
                        MServiceUtils.calc_IK(data_set.rep_model, arm_link, data_set.motion, fno, rep_collision_vec, ik_links, max_count=ik_max_count)

                        # 現在のエフェクタ位置
                        rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, arm_link, data_set.motion, fno)
                        now_rep_effector_pos = rep_global_3ds[arm_link.last_name()].data()

                        # 現在のエフェクタ位置との差分
                        rep_diff = rep_collision_vec - now_rep_effector_pos
                        
                        # IKの関連ボーンの内積チェック
                        dot_dict = {}
                        dot_limit_dict = {}
                        for link_name, link_bone in ik_links.all().items():
                            dot_dict[link_name] = MQuaternion.dotProduct(org_bfs[link_name].rotation, data_set.motion.calc_bf(link_name, fno).rotation)
                            dot_limit_dict[link_name] = link_bone.dot_limit

                        logger.debug("☆剛体接触回避実行(%s): f: %s(%s-%s), rep: %s, vec: %s, dot: %s", ik_cnt, fno, (data_set_idx + 1), \
                                     arm_link.last_name(), rep_collision_vec.to_log(), rep_diff.to_log(), list(dot_dict.values()))

                        if np.count_nonzero(np.where(np.abs(rep_diff.data()) > 0.3, 1, 0)) == 0 and \
                                np.count_nonzero(np.where(np.abs(np.array(list(dot_dict.values()))) < np.array(list(dot_limit_dict.values())), 1, 0)) == 0:
                            # 大体同じ位置にあって、角度もそう大きくズレてない場合、OK
                            is_success = True
                            break
                    
                    if not is_success:
                        # 最終的に失敗している場合、元に戻す
                        logger.info("×回避失敗: f: %s(%s-%s), 近似度: %s", fno, (data_set_idx + 1), \
                                    arm_link.last_name(), ", ".join([str(round(d, 5)) for d in dot_dict.values()]))
                        for link_name in ik_links.all().keys():
                            data_set.motion.bones[link_name][fno] = org_bfs[link_name]
                    
                    # どっちにしろbf確定(手首もここで確定)
                    for ik_links in avoidance_options.ik_links_list[arm_link.last_name()]:
                        for link_name in ik_links.all().keys():
                            data_set.motion.regist_bf(data_set.motion.calc_bf(link_name, fno), link_name, fno)

            # FIXME DEBUG ------------------
            # 剛体の原点 ---------------
            debug_bone_name = "右1"

            debug_bf = VmdBoneFrame(fno)
            debug_bf.key = True
            debug_bf.set_name(debug_bone_name)
            debug_bf.position = obb.origin
            
            if debug_bone_name not in data_set.motion.bones:
                data_set.motion.bones[debug_bone_name] = {}
            
            data_set.motion.bones[debug_bone_name][fno] = debug_bf

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

            if collision:
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
            
            # FIXME DEBUG ------------------

    # 剛体接触回避の準備
    def prepare_avoidance(self, data_set_idx: int, direction: str):
        data_set = self.options.data_set_list[data_set_idx]

        avoidance_links = {}
        avoidances = {}
        
        for avoidance_target in self.options.arm_options.avoidance_target_list:
            for rigidbody_name, rigidbody in data_set.rep_model.rigidbodies.items():
                # 処理対象剛体：剛体名が指定の文字列を含んでおり、かつボーン追従剛体
                if avoidance_target in rigidbody_name and (rigidbody.isModeStatic() or rigidbody.isModeMix()) and rigidbody.bone_index in data_set.rep_model.bone_indexes:
                    # 追従するボーンINDEXのリンク
                    avoidance_links[rigidbody_name] = data_set.rep_model.create_link_2_top_one(data_set.rep_model.bone_indexes[rigidbody.bone_index])
                    avoidances[rigidbody_name] = rigidbody

                    logger.debug("%s-%s, %s: %s", data_set_idx, direction, rigidbody_name, rigidbody)

        # グローバル位置計算用リンク
        arm_links = []
        # IK用リンク（エフェクタから追加していく）
        ik_links_list = {}
        ik_count_list = {}

        effector_bone_name_list = []

        effector_bone_name_list.append("{0}ひじ手首中間".format(direction))
        effector_bone_name_list.append("{0}手首".format(direction))
        if "{0}人指先".format(direction) in data_set.rep_model.bones:
            effector_bone_name_list.append("{0}人指先".format(direction))

        # 指先がどっちかにない場合、手首を対象とする
        for effector_bone_name in effector_bone_name_list:
            # 末端までのリンク
            arm_link = data_set.rep_model.create_link_2_top_one(effector_bone_name)
            arm_links.append(arm_link)

            ik_links_list[effector_bone_name] = []
            ik_count_list[effector_bone_name] = []

            effector_bone = arm_link.get(effector_bone_name)

            # ひじは角度制限をつける
            elbow_bone = arm_link.get("{0}ひじ".format(direction))
            elbow_bone.ik_limit_min = MVector3D(-180, -0.5, 0)
            elbow_bone.ik_limit_min = MVector3D(180, 180, 0)
            elbow_bone.dot_limit = 0.7

            arm_bone = arm_link.get("{0}腕".format(direction))
            arm_bone.dot_limit = 0.7

            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(arm_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(2)
                        
            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(elbow_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(2)

            ik_links = BoneLinks()
            ik_links.append(effector_bone)
            ik_links.append(elbow_bone)
            ik_links.append(arm_bone)
            ik_links_list[effector_bone_name].append(ik_links)
            ik_count_list[effector_bone_name].append(3)

        # 手首リンク登録
        return ArmAvoidanceOption(arm_links, ik_links_list, ik_count_list, avoidance_links, avoidances)

    # 処理対象データセットINDEX取得
    def get_target_set_idxs(self):
        target_data_set_idxs = []
        for data_set_idx, data_set in enumerate(self.options.data_set_list):
            if data_set.motion.motion_cnt <= 0:
                # モーションデータが無い場合、処理スキップ
                continue
            
            if (self.options.arm_options.arm_check_skip_flg or (data_set.rep_model.can_arm_sizing and data_set.org_model.can_arm_sizing)) \
                    and data_set_idx not in target_data_set_idxs:
                # ボーンセットがあり、腕系サイジング可能で、かつまだ登録されていない場合
                target_data_set_idxs.append(data_set_idx)
            
        return target_data_set_idxs
