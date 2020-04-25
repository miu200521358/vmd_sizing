# -*- coding: utf-8 -*-
#
import numpy as np
import math

from mmd.PmxData import PmxModel, Bone # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions, MOptionsDataSet
from module.MParams import BoneLinks
from utils import MUtils, MServiceUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException

logger = MLogger(__name__, level=1)


class ArmAlignmentService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        # 腕処理対象データセットを取得
        self.target_data_set_idxs = self.get_target_set_idxs()
        logger.test("target_data_set_idxs: %s", self.target_data_set_idxs)

        if len(self.target_data_set_idxs) == 0:
            # データセットがない場合、処理スキップ
            logger.warning("手首位置合わせができるファイルセットが見つからなかったため、位置合わせ処理をスキップします。", decoration=MLogger.DECORATION_BOX)
            return True

        # リンク辞書
        self.target_links = {}
        # 処理対象キーフレ
        fnos = []

        for data_set_idx in self.target_data_set_idxs:
            # 処理対象データセットに対して、準備実行

            # 手首位置合わせ用準備
            fnos.extend(self.prepare_wrist(data_set_idx))

            # 準備が終わったら、キーフレを追加していく
            if self.options.arm_options.alignment_finger_flg:
                # 指位置合わせ用準備
                fnos.extend(self.prepare_finger(data_set_idx))
            
        # キーフレを重複を除外してソートする
        self.target_fnos = sorted(list(set(fnos)))

        result = True

        if self.options.arm_options.alignment_finger_flg:
            # 指位置合わせ実行
            pass
        else:
            # 手首位置合わせ実行（先頭からキーフレ単位で見ていく必要があるので、並列化不可）
            for fno in self.target_fnos:
                self.execute_alignment(fno)
    
        return result

    # 位置合わせ実行
    def execute_alignment(self, fno: int):
        org_global_3ds_dict = {}
        org_front_global_3ds_dict = {}
        org_direction_qq_dict = {}

        # 処理対象キーフレを先頭からひとつずつチェックしていく
        for data_set_idx, alignment_options in self.target_links.items():
            for alignment_idx, alignment_option in enumerate(alignment_options):
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]

                # 元モデルのそれぞれの位置
                org_global_3ds, org_front_global_3ds, org_direction_qq = \
                    MServiceUtils.calc_front_global_pos(data_set.org_model, alignment_option.org_links, data_set.org_motion, fno)
                # 辞書に追加
                org_global_3ds_dict[(data_set_idx, alignment_idx)] = org_global_3ds
                org_front_global_3ds_dict[(data_set_idx, alignment_idx)] = org_front_global_3ds
                org_direction_qq_dict[(data_set_idx, alignment_idx)] = org_direction_qq

        distances = {}

        # それぞれの距離を算出
        # 起点となるボーン
        for (from_data_set_idx, from_alignment_idx), org_from_global_3ds in org_global_3ds_dict.items():
            for (to_data_set_idx, to_alignment_idx), org_from_to_global_3ds in org_global_3ds_dict.items():
                if (from_data_set_idx, from_alignment_idx) == (to_data_set_idx, to_alignment_idx) or from_data_set_idx > to_data_set_idx or \
                        (from_data_set_idx == to_data_set_idx and \
                            (from_alignment_idx > to_alignment_idx or \
                             self.target_links[from_data_set_idx][from_alignment_idx].org_links.last_name() == self.target_links[to_data_set_idx][to_alignment_idx].org_links.last_name())):
                    # 同じINDEXか前のINDEXは計算不要
                    continue

                # 2点間の距離を算出
                distances[(from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx)] \
                    = org_from_global_3ds[self.target_links[from_data_set_idx][from_alignment_idx].org_links.last_name()].distanceToPoint(\
                        org_from_to_global_3ds[self.target_links[to_data_set_idx][to_alignment_idx].org_links.last_name()])

        target_idxs = {}
        for (from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx), distance in distances.items():
            # 距離を2点間の手のひらの大きさの平均から比率として求める
            distance_ratio = distance / np.mean([self.target_links[from_data_set_idx][from_alignment_idx].org_palm_length, self.target_links[to_data_set_idx][to_alignment_idx].org_palm_length])
            logger.test("fno: %s, (%s,%s,%s,%s): d: %s, dr: %s", fno, from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx, distance, distance_ratio)
            
            # 基準距離（FROMもTOも同じ値）
            base_distance = self.target_links[from_data_set_idx][from_alignment_idx].distance
            if 0 < distance_ratio <= base_distance or base_distance == 10:
                # 基準距離以内か常に位置合わせを行うかの場合、位置合わせ処理実行
                logger.info("○近接あり: f: %s(%s-%s:%s-%s), 境界: %s, 手首間の距離: %s", fno, \
                            (from_data_set_idx + 1), self.target_links[from_data_set_idx][from_alignment_idx].org_links.last_name()[:3], \
                            (to_data_set_idx + 1), self.target_links[to_data_set_idx][to_alignment_idx].org_links.last_name()[:3], distance_ratio, base_distance)

                # 近接処理対象INDEXとその位置（numpyデータ）を配置
                if (from_data_set_idx, from_alignment_idx) not in target_idxs:
                    target_idxs[(from_data_set_idx, from_alignment_idx)] = org_global_3ds_dict[(from_data_set_idx, from_alignment_idx)][\
                        self.target_links[from_data_set_idx][from_alignment_idx].org_links.last_name()].data()

                if (to_data_set_idx, to_alignment_idx) not in target_idxs:
                    target_idxs[(to_data_set_idx, to_alignment_idx)] = org_global_3ds_dict[(to_data_set_idx, to_alignment_idx)][
                        self.target_links[to_data_set_idx][to_alignment_idx].org_links.last_name()].data()

            elif base_distance < distance_ratio <= base_distance * 1.5:
                # 基準距離に近い場合、ログだけ出す
                logger.info("－近接なし: f: %s(%s-%s:%s-%s), 境界: %s, 手首間の距離: %s", fno, \
                            (from_data_set_idx + 1), self.target_links[from_data_set_idx][from_alignment_idx].org_links.last_name()[:3], \
                            (to_data_set_idx + 1), self.target_links[to_data_set_idx][to_alignment_idx].org_links.last_name()[:3], distance_ratio, base_distance)

        if len(target_idxs.keys()) > 0:
            rep_global_3ds_dict = {}
            rep_front_global_3ds_dict = {}
            rep_direction_qq_dict = {}

            org_front_to_pos_dict = {}
            rep_front_to_pos_dict = {}
            rep_ratios = {}
            for (data_set_idx, alignment_idx), org_front_to_pos in target_idxs.items():
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]

                # 先モデルのそれぞれの位置
                rep_global_3ds, rep_front_global_3ds, rep_direction_qq = \
                    MServiceUtils.calc_front_global_pos(data_set.rep_model, self.target_links[data_set_idx][alignment_idx].rep_links, data_set.motion, fno)
                # 辞書に追加
                rep_global_3ds_dict[(data_set_idx, alignment_idx)] = rep_global_3ds
                rep_front_global_3ds_dict[(data_set_idx, alignment_idx)] = rep_front_global_3ds
                rep_direction_qq_dict[(data_set_idx, alignment_idx)] = rep_direction_qq

                # 正面向きのFROMボーンの位置
                org_front_from_pos = org_front_global_3ds_dict[(data_set_idx, alignment_idx)][\
                    self.target_links[data_set_idx][alignment_idx].ik_links.first_name()].data()
                rep_front_from_pos = rep_front_global_3ds_dict[(data_set_idx, alignment_idx)][\
                    self.target_links[data_set_idx][alignment_idx].ik_links.first_name()].data()

                # 先モデルのTOボーンの位置を再算出
                rep_front_to_pos = rep_front_from_pos + ((org_front_to_pos - org_front_from_pos) * self.target_links[data_set_idx][alignment_idx].ratio.data())
                rep_front_to_pos_dict[(data_set_idx, alignment_idx)] = rep_front_to_pos

                # 比率保持
                rep_ratios[(data_set_idx, alignment_idx)] = self.target_links[data_set_idx][alignment_idx].ratio.data()

                # 元モデルのTOボーンの位置
                org_front_to_pos_dict[(data_set_idx, alignment_idx)] = org_front_to_pos

            # 先モデルの再算出TO位置の中心点
            rep_front_to_poses = np.array(list(rep_front_to_pos_dict.values()))
            rep_data_set_mean = np.mean(rep_front_to_poses, axis=0)

            logger.test("fno: %s, rep avg: %s, rep: %s", fno, rep_data_set_mean, rep_front_to_poses)

            # 元モデルの中心点
            org_front_to_poses = np.array(list(org_front_to_pos_dict.values()))
            org_data_set_mean = np.mean(org_front_to_poses, axis=0)

            # 元モデルの中心点との差を求める
            org_data_set_diff = org_front_to_poses - np.tile(org_data_set_mean, (org_front_to_poses.shape[0], 1))
            logger.test("fno: %s, org avg: %s, org: %s", fno, org_data_set_mean, org_front_to_poses)
            logger.test("fno: %s, org diff: %s", fno, org_data_set_diff)

            # # 先モデルの比率に合わせる
            # rep_data_set_diff = org_data_set_diff * list(rep_ratios.values())
            # logger.test("fno: %s, rep diff: %s", fno, rep_data_set_diff)

            # 差を先モデルの位置に加算する
            new_rep_front_to_poses = org_data_set_diff + np.tile(rep_data_set_mean, (rep_front_to_poses.shape[0], 1))
            logger.test("fno: %s, rep new pos: %s", fno, new_rep_front_to_poses)

            for (data_set_idx, alignment_idx) in target_idxs.keys():
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]

                # 中心点 ---------------
                avg_bone_name = "右1"

                avg_bf = VmdBoneFrame(fno)
                avg_bf.key = True
                avg_bf.set_name(avg_bone_name)
                avg_bf.position = MVector3D(rep_data_set_mean)
                
                if avg_bone_name not in data_set.motion.bones:
                    data_set.motion.bones[avg_bone_name] = {}
                
                data_set.motion.bones[avg_bone_name][fno] = avg_bf

                # 変換先のTO再算出位置 -----------
                rep_entity_bone_name = "{0}2".format(self.target_links[data_set_idx][alignment_idx].org_links.last_name()[0])

                rep_entity_bf = VmdBoneFrame(fno)
                rep_entity_bf.key = True
                rep_entity_bf.set_name(rep_entity_bone_name)
                rep_entity_bf.position = MVector3D(rep_front_to_poses[data_set_idx])
                
                if rep_entity_bone_name not in data_set.motion.bones:
                    data_set.motion.bones[rep_entity_bone_name] = {}
                
                data_set.motion.bones[rep_entity_bone_name][fno] = rep_entity_bf

                # 計算後のTOボーン位置 -------------
                wrist_bone_name = "{0}3".format(self.target_links[data_set_idx][alignment_idx].rep_links.last_name()[0])

                wrist_bf = VmdBoneFrame(fno)
                wrist_bf.key = True
                wrist_bf.set_name(wrist_bone_name)
                wrist_bf.position = MVector3D(new_rep_front_to_poses[data_set_idx])
                
                if wrist_bone_name not in data_set.motion.bones:
                    data_set.motion.bones[wrist_bone_name] = {}
                
                data_set.motion.bones[wrist_bone_name][fno] = wrist_bf

                # 実体ボーン位置 -------------
                entity_bone_name = "{0}4".format(self.target_links[data_set_idx][alignment_idx].rep_links.last_name()[0])

                entity_bf = VmdBoneFrame(fno)
                entity_bf.key = True
                entity_bf.set_name(entity_bone_name)
                entity_bf.position = rep_global_3ds_dict[(data_set_idx, alignment_idx)][self.target_links[data_set_idx][alignment_idx].rep_links.last_name()]
                
                if entity_bone_name not in data_set.motion.bones:
                    data_set.motion.bones[entity_bone_name] = {}
                
                data_set.motion.bones[entity_bone_name][fno] = entity_bf
            
    # 手首位置合わせの準備
    def prepare_wrist(self, data_set_idx: int):
        self.target_links[data_set_idx] = []
        data_set = self.options.data_set_list[data_set_idx]

        fnos = []

        org_arm_links = data_set.org_model.create_link_2_top_lr("手首")
        rep_arm_links = data_set.rep_model.create_link_2_top_lr("手首")

        for direction in ["左", "右"]:
            # 手のひら頂点計算
            self.calc_wrist_entity_vertex(data_set_idx, data_set.org_model, "作成元", direction)
            self.calc_wrist_entity_vertex(data_set_idx, data_set.rep_model, "変換先", direction)

            # 手首実体リンク
            org_wrist_links = data_set.org_model.create_link_2_top_one("{0}手首実体".format(direction))
            rep_wrist_links = data_set.rep_model.create_link_2_top_one("{0}手首実体".format(direction))

            # IK用リンク（末端から追加していく）
            ik_links = BoneLinks()
            ik_links.append(rep_wrist_links.get("{0}手首".format(direction)))
            ik_links.append(rep_wrist_links.get("{0}ひじ".format(direction)))
            ik_links.append(rep_wrist_links.get("{0}腕".format(direction)))

            # 手のひらの長さ
            org_palm_length = (data_set.org_model.bones["{0}手首".format(direction)].position - data_set.org_model.bones["{0}人指先".format(direction)].position).length()
            rep_palm_length = (data_set.rep_model.bones["{0}手首".format(direction)].position - data_set.rep_model.bones["{0}人指先".format(direction)].position).length()

            # 手首リンク登録
            self.target_links[data_set_idx].append(ArmAlignmentOption(org_wrist_links, rep_wrist_links, ik_links, org_palm_length, rep_palm_length, \
                                                                      org_arm_links, rep_arm_links, self.options.arm_options.alignment_distance_wrist))

            # 腕・ひじ・手首のキーフレ
            fnos.extend(data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction)))

        return fnos

    # 指位置合わせの準備
    def prepare_finger(self, data_set_idx: int):
        data_set = self.options.data_set_list[data_set_idx]

        fnos = []

        org_arm_links = data_set.org_model.create_link_2_top_lr("手首")
        rep_arm_links = data_set.rep_model.create_link_2_top_lr("手首")

        for direction in ["左", "右"]:
            rep_wrist_links = data_set.rep_model.create_link_2_top_one("{0}手首".format(direction))

            # IK用リンク（末端から追加していく）
            ik_links = BoneLinks()
            ik_links.append(rep_wrist_links.get("{0}手首".format(direction)))
            ik_links.append(rep_wrist_links.get("{0}ひじ".format(direction)))
            ik_links.append(rep_wrist_links.get("{0}腕".format(direction)))

            # 手のひらの長さ
            org_palm_length = (data_set.org_model.bones["{0}手首".format(direction)].position - data_set.org_model.bones["{0}人指先".format(direction)].position).length()
            rep_palm_length = (data_set.rep_model.bones["{0}手首".format(direction)].position - data_set.rep_model.bones["{0}人指先".format(direction)].position).length()

            for finger_name in ["親指", "人指", "中指", "薬指", "小指"]:
                # 指リンク
                org_finger_links = data_set.org_model.create_link_2_top_one("{0}{1}先".format(direction, finger_name))
                rep_finger_links = data_set.rep_model.create_link_2_top_one("{0}{1}先".format(direction, finger_name))

                # 指リンク登録
                self.target_links[data_set_idx].append(ArmAlignmentOption(org_finger_links, rep_finger_links, ik_links, org_palm_length, rep_palm_length, \
                                                                          org_arm_links, rep_arm_links, self.options.arm_options.alignment_distance_finger))

                # 腕・ひじ・手首・指のキーフレ（なければスルー）
                fnos.extend(data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction), "{0}{1}０".format(direction, finger_name), \
                                                          "{0}{1}１".format(direction, finger_name), "{0}{1}２".format(direction, finger_name), "{0}{1}３".format(direction, finger_name)))

        return fnos

    # 指定したモデル・方向の手のひら頂点
    def calc_wrist_entity_vertex(self, data_set_idx: int, model: PmxModel, target_model_type: str, direction: str):
        if "{0}手首実体".format(direction) not in model.bones:
            wrist_entity_vertex = model.get_wrist_vertex(direction)
            wrist_entity_bone = Bone("{0}手首実体".format(direction), "", wrist_entity_vertex.position.copy(), -1, 0, 0)
            wrist_entity_bone.index = len(model.bones.keys())
            model.bones[wrist_entity_bone.name] = wrist_entity_bone
            model.bone_indexes[wrist_entity_bone.index] = wrist_entity_bone.name
            model.wrist_entity_vertex[direction] = wrist_entity_vertex

        logger.info("【No.%s】%sモデルの%s手のひら頂点INDEX: %s (%s)", (data_set_idx + 1), target_model_type, direction, \
                    model.wrist_entity_vertex[direction].index, model.wrist_entity_vertex[direction].position.to_log())

    # 処理対象データセットINDEX取得
    def get_target_set_idxs(self):
        target_data_set_idxs = []
        for data_set_idx, data_set in enumerate(self.options.data_set_list):
            if data_set.motion.motion_cnt <= 0:
                # モーションデータが無い場合、処理スキップ
                continue
            
            if data_set.rep_model.can_arm_sizing and data_set.org_model.can_arm_sizing and data_set_idx not in target_data_set_idxs:
                # ボーンセットがあり、腕系サイジング可能で、かつまだ登録されていない場合
                target_data_set_idxs.append(data_set_idx)
            
        return target_data_set_idxs


# 位置合わせ用オプション
class ArmAlignmentOption():

    def __init__(self, org_links: BoneLinks, rep_links: BoneLinks, ik_links: BoneLinks, org_palm_length: float, rep_palm_length: float, \
                 org_arm_links: BoneLinks, rep_arm_links: BoneLinks, distance: float):
        super().__init__()

        self.org_links = org_links
        self.rep_links = rep_links
        self.ik_links = ik_links
        self.org_palm_length = org_palm_length
        self.rep_palm_length = rep_palm_length
        self.distance = distance
        
        # 肩幅比率
        org_arm_diff = (org_arm_links["左"].get("左腕").position - org_arm_links["右"].get("右腕").position)
        rep_arm_diff = (rep_arm_links["左"].get("左腕").position - rep_arm_links["右"].get("右腕").position)
        arm_diff_ratio = rep_arm_diff / org_arm_diff
        arm_diff_ratio.one()    # 比率なので、0は1に変換する

        # TOの長さ比率（IKは末端から登録されているので、腕は最後）
        org_to_diff = (org_links.get(org_links.last_name()).position - ik_links.get(ik_links.last_name()).position)
        org_to_diff.abs()
        rep_to_diff = (rep_links.get(rep_links.last_name()).position - ik_links.get(ik_links.last_name()).position)
        rep_to_diff.abs()
        to_diff_ratio = rep_to_diff / org_to_diff

        # 元と先の比率
        self.ratio = MVector3D(arm_diff_ratio.x(), to_diff_ratio.y(), arm_diff_ratio.x())
        
        # 先の腕の長さ
        self.arm_diff = rep_arm_links["右"].get("右腕").position - rep_arm_links["右"].get("右手首").position
        self.arm_diff.abs()


