# -*- coding: utf-8 -*-
#
import copy
import numpy as np

from mmd.PmxData import PmxModel, Bone # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions, MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MUtils, MServiceUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException # noqa

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
            all_prev_org_last_poses_indexes = {}
            all_prev_rep_last_poses_indexes = {}
            # 手首位置合わせ実行（先頭からキーフレ単位で見ていく必要があるので、並列化不可）
            for fno in self.target_fnos:
                all_prev_org_last_poses_indexes, all_prev_rep_last_poses_indexes = \
                    self.execute_alignment(fno, all_prev_org_last_poses_indexes, all_prev_rep_last_poses_indexes)
    
        return result

    # 位置合わせ実行
    def execute_alignment(self, fno: int, all_prev_org_last_poses_indexes: dict, all_prev_rep_last_poses_indexes: dict):
        all_org_global_3ds = {}
        all_org_last_poses_indexes = {}
        all_rep_last_poses_indexes = {}

        # 処理対象キーフレを先頭からひとつずつチェックしていく
        for data_set_idx, alignment_options in self.target_links.items():
            for alignment_idx, alignment_option in enumerate(alignment_options):
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]
                # 処理対象
                target_link = self.target_links[data_set_idx][alignment_idx]

                # 元モデルのそれぞれの位置
                org_global_3ds = MServiceUtils.calc_global_pos(data_set.org_model, alignment_option.org_links, data_set.org_motion, fno)
                # 辞書に追加
                all_org_global_3ds[(data_set_idx, alignment_idx)] = org_global_3ds

                # 元モデルの末端位置（numpyデータ）
                all_org_last_poses_indexes[(data_set_idx, alignment_idx)] = all_org_global_3ds[(data_set_idx, alignment_idx)][target_link.last_bone_name].data()

                # 先モデルの末端位置（numpyデータ）
                rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, target_link.rep_links, data_set.motion, fno)
                all_rep_last_poses_indexes[(data_set_idx, alignment_idx)] = rep_global_3ds[target_link.last_bone_name].data()

        distances = {}

        # それぞれの距離を算出
        # 起点となるボーン
        for (from_data_set_idx, from_alignment_idx), org_from_global_3ds in all_org_global_3ds.items():
            for (to_data_set_idx, to_alignment_idx), org_from_to_global_3ds in all_org_global_3ds.items():
                if (from_data_set_idx, from_alignment_idx) == (to_data_set_idx, to_alignment_idx) or from_data_set_idx > to_data_set_idx or \
                        (from_data_set_idx == to_data_set_idx and \
                            (from_alignment_idx > to_alignment_idx or \
                             self.target_links[from_data_set_idx][from_alignment_idx].last_bone_name == self.target_links[to_data_set_idx][to_alignment_idx].last_bone_name)):
                    # 同じINDEXか前のINDEX、同じ計算対象は計算不要
                    continue

                # 2点間の距離を算出
                distances[(from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx)] \
                    = org_from_global_3ds[self.target_links[from_data_set_idx][from_alignment_idx].last_bone_name].distanceToPoint(\
                        org_from_to_global_3ds[self.target_links[to_data_set_idx][to_alignment_idx].last_bone_name])

        all_target_distances = {}
        for (from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx), distance in distances.items():
            # 距離を2点間の手のひらの大きさの平均から比率として求める
            distance_ratio = distance / np.mean([self.target_links[from_data_set_idx][from_alignment_idx].org_palm_length, self.target_links[to_data_set_idx][to_alignment_idx].org_palm_length])
            logger.test("fno: %s, (%s,%s,%s,%s): d: %s, dr: %s", fno, from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx, distance, distance_ratio)
            
            # 基準距離（FROMもTOも同じ値）
            base_distance = self.target_links[from_data_set_idx][from_alignment_idx].distance
            if 0 < distance_ratio <= base_distance or base_distance == 10:
                # 基準距離以内か常に位置合わせを行うかの場合、位置合わせ処理実行
                logger.info("○近接あり: f: %s(%s-%s:%s-%s), 境界: %s, 手首間の距離: %s", fno, \
                            (from_data_set_idx + 1), self.target_links[from_data_set_idx][from_alignment_idx].last_bone_name, \
                            (to_data_set_idx + 1), self.target_links[to_data_set_idx][to_alignment_idx].last_bone_name, round(distance_ratio, 5), base_distance)
                
                # 距離をキーにして、INDEXの組合せを登録
                if distance_ratio not in all_target_distances:
                    all_target_distances[distance_ratio] = []
                all_target_distances[distance_ratio].append((from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx))

            elif base_distance < distance_ratio <= base_distance * 1.5:
                # 基準距離に近い場合、ログだけ出す
                logger.info("－近接なし: f: %s(%s-%s:%s-%s), 境界: %s, 手首間の距離: %s", fno, \
                            (from_data_set_idx + 1), self.target_links[from_data_set_idx][from_alignment_idx].last_bone_name, \
                            (to_data_set_idx + 1), self.target_links[to_data_set_idx][to_alignment_idx].last_bone_name, round(distance_ratio, 5), base_distance)

        # 距離の近いものからINDEXの組合せを登録
        # 基本的には全部の中心点を算出するが、それぞれのモデルの両手のみが近かった場合を想定
        all_index_group = []
        all_index_reversed = {}
        for distance_ratio in sorted(all_target_distances.keys()):
            for from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx in all_target_distances[distance_ratio]:
                
                if from_data_set_idx not in all_index_reversed:
                    # まだFROMが登録されていない場合
                    if to_data_set_idx not in all_index_reversed:
                        # TOも登録されていない場合、完全新規組み合わせ

                        # リストのINDEXを逆引きで登録
                        all_index_reversed[from_data_set_idx] = len(all_index_group)
                        all_index_reversed[to_data_set_idx] = len(all_index_group)

                        # リストにINDEXペア登録
                        all_index_group.append([])
                        all_index_group[-1].append((from_data_set_idx, from_alignment_idx))
                        all_index_group[-1].append((to_data_set_idx, to_alignment_idx))
                    else:
                        # FROMが登録されておらず、TOが登録されている場合、TOと同じリストのとこにFROMを追加する
                        group_idx = all_index_reversed[to_data_set_idx]
                        if (from_data_set_idx, from_alignment_idx) not in all_index_group[group_idx]:
                            all_index_group[group_idx].append((from_data_set_idx, from_alignment_idx))
                            all_index_reversed[from_data_set_idx] = group_idx
                else:
                    # FROMが登録されている場合
                    if to_data_set_idx not in all_index_reversed:
                        # TOが登録されていない場合、FROMと同じところのリストにTOを追加する
                        group_idx = all_index_reversed[from_data_set_idx]
                        if (to_data_set_idx, to_alignment_idx) not in all_index_group[group_idx]:
                            all_index_group[group_idx].append((to_data_set_idx, to_alignment_idx))
                            all_index_reversed[to_data_set_idx] = group_idx
                    else:
                        # FROMもTOも登録済みの場合、データがまだなければ登録
                        from_group_idx = all_index_reversed[from_data_set_idx]
                        if (from_data_set_idx, from_alignment_idx) not in all_index_group[from_group_idx]:
                            all_index_group[from_group_idx].append((from_data_set_idx, from_alignment_idx))

                        to_group_idx = all_index_reversed[to_data_set_idx]
                        if (to_data_set_idx, to_alignment_idx) not in all_index_group[to_group_idx]:
                            all_index_group[to_group_idx].append((to_data_set_idx, to_alignment_idx))

        logger.test("fno: %s, index_group: %s", fno, all_index_group)

        if len(all_index_group) == 0:
            all_prev_org_last_poses_indexes = {}
            all_prev_rep_last_poses_indexes = {}
            # 位置合わせ組合せがない場合、スルー
            return None, None

        # INDEXグループ単位で位置合わせ
        for index_group_list in all_index_group:
            new_rep_last_poses_indexes = {}
            org_last_poses_indexes = {}
            rep_last_poses_indexes = {}
            ratio_indexes = {}
            prev_org_last_poses_indexes = None
            prev_rep_last_poses_indexes = None

            logger.test("fno: %s, index_group_list: %s", fno, index_group_list)

            # 他データとの位置合わせがある場合、TRUE
            is_multi = len(set([di for (di, ai) in index_group_list])) > 1

            for data_set_idx, alignment_idx in index_group_list:
                # INDEXペア単位で位置計算

                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]
                # 処理対象
                target_link = self.target_links[data_set_idx][alignment_idx]

                # 比率
                if is_multi:
                    ratio_indexes[(data_set_idx, alignment_idx)] = target_link.multi_ratio.data()
                else:
                    ratio_indexes[(data_set_idx, alignment_idx)] = target_link.ratio.data()

                # 元モデルの末端位置（numpyデータ）
                org_last_poses_indexes[(data_set_idx, alignment_idx)] = all_org_last_poses_indexes[(data_set_idx, alignment_idx)]

                # 先モデルの末端位置（numpyデータ）
                rep_last_poses_indexes[(data_set_idx, alignment_idx)] = all_rep_last_poses_indexes[(data_set_idx, alignment_idx)]

                if all_prev_org_last_poses_indexes and all_prev_rep_last_poses_indexes and (data_set_idx, alignment_idx) in all_prev_org_last_poses_indexes \
                        and (data_set_idx, alignment_idx) in all_prev_rep_last_poses_indexes:
                    
                    if not prev_org_last_poses_indexes:
                        prev_org_last_poses_indexes = {}

                    if not prev_rep_last_poses_indexes:
                        prev_rep_last_poses_indexes = {}

                    # 元モデルの末端位置（numpyデータ）
                    prev_org_last_poses_indexes[(data_set_idx, alignment_idx)] = all_prev_org_last_poses_indexes[(data_set_idx, alignment_idx)]

                    # 先モデルの末端位置（numpyデータ）
                    prev_rep_last_poses_indexes[(data_set_idx, alignment_idx)] = all_prev_rep_last_poses_indexes[(data_set_idx, alignment_idx)]

            # 元モデルの中心点
            org_last_poses = np.array(list(org_last_poses_indexes.values()))
            logger.test("fno: %s, org: %s", fno, org_last_poses)
            org_mean = np.mean(org_last_poses, axis=0)
            logger.test("fno: %s, org mean: %s", fno, org_mean)

            # 先モデルの末端位置の中心点
            rep_last_poses = np.array(list(rep_last_poses_indexes.values()))
            logger.debug("fno: %s, rep: %s", fno, rep_last_poses)

            if prev_org_last_poses_indexes and prev_rep_last_poses_indexes and is_multi:
                # 前回の同じインデックスとの比較
                prev_org_last_poses = np.array(list(prev_org_last_poses_indexes.values()))
                logger.test("fno: %s, prev org: %s", fno, prev_org_last_poses)

                prev_rep_last_poses = np.array(list(prev_rep_last_poses_indexes.values()))
                logger.test("fno: %s, prev rep: %s", fno, prev_rep_last_poses)

                prev_now_org_diff = org_last_poses - prev_org_last_poses
                logger.test("fno: %s, prev org diff: %s", fno, prev_now_org_diff)
                
                # 現在の末端位置は、元モデルの位置から比率を加算する
                rep_last_poses = prev_rep_last_poses + (prev_now_org_diff * np.array(list(ratio_indexes.values())))
                logger.debug("fno: %s, rep calc: %s", fno, rep_last_poses)

            # 先モデルの計算上の位置から中央値を算出
            rep_mean = np.mean(rep_last_poses, axis=0)
            logger.test("fno: %s, rep mean: %s", fno, rep_mean)

            # 元モデルの中心点からの差分
            org_diffs = org_last_poses - org_mean
            logger.test("fno: %s, org diff: %s", fno, org_diffs)
               
            # 差を先モデルの位置に加算する（元モデルと同じ位置に末端を配置）
            new_rep_last_poses = org_diffs + rep_mean
            logger.test("fno: %s, rep new pos: %s", fno, new_rep_last_poses)

            # INDEX別に保持
            for ((data_set_idx, alignment_idx), new_rep_last_pos) in zip(index_group_list, new_rep_last_poses):
                new_rep_last_poses_indexes[(data_set_idx, alignment_idx)] = new_rep_last_pos
                all_rep_last_poses_indexes[(data_set_idx, alignment_idx)] = new_rep_last_pos

            # FIXME デバッグ用↓ ----------------
            for (data_set_idx, alignment_idx) in index_group_list:

                # 変換先の中心点 ---------------
                debug_bone_name = "右1"

                debug_bf = VmdBoneFrame(fno)
                debug_bf.key = True
                debug_bf.set_name(debug_bone_name)
                debug_bf.position = MVector3D(rep_mean)
                
                if debug_bone_name not in data_set.motion.bones:
                    data_set.motion.bones[debug_bone_name] = {}
                
                data_set.motion.bones[debug_bone_name][fno] = debug_bf

                # 作成元の中心点 ---------------
                debug_bone_name = "左1"

                debug_bf = VmdBoneFrame(fno)
                debug_bf.key = True
                debug_bf.set_name(debug_bone_name)
                debug_bf.position = MVector3D(org_mean)
                
                if debug_bone_name not in data_set.motion.bones:
                    data_set.motion.bones[debug_bone_name] = {}
                
                data_set.motion.bones[debug_bone_name][fno] = debug_bf

                if (data_set_idx, alignment_idx) in org_last_poses_indexes and (data_set_idx, alignment_idx) in new_rep_last_poses_indexes \
                        and (data_set_idx, alignment_idx) in rep_last_poses_indexes:
                    org_last_pos = org_last_poses_indexes[(data_set_idx, alignment_idx)]
                    rep_last_pos = rep_last_poses_indexes[(data_set_idx, alignment_idx)]
                    new_rep_last_pos = new_rep_last_poses_indexes[(data_set_idx, alignment_idx)]

                    # 処理対象データセット
                    data_set = self.options.data_set_list[data_set_idx]
                    # 処理対象
                    target_link = self.target_links[data_set_idx][alignment_idx]

                    # 元の末端ボーン位置 -------------
                    debug_bone_name = "{0}2".format(target_link.last_bone_name[0])

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = MVector3D(org_last_pos)
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf

                    # 末端ボーン位置 -------------
                    debug_bone_name = "{0}3".format(target_link.last_bone_name[0])

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = MVector3D(rep_last_pos)
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf

                    # 計算後の末端ボーン位置 -------------
                    debug_bone_name = "{0}4".format(target_link.last_bone_name[0])

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = MVector3D(new_rep_last_pos)
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf
            # FIXME デバッグ用↑ ----------------

            org_bfs = {}
            for group_cnt, (data_set_idx, alignment_idx) in enumerate(index_group_list):
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]
                # 処理対象
                target_link = self.target_links[data_set_idx][alignment_idx]

                for link_name in target_link.rep_links.all().keys():
                    # 変更前のbf（オリジナルモーションではなく、スタンス補正後なので、この時点のを保持）
                    org_bfs[(data_set_idx, alignment_idx, link_name)] = data_set.motion.calc_bf(link_name, fno).copy()

            for cnt in range(3):
                # 各データセットの成功可否
                is_success = [False for _ in range(len(index_group_list))]
                recalc_rep_last_poses = {}
                
                for group_cnt, (data_set_idx, alignment_idx) in enumerate(index_group_list):

                    # 処理対象データセット
                    data_set = self.options.data_set_list[data_set_idx]
                    # 処理対象
                    target_link = self.target_links[data_set_idx][alignment_idx]

                    # 持って行きたい位置
                    new_rep_last_pos = new_rep_last_poses_indexes[(data_set_idx, alignment_idx)]
                    test_vec = MVector3D(new_rep_last_pos)

                    if not is_success[group_cnt]:

                        # まだIK処理が成功していない場合、IK処理実行
                        for ik_cnt, (ik_links, ik_max_count) in enumerate(zip(target_link.ik_links_list, target_link.ik_count_list)):
                            # IK計算実行
                            MServiceUtils.calc_IK(data_set.rep_model, target_link.rep_links, data_set.motion, fno, test_vec, ik_links, max_count=ik_max_count)

                            # 現在の末端位置
                            rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, target_link.rep_links, data_set.motion, fno)
                            now_rep_last_pos = rep_global_3ds[target_link.last_bone_name].data()

                            # 現在の末端位置との差分
                            rep_diff = new_rep_last_pos - now_rep_last_pos
                            recalc_rep_last_poses[(data_set_idx, alignment_idx)] = now_rep_last_pos
                            
                            # IKの関連ボーンの内積チェック
                            dot_dict = {}
                            for link_name in ik_links.all():
                                dot_dict[link_name] = MQuaternion.dotProduct(org_bfs[(data_set_idx, alignment_idx, link_name)].rotation, data_set.motion.calc_bf(link_name, fno).rotation)

                            logger.debug("☆位置合わせ実行(%s-%s): f: %s(%s-%s), rep: %s, vec: %s, dot: %s", cnt, ik_cnt, fno, (data_set_idx + 1), \
                                         target_link.last_bone_name, test_vec.to_log(), MVector3D(rep_diff).to_log(), list(dot_dict.values()))

                            if np.count_nonzero(np.where(np.abs(rep_diff) > 0.2, 1, 0)) == 0 and np.count_nonzero(np.where(np.abs(np.array(list(dot_dict.values()))) < 0.8, 1, 0)) == 0:
                                # 大体同じ位置にあって、角度もそう大きくズレてない場合、OK
                                is_success[group_cnt] = True
                                break
                            
                if is_success.count(True) == len(index_group_list):
                    # すべてのグループが成功していたら終了
                    logger.debug("◎全成功(%s-%s): f: %s", cnt, ik_cnt, fno)
                    break
                else:
                    # 失敗していて、かつ他データとの調整がある場合、中央値を再算出する

                    # 先モデルの末端位置の中心点
                    rep_last_poses = np.array(list(recalc_rep_last_poses.values()))
                    logger.test("fno: %s, recalc: %s, rep: %s", fno, cnt, rep_last_poses)
                    rep_mean = np.mean(rep_last_poses, axis=0)
                    logger.test("fno: %s, recalc: %s, rep mean: %s", fno, cnt, rep_mean)

                    # 差を先モデルの位置に加算する（元モデルと同じ位置に末端を配置）
                    new_rep_last_poses = org_diffs + rep_mean
                    logger.test("fno: %s, recalc: %s, rep new pos: %s", fno, cnt, new_rep_last_poses)

                    # INDEX別に保持
                    for ((data_set_idx, alignment_idx), new_rep_last_pos) in zip(index_group_list, new_rep_last_poses):
                        new_rep_last_poses_indexes[(data_set_idx, alignment_idx)] = new_rep_last_pos

            for group_cnt, (data_set_idx, alignment_idx) in enumerate(index_group_list):
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]
                # 処理対象
                target_link = self.target_links[data_set_idx][alignment_idx]

                if not is_success[group_cnt]:
                    # 最終的に失敗してる場合、元に戻す
                    
                    # 元に戻す処理
                    for link_name in target_link.rep_links.all().keys():
                        bf = data_set.motion.calc_bf(link_name, fno)
                        dot = MQuaternion.dotProduct(org_bfs[(data_set_idx, alignment_idx, link_name)].rotation, bf.rotation)

                        if dot < 0.8:
                            # 内積もNGなら元に戻す
                            logger.info("×位置合わせ失敗: f: %s(%s-%s), 近似度: %s", fno, (data_set_idx + 1), target_link.last_bone_name, round(dot, 5))
                            bf.rotation = org_bfs[(data_set_idx, alignment_idx, link_name)].rotation

                for link_name in target_link.rep_links.all().keys():
                    # どっちにしろbf確定
                    data_set.motion.regist_bf(data_set.motion.calc_bf(link_name, fno), link_name, fno)

        # 前回分保持
        all_prev_org_last_poses_indexes = all_org_last_poses_indexes
        all_prev_rep_last_poses_indexes = all_rep_last_poses_indexes
        
        return all_prev_org_last_poses_indexes, all_prev_rep_last_poses_indexes

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

            # 手首リンク
            org_wrist_links = data_set.org_model.create_link_2_top_one("{0}手首実体".format(direction))
            rep_wrist_links = data_set.rep_model.create_link_2_top_one("{0}手首実体".format(direction))

            # IK用リンク（末端から追加していく）
            ik_links_list = []
            ik_count_list = []

            # ひじは角度制限をつける
            elbow_bone = rep_wrist_links.get("{0}ひじ".format(direction))
            elbow_bone.ik_limit_min = MVector3D(-180, -0.5, 0)
            elbow_bone.ik_limit_min = MVector3D(180, 180, 0)

            ik_links = BoneLinks()
            ik_links.append(rep_wrist_links.get("{0}手首".format(direction)))
            ik_links.append(rep_wrist_links.get("{0}腕".format(direction)))
            ik_links_list.append(ik_links)
            ik_count_list.append(2)
                        
            ik_links = BoneLinks()
            ik_links.append(rep_wrist_links.get("{0}手首".format(direction)))
            ik_links.append(elbow_bone)
            ik_links_list.append(ik_links)
            ik_count_list.append(2)

            ik_links = BoneLinks()
            ik_links.append(rep_wrist_links.get("{0}手首".format(direction)))
            ik_links.append(elbow_bone)
            ik_links.append(rep_wrist_links.get("{0}腕".format(direction)))
            ik_links_list.append(ik_links)
            ik_count_list.append(3)

            # 手のひらの長さ
            org_palm_length = (data_set.org_model.bones["{0}手首".format(direction)].position - data_set.org_model.bones["{0}人指先".format(direction)].position).length()
            rep_palm_length = (data_set.rep_model.bones["{0}手首".format(direction)].position - data_set.rep_model.bones["{0}人指先".format(direction)].position).length()

            # グルーブが処理対象であるか
            is_groove = ("グルーブ" in data_set.rep_model.bones and "グルーブ" in data_set.motion.bones)

            # 手首リンク登録
            self.target_links[data_set_idx].append(ArmAlignmentOption(org_wrist_links, rep_wrist_links, ik_links_list, ik_count_list, org_palm_length, rep_palm_length, \
                                                                      org_arm_links, rep_arm_links, "{0}腕".format(direction), "{0}手首".format(direction), \
                                                                      self.options.arm_options.alignment_distance_wrist, is_groove))

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
            ik_links_list = BoneLinks()
            ik_links_list.append(rep_wrist_links.get("{0}手首".format(direction)))
            ik_links_list.append(rep_wrist_links.get("{0}ひじ".format(direction)))
            ik_links_list.append(rep_wrist_links.get("{0}腕".format(direction)))

            # 手のひらの長さ
            org_palm_length = (data_set.org_model.bones["{0}手首".format(direction)].position - data_set.org_model.bones["{0}人指先".format(direction)].position).length()
            rep_palm_length = (data_set.rep_model.bones["{0}手首".format(direction)].position - data_set.rep_model.bones["{0}人指先".format(direction)].position).length()

            # グルーブが処理対象であるか
            is_groove = ("グルーブ" in data_set.rep_model.bones and "グルーブ" in data_set.motion.bones)

            for finger_name in ["親指", "人指", "中指", "薬指", "小指"]:
                # 指リンク
                org_finger_links = data_set.org_model.create_link_2_top_one("{0}{1}先".format(direction, finger_name))
                rep_finger_links = data_set.rep_model.create_link_2_top_one("{0}{1}先".format(direction, finger_name))

                # 指リンク登録
                self.target_links[data_set_idx].append(ArmAlignmentOption(org_finger_links, rep_finger_links, ik_links_list, org_palm_length, rep_palm_length, \
                                                                          org_arm_links, rep_arm_links, "{0}腕".format(direction), "{0}{1}".format(direction, finger_name), \
                                                                          self.options.arm_options.alignment_distance_finger, is_groove))

                # 腕・ひじ・手首・指のキーフレ（なければスルー）
                fnos.extend(data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction), "{0}{1}０".format(direction, finger_name), \
                                                          "{0}{1}１".format(direction, finger_name), "{0}{1}２".format(direction, finger_name), "{0}{1}３".format(direction, finger_name)))

        return fnos

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
            
            if data_set.rep_model.can_arm_sizing and data_set.org_model.can_arm_sizing and data_set_idx not in target_data_set_idxs:
                # ボーンセットがあり、腕系サイジング可能で、かつまだ登録されていない場合
                target_data_set_idxs.append(data_set_idx)
            
        return target_data_set_idxs


# 位置合わせ用オプション
class ArmAlignmentOption():

    def __init__(self, org_links: BoneLinks, rep_links: BoneLinks, ik_links_list: BoneLinks, ik_count_list: list, org_palm_length: float, rep_palm_length: float, \
                 org_arm_links: BoneLinks, rep_arm_links: BoneLinks, start_bone_name: str, last_bone_name: str, distance: float, is_groove: bool):
        super().__init__()

        self.org_links = org_links
        self.rep_links = rep_links
        self.ik_links_list = ik_links_list
        self.ik_count_list = ik_count_list
        self.org_palm_length = org_palm_length
        self.rep_palm_length = rep_palm_length
        self.start_bone_name = start_bone_name
        self.last_bone_name = last_bone_name
        self.distance = distance

        # グルーブがあるか
        self.is_groove = is_groove
        
        # 肩幅比率
        org_arm_diff = (org_arm_links["左"].get("左腕").position - org_arm_links["右"].get("右腕").position)
        rep_arm_diff = (rep_arm_links["左"].get("左腕").position - rep_arm_links["右"].get("右腕").position)
        arm_diff_ratio = rep_arm_diff / org_arm_diff
        arm_diff_ratio.one()    # 比率なので、0は1に変換する

        # TOの長さ比率
        org_to_diff = (org_links.get(last_bone_name).position - org_links.get(start_bone_name).position)
        org_to_diff.abs()
        rep_to_diff = (rep_links.get(last_bone_name).position - rep_links.get(start_bone_name).position)
        rep_to_diff.abs()
        to_diff_ratio = rep_to_diff.length() / org_to_diff.length()

        # 元と先の比率
        self.ratio = MVector3D(to_diff_ratio, to_diff_ratio, to_diff_ratio)
        # 元と先の比率（複数モーション時）
        self.multi_ratio = MVector3D(to_diff_ratio, 1, to_diff_ratio)
        
        # 先の腕の長さ
        self.arm_diff = rep_arm_links["右"].get("右腕").position - rep_arm_links["右"].get("右手首").position
        self.arm_diff.abs()


