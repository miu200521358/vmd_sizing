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


class ArmAlignmentService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        # 腕処理対象データセットを取得
        self.target_data_set_idxs = self.get_target_set_idxs()
        logger.test("target_data_set_idxs: %s", self.target_data_set_idxs)

        if len(self.target_data_set_idxs) == 0:
            # データセットがない場合、処理スキップ
            logger.warning("位置合わせができるファイルセットが見つからなかったため、位置合わせ処理をスキップします。", decoration=MLogger.DECORATION_BOX)
            return True

        # リンク辞書
        self.target_links = {}
        # 処理対象ボーン名リスト
        bone_names = []

        logger.info("位置合わせ　", decoration=MLogger.DECORATION_LINE)

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
            fnos.extend(data_set.motion.get_bone_fnos(*bone_names))

        # キーフレを重複除外してソートする
        fnos = sorted(list(set(fnos)))

        # 位置合わせ準備
        all_alignment_group_list, all_messages = self.prepare_alignment(fnos)

        # 位置合わせ実行
        self.execute_alignment(fnos, all_alignment_group_list, all_messages)

        futures = []
        with ThreadPoolExecutor(thread_name_prefix="alignment_after") as executor:
            for data_set_idx, data_set in enumerate(self.options.data_set_list):
                for direction in ["右", "左"]:
                    for bone_name in ["{0}腕".format(direction), "{0}ひじ".format(direction), "{0}手首".format(direction)]:
                        futures.append(executor.submit(self.alignment_after, data_set_idx, bone_name))

        concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

        for f in futures:
            if not f.result():
                return False

        return True

    # 位置合わせ準備
    def prepare_alignment(self, fnos: list):
        all_distances = {}
        all_messages = {}
        all_is_alignment = {}
        all_alignment_idx = {}

        org_global_3ds = {}
        org_global_matrixs = {}

        prev_block_fno = 0

        for data_set_idx, alignment_options in self.target_links.items():
            for alignment_idx, target_link in alignment_options.items():
                # indexを保持
                all_is_alignment[(data_set_idx, alignment_idx)] = {}
                all_alignment_idx[(data_set_idx, alignment_idx)] = -1

        for fno in fnos:
            org_global_3ds[fno] = {}
            org_global_matrixs[fno] = {}

            # 処理対象キーフレを先頭からひとつずつチェックしていく
            for data_set_idx, alignment_options in self.target_links.items():
                for alignment_idx, target_link in alignment_options.items():
                    # 処理対象データセット
                    data_set = self.options.data_set_list[data_set_idx]

                    # 元モデルのそれぞれのグローバル位置
                    org_global_3ds[fno][(data_set_idx, alignment_idx)], org_global_matrixs[fno][(data_set_idx, alignment_idx)] = \
                        MServiceUtils.calc_global_pos(data_set.org_model, target_link.org_links, data_set.org_motion, fno, return_matrix=True)

                    if alignment_idx < 0:
                        # 床の位置は各位置のY0をvectorの場合のみ定義し直す（距離を測る用）
                        for org_global_vec in org_global_3ds[fno][(data_set_idx, alignment_idx)].values():
                            org_global_vec.setY(0)
                    
            distances = {}

            # それぞれの距離を算出
            # 起点となるボーン
            for (from_data_set_idx, from_alignment_idx), org_from_global_3ds in org_global_3ds[fno].items():
                for (to_data_set_idx, to_alignment_idx), org_to_global_3ds in org_global_3ds[fno].items():

                    # 処理対象
                    from_target_link = self.target_links[from_data_set_idx][from_alignment_idx]
                    to_target_link = self.target_links[to_data_set_idx][to_alignment_idx]

                    if (from_data_set_idx, from_alignment_idx) == (to_data_set_idx, to_alignment_idx) or \
                        from_target_link.start_bone_name == to_target_link.start_bone_name or \
                            (from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx) in distances or \
                            (to_data_set_idx, to_alignment_idx, from_data_set_idx, from_alignment_idx) in distances or \
                            (from_alignment_idx < 0 and to_alignment_idx < 0) or \
                            ((from_alignment_idx < 0 or to_alignment_idx < 0) and \
                                (from_data_set_idx != to_data_set_idx or (from_data_set_idx == to_data_set_idx and abs(to_alignment_idx) != abs(from_alignment_idx)))):
                        # 同じINDEXか、同じ計算対象、両方床、既に計算済みのペア、床の場合は自身以外とは計算不要
                        continue
                                    
                    # 2点間の距離を算出
                    distances[(from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx)] \
                        = org_from_global_3ds[from_target_link.effector_bone_name].distanceToPoint(\
                            org_to_global_3ds[to_target_link.effector_bone_name])

            logger.test("fno: %s, distances: %s", fno, distances)
            
            all_messages[fno] = []
            all_distances[fno] = {}
            for (from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx), distance in distances.items():
                # 距離を2点間の手のひらの大きさの平均から比率として求める
                distance_ratio = distance / np.mean([self.target_links[from_data_set_idx][from_alignment_idx].org_palm_length, self.target_links[to_data_set_idx][to_alignment_idx].org_palm_length])
                logger.test("fno: %s, (%s,%s,%s,%s): d: %s, dr: %s", fno, from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx, distance, distance_ratio)
                
                # 基準距離（床は床位置合わせの距離が入ってる）
                base_distance = self.target_links[to_data_set_idx][to_alignment_idx].distance
                # 基準距離以内か常に位置合わせを行うかの場合、位置合わせ処理実行
                is_alignment = 0 < distance_ratio <= base_distance or base_distance == 10

                # 距離をキーにして、INDEXの組合せを登録
                if distance_ratio not in all_distances[fno]:
                    all_distances[fno][distance_ratio] = []

                all_distances[fno][distance_ratio].append((from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx, is_alignment))
                all_is_alignment[(from_data_set_idx, from_alignment_idx)][fno] = is_alignment
                all_is_alignment[(to_data_set_idx, to_alignment_idx)][fno] = is_alignment

                if is_alignment:
                    # ログ用情報保持
                    all_messages[fno].append("○近接あり: f: {0}({1}-{2}:{3}-{4}), 境界: {5}".format(fno, \
                                             (from_data_set_idx + 1), self.target_links[from_data_set_idx][from_alignment_idx].effector_display_bone_name, \
                                             (to_data_set_idx + 1), self.target_links[to_data_set_idx][to_alignment_idx].effector_display_bone_name, round(distance_ratio, 5)))
                
                elif base_distance < distance_ratio <= base_distance * 3:
                    # 基準距離に近い場合、情報だけ保持
                    # 各キーフレにおける距離情報保持
                    if fno not in all_messages:
                        all_messages[fno] = []

                    # ログ用情報保持
                    all_messages[fno].append("－近接なし: f: {0}({1}-{2}:{3}-{4}), 境界: {5}".format(fno, \
                                             (from_data_set_idx + 1), self.target_links[from_data_set_idx][from_alignment_idx].effector_display_bone_name, \
                                             (to_data_set_idx + 1), self.target_links[to_data_set_idx][to_alignment_idx].effector_display_bone_name, round(distance_ratio, 5)))

            if fno // 200 > prev_block_fno:
                logger.info("-- %sフレーム目:終了(%s％)【位置合わせ準備①】", fno, round((fno / fnos[-1]) * 100, 3))
                prev_block_fno = fno // 200

        logger.info("-- %sフレーム目:終了(%s％)【位置合わせ準備①】", fno, round((fno / fnos[-1]) * 100, 3))

        all_alignment_group_list = []
        prev_block_fno = 0

        # 距離の近いものからINDEXの組合せを登録
        # 基本的には全部の中心点を算出するが、それぞれのモデルの両手のみが近かった場合を想定
        for fidx, fno in enumerate(all_distances.keys()):
            for distance_ratio in sorted(all_distances[fno].keys()):
                for from_data_set_idx, from_alignment_idx, to_data_set_idx, to_alignment_idx, is_alignment in all_distances[fno][distance_ratio]:
                    # 前回の位置合わせ
                    prev_from_alignment = False if fidx == 0 else all_is_alignment[(from_data_set_idx, from_alignment_idx)][list(all_distances.keys())[fidx - 1]]
                    prev_to_alignment = False if fidx == 0 else all_is_alignment[(to_data_set_idx, to_alignment_idx)][list(all_distances.keys())[fidx - 1]]

                    # 処理対象
                    from_target_link = self.target_links[from_data_set_idx][from_alignment_idx]
                    to_target_link = self.target_links[to_data_set_idx][to_alignment_idx]

                    if is_alignment:
                        # 位置合わせする場合

                        # 前回既に位置合わせが必要であった場合、そのINDEXを使用する
                        if prev_from_alignment:
                            # FROM前回が位置合わせONの場合、FROMに寄せる
                            alignment_idx = all_alignment_idx[(from_data_set_idx, from_alignment_idx)]
                        elif prev_to_alignment:
                            # FROMが前回位置合わせOFFで、前回TOがONの場合、TOに寄せる
                            alignment_idx = all_alignment_idx[(to_data_set_idx, to_alignment_idx)]
                        else:
                            # FROMもTOも前回位置合わせOFFの場合、新たに発行
                            all_alignment_group_list.append({
                                "fnos": [], "alignment_idxs": {}, "org_fno_global_effector": {}, "org_block_global_effector": [], \
                                "org_mean_vec": {}, "org_origin_matrix": {}, "rep_fno_global_effector": {}, "rep_block_global_effector": []
                            })
                            alignment_idx = len(all_alignment_group_list) - 1

                            # 位置合わせIDXを設定
                            all_alignment_idx[(from_data_set_idx, from_alignment_idx)] = alignment_idx
                            all_alignment_idx[(to_data_set_idx, to_alignment_idx)] = alignment_idx

                        # fno
                        all_alignment_group_list[alignment_idx]["fnos"].append(fno)

                        # 方向
                        # キーフレ単位の情報（1-2, 2-3 とかあるので、同じキーフレに複数の情報の可能性あり）
                        if fno not in all_alignment_group_list[alignment_idx]["alignment_idxs"]:
                            all_alignment_group_list[alignment_idx]["alignment_idxs"][fno] = []
                            
                        if (from_data_set_idx, from_alignment_idx) not in all_alignment_group_list[alignment_idx]["alignment_idxs"][fno]:
                            all_alignment_group_list[alignment_idx]["alignment_idxs"][fno].append((from_data_set_idx, from_alignment_idx))

                        if (to_data_set_idx, to_alignment_idx) not in all_alignment_group_list[alignment_idx]["alignment_idxs"][fno]:
                            all_alignment_group_list[alignment_idx]["alignment_idxs"][fno].append((to_data_set_idx, to_alignment_idx))
                            
                        # キーフレ単位のエフェクタ位置情報
                        if fno not in all_alignment_group_list[alignment_idx]["org_fno_global_effector"]:
                            all_alignment_group_list[alignment_idx]["org_fno_global_effector"][fno] = {}
                            
                        all_alignment_group_list[alignment_idx]["org_fno_global_effector"][fno][(from_data_set_idx, from_alignment_idx)] \
                            = org_global_3ds[fno][(from_data_set_idx, from_alignment_idx)][from_target_link.effector_bone_name].data()

                        all_alignment_group_list[alignment_idx]["org_fno_global_effector"][fno][(to_data_set_idx, to_alignment_idx)] \
                            = org_global_3ds[fno][(to_data_set_idx, to_alignment_idx)][to_target_link.effector_bone_name].data()

                        # ブロック単位のエフェクタ位置情報（とりあえず全部まとめて）
                        all_alignment_group_list[alignment_idx]["org_block_global_effector"].append(org_global_3ds[fno][(from_data_set_idx, from_alignment_idx)][from_target_link.effector_bone_name].data())
                        all_alignment_group_list[alignment_idx]["org_block_global_effector"].append(org_global_3ds[fno][(to_data_set_idx, to_alignment_idx)][to_target_link.effector_bone_name].data())
        
            if fno // 500 > prev_block_fno:
                logger.info("-- %sフレーム目:終了(%s％)【位置合わせ準備②】", fno, round((fno / fnos[-1]) * 100, 3))
                prev_block_fno = fno // 500

        logger.info("-- %sフレーム目:終了(%s％)【位置合わせ準備②】", fno, round((fno / fnos[-1]) * 100, 3))

        prev_block_fno = 0

        # グループ単位で中央値
        for all_alignment_group in all_alignment_group_list:
            # ブロック単位の中央値
            org_block_mean_vec = MVector3D(np.mean(all_alignment_group["org_block_global_effector"], axis=0))

            for fno in fnos:
                if fno not in all_alignment_group["fnos"]:
                    continue

                # キーフレ単位の中央値
                org_fno_mean_vec = MVector3D(np.mean(list(all_alignment_group["org_fno_global_effector"][fno].values()), axis=0))

                for data_set_idx, alignment_idx in all_alignment_group["alignment_idxs"][fno]:
                    # 処理対象データセット
                    data_set = self.options.data_set_list[data_set_idx]
                    # 処理対象
                    target_link = self.target_links[data_set_idx][alignment_idx]

                    # 首根元（体幹の最終的な向き）までの行列
                    org_trunk_matrix = org_global_matrixs[fno][(data_set_idx, alignment_idx)]["首根元"].copy()

                    # エフェクタのグローバル位置
                    org_global_effector = org_global_3ds[fno][(data_set_idx, alignment_idx)][target_link.effector_bone_name]

                    # 体幹から見たキーフレ中央値のローカル位置
                    org_trunk_local_fno_origin = org_trunk_matrix.inverted() * org_fno_mean_vec

                    # 体幹から見たブロック中央値のローカル位置
                    org_trunk_local_block_origin = org_trunk_matrix.inverted() * org_block_mean_vec

                    # ローカルYはブロック中央値を採用
                    org_trunk_local_fno_origin.setY(org_trunk_local_block_origin.y())

                    # 作成元中点のローカル座標系
                    org_origin_matrix = org_trunk_matrix.copy()

                    # 作成元中点のローカル座標とする
                    org_origin_matrix.translate(org_trunk_local_fno_origin)
                
                    # 再生成した元中央値
                    org_mean_vec = MVector3D(org_trunk_matrix * org_trunk_local_fno_origin)

                    # 作成元の中心点 ---------------
                    debug_bone_name = "左1"

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = org_mean_vec
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf

                    # 作成元のエフェクタボーン位置 -------------
                    debug_bone_name = "{0}2".format(target_link.effector_bone_name[0])

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = org_global_effector
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf

                    all_alignment_group["org_mean_vec"][(fno, data_set_idx, alignment_idx)] = org_mean_vec
                    all_alignment_group["org_origin_matrix"][(fno, data_set_idx, alignment_idx)] = org_origin_matrix

        return all_alignment_group_list, all_messages
    
    # 位置合わせ実行
    def execute_alignment(self, fnos: list, all_alignment_group_list: list, all_messages: dict):
        rep_global_3ds = {}
        rep_global_matrixs = {}
        
        prev_block_fno = 0
        for all_alignment_group in all_alignment_group_list:
            for fno in all_alignment_group["fnos"]:
                rep_global_3ds[fno] = {}
                rep_global_matrixs[fno] = {}

                for data_set_idx, alignment_idx in all_alignment_group["alignment_idxs"][fno]:
                    # 処理対象データセット
                    data_set = self.options.data_set_list[data_set_idx]
                    # 処理対象
                    target_link = self.target_links[data_set_idx][alignment_idx]

                    # 元モデルのそれぞれのグローバル位置
                    rep_global_3ds[fno][(data_set_idx, alignment_idx)], rep_global_matrixs[fno][(data_set_idx, alignment_idx)] = \
                        MServiceUtils.calc_global_pos(data_set.rep_model, target_link.rep_links, data_set.motion, fno, return_matrix=True)

                    # キーフレ単位のエフェクタ位置情報
                    if fno not in all_alignment_group["rep_fno_global_effector"]:
                        all_alignment_group["rep_fno_global_effector"][fno] = {}
                        
                    all_alignment_group["rep_fno_global_effector"][fno][(data_set_idx, alignment_idx)] \
                        = rep_global_3ds[fno][(data_set_idx, alignment_idx)][target_link.effector_bone_name].data()

                    # ブロック単位のエフェクタ位置情報（とりあえず全部まとめて）
                    all_alignment_group["rep_block_global_effector"].append(rep_global_3ds[fno][(data_set_idx, alignment_idx)][target_link.effector_bone_name].data())

            if fno // 1000 > prev_block_fno and fnos[-1] > 0:
                logger.info("-- %sフレーム目:終了(%s％)【位置合わせ準備③】", fno, round((fno / fnos[-1]) * 100, 3))
                prev_block_fno = fno // 1000
    
        prev_block_fno = 0
                
        # グループ単位で中央値
        for all_alignment_group in all_alignment_group_list:
            # ブロック単位の中央値
            rep_block_mean_vec = MVector3D(np.mean(all_alignment_group["rep_block_global_effector"], axis=0))

            for fno in all_alignment_group["fnos"]:
                if fno in all_messages.keys():
                    # 位置合わせメッセージ出力
                    [logger.info(msg) for msg in all_messages[fno]]

                # キーフレ単位の中央値
                rep_fno_mean_vec = MVector3D(np.mean(list(all_alignment_group["rep_fno_global_effector"][fno].values()), axis=0))

                # 床との位置合わせがある場合、TRUE
                is_floor = ([ai < 0 for (di, ai) in all_alignment_group["alignment_idxs"][fno]].count(True) > 0)
                # 他データとの位置合わせ（床との組合せは除く）がある場合、TRUE
                is_multi = len(set([di for (di, ai) in all_alignment_group["alignment_idxs"][fno]])) > 1 and not is_floor

                for data_set_idx, alignment_idx in all_alignment_group["alignment_idxs"][fno]:
                    # 処理対象データセット
                    data_set = self.options.data_set_list[data_set_idx]
                    # 処理対象
                    target_link = self.target_links[data_set_idx][alignment_idx]

                    # 首根先（体幹の最終的な向き）までの行列
                    rep_trunk_matrix = rep_global_matrixs[fno][(data_set_idx, alignment_idx)]["首根元"].copy()

                    # エフェクタのグローバル位置
                    rep_global_effector = rep_global_3ds[fno][(data_set_idx, alignment_idx)][target_link.effector_bone_name]

                    # 体幹から見たキーフレ中央値のローカル位置
                    rep_trunk_local_fno_origin = rep_trunk_matrix.inverted() * rep_fno_mean_vec

                    # 体幹から見たブロック中央値のローカル位置
                    rep_trunk_local_block_origin = rep_trunk_matrix.inverted() * rep_block_mean_vec

                    # ローカルYはブロック中央値を採用
                    rep_trunk_local_fno_origin.setY(rep_trunk_local_block_origin.y())

                    # 変換先中点のローカル座標系
                    rep_origin_matrix = rep_trunk_matrix.copy()

                    # 変換先中点のローカル座標とする
                    rep_origin_matrix.translate(rep_trunk_local_fno_origin)
                
                    # 再生成した先中央値
                    rep_mean_vec = MVector3D(rep_trunk_matrix * rep_trunk_local_fno_origin)

                    # 現在のエフェクタ位置
                    rep_effector_vec = MVector3D(all_alignment_group["rep_fno_global_effector"][fno][(data_set_idx, alignment_idx)])

                    # 変換先の中心点 ---------------
                    debug_bone_name = "右1"

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = rep_mean_vec
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf

                    # 変換先のエフェクタボーン位置 -------------
                    debug_bone_name = "{0}3".format(target_link.effector_bone_name[0])

                    debug_bf = VmdBoneFrame(fno)
                    debug_bf.key = True
                    debug_bf.set_name(debug_bone_name)
                    debug_bf.position = rep_global_effector
                    
                    if debug_bone_name not in data_set.motion.bones:
                        data_set.motion.bones[debug_bone_name] = {}
                    
                    data_set.motion.bones[debug_bone_name][fno] = debug_bf

                    org_fno_global_effector = MVector3D(all_alignment_group["org_fno_global_effector"][fno][(data_set_idx, alignment_idx)])

                    # 作成元中点から見た、作成元エフェクタのローカル位置
                    org_origin_matrix = all_alignment_group["org_origin_matrix"][(fno, data_set_idx, alignment_idx)]
                    org_local_effector = org_origin_matrix.inverted() * org_fno_global_effector

                    logger.debug("f: %s(%s:%s), org_origin[%s], org_fno_global_effector[%s]", fno, (data_set_idx + 1), \
                                 target_link.effector_bone_name[0], (org_origin_matrix * MVector3D()).to_log(), \
                                 org_fno_global_effector.to_log())

                    # 変換先エフェクタのローカル位置（作成元をコピー）
                    rep_local_effector = org_local_effector.copy()

                    # ローカルエフェクタのYはY差
                    rep_local_effector.setY(rep_local_effector.y() * target_link.ratio)
                    # ローカルエフェクタのZはXZ差
                    rep_local_effector.setZ(rep_local_effector.z() * target_link.ratio)

                    logger.debug("f: %s(%s:%s), org_local_effector[%s], rep_trunk_local_fno_origin[%s], rep_local_effector[%s]", fno, (data_set_idx + 1), \
                                 target_link.effector_bone_name[0], org_local_effector.to_log(), rep_trunk_local_fno_origin.to_log(), rep_local_effector.to_log())

                    # 変換先エフェクタのグローバル位置
                    rep_global_effector = rep_origin_matrix * rep_local_effector

                    is_success = []
                    is_failure_last_names = []

                    # 位置合わせ前のbf情報
                    org_bfs = {}
                    for ik_links in target_link.ik_links_list:
                        for link_name in ik_links.all().keys():
                            if link_name not in org_bfs:
                                org_bfs[link_name] = data_set.motion.calc_bf(link_name, fno).copy()

                    prev_rep_diff = MVector3D()

                    # IK処理実行
                    for ik_cnt, (ik_links, ik_max_count) in enumerate(zip(target_link.ik_links_list, target_link.ik_count_list)):
                        for now_ik_max_count in range(1, ik_max_count + 1):
                            logger.debug("IK計算開始(%s): f: %s(%s:%s), 現在[%s], 指定[%s]", now_ik_max_count, fno, (data_set_idx + 1), \
                                         list(ik_links.all().keys()), rep_effector_vec.to_log(), rep_global_effector.to_log())
                            
                            # IK計算実行
                            MServiceUtils.calc_IK(data_set.rep_model, target_link.rep_links, data_set.motion, fno, rep_global_effector, ik_links, max_count=now_ik_max_count)

                            # 現在のエフェクタ位置
                            aligned_rep_global_3ds = MServiceUtils.calc_global_pos(data_set.rep_model, target_link.rep_links, data_set.motion, fno)
                            aligned_rep_effector_vec = aligned_rep_global_3ds[target_link.effector_bone_name]

                            # 現在のエフェクタ位置との差分(エフェクタ位置が指定されている場合のみ)
                            rep_diff = rep_global_effector - aligned_rep_effector_vec

                            # IKの関連ボーンの内積チェック
                            dot_dict = {}
                            dot_limit_dict = {}
                            for link_name, link_bone in ik_links.all().items():
                                dot_dict[link_name] = MQuaternion.dotProduct(org_bfs[link_name].rotation, data_set.motion.calc_bf(link_name, fno).rotation)
                                dot_limit_dict[link_name] = link_bone.dot_limit + (-0.2 if is_multi else 0)

                            if (np.count_nonzero(np.where(np.abs(rep_diff.data()) > 0.2, 1, 0)) == 0 and \
                                    np.count_nonzero(np.where(np.array(list(dot_dict.values())) < np.array(list(dot_limit_dict.values())), 1, 0)) == 0):
                                logger.debug("☆位置合わせ実行成功(%s): f: %s(%s:%s), 指定[%s], 結果[%s], diff[%s], dot: %s", now_ik_max_count, fno, (data_set_idx + 1), \
                                             list(ik_links.all().keys()), rep_global_effector.to_log(), aligned_rep_effector_vec.to_log(), \
                                             rep_diff.to_log(), list(dot_dict.values()))

                                # 位置合わせ後のエフェクタボーン位置 -------------
                                debug_bone_name = "{0}4".format(target_link.effector_bone_name[0])

                                debug_bf = VmdBoneFrame(fno)
                                debug_bf.key = True
                                debug_bf.set_name(debug_bone_name)
                                debug_bf.position = aligned_rep_effector_vec
                                
                                if debug_bone_name not in data_set.motion.bones:
                                    data_set.motion.bones[debug_bone_name] = {}
                                
                                data_set.motion.bones[debug_bone_name][fno] = debug_bf
                                # ----------

                                # 大体同じ位置にあって、角度もそう大きくズレてない場合、OK(全部上書き)
                                is_success = [True]

                                # bf確定
                                for link_name, link_bone in ik_links.all().items():
                                    ik_bf = data_set.motion.calc_bf(link_name, fno)
                                    logger.test("f: %s(%s:%s), ik_rot[%s]", fno, (data_set_idx + 1), \
                                                target_link.effector_bone_name[0], ik_bf.rotation.toEulerAngles().to_log())
                                    data_set.motion.regist_bf(ik_bf, link_name, fno)

                                break
                            elif (np.count_nonzero(np.where(np.abs(rep_diff.data()) > 1, 1, 0)) == 0 and \
                                    np.count_nonzero(np.where(np.array(list(dot_dict.values())) < np.array(list(dot_limit_dict.values())), 1, 0)) == 0):
                                if prev_rep_diff == MVector3D() or np.sum(np.abs(rep_diff.data())) < np.sum(np.abs(prev_rep_diff.data())):
                                    logger.debug("☆位置合わせ実行ちょっと失敗採用(%s): f: %s(%s:%s), 指定[%s], 結果[%s], diff[%s], dot: %s", now_ik_max_count, fno, (data_set_idx + 1), \
                                                 list(ik_links.all().keys()), rep_global_effector.to_log(), aligned_rep_effector_vec.to_log(), \
                                                 rep_diff.to_log(), list(dot_dict.values()))

                                    is_success.append(True)

                                    # 位置合わせ後のエフェクタボーン位置 -------------
                                    debug_bone_name = "{0}4".format(target_link.effector_bone_name[0])

                                    debug_bf = VmdBoneFrame(fno)
                                    debug_bf.key = True
                                    debug_bf.set_name(debug_bone_name)
                                    debug_bf.position = aligned_rep_effector_vec
                                    
                                    if debug_bone_name not in data_set.motion.bones:
                                        data_set.motion.bones[debug_bone_name] = {}
                                    
                                    data_set.motion.bones[debug_bone_name][fno] = debug_bf
                                    # ----------

                                    # ちょっと失敗初回か、前回より差が小さくなってる場合、org_bfを保持し直して、もう一周試す
                                    for link_name in ik_links.all().keys():
                                        org_bfs[link_name] = data_set.motion.calc_bf(link_name, fno).copy()

                                    # bf確定
                                    for link_name, link_bone in ik_links.all().items():
                                        ik_bf = data_set.motion.calc_bf(link_name, fno)
                                        logger.debug("f: %s(%s:%s), ik_rot[%s]", fno, (data_set_idx + 1), \
                                                     target_link.effector_bone_name[0], ik_bf.rotation.toEulerAngles().to_log())
                                        data_set.motion.regist_bf(ik_bf, link_name, fno)

                                    prev_rep_diff = rep_diff
                                else:
                                    logger.debug("★位置合わせ実行ちょっと失敗不採用(%s): f: %s(%s:%s), 指定[%s], 結果[%s], diff[%s], dot: %s", now_ik_max_count, fno, (data_set_idx + 1), \
                                                 list(ik_links.all().keys()), rep_global_effector.to_log(), aligned_rep_effector_vec.to_log(), \
                                                 rep_diff.to_log(), list(dot_dict.values()))

                                    is_success.append(False)

                                    # 失敗していたら一旦元に戻す
                                    for link_name in list(ik_links.all().keys())[1:]:
                                        data_set.motion.regist_bf(org_bfs[link_name].copy(), link_name, fno)

                            else:
                                logger.debug("★位置合わせ実行失敗(%s): f: %s(%s:%s), 指定[%s], 結果[%s], vec[%s], dot: %s", now_ik_max_count, fno, (data_set_idx + 1), \
                                             list(ik_links.all().keys()), rep_global_effector.to_log(), aligned_rep_effector_vec.to_log(), rep_diff.to_log(), list(dot_dict.values()))

                                # 失敗していたら一旦元に戻す
                                for link_name in list(ik_links.all().keys())[1:]:
                                    data_set.motion.regist_bf(org_bfs[link_name].copy(), link_name, fno)

                                if ik_cnt == len(target_link.ik_links_list) - 1:
                                    # 最後が失敗していたら失敗
                                    is_success.append(False)
                                    is_failure_last_names.append(target_link.rep_links.last_display_name())

                        if is_success == [True]:
                            # 成功していたらそのまま終了
                            break

                    if len(is_success) > 0 and is_success.count(False) > 0:
                        # どこかのパターンで失敗してる場合、失敗ログ
                        dot_values = ",".join([str(round(dot, 5)) for dot in list(dot_dict.values())])
                        logger.info("×位置合わせ失敗: f: %s(%s-%s), 近似度: %s", fno, (data_set_idx + 1), target_link.effector_display_bone_name, dot_values)
                
            if fno // 500 > prev_block_fno:
                logger.info("-- %sフレーム目:終了(%s％)【位置合わせ】", fno, round((fno / fnos[-1]) * 100, 3))
                prev_block_fno = fno // 500

        logger.info("-- %sフレーム目:終了(%s％)【位置合わせ】", fno, round((fno / fnos[-1]) * 100, 3))

    # 位置合わせ後処理
    def alignment_after(self, data_set_idx: int, bone_name: str):
        try:
            logger.copy(self.options)
            data_set = self.options.data_set_list[data_set_idx]
            
            # logger.info("位置合わせ処理 - 円滑化【No.%s - %s】", (data_set_idx + 1), bone_name)

            # data_set.motion.smooth_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
            #                           data_set.rep_model.bones[bone_name].getTranslatable(), limit_degrees=1)

            logger.info("位置合わせ処理 - フィルタリング【No.%s - %s】", (data_set_idx + 1), bone_name)

            data_set.motion.smooth_filter_bf(data_set_idx + 1, bone_name, data_set.rep_model.bones[bone_name].getRotatable(), \
                                             data_set.rep_model.bones[bone_name].getTranslatable(), \
                                             config={"freq": 30, "mincutoff": 0.03, "beta": 0.1, "dcutoff": 1}, loop=1)

            # logger.info("位置合わせ処理 - 不要キー削除【No.%s - %s】", (data_set_idx + 1), bone_name)

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

            elbow_bone = rep_wrist_links.get("{0}ひじ".format(direction))
            elbow_bone.dot_limit = 0.8
            elbow_bone.degree_limit = 114.5916
            
            arm_bone = rep_wrist_links.get("{0}腕".format(direction))
            arm_bone.dot_limit = 0.9
            arm_bone.degree_limit = 57.2957

            # if not self.options.arm_options.avoidance:
            #     # 腕だけ動かすパターンは接触回避もやった場合は行わない
            #     ik_links = BoneLinks()
            #     ik_links.append(wrist_bone)
            #     ik_links.append(arm_bone)
            #     ik_links_list.append(ik_links)
            #     ik_count_list.append(5)
            
            # ik_links = BoneLinks()
            # ik_links.append(wrist_bone)
            # ik_links.append(elbow_bone)
            # ik_links_list.append(ik_links)
            # ik_count_list.append(5)

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
            bone_names.extend(["{0}腕".format(direction), "{0}腕捩".format(direction), "{0}ひじ".format(direction), "{0}手捩".format(direction), "{0}手首".format(direction)])

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
                    upper_bone2.degree_limit = 57.2957
                    ik_links.append(upper_bone2)

                upper_bone = rep_wrist_links.get("上半身")
                upper_bone.dot_limit = 0.9
                upper_bone.degree_limit = 57.2957
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

                elbow_bone = rep_finger_links.get("{0}ひじ".format(direction))
                elbow_bone.dot_limit = 0.8
                elbow_bone.degree_limit = 114.5916

                arm_bone = rep_finger_links.get("{0}腕".format(direction))
                arm_bone.dot_limit = 0.9
                arm_bone.degree_limit = 57.2957

                # if not self.options.arm_options.avoidance:
                #     # 腕だけ動かすパターンは接触回避もやった場合は行わない
                #     ik_links = BoneLinks()
                #     ik_links.append(rep_finger_links.get(total_finger_name))
                #     ik_links.append(arm_bone)
                #     ik_links_list.append(ik_links)
                #     ik_count_list.append(5)
                            
                # ik_links = BoneLinks()
                # ik_links.append(rep_finger_links.get(total_finger_name))
                # ik_links.append(elbow_bone)
                # ik_links_list.append(ik_links)
                # ik_count_list.append(5)

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



