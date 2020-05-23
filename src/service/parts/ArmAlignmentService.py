# -*- coding: utf-8 -*-
#
import numpy as np

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
        # 処理対象ボーン名リスト
        bone_names = []

        logger.info("手首位置合わせ　", decoration=MLogger.DECORATION_LINE)

        for data_set_idx in self.target_data_set_idxs:
            # 処理対象データセットに対して、準備実行

            # 手首位置合わせ用準備（床位置合わせも含む）
            bone_names.extend(self.prepare_wrist(data_set_idx))

            # 準備が終わったら、キーフレを追加していく
            if self.options.arm_options.alignment_finger_flg:
                # 指位置合わせ用準備
                bone_names.extend(self.prepare_finger(data_set_idx))
        
        # ボーン名重複除去
        bone_names = list(set(bone_names))

        fnos = []
        # 処理対象全ファイルセット単位でキーフレ検出
        for data_set_idx in self.target_data_set_idxs:
            # 処理対象データセット
            data_set = self.options.data_set_list[data_set_idx]
            fnos = data_set.motion.get_bone_fnos(*bone_names)
            # キーフレを重複除外してソートする
            fnos = sorted(list(set(fnos)))

        all_prev_org_effector_poses_indexes = {}
        all_prev_rep_effector_poses_indexes = {}
        all_prev_org_tip_poses_indexes = {}
        all_prev_rep_tip_poses_indexes = {}
        # 手首位置合わせ実行（先頭からキーフレ単位で見ていく必要があるので、並列化不可）
        while len(fnos) > 0:
            fno = fnos[0]

            all_prev_org_effector_poses_indexes, all_prev_rep_effector_poses_indexes, \
                all_prev_org_tip_poses_indexes, all_prev_rep_tip_poses_indexes = \
                self.execute_alignment(fno, all_prev_org_effector_poses_indexes, all_prev_rep_effector_poses_indexes, \
                                       all_prev_org_tip_poses_indexes, all_prev_rep_tip_poses_indexes)

            # キーフレが増えている可能性があるので、ここで再取得
            for data_set_idx in self.target_data_set_idxs:
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]
                # 次の範囲でキーフレ検索
                fnos = data_set.motion.get_bone_fnos(*bone_names, start_fno=(fno + 1))
                # キーフレを重複除外してソートする
                fnos = sorted(list(set(fnos)))
        
        # futures = []
        # with ThreadPoolExecutor(thread_name_prefix="alignment_after") as executor:
        #     for data_set_idx, data_set in enumerate(self.options.data_set_list):
        #         futures.append(executor.submit(self.alignment_after, data_set_idx, "右"))
        #         futures.append(executor.submit(self.alignment_after, data_set_idx, "左"))

        # concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        # for f in futures:
        #     if not f.result():
        #         return False

        return True
    
    # 位置合わせ後処理
    def alignment_after(self, data_set_idx: int, direction: str):
        try:
            logger.info("%s位置合わせ後処理【No.%s】", direction, (data_set_idx + 1))

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

    # 位置合わせ実行
    def execute_alignment(self, fno: int, all_prev_org_effector_poses_indexes: dict, all_prev_rep_effector_poses_indexes: dict, \
                          all_prev_org_tip_poses_indexes: dict, all_prev_rep_tip_poses_indexes: dict):
        all_org_global_3ds = {}
        all_rep_global_3ds = {}
        all_org_effector_poses_indexes = {}
        all_rep_effector_poses_indexes = {}
        all_org_tip_poses_indexes = {}
        all_rep_tip_poses_indexes = {}

        # 処理対象キーフレを先頭からひとつずつチェックしていく
        for data_set_idx, alignment_options in self.target_links.items():
            for alignment_idx, target_link in alignment_options.items():
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]

                # 元モデルのそれぞれのグローバル位置
                all_org_global_3ds[(data_set_idx, alignment_idx)] = \
                    MServiceUtils.calc_global_pos(data_set.org_model, target_link.org_links, data_set.org_motion, fno)

                # 元モデルのエフェクタ位置（numpyデータ）
                all_org_effector_poses_indexes[(data_set_idx, alignment_idx)] = \
                    all_org_global_3ds[(data_set_idx, alignment_idx)][target_link.effector_bone_name].copy().data()

                # 先端（指先）位置（numpyデータ）
                all_org_tip_poses_indexes[(data_set_idx, alignment_idx)] = \
                    all_org_global_3ds[(data_set_idx, alignment_idx)][target_link.tip_bone_name].copy().data()

                if alignment_idx < 0:
                    # 床の位置は各位置のY0をvectorの場合のみ定義し直す（距離を測る用）
                    for org_global_vec in all_org_global_3ds[(data_set_idx, alignment_idx)].values():
                        org_global_vec.setY(0)

        distances = {}

        # それぞれの距離を算出
        # 起点となるボーン
        for (from_data_set_idx, from_alignment_idx), org_from_global_3ds in all_org_global_3ds.items():
            for (to_data_set_idx, to_alignment_idx), org_to_global_3ds in all_org_global_3ds.items():
                if (from_data_set_idx, from_alignment_idx) == (to_data_set_idx, to_alignment_idx) or \
                    self.target_links[from_data_set_idx][from_alignment_idx].start_bone_name == self.target_links[to_data_set_idx][to_alignment_idx].start_bone_name or \
                        (from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx) in distances or \
                        (to_data_set_idx, to_alignment_idx, from_data_set_idx, from_alignment_idx) in distances or \
                        (from_alignment_idx < 0 and to_alignment_idx < 0) or \
                        ((from_alignment_idx < 0 or to_alignment_idx < 0) and \
                            (from_data_set_idx != to_data_set_idx or (from_data_set_idx == to_data_set_idx and abs(to_alignment_idx) != abs(from_alignment_idx)))):
                    # 同じINDEXか、同じ計算対象、両方床、既に計算済みのペア、床の場合は自身以外とは計算不要
                    continue
                                
                # 2点間の距離を算出
                distances[(from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx)] \
                    = org_from_global_3ds[self.target_links[from_data_set_idx][from_alignment_idx].effector_bone_name].distanceToPoint(\
                        org_to_global_3ds[self.target_links[to_data_set_idx][to_alignment_idx].effector_bone_name])
            
        logger.debug("fno: %s, distances: %s", fno, distances)
            
        all_target_distances = {}
        for (from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx), distance in distances.items():
            # 距離を2点間の手のひらの大きさの平均から比率として求める
            distance_ratio = distance / np.mean([self.target_links[from_data_set_idx][from_alignment_idx].org_palm_length, self.target_links[to_data_set_idx][to_alignment_idx].org_palm_length])
            logger.test("fno: %s, (%s,%s,%s,%s): d: %s, dr: %s", fno, from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx, distance, distance_ratio)
            
            # 基準距離（床は床位置合わせの距離が入ってる）
            base_distance = self.target_links[to_data_set_idx][to_alignment_idx].distance
            if 0 < distance_ratio <= base_distance or base_distance == 10:
                # 基準距離以内か常に位置合わせを行うかの場合、位置合わせ処理実行

                # 距離をキーにして、INDEXの組合せを登録
                if distance_ratio not in all_target_distances:
                    all_target_distances[distance_ratio] = []
                all_target_distances[distance_ratio].append((from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx))

            elif base_distance < distance_ratio <= base_distance * 3:
                # 基準距離に近い場合、ログだけ出す
                logger.info("－近接なし: f: %s(%s-%s:%s-%s), 境界: %s", fno, \
                            (from_data_set_idx + 1), self.target_links[from_data_set_idx][from_alignment_idx].effector_display_bone_name, \
                            (to_data_set_idx + 1), self.target_links[to_data_set_idx][to_alignment_idx].effector_display_bone_name, round(distance_ratio, 5))

        # 距離の近いものからINDEXの組合せを登録
        # 基本的には全部の中心点を算出するが、それぞれのモデルの両手のみが近かった場合を想定
        all_index_group = []
        all_index_reversed = {}
        for distance_ratio in sorted(all_target_distances.keys()):
            for from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx in all_target_distances[distance_ratio]:
                
                if from_alignment_idx < 0 or to_alignment_idx < 0:
                    # どっちか床である場合、常に新しいグループで登録する
                    group_idx = len(all_index_group)

                    # リストにINDEXペア登録
                    all_index_group.append([])
                    if from_alignment_idx < 0:
                        all_index_group[group_idx].append((from_data_set_idx, from_alignment_idx))
                        all_index_reversed[from_data_set_idx] = group_idx
                    
                    if to_alignment_idx < 0:
                        all_index_group[group_idx].append((to_data_set_idx, to_alignment_idx))
                        all_index_reversed[to_data_set_idx] = group_idx
                else:
                    if from_data_set_idx not in all_index_reversed:
                        # まだFROMが登録されていない場合
                        if to_data_set_idx not in all_index_reversed:
                            # TOも登録されていない場合、完全新規組み合わせ
                            group_idx = len(all_index_group)

                            # リストにINDEXペア登録
                            all_index_group.append([])
                            all_index_group[group_idx].append((from_data_set_idx, from_alignment_idx))
                            all_index_group[group_idx].append((to_data_set_idx, to_alignment_idx))

                            # リストのINDEXを逆引きで登録
                            all_index_reversed[from_data_set_idx] = group_idx
                            all_index_reversed[to_data_set_idx] = group_idx
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
                            # FROMもTOも登録済みの場合、他データセットとの組み合わせかつデータがまだなければ登録
                            if from_data_set_idx != to_data_set_idx:
                                from_group_idx = all_index_reversed[from_data_set_idx]
                                if (from_data_set_idx, from_alignment_idx) not in all_index_group[from_group_idx]:
                                    all_index_group[from_group_idx].append((from_data_set_idx, from_alignment_idx))
                                
                                to_group_idx = all_index_reversed[to_data_set_idx]
                                if (to_data_set_idx, to_alignment_idx) not in all_index_group[to_group_idx]:
                                    all_index_group[to_group_idx].append((to_data_set_idx, to_alignment_idx))
                    
                # 対象の場合、ログ表示
                base_distance = self.target_links[to_data_set_idx][to_alignment_idx].distance

                logger.info("○近接あり: f: %s(%s-%s:%s-%s), 境界: %s", fno, \
                            (from_data_set_idx + 1), self.target_links[from_data_set_idx][from_alignment_idx].effector_display_bone_name, \
                            (to_data_set_idx + 1), self.target_links[to_data_set_idx][to_alignment_idx].effector_display_bone_name, round(distance_ratio, 5))

        if len(all_index_group) == 0:
            # 位置合わせ組合せがない場合、スルー
            return None, None, None, None

        logger.debug("fno: %s, index_group: %s", fno, all_index_group)

        # INDEXグループ単位で位置合わせ
        for index_group_list in all_index_group:
            new_rep_effector_poses_indexes = {}
            new_rep_tip_poses_indexes = {}
            org_effector_poses_indexes = {}
            rep_effector_poses_indexes = {}
            org_tip_poses_indexes = {}
            rep_tip_poses_indexes = {}
            ratio_indexes = {}
            entity_ratio_indexes = {}
            palm_ratio_indexes = {}
            prev_org_effector_poses_indexes = None
            prev_rep_effector_poses_indexes = None
            prev_org_tip_poses_indexes = None
            prev_rep_tip_poses_indexes = None

            logger.test("fno: %s, index_group_list: %s", fno, index_group_list)

            # 床との位置合わせがある場合、TRUE
            is_floor = ([ai < 0 for (di, ai) in index_group_list].count(True) > 0)
            # 他データとの位置合わせ（床との組合せは除く）がある場合、TRUE
            is_multi = len(set([di for (di, ai) in index_group_list])) > 1 and not is_floor

            for data_set_idx, alignment_idx in index_group_list:
                # INDEXペア単位で位置計算

                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]
                # 処理対象
                target_link = self.target_links[data_set_idx][alignment_idx]

                # 先モデルのそれぞれのグローバル位置
                rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, target_link.rep_links, data_set.motion, fno)
                all_rep_global_3ds[(data_set_idx, alignment_idx)] = rep_global_3ds

                # 先モデルのエフェクタ位置（numpyデータ）
                rep_effector_pos = all_rep_global_3ds[(data_set_idx, alignment_idx)][target_link.effector_bone_name].data()
                all_rep_effector_poses_indexes[(data_set_idx, alignment_idx)] = rep_effector_pos

                all_rep_tip_poses_indexes[(data_set_idx, alignment_idx)] = all_rep_global_3ds[(data_set_idx, alignment_idx)][target_link.tip_bone_name].data()

                # 比率
                if is_multi:
                    ratio_indexes[(data_set_idx, alignment_idx)] = target_link.multi_ratio
                else:
                    ratio_indexes[(data_set_idx, alignment_idx)] = target_link.ratio
                
                # 手首の厚み比率
                entity_ratio_indexes[(data_set_idx, alignment_idx)] = target_link.entity_ratio

                palm_ratio = target_link.rep_palm_length / target_link.org_palm_length

                # 手のひらの大きさ比率
                palm_ratio_indexes[(data_set_idx, alignment_idx)] = np.array([palm_ratio, 1, palm_ratio])

                # 元モデルのエフェクタ位置（numpyデータ）
                org_effector_poses_indexes[(data_set_idx, alignment_idx)] = all_org_effector_poses_indexes[(data_set_idx, alignment_idx)]

                # 先モデルのエフェクタ位置（numpyデータ）
                rep_effector_poses_indexes[(data_set_idx, alignment_idx)] = all_rep_effector_poses_indexes[(data_set_idx, alignment_idx)]

                # 元モデルの先端位置（numpyデータ）
                org_tip_poses_indexes[(data_set_idx, alignment_idx)] = all_org_tip_poses_indexes[(data_set_idx, alignment_idx)]

                # 先モデルの先端位置（numpyデータ）
                rep_tip_poses_indexes[(data_set_idx, alignment_idx)] = all_rep_tip_poses_indexes[(data_set_idx, alignment_idx)]

                if all_prev_org_effector_poses_indexes and all_prev_rep_effector_poses_indexes and (data_set_idx, alignment_idx) in all_prev_org_effector_poses_indexes \
                        and (data_set_idx, alignment_idx) in all_prev_rep_effector_poses_indexes:
                    
                    if not prev_org_effector_poses_indexes:
                        prev_org_effector_poses_indexes = {}

                    if not prev_rep_effector_poses_indexes:
                        prev_rep_effector_poses_indexes = {}

                    # 元モデルのエフェクタ位置（numpyデータ）
                    prev_org_effector_poses_indexes[(data_set_idx, alignment_idx)] = all_prev_org_effector_poses_indexes[(data_set_idx, alignment_idx)]

                    # 先モデルのエフェクタ位置（numpyデータ）
                    prev_rep_effector_poses_indexes[(data_set_idx, alignment_idx)] = all_prev_rep_effector_poses_indexes[(data_set_idx, alignment_idx)]

                if all_prev_org_tip_poses_indexes and all_prev_rep_tip_poses_indexes and (data_set_idx, alignment_idx) in all_prev_org_tip_poses_indexes \
                        and (data_set_idx, alignment_idx) in all_prev_rep_tip_poses_indexes:
                    
                    if not prev_org_tip_poses_indexes:
                        prev_org_tip_poses_indexes = {}

                    if not prev_rep_tip_poses_indexes:
                        prev_rep_tip_poses_indexes = {}

                    # 元モデルの先端位置（numpyデータ）
                    prev_org_tip_poses_indexes[(data_set_idx, alignment_idx)] = all_prev_org_tip_poses_indexes[(data_set_idx, alignment_idx)]

                    # 先モデルの先端位置（numpyデータ）
                    prev_rep_tip_poses_indexes[(data_set_idx, alignment_idx)] = all_prev_rep_tip_poses_indexes[(data_set_idx, alignment_idx)]

            # 元モデルのエフェクタ
            org_effector_poses = np.array(list(org_effector_poses_indexes.values())) * np.mean(np.array(list(palm_ratio_indexes.values())), axis=0)
            logger.test("fno: %s, org: %s", fno, org_effector_poses)
            # エフェクタ中心点
            org_mean = np.mean(org_effector_poses, axis=0)
            logger.test("fno: %s, org mean: %s", fno, org_mean)

            if is_multi:
                # 複数セット位置合わせの場合
                if prev_org_effector_poses_indexes and prev_rep_effector_poses_indexes:
                    for ((prev_data_set_idx, prev_alignment_idx), prev_org_effector_pos), prev_rep_effector_pos \
                            in zip(prev_org_effector_poses_indexes.items(), prev_rep_effector_poses_indexes.values()):
                        if (prev_data_set_idx, prev_alignment_idx) in rep_effector_poses_indexes.keys():
                            # 前回の同じインデックスとの比較
                            logger.test("fno: %s, prev org: %s", fno, prev_org_effector_pos)
                            logger.test("fno: %s, prev rep: %s", fno, prev_rep_effector_pos)

                            prev_now_org_diff = org_effector_poses_indexes[(prev_data_set_idx, prev_alignment_idx)] - prev_org_effector_pos
                            logger.test("fno: %s, prev org diff: %s", fno, prev_now_org_diff)
                            
                            # 現在のエフェクタ位置Yは、元モデルの位置から比率を加算する
                            rep_effector_poses_indexes[(prev_data_set_idx, prev_alignment_idx)][1] \
                                = prev_rep_effector_pos[1] + (prev_now_org_diff[1] * ratio_indexes[(prev_data_set_idx, prev_alignment_idx)])
                            logger.debug("fno: %s, rep calc: %s", fno, rep_effector_poses_indexes[(prev_data_set_idx, prev_alignment_idx)])
                else:
                    # 前回がない（位置合わせ起点）の場合
                    pass

            # 先モデルのエフェクタ位置
            rep_effector_poses = np.array(list(rep_effector_poses_indexes.values()))
            logger.debug("fno: %s, rep: %s", fno, rep_effector_poses)

            # 先モデルの計算上の位置から中央値を算出
            rep_mean = np.mean(rep_effector_poses, axis=0)
            logger.test("fno: %s, rep mean: %s", fno, rep_mean)

            # 元モデルの中心点からの差分
            org_diffs = org_effector_poses - org_mean
            logger.test("fno: %s, org diff: %s", fno, org_diffs)

            if is_floor:
                # 床位置合わせの場合、床からの位置
                new_rep_effector_poses = rep_effector_poses
                new_rep_effector_poses[:, 1] = org_effector_poses[:, 1] * np.array(list(ratio_indexes.values()))
            else:
                logger.test("entity: %s", np.array(list(entity_ratio_indexes.values())))
                
                # 差を先モデルの位置に加算する（元モデルと同じ位置にエフェクタを配置）
                new_rep_effector_poses = org_diffs + rep_mean
                
            logger.test("fno: %s, rep new pos: %s", fno, new_rep_effector_poses)

            # --------------

            # 元モデルの先端
            org_tip_poses = np.array(list(org_tip_poses_indexes.values())) * np.mean(np.array(list(palm_ratio_indexes.values())), axis=0)
            logger.test("fno: %s, org: %s", fno, org_tip_poses)

            # 元モデルの先端中心点
            org_mean = np.mean(org_tip_poses, axis=0)
            logger.test("fno: %s, org mean: %s", fno, org_mean)

            # 先モデルの末端の差異
            new_rep_effector_diff = new_rep_effector_poses - np.array(list(rep_effector_poses_indexes.values()))

            # 先モデルの先端位置の中心点
            rep_tip_poses = np.array(list(rep_tip_poses_indexes.values())) + new_rep_effector_diff
            logger.debug("fno: %s, rep: %s", fno, rep_tip_poses)

            # 先モデルの計算上の位置から中央値を算出
            rep_mean = np.mean(rep_tip_poses, axis=0)
            logger.test("fno: %s, rep mean: %s", fno, rep_mean)

            # 元モデルの中心点からの差分
            org_diffs = org_tip_poses - org_mean
            logger.test("fno: %s, org diff: %s", fno, org_diffs)

            if is_floor:
                # 床位置合わせの場合、床からの位置
                new_rep_tip_poses = rep_tip_poses
                new_rep_tip_poses[:, 1] = org_tip_poses[:, 1] * np.array(list(ratio_indexes.values()))
            else:
                # 差を先モデルの位置に加算する（元モデルと同じ位置に先端を配置）
                new_rep_tip_poses = org_diffs + rep_mean
                logger.test("fno: %s, rep new pos: %s", fno, new_rep_tip_poses)

            # INDEX別に保持
            for ((data_set_idx, alignment_idx), new_rep_effector_pos, new_rep_tip_pos) in zip(index_group_list, new_rep_effector_poses, new_rep_tip_poses):
                new_rep_effector_poses_indexes[(data_set_idx, alignment_idx)] = new_rep_effector_pos
                all_rep_effector_poses_indexes[(data_set_idx, alignment_idx)] = new_rep_effector_pos
                new_rep_tip_poses_indexes[(data_set_idx, alignment_idx)] = new_rep_tip_pos
                all_rep_tip_poses_indexes[(data_set_idx, alignment_idx)] = new_rep_tip_pos

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

                if (data_set_idx, alignment_idx) in org_effector_poses_indexes and (data_set_idx, alignment_idx) in new_rep_effector_poses_indexes \
                        and (data_set_idx, alignment_idx) in rep_effector_poses_indexes and (data_set_idx, alignment_idx) in new_rep_tip_poses_indexes:
                    org_effector_pos = org_effector_poses_indexes[(data_set_idx, alignment_idx)]
                    rep_effector_pos = rep_effector_poses_indexes[(data_set_idx, alignment_idx)]
                    new_rep_effector_pos = new_rep_effector_poses_indexes[(data_set_idx, alignment_idx)]
                    new_rep_tip_pos = new_rep_tip_poses_indexes[(data_set_idx, alignment_idx)]

                    # 処理対象データセット
                    data_set = self.options.data_set_list[data_set_idx]
                    # 処理対象
                    target_link = self.target_links[data_set_idx][alignment_idx]

                    # 元のエフェクタボーン位置 -------------
                    debug_bone_name = "{0}2".format(target_link.effector_bone_name[0])

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = MVector3D(org_effector_pos)
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf

                    # エフェクタボーン位置 -------------
                    debug_bone_name = "{0}3".format(target_link.effector_bone_name[0])

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = MVector3D(rep_effector_pos)
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf

                    # 計算後のエフェクタボーン位置 -------------
                    debug_bone_name = "{0}4".format(target_link.effector_bone_name[0])

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = MVector3D(new_rep_effector_pos)
                    
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

                # 変更前のbf（オリジナルモーションではなく、スタンス補正後なので、この時点のを保持）
                for ik_links in target_link.ik_links_list:
                    for link_name in ik_links.all().keys():
                        org_bfs[(data_set_idx, alignment_idx, link_name)] = data_set.motion.calc_bf(link_name, fno).copy()

                    if target_link.tip_ik_links:
                        org_bfs[(data_set_idx, alignment_idx, target_link.tip_ik_links.last_name())] = data_set.motion.calc_bf(target_link.tip_ik_links.last_name(), fno).copy()

            is_success = [False for _ in range(len(index_group_list))]

            # 各データセットの成功可否
            recalc_rep_effector_poses = {}
            
            for group_cnt, (data_set_idx, alignment_idx) in enumerate(index_group_list):

                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]
                # 処理対象
                target_link = self.target_links[data_set_idx][alignment_idx]

                # 持って行きたい位置
                new_rep_effector_pos = new_rep_effector_poses_indexes[(data_set_idx, alignment_idx)]
                effector_vec = MVector3D(new_rep_effector_pos)

                if not is_success[group_cnt]:
                    # まだIK処理が成功していない場合、IK処理実行
                    for ik_cnt, (ik_links, ik_max_count) in enumerate(zip(target_link.ik_links_list, target_link.ik_count_list)):
                        # IK計算実行
                        MServiceUtils.calc_IK(data_set.rep_model, target_link.rep_links, data_set.motion, fno, effector_vec, ik_links, max_count=ik_max_count)

                        # 現在のエフェクタ位置
                        rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, target_link.rep_links, data_set.motion, fno)
                        now_rep_effector_pos = rep_global_3ds[target_link.effector_bone_name].data()

                        # 現在のエフェクタ位置との差分
                        rep_diff = new_rep_effector_pos - now_rep_effector_pos
                        recalc_rep_effector_poses[(data_set_idx, alignment_idx)] = now_rep_effector_pos
                        
                        # IKの関連ボーンの内積チェック
                        dot_dict = {}
                        dot_limit_dict = {}
                        for link_name, link_bone in ik_links.all().items():
                            dot_dict[link_name] = MQuaternion.dotProduct(org_bfs[(data_set_idx, alignment_idx, link_name)].rotation, data_set.motion.calc_bf(link_name, fno).rotation)
                            dot_limit_dict[link_name] = link_bone.dot_limit

                        logger.debug("☆位置合わせ実行(%s): f: %s(%s-%s), rep: %s, vec: %s, dot: %s", ik_cnt, fno, (data_set_idx + 1), \
                                     target_link.effector_display_bone_name, effector_vec.to_log(), MVector3D(rep_diff).to_log(), list(dot_dict.values()))

                        if np.count_nonzero(np.where(np.abs(rep_diff) > 0.2, 1, 0)) == 0 and \
                                np.count_nonzero(np.where(np.array(list(dot_dict.values())) < np.array(list(dot_limit_dict.values())), 1, 0)) == 0:
                            # 大体同じ位置にあって、角度もそう大きくズレてない場合、OK
                            is_success[group_cnt] = True
                            break
                        
            for group_cnt, (data_set_idx, alignment_idx) in enumerate(index_group_list):
                # 処理対象データセット
                data_set = self.options.data_set_list[data_set_idx]
                # 処理対象
                target_link = self.target_links[data_set_idx][alignment_idx]

                if not is_success[group_cnt]:
                    # 最終的に失敗してる場合、元に戻す
                    
                    # 元に戻す処理
                    for ik_links in target_link.ik_links_list:
                        for link_name in ik_links.all().keys():
                            bf = data_set.motion.calc_bf(link_name, fno)
                            dot = MQuaternion.dotProduct(org_bfs[(data_set_idx, alignment_idx, link_name)].rotation, bf.rotation)

                            if dot < 0.8:
                                # 内積もNGなら元に戻す
                                logger.info("×位置合わせ失敗: f: %s(%s-%s), 近似度: %s", fno, (data_set_idx + 1), target_link.effector_display_bone_name, round(dot, 5))
                                bf.rotation = org_bfs[(data_set_idx, alignment_idx, link_name)].rotation.copy()
                            else:
                                # 最後まで回して内積OKならとりあえずFLG=ON
                                is_success[group_cnt] = True

                if is_success[group_cnt] and target_link.tip_ik_links:
                    # IK処理が成功していて、かつ先端リンクがある場合、先端調整

                    new_rep_tip_pos = new_rep_tip_poses_indexes[(data_set_idx, alignment_idx)]
                    tip_vec = MVector3D(new_rep_tip_pos)

                    # IK計算実行
                    MServiceUtils.calc_IK(data_set.rep_model, target_link.rep_links, data_set.motion, fno, tip_vec, target_link.tip_ik_links, max_count=2)

                    bf = data_set.motion.calc_bf(target_link.tip_ik_links.last_name(), fno)
                    dot = MQuaternion.dotProduct(org_bfs[(data_set_idx, alignment_idx, target_link.tip_ik_links.last_name())].rotation, bf.rotation)

                    logger.debug("☆先端位置合わせ実行(%s): f: %s(%s-%s), rep: %s, dot: %s", ik_cnt, fno, (data_set_idx + 1), \
                                 target_link.tip_bone_name, tip_vec.to_log(), dot)

                    if dot < 0.75:
                        # 内積NGなら元に戻す
                        logger.info("×先端位置合わせ失敗: f: %s(%s-%s), 近似度: %s", fno, (data_set_idx + 1), target_link.tip_ik_links.last_name(), round(dot, 5))
                        bf.rotation = org_bfs[(data_set_idx, alignment_idx, target_link.tip_ik_links.last_name())].rotation.copy()

                # どっちにしろbf確定(手首もここで確定)
                for ik_links in target_link.ik_links_list:
                    for link_name in ik_links.all().keys():
                        data_set.motion.regist_bf(data_set.motion.calc_bf(link_name, fno), link_name, fno)

        # 前回分保持
        all_prev_org_effector_poses_indexes = all_org_effector_poses_indexes
        all_prev_rep_effector_poses_indexes = all_rep_effector_poses_indexes
        all_prev_org_tip_poses_indexes = all_org_tip_poses_indexes
        all_prev_rep_tip_poses_indexes = all_rep_tip_poses_indexes
        
        return all_prev_org_effector_poses_indexes, all_prev_rep_effector_poses_indexes, all_prev_org_tip_poses_indexes, all_prev_rep_tip_poses_indexes

    # 手首位置合わせの準備
    def prepare_wrist(self, data_set_idx: int):
        self.target_links[data_set_idx] = {}
        data_set = self.options.data_set_list[data_set_idx]

        bone_names = []

        for (alignment_idx, direction) in [(1, "左"), (2, "右")]:
            # 手のひら頂点計算
            self.calc_wrist_entity_vertex(data_set_idx, data_set.org_model, "作成元", direction)
            self.calc_wrist_entity_vertex(data_set_idx, data_set.rep_model, "変換先", direction)

            tip_bone_name = "{0}人指先".format(direction)
            if tip_bone_name not in data_set.org_model.bones or tip_bone_name not in data_set.rep_model.bones:
                # 指先がどっちかにない場合、手首を対象とする
                tip_bone_name = "{0}手首".format(direction)

            # 指先までのリンク
            org_wrist_links = data_set.org_model.create_link_2_top_one(tip_bone_name)
            rep_wrist_links = data_set.rep_model.create_link_2_top_one(tip_bone_name)

            # IK用リンク（エフェクタから追加していく）
            ik_links_list = []
            ik_count_list = []

            wrist_bone = rep_wrist_links.get("{0}手首".format(direction))

            # ひじは角度制限をつける
            elbow_bone = rep_wrist_links.get("{0}ひじ".format(direction))
            # elbow_bone.ik_limit_min = MVector3D(-180, -0.5, -10)
            # elbow_bone.ik_limit_max = MVector3D(180, 180, 10)
            elbow_bone.dot_limit = 0.7
            
            arm_bone = rep_wrist_links.get("{0}腕".format(direction))
            arm_bone.dot_limit = 0.7

            if not self.options.arm_options.avoidance:
                # 腕だけ動かすパターンは接触回避もやった場合は行わない
                ik_links = BoneLinks()
                ik_links.append(wrist_bone)
                ik_links.append(arm_bone)
                ik_links_list.append(ik_links)
                ik_count_list.append(10)
            
            ik_links = BoneLinks()
            ik_links.append(wrist_bone)
            ik_links.append(elbow_bone)
            ik_links_list.append(ik_links)
            ik_count_list.append(10)

            ik_links = BoneLinks()
            ik_links.append(wrist_bone)
            ik_links.append(elbow_bone)
            ik_links.append(arm_bone)
            ik_links_list.append(ik_links)
            ik_count_list.append(10)

            if tip_bone_name == "{0}手首".format(direction):
                # 位置合わせが手首の場合、先端調整不要
                tip_ik_links = None
                # 手のひらの長さ（指のないモデルである場合、仮に1を設定）
                org_palm_length = 1
                rep_palm_length = 1
            else:
                tip_ik_links = BoneLinks()
                tip_ik_links.append(rep_wrist_links.get(tip_bone_name))
                tip_ik_links.append(rep_wrist_links.get("{0}手首".format(direction)))
                # 手のひらの長さ
                org_palm_length = (data_set.org_model.bones["{0}手首".format(direction)].position.distanceToPoint(data_set.org_model.bones[tip_bone_name].position))
                rep_palm_length = (data_set.rep_model.bones["{0}手首".format(direction)].position.distanceToPoint(data_set.rep_model.bones[tip_bone_name].position))

            logger.info("【No.%s】作成元モデルの%s手のひらの大きさ: %s", (data_set_idx + 1), direction, org_palm_length)
            logger.info("【No.%s】変換先モデルの%s手のひらの大きさ: %s", (data_set_idx + 1), direction, rep_palm_length)

            # 手首リンク登録
            self.target_links[data_set_idx][alignment_idx] = \
                ArmAlignmentOption(org_wrist_links, rep_wrist_links, ik_links_list, ik_count_list, tip_ik_links, \
                                   org_palm_length, rep_palm_length, data_set.org_model, data_set.rep_model, "{0}腕".format(direction), \
                                   "{0}手首".format(direction), "{0}手首".format(direction), tip_bone_name, self.options.arm_options.alignment_distance_wrist, data_set.xz_ratio)

            # 腕・ひじ・手首のキーフレ
            bone_names.extend(["{0}腕".format(direction), "{0}腕捩り".format(direction), "{0}ひじ".format(direction), "{0}手捩り".format(direction), "{0}手首".format(direction)])

            # 床位置合わせも行う場合、リンク追加生成
            if self.options.arm_options.alignment_floor_flg:
                # IK用リンク（エフェクタから追加していく）
                ik_links_list = []
                ik_count_list = []

                ik_links = BoneLinks()
                ik_links.append(wrist_bone)
                
                if rep_wrist_links.get("上半身2") and "上半身2" in data_set.motion.bones:
                    # 上半身2もある場合、上半身2も補正する
                    upper_bone2 = rep_wrist_links.get("上半身2")
                    upper_bone2.dot_limit = 0.9
                    ik_links.append(upper_bone2)

                upper_bone = rep_wrist_links.get("上半身")
                upper_bone.dot_limit = 0.9
                ik_links.append(upper_bone)

                ik_links_list.append(ik_links)
                ik_count_list.append(10)

                # 手首リンク登録(alignmentをマイナスとする)
                self.target_links[data_set_idx][-alignment_idx] = \
                    ArmAlignmentOption(org_wrist_links, rep_wrist_links, ik_links_list, ik_count_list, tip_ik_links, \
                                       org_palm_length, rep_palm_length, data_set.org_model, data_set.rep_model, "床", \
                                       "{0}手首".format(direction), "床", tip_bone_name, \
                                       self.options.arm_options.alignment_distance_floor, data_set.xz_ratio)

        if self.options.arm_options.alignment_floor_flg:
            # 床位置合わせの場合、上半身系も対象とする
            bone_names.extend(["上半身", "上半身2"])

        return bone_names

    # 指位置合わせの準備
    def prepare_finger(self, data_set_idx: int):
        data_set = self.options.data_set_list[data_set_idx]

        # ボーンセット確認
        finger_name_list = []
        for direction in ["左", "右"]:
            for finger_name in ["親指", "人指", "中指", "薬指", "小指"]:
                finger_name_list.append("{0}{1}先".format(direction, finger_name))
        
        if not set(finger_name_list).issubset(data_set.org_model.bones) or not set(finger_name_list).issubset(data_set.org_model.bones):
            logger.warning("指ボーンが不足しているため、指位置合わせはスキップします。", decoration=MLogger.DECORATION_BOX)
            return []
        
        alignment_start_idx = len(self.target_links[data_set_idx].keys()) + 1

        for direction_idx, direction in enumerate(["左", "右"]):
            for finger_idx, finger_name in enumerate(["親指", "人指", "中指", "薬指", "小指"]):
                alignment_idx = (direction_idx * 5) + finger_idx + alignment_start_idx
            
                total_finger_name = "{0}{1}先".format(direction, finger_name)

                # 手のひらの長さ
                org_palm_length = (data_set.org_model.bones["{0}手首".format(direction)].position.distanceToPoint(data_set.org_model.bones[total_finger_name].position))
                rep_palm_length = (data_set.rep_model.bones["{0}手首".format(direction)].position.distanceToPoint(data_set.rep_model.bones[total_finger_name].position))

                # 指リンク
                org_finger_links = data_set.org_model.create_link_2_top_one(total_finger_name)
                rep_finger_links = data_set.rep_model.create_link_2_top_one(total_finger_name)

                # IK用リンク（エフェクタから追加していく）
                ik_links_list = []
                ik_count_list = []

                # ひじは角度制限をつける
                elbow_bone = rep_finger_links.get("{0}ひじ".format(direction))
                # elbow_bone.ik_limit_min = MVector3D(-180, -0.5, -90)
                # elbow_bone.ik_limit_max = MVector3D(180, 180, 90)
                elbow_bone.dot_limit = 0.7

                arm_bone = rep_finger_links.get("{0}腕".format(direction))
                arm_bone.dot_limit = 0.7

                if not self.options.arm_options.avoidance:
                    # 腕だけ動かすパターンは接触回避もやった場合は行わない
                    ik_links = BoneLinks()
                    ik_links.append(rep_finger_links.get(total_finger_name))
                    ik_links.append(arm_bone)
                    ik_links_list.append(ik_links)
                    ik_count_list.append(10)
                            
                ik_links = BoneLinks()
                ik_links.append(rep_finger_links.get(total_finger_name))
                ik_links.append(elbow_bone)
                ik_links_list.append(ik_links)
                ik_count_list.append(10)

                ik_links = BoneLinks()
                ik_links.append(rep_finger_links.get(total_finger_name))
                ik_links.append(elbow_bone)
                ik_links.append(arm_bone)
                ik_links_list.append(ik_links)
                ik_count_list.append(10)

                # 先端リンク
                tip_ik_links = BoneLinks()
                tip_ik_links.append(rep_finger_links.get(total_finger_name))
                tip_ik_links.append(rep_finger_links.get("{0}手首".format(direction)))

                # 指リンク登録
                self.target_links[data_set_idx][alignment_idx] = \
                    ArmAlignmentOption(org_finger_links, rep_finger_links, ik_links_list, ik_count_list, tip_ik_links, \
                                       org_palm_length, rep_palm_length, data_set.org_model, data_set.rep_model, "{0}腕".format(direction), \
                                       total_finger_name, total_finger_name[:3], total_finger_name, self.options.arm_options.alignment_distance_finger, data_set.xz_ratio)

            # # 腕・ひじ・手首・指のキーフレ（なければスルー）
            # fnos.extend(data_set.motion.get_bone_fnos("{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction), "{0}{1}０".format(direction, finger_name), \
            #                                             "{0}{1}１".format(direction, finger_name), "{0}{1}２".format(direction, finger_name), "{0}{1}３".format(direction, finger_name)))

        return []

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
                    and data_set_idx not in target_data_set_idxs:
                # ボーンセットがあり、腕系サイジング可能で、かつまだ登録されていない場合
                target_data_set_idxs.append(data_set_idx)
            
        return target_data_set_idxs


# 位置合わせ用オプション
class ArmAlignmentOption():

    def __init__(self, org_links: BoneLinks, rep_links: BoneLinks, ik_links_list: list, ik_count_list: list, \
                 tip_ik_links: BoneLinks, org_palm_length: float, rep_palm_length: float, org_model: PmxModel, rep_model: PmxModel, \
                 start_bone_name: str, effector_bone_name: str, effector_display_bone_name: str, tip_bone_name: str, distance: float, xz_ratio: float):
        super().__init__()

        self.org_links = org_links
        self.rep_links = rep_links
        self.ik_links_list = ik_links_list
        self.ik_count_list = ik_count_list
        self.tip_ik_links = tip_ik_links
        self.org_palm_length = org_palm_length
        self.rep_palm_length = rep_palm_length
        self.start_bone_name = start_bone_name
        self.effector_bone_name = effector_bone_name
        self.effector_display_bone_name = effector_display_bone_name
        self.distance = distance
        self.tip_bone_name = tip_bone_name

        if "床" in start_bone_name:
            # 元と先の比率（床の場合、XZ比率で身体の大きさだけ検討する）
            self.ratio = xz_ratio
        else:
            # エフェクタまでの長さ比率
            org_effector_diff = (org_model.bones[effector_bone_name].position - org_model.bones[start_bone_name].position)
            org_effector_diff.one()
            rep_effector_diff = (rep_model.bones[effector_bone_name].position - rep_model.bones[start_bone_name].position)
            rep_effector_diff.one()
            effector_diff_ratio = rep_effector_diff.length() / org_effector_diff.length()

            # 元と先の比率
            self.ratio = effector_diff_ratio
        # 元と先の比率（複数モーション時）
        self.multi_ratio = xz_ratio
        
        # 手首実体の厚み比
        org_wrist_entity_diff = org_model.bones["{0}手首実体".format(effector_bone_name[0])].position - org_model.bones["{0}手首".format(effector_bone_name[0])].position
        org_wrist_entity_diff.one()
        rep_wrist_entity_diff = rep_model.bones["{0}手首実体".format(effector_bone_name[0])].position - rep_model.bones["{0}手首".format(effector_bone_name[0])].position
        rep_wrist_entity_diff.one()
        effector_diff_ratio = rep_wrist_entity_diff.length() / org_wrist_entity_diff.length()

        self.entity_ratio = np.array([effector_diff_ratio, effector_diff_ratio, effector_diff_ratio])



