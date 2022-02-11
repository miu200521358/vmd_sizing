# -*- coding: utf-8 -*-
#
from datetime import datetime
import sys
import pathlib
import numpy as np
import math
# このソースのあるディレクトリの絶対パスを取得
current_dir = pathlib.Path(__file__).resolve().parent
# モジュールのあるパスを追加
sys.path.append(str(current_dir) + '/../')
sys.path.append(str(current_dir) + '/../src/')

from mmd.PmxReader import PmxReader # noqa
from mmd.VmdReader import VmdReader # noqa
from mmd.VmdWriter import VmdWriter # noqa
from mmd.PmxWriter import PmxWriter # noqa
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint, Bdef1, Bdef2, Bdef4, RigidBodyParam # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils, MServiceUtils # noqa
from utils.MException import SizingException # noqa
from utils.MLogger import MLogger # noqa


MLogger.initialize(level=MLogger.DEBUG_INFO, is_file=True)
logger = MLogger(__name__, level=MLogger.DEBUG_INFO)


def exec():
    # 縦方向のボーン数
    max_y_cnt = 8
    # 横方向のボーン密度（面をいくつごとにボーンを配置するか）
    x_density = 3

    model = PmxReader("D:\\MMD\\Blender\\スカート\\double06.pmx", is_check=False, is_sizing=False).read_data()

    logger.info("頂点位置チェック")

    # まず内スカートにボーンを入れる
    target_bone_name = "内スカート"
    
    # 表示枠定義
    model.display_slots[target_bone_name] = DisplaySlot(target_bone_name, target_bone_name, 0, 0)

    # 中心ボーン登録
    bone_name = f'{target_bone_name}中心'

    root_bone = Bone(bone_name, bone_name, model.bones["下半身"].position, model.bones["下半身"].index, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
    root_bone.index = len(list(model.bones.keys()))

    # ボーン
    model.bones[root_bone.name] = root_bone
    
    # 表示枠
    model.display_slots[target_bone_name].references.append(model.bones[root_bone.name].index)

    vertices_dict = {}
    vertex_idxs_dict = {}
    indices_dict = {}
    added_vertices = []
    vertex_vecs = {}
    for ik, index_idx in enumerate(model.material_indices[target_bone_name]):
        for vk, vertex_idx in enumerate(model.indices[index_idx]):
            v = model.vertex_dict[vertex_idx]
            if v.index not in added_vertices:
                # x = round(v.position.x(), 3)
                y = round(v.position.y(), 3)
                # z = round(v.position.z(), 3)

                if y not in vertices_dict:
                    vertices_dict[y] = []
                    vertex_idxs_dict[y] = []
                
                vertices_dict[y].append(v.position.data())
                vertex_idxs_dict[y].append(v.index)
                added_vertices.append(v.index)
                if v.position.to_log() not in vertex_vecs:
                    vertex_vecs[v.position.to_log()] = []
                vertex_vecs[v.position.to_log()].append(v.index)
        
        v0 = model.vertex_dict[model.indices[index_idx][0]]
        v1 = model.vertex_dict[model.indices[index_idx][1]]
        v2 = model.vertex_dict[model.indices[index_idx][2]]

        v01_diff = (v0.position - v1.position)
        v12_diff = (v1.position - v2.position)
        v20_diff = (v2.position - v0.position)

        # もっともY差が小さいのが水平方向と見なす
        xz_idx = np.argmin(np.abs([v01_diff.y(), v12_diff.y(), v20_diff.y()]))
        # もっとも長さがあるのが斜め方向とみなす
        diagonal_idx = np.argmax([v01_diff.length(), v12_diff.length(), v20_diff.length()])
        # 残りが垂直方向と見なす
        y_idx = list({0, 1, 2} - {xz_idx, diagonal_idx})[0]

        sorted_dot_dict = [{"start": v0, "end": v1}, {"start": v1, "end": v2}, {"start": v2, "end": v0}]

        if v0.index not in indices_dict:
            indices_dict[v0.index] = {"x": [], "y+": [], "y-": [], "diagonal+": [], "diagonal-": [], "duplicate": []}

        if v1.index not in indices_dict:
            indices_dict[v1.index] = {"x": [], "y+": [], "y-": [], "diagonal+": [], "diagonal-": [], "duplicate": []}

        if v2.index not in indices_dict:
            indices_dict[v2.index] = {"x": [], "y+": [], "y-": [], "diagonal+": [], "diagonal-": [], "duplicate": []}

        # 内積が小さい方が水平と見なす
        # 内積が中間のは斜め
        # 内積が大きいのは垂直
        for axis_idx, axis in [(y_idx, ["y+", "y-"]), (diagonal_idx, ["diagonal+", "diagonal-"]), (xz_idx, ["x", "x"])]:
            target_dot_dict = sorted_dot_dict[axis_idx]
            if target_dot_dict["start"].position.y() > target_dot_dict["end"].position.y():
                if target_dot_dict["end"] not in indices_dict[target_dot_dict["start"].index][axis[0]]:
                    indices_dict[target_dot_dict["start"].index][axis[1]].append(target_dot_dict["end"])
                if target_dot_dict["start"] not in indices_dict[target_dot_dict["end"].index][axis[0]]:
                    indices_dict[target_dot_dict["end"].index][axis[0]].append(target_dot_dict["start"])
            else:
                if target_dot_dict["end"] not in indices_dict[target_dot_dict["start"].index][axis[0]]:
                    indices_dict[target_dot_dict["start"].index][axis[0]].append(target_dot_dict["end"])
                if target_dot_dict["start"] not in indices_dict[target_dot_dict["end"].index][axis[0]]:
                    indices_dict[target_dot_dict["end"].index][axis[1]].append(target_dot_dict["start"])
    
    logger.info("重複頂点チェック")

    # 重複頂点を確認する
    for duplicate_idxs in vertex_vecs.values():
        if len(duplicate_idxs) > 1:
            for i0 in duplicate_idxs:
                for i1 in duplicate_idxs:
                    if i0 != i1:
                        if model.vertex_dict[i1] not in indices_dict[i0]["duplicate"]:
                            indices_dict[i0]["duplicate"].append(model.vertex_dict[i1])
                        if model.vertex_dict[i0] not in indices_dict[i1]["duplicate"]:
                            indices_dict[i1]["duplicate"].append(model.vertex_dict[i0])

    logger.info("辺走査")

    # Yの昇順ソート
    sorted_ys = np.sort(list(vertices_dict.keys()))
    # 一番上の最前頂点
    sorted_top_vertex_poses = sorted(vertices_dict[sorted_ys[-1]], key=lambda x: [round(x[2], 3), round(abs(x[0]), 3)])
    # 最前頂点のINDEX
    start_vertex_idx = [i for i in vertex_idxs_dict[sorted_ys[-1]] if model.vertex_dict[i].position == MVector3D(sorted_top_vertex_poses[0])][0]

    # 開始頂点から縦に伸ばす
    target_y_idx = start_vertex_idx
    # 該当Yの開始頂点INDEX
    start_y_idxs = [start_vertex_idx]
    start_ys = [model.vertex_dict[start_vertex_idx].position.y()]
    while len(indices_dict[target_y_idx]["y-"]) > 0:
        next_y_v = indices_dict[target_y_idx]["y-"][0]
        start_y_idxs.append(next_y_v.index)
        start_ys.append(model.vertex_dict[next_y_v.index].position.y())
        target_y_idx = next_y_v.index
    
    target_bones = {}
    target_bone_indexes = {}

    # 頂点マップ生成(二次元配列)
    vertices_map = []
    for yidx, start_y_idx in enumerate(start_y_idxs):
        vertices_map.append(get_horizonal_x_idxs(start_y_idx, indices_dict))
    vertices_map = np.array(vertices_map)

    # ボーン名と頂点の対応表
    bone_vertex_map = {}

    # Y軸に等間隔にボーンを配置する
    for yidx, now_y in enumerate(np.linspace(start_ys[0], start_ys[-1], max_y_cnt)):
        # 等分割したYに最も近い頂点のY値
        now_y_idx = np.abs(np.asarray(start_ys) - now_y).argmin()
        # 登録対象頂点INDEX
        start_y_idx = start_y_idxs[now_y_idx]

        # 指定された頂点から横方向のINDEXリストを取得
        x_idxs = get_horizonal_x_idxs(start_y_idx, indices_dict)

        # メッシュ状のYINDEXを取得
        mesh_yidx = now_y_idx

        max_x_idx = 0
        # for xidx, nearest_x_idx in enumerate(list(np.linspace(0, len(x_idxs) - 1, max_x_cnt + 1, dtype=int))[:-1]):
        for xidx, now_x_idx in enumerate(x_idxs[::x_density] + [x_idxs[0]]):
            # ボーン登録
            bone_name = f'{target_bone_name}-{(yidx + 1):02d}-{(xidx + 1):02d}'

            # 親ボーン
            parent_bone_name = f'{target_bone_name}-{(yidx):02d}-{(xidx + 1):02d}'
            parent_bone_index = -1 if yidx == 0 or parent_bone_name not in target_bones else target_bones[parent_bone_name].index

            # 自身の位置
            bone_vec = model.vertex_dict[now_x_idx].position

            bone = Bone(bone_name, bone_name, bone_vec, parent_bone_index, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
            bone.index = len(list(target_bones.keys()))

            # ボーン仮登録
            target_bones[bone.name] = bone
            target_bone_indexes[bone.index] = bone.name
            
            # 最大X数として保持(最後は保持しない)
            if not (xidx > 0 and now_x_idx == x_idxs[0]):
                max_x_idx = xidx

            # メッシュ状のXINDEXを取得
            mesh_xidx = [xi for xi, x in enumerate(x_idxs) if x == now_x_idx][0]

            # 対応表に追記
            bone_vertex_map[bone_name] = {"xidx": mesh_xidx, "yidx": mesh_yidx, "vertex_idx": now_x_idx}

    # 高密度ボーンをを排除して登録
    for yidx in range(1, max_y_cnt + 1):
        for xidx in range(0, max_x_idx + 1):
            # 処理対象ボーン名
            bone_name = f'{target_bone_name}-{(yidx):02d}-{(xidx + 1):02d}'
            # 表示先ボーン名
            display_bone_name = f'{target_bone_name}-{(yidx + 1):02d}-{(xidx + 1):02d}'

            if bone_name not in target_bones:
                continue

            bone = target_bones[bone_name]

            if yidx == max_y_cnt:
                if bone.parent_index in target_bone_indexes and target_bone_indexes[bone.parent_index] in model.bones:
                    # 末端は親ボーンがいたら登録
                    bone = target_bones[bone_name]
                    parent_bone = model.bones[target_bone_indexes[bone.parent_index]]

                    bone.parent_index = parent_bone.index
                    bone.index = len(list(model.bones.keys()))

                    model.bones[bone.name] = bone
                    model.bone_indexes[bone.index] = bone.name

                    # 表示枠
                    model.display_slots[target_bone_name].references.append(bone.index)

            elif display_bone_name in target_bones:
                # 正面か親ボーンが既に登録済みの場合は問答無用で登録
                is_regist = True if xidx == 0 or (bone.parent_index in target_bone_indexes and target_bone_indexes[bone.parent_index] in model.bones) else False

                if not is_regist:
                    # 表示先ボーンとの距離
                    display_length = target_bones[display_bone_name].position.distanceToPoint(bone.position)

                    # 隣のボーンとの距離
                    brother_length = 0
                    for bxidx in range(xidx, -1, -1):
                        brother_bone_name = f'{target_bone_name}-{(yidx):02d}-{(bxidx):02d}'
                        if brother_bone_name not in model.bones:
                            # 隣がない場合、もうひとつ前をチェック
                            continue
                        else:
                            # 隣ボーンとの距離
                            brother_length = target_bones[brother_bone_name].position.distanceToPoint(bone.position)
                            break

                    if display_length * 0.8 < brother_length:
                        # 表示先より隣の方が遠い場合、対象ボーン登録
                        is_regist = True

                # FIXME ウェイトテストのため、常に登録
                is_regist = True
                
                if is_regist:
                    bone.parent_index = model.bones[target_bone_indexes[bone.parent_index]].index \
                        if bone.parent_index >= 0 and target_bone_indexes[bone.parent_index] in model.bones else root_bone.index
                    bone.index = len(list(model.bones.keys()))

                    model.bones[bone.name] = bone
                    model.bone_indexes[bone.index] = bone.name

                    # 表示枠
                    model.display_slots[target_bone_name].references.append(bone.index)

    # 表示先を定義
    for yidx in range(0, max_y_cnt - 1):
        for xidx in range(0, max_x_idx + 1):
            # 処理対象ボーン名
            bone_name = f'{target_bone_name}-{(yidx + 1):02d}-{(xidx + 1):02d}'
            # 表示先ボーン名
            display_bone_name = f'{target_bone_name}-{(yidx + 2):02d}-{(xidx + 1):02d}'

            if bone_name in model.bones and display_bone_name in model.bones:
                # 表示先ボーンを定義
                model.bones[bone_name].tail_index = model.bones[display_bone_name].index
                model.bones[bone_name].flag |= 0x0001

    logger.info("ボーン完了")
    
    # 自身のグループ
    collision_group_idx = 1

    rigidbody_param_to = RigidBodyParam(0.5, 0.9999, 0.9999, 0, 0.5)
    rigidbody_param_from = RigidBodyParam(rigidbody_param_to.mass * ((max_y_cnt + 1) ** 2), 0.9, 0.9, 0, 0.5)

    bone_distances = {}
    weighted_indecies = []
    for yidx1, yidx2 in zip(list(range(0, max_y_cnt - 1)), list(range(1, max_y_cnt + 1))):
        for xidx1, xidx2 in zip(list(range(0, max_x_idx + 1)), list(range(1, max_x_idx + 2))):
            # 処理対象ボーン名
            left_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(xidx1 + 1):02d}'
            right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(xidx2 + 1):02d}'
            left_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(xidx1 + 1):02d}'
            right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(xidx2 + 1):02d}'

            for lbidx, left_bone_name in enumerate([left_top_bone_name, left_bottom_bone_name]):
                if left_bone_name not in model.bones:
                    for bxidx in range(xidx1, -1, -1):
                        brother_bone_name = f'{target_bone_name}-{(yidx + 1):02d}-{(bxidx):02d}'
                        if brother_bone_name not in model.bones:
                            # 隣がない場合、もうひとつ前をチェック
                            continue
                        else:
                            # あったら抜ける
                            if lbidx == 0:
                                left_top_bone_name = brother_bone_name
                            else:
                                left_bottom_bone_name = brother_bone_name
                            break
            
            if xidx1 < max_x_idx:
                for rbidx, right_bone_name in enumerate([right_top_bone_name, right_bottom_bone_name]):
                    if right_bone_name not in model.bones:
                        for bxidx in range(xidx2, max_x_idx + 1):
                            brother_bone_name = f'{target_bone_name}-{(yidx + 1):02d}-{(bxidx):02d}'
                            if brother_bone_name not in model.bones:
                                # 隣がない場合、もうひとつ前をチェック
                                continue
                            else:
                                # あったら抜ける
                                if rbidx == 0:
                                    right_top_bone_name = brother_bone_name
                                else:
                                    right_bottom_bone_name = brother_bone_name
                                break

            # 各ボーンに対応する頂点情報
            left_top_bone_map = bone_vertex_map[left_top_bone_name]
            left_bottom_bone_map = bone_vertex_map[left_bottom_bone_name]

            if right_top_bone_name not in model.bones and right_bottom_bone_name not in model.bones and xidx1 == max_x_idx:
                # 右端がない場合、最後まで
                vertices_range = \
                    vertices_map[np.min([left_top_bone_map["yidx"], left_bottom_bone_map["yidx"]]): \
                                 np.max([left_top_bone_map["yidx"], left_bottom_bone_map["yidx"]]) + 1, \
                                 np.min([left_top_bone_map["xidx"], left_bottom_bone_map["xidx"]]):]
                
                # 右端は最初のボーンで置き換える
                right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(1):02d}'
                right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(1):02d}'
            else:
                # 全部がある場合はそこまで
                right_top_bone_map = bone_vertex_map[right_top_bone_name]
                right_bottom_bone_map = bone_vertex_map[right_bottom_bone_name]

                vertices_range = \
                    vertices_map[np.min([left_top_bone_map["yidx"], right_top_bone_map["yidx"], left_bottom_bone_map["yidx"], right_bottom_bone_map["yidx"]]): \
                                 np.max([left_top_bone_map["yidx"], right_top_bone_map["yidx"], left_bottom_bone_map["yidx"], right_bottom_bone_map["yidx"]]) + 1, \
                                 np.min([left_top_bone_map["xidx"], right_top_bone_map["xidx"], left_bottom_bone_map["xidx"], right_bottom_bone_map["xidx"]]): \
                                 np.max([left_top_bone_map["xidx"], right_top_bone_map["xidx"], left_bottom_bone_map["xidx"], right_bottom_bone_map["xidx"]]) + 1]
            
            top_horizonal_length = 0
            bottom_horizonal_length = 0
            left_vertical_length = 0
            right_vertical_length = 0

            # 頂点を二次元に展開した時の長さ
            for hi, h_vertices in enumerate(vertices_range):
                
                if hi > 0:
                    # 左ライン
                    left_vertical_length += model.vertex_dict[vertices_range[hi, 0]].position.distanceToPoint(model.vertex_dict[vertices_range[hi - 1, 0]].position)
                    
                    # 右ライン
                    right_vertical_length += model.vertex_dict[vertices_range[hi, -1]].position.distanceToPoint(model.vertex_dict[vertices_range[hi - 1, -1]].position)

                for vi, vertex_idx in enumerate(h_vertices):
                    v = model.vertex_dict[vertex_idx]

                    if vi > 0:
                        if hi == 0:
                            # 上部ライン
                            top_horizonal_length += model.vertex_dict[vertices_range[hi, vi - 1]].position.distanceToPoint(v.position)
                        
                        if hi == len(vertices_range) - 1:
                            # 下部ライン
                            bottom_horizonal_length += model.vertex_dict[vertices_range[hi, vi - 1]].position.distanceToPoint(v.position)

            bone_distances[(left_top_bone_name, left_bottom_bone_name)] = left_vertical_length
            bone_distances[(right_top_bone_name, right_bottom_bone_name)] = right_vertical_length
            bone_distances[(left_top_bone_name, right_top_bone_name)] = top_horizonal_length
            bone_distances[(left_bottom_bone_name, right_bottom_bone_name)] = bottom_horizonal_length

            for hi, h_vertices in enumerate(vertices_range):
                for vi, vertex_idx in enumerate(h_vertices):
                    v = model.vertex_dict[vertex_idx]

                    v_horizonal_length = 0
                    v_vertical_length = 0

                    # 頂点を二次元に展開した時の長さ
                    # 縦ライン
                    for vhi in range(hi + 1):
                        if vhi > 0:
                            v_vertical_length += model.vertex_dict[vertices_range[vhi, vi]].position.distanceToPoint(model.vertex_dict[vertices_range[vhi - 1, vi]].position)

                    # 横ライン
                    for vvi in range(vi + 1):
                        if vvi > 0:
                            v_horizonal_length += model.vertex_dict[vertices_range[hi, vvi]].position.distanceToPoint(model.vertex_dict[vertices_range[hi, vvi - 1]].position)
                                
                    left_top_weight = max(0, ((top_horizonal_length - v_horizonal_length) / top_horizonal_length) * \
                                          ((left_vertical_length - v_vertical_length) / left_vertical_length))
                    left_bottom_weight = max(0, ((bottom_horizonal_length - v_horizonal_length) / bottom_horizonal_length) * \
                                             (v_vertical_length / left_vertical_length))
                    right_top_weight = max(0, (v_horizonal_length / top_horizonal_length) * \
                                           ((right_vertical_length - v_vertical_length) / right_vertical_length))
                    right_bottom_weight = max(0, (v_horizonal_length / bottom_horizonal_length) * \
                                              (v_vertical_length / right_vertical_length))

                    # 距離からウェイトを計算
                    total_weights = np.array([left_top_weight, left_bottom_weight, right_top_weight, right_bottom_weight])
                    weight_values = total_weights / total_weights.sum(axis=0, keepdims=1)

                    weight_names = np.array([left_top_bone_name, left_bottom_bone_name, right_top_bone_name, right_bottom_bone_name])
                    target_names = weight_names[np.nonzero(weight_values)]

                    for vv in [v] + indices_dict[v.index]["duplicate"]:
                        if vv.index not in weighted_indecies:
                            # 重複頂点にも同じウェイトを割り当てる
                            if np.count_nonzero(weight_values) == 1:
                                vv.deform = Bdef1(model.bones[target_names[0]].index)
                            elif np.count_nonzero(weight_values) == 2:
                                vv.deform = Bdef2(model.bones[target_names[0]].index, model.bones[target_names[1]].index, weight_values[weight_values.nonzero()][0])
                            else:
                                vv.deform = Bdef4(model.bones[weight_names[0]].index, model.bones[weight_names[1]].index, \
                                                  model.bones[weight_names[2]].index, model.bones[weight_names[3]].index, \
                                                  weight_values[0], weight_values[1], weight_values[2], weight_values[3])
                            
                            weighted_indecies.append(vv.index)
            
            # 剛体処理対象ボーン名リスト
            rigidbody_target_bones = [left_top_bone_name, left_bottom_bone_name] if yidx2 == max_y_cnt - 1 else [left_top_bone_name]
            for rigidbody_target_bone in rigidbody_target_bones:
                # 剛体設定
                rigidbody_bone = model.bones[rigidbody_target_bone]

                # 質量：末端からの二乗
                # 減衰：根元から末端の線形補間
                # 反発・摩擦：根元一定
                mass = rigidbody_param_to.mass * ((max_y_cnt - yidx1 + 1) ** 2)
                linear_damping = rigidbody_param_from.linear_damping + ((rigidbody_param_to.linear_damping - rigidbody_param_from.linear_damping) * (yidx1 / max_y_cnt))
                angular_damping = rigidbody_param_from.angular_damping + ((rigidbody_param_to.angular_damping - rigidbody_param_from.angular_damping) * (yidx1 / max_y_cnt))

                shape_position = rigidbody_bone.position
                min_length = np.mean([left_vertical_length, right_vertical_length, top_horizonal_length, bottom_horizonal_length])
                shape_size = MVector3D(min_length / 2, min_length / 2, min_length / 2)

                # 衝突剛体
                for yidx in range(max_y_cnt + 1):
                    rigidbody_no_collisions = 0
                    for nc in range(16):
                        # 最上部はボディとの剛体非接触
                        # 以降は剛体接触判定あり
                        if nc not in ([0, collision_group_idx] if yidx1 == 0 else [collision_group_idx]):
                            rigidbody_no_collisions |= 1 << nc

                # 剛体(円)
                shape_type = 0
                mode = 0 if yidx1 == 0 else 1
                rigidbody = RigidBody(rigidbody_bone.name, rigidbody_bone.english_name, rigidbody_bone.index, collision_group_idx, rigidbody_no_collisions, \
                                      shape_type, shape_size, shape_position, MVector3D(), \
                                      mass, linear_damping, angular_damping, rigidbody_param_from.restitution, rigidbody_param_from.friction, mode)
                rigidbody.index = len(model.rigidbodies)
                model.rigidbodies[rigidbody.name] = rigidbody

    logger.info("ウェイト・剛体完了")
    
    for yidx1, yidx2 in zip(list(range(0, max_y_cnt - 1)), list(range(1, max_y_cnt + 1))):
        for xidx1, xidx2 in zip(list(range(0, max_x_idx + 1)), list(range(1, max_x_idx + 2))):
            # 処理対象ボーン名
            left_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(xidx1 + 1):02d}'
            right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(xidx2 + 1):02d}'
            left_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(xidx1 + 1):02d}'
            right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(xidx2 + 1):02d}'

            if right_top_bone_name not in model.bones and right_bottom_bone_name not in model.bones:
                # 右端は最初のボーンで置き換える
                right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(1):02d}'
                right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(1):02d}'
            
            # 縦ジョイント
            vertical_joint_name = f'↓|{left_top_bone_name}|{left_bottom_bone_name}'
            vertical_joint_vec = model.bones[left_top_bone_name].position + ((model.bones[left_bottom_bone_name].position - model.bones[left_top_bone_name].position) / 2)
            vertical_joint_vec_euler = MQuaternion.rotationTo(MVector3D(0, 1, 0), (model.bones[left_top_bone_name].position - model.bones[left_bottom_bone_name].position).normalized()).toEulerAngles()
            vertical_joint_vec_radians = MVector3D(math.radians(vertical_joint_vec_euler.x()), math.radians(vertical_joint_vec_euler.y()), math.radians(vertical_joint_vec_euler.z()))
            vertical_joint = Joint(vertical_joint_name, vertical_joint_name, 0, model.rigidbodies[left_top_bone_name].index, model.rigidbodies[left_bottom_bone_name].index,
                                   vertical_joint_vec, vertical_joint_vec_radians, MVector3D(), MVector3D(),
                                   MVector3D(math.radians(-10), math.radians(-10), math.radians(-10)),
                                   MVector3D(math.radians(10), math.radians(10), math.radians(10)), MVector3D(), MVector3D())
            model.joints[vertical_joint.name] = vertical_joint
    
    logger.info("横ジョイント完了")

    for yidx1, yidx2 in zip(list(range(0, max_y_cnt - 1)), list(range(1, max_y_cnt + 1))):
        for xidx1, xidx2 in zip(list(range(0, max_x_idx + 1)), list(range(1, max_x_idx + 2))):
            # 処理対象ボーン名
            left_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(xidx1 + 1):02d}'
            right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(xidx2 + 1):02d}'
            left_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(xidx1 + 1):02d}'
            right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(xidx2 + 1):02d}'

            if right_top_bone_name not in model.bones and right_bottom_bone_name not in model.bones:
                # 右端は最初のボーンで置き換える
                right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):02d}-{(1):02d}'
                right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):02d}-{(1):02d}'
            
            # 横ジョイント
            horizonal_joint_name = f'→|{left_top_bone_name}|{right_top_bone_name}'
            horizonal_joint_vec = model.bones[left_top_bone_name].position + ((model.bones[right_top_bone_name].position - model.bones[left_top_bone_name].position) / 2)
            horizonal_joint_vec_euler = MQuaternion.rotationTo(MVector3D(1, 0, 0), (model.bones[left_top_bone_name].position - model.bones[right_top_bone_name].position).normalized()).toEulerAngles()
            horizonal_joint_vec_radians = MVector3D(math.radians(horizonal_joint_vec_euler.x()), math.radians(horizonal_joint_vec_euler.y()), math.radians(horizonal_joint_vec_euler.z()))
            horizonal_joint = Joint(horizonal_joint_name, horizonal_joint_name, 0, model.rigidbodies[left_top_bone_name].index, model.rigidbodies[right_top_bone_name].index,
                                    horizonal_joint_vec, horizonal_joint_vec_radians, MVector3D(), MVector3D(),
                                    MVector3D(math.radians(-45), math.radians(-45), math.radians(-45)),
                                    MVector3D(math.radians(45), math.radians(45), math.radians(45)), MVector3D(), MVector3D())
            model.joints[horizonal_joint.name] = horizonal_joint

    logger.info("横ジョイント完了")

    # for xidx in range(max_x_cnt + 1):
    #     rigidbody_no_collisions = 0
    #     for nc in range(16):
    #         if nc not in [0, 13, 14]:
    #             rigidbody_no_collisions |= 1 << nc

    #     pole_bone_name = f'{target_bone_name}-{(xidx):02d}-00-00'

    #     left_top_name = f'{target_bone_name}-{(xidx):02d}-00-00'
    #     right_top_name = f'{target_bone_name}-{(xidx + 1):02d}-00-00'

    #     target_poses = []
    #     for target_name in [left_top_name, right_top_name]:
    #         if target_name in model.bones:
    #             target_poses.append(model.bones[target_name].position.data())
    #     center_pos = MVector3D(np.mean(target_poses, axis=0)) + MVector3D(-r_size.x() / 2, 0, 0)
    #     if right_top_name not in model.bones:
    #         center_pos.setX(center_pos.x() + (r_size.x() / 2))

    #     # 剛体
    #     mode = 0
    #     rigidbody = RigidBody(model.bones[pole_bone_name].name, model.bones[pole_bone_name].english_name, model.bones[pole_bone_name].index, 14, rigidbody_no_collisions, \
    #                           0, MVector3D(r_size.x() / 2, r_size.y() / 2, 0.1), center_pos, MVector3D(), \
    #                           rigidbody_param_from.mass, rigidbody_param_from.linear_damping, rigidbody_param_from.angular_damping, \
    #                           rigidbody_param_from.restitution, rigidbody_param_from.friction, mode)
    #     rigidbody.index = len(model.rigidbodies)
    #     model.rigidbodies[rigidbody.name] = rigidbody

    #     for zidx, z_direction in enumerate([min_vec.z(), max_vec.z()]):
            
    #         collision_idx = 13 if zidx == 0 else 14
    #         rigidbody_no_collisions = 0
    #         for nc in range(16):
    #             if nc not in [0, collision_idx]:
    #                 rigidbody_no_collisions |= 1 << nc

    #         for yi, yidx in enumerate(range(max_cnt + 1)):
    #             if yi == 0:
    #                 continue

    #             bone_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}'
    #             bone = model.bones[bone_name]
    #             left_top_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}'
    #             right_top_name = f'布-{(xidx + 1):02d}-{(zidx):02d}-{(yidx):02d}'
    #             left_bottom_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx + 1):02d}'
    #             right_bottom_name = f'布-{(xidx + 1):02d}-{(zidx):02d}-{(yidx + 1):02d}'

    #             target_poses = []
    #             for target_name in [left_top_name, right_top_name, left_bottom_name, right_bottom_name]:
    #                 if target_name in model.bones:
    #                     target_poses.append(model.bones[target_name].position.data())
    #             center_pos = MVector3D(np.mean(target_poses, axis=0)) + MVector3D(-r_size.x() / 2, r_size.y() / 2, 0)
    #             if right_top_name not in model.bones:
    #                 center_pos.setX(center_pos.x() + (r_size.x() / 2))
    #             if left_bottom_name not in model.bones:
    #                 center_pos.setY(center_pos.y() - (r_size.y() / 2))


    # logger.info("剛体完了")
        
    # for xidx in range(max_cnt + 1):
    #     for zidx, z_direction in enumerate([min_vec.z(), max_vec.z()]):
    #         for yi, yidx in enumerate(range(max_cnt + 1)):
    #             bone_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}' if yi > 0 else f'布-{(xidx):02d}-00-00'
    #             vertical_joint_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx + 1):02d}'

    #             if vertical_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
    #                 joint = Joint(vertical_joint_name, vertical_joint_name, 0, model.rigidbodies[bone_name].index, model.rigidbodies[vertical_joint_name].index,
    #                               model.bones[vertical_joint_name].position + MVector3D(0, r_size.y() / 2, 0), MVector3D(), MVector3D(), MVector3D(),
    #                               MVector3D(math.radians(-15), math.radians(-2), math.radians(-25)),
    #                               MVector3D(math.radians(135), math.radians(2), math.radians(25)), MVector3D(), MVector3D())

    #                 model.joints[joint.name] = joint
    #             else:
    #                 logger.debug("%s -> %s", bone_name, vertical_joint_name)

    # logger.info("縦ジョイント完了")

    # for xidx in range(max_cnt + 1):
    #     for zidx, z_direction in enumerate([min_vec.z(), max_vec.z()]):
    #         for yi, yidx in enumerate(range(max_cnt + 1)):
    #             if yi == 0:
    #                 continue

    #             bone_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}' if yi > 0 else f'布-{(xidx):02d}-00-00'
    #             right_joint_name = f'布-{(xidx + 1):02d}-{(zidx):02d}-{(yidx):02d}'

    #             if right_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
    #                 joint = Joint(f'{bone_name}_横', f'{bone_name}_横', 0, model.rigidbodies[bone_name].index, model.rigidbodies[right_joint_name].index,
    #                               model.bones[bone_name].position + MVector3D(r_size.x() / 2, 0, 0), MVector3D(), MVector3D(), MVector3D(),
    #                               MVector3D(math.radians(1), math.radians(1), math.radians(1)),
    #                               MVector3D(math.radians(0), math.radians(0), math.radians(0)), MVector3D(), MVector3D())

    #                 model.joints[joint.name] = joint
    #             else:
    #                 logger.debug("%s -> %s", bone_name, right_joint_name)

    # logger.info("横ジョイント完了")






    # for k, vs in model.vertices.items():
    #     for v in vs:
    #         target_xs = {}
    #         target_ys = {}
    #         target_zs = {}

    #         for zi, z in enumerate([min_vec.z(), max_vec.z()]):
    #             if z - (r_size.z()) < v.position.z() < z + (r_size.z()):
    #                 target_zs[z] = zi
    #         for yi, y in enumerate(bone_ys):
    #             if y - (r_size.y()) < v.position.y() < y + (r_size.y()):
    #                 target_ys[y] = yi
    #         for xi, x in enumerate(bone_xs):
    #             if x - (r_size.x()) < v.position.x() < x + (r_size.x()):
    #                 target_xs[x] = xi
            
    #         r_min_vec = MVector3D(list(target_xs.keys())[0], list(target_ys.keys())[-1], list(target_zs.keys())[0])
    #         r_max_vec = MVector3D(list(target_xs.keys())[-1], list(target_ys.keys())[0], list(target_zs.keys())[-1])

    #         left_top_weight = max(0, ((r_size.x() - (v.position.x() - r_min_vec.x())) / r_size.x()) * (((v.position.y() - r_min_vec.y())) / r_size.y()))
    #         left_bottom_weight = max(0, ((r_size.x() - (v.position.x() - r_min_vec.x())) / r_size.x()) * (r_size.y() - (v.position.y() - r_min_vec.y())) / r_size.y())
    #         right_bottom_weight = max(0, (((v.position.x() - r_min_vec.x())) / r_size.x()) * (r_size.y() - (v.position.y() - r_min_vec.y())) / r_size.y())
    #         right_top_weight = max(0, (((v.position.x() - r_min_vec.x())) / r_size.x()) * (((v.position.y() - r_min_vec.y())) / r_size.y()))

    #         total_weights = np.array([left_top_weight, right_top_weight, left_bottom_weight, right_bottom_weight])
    #         weight_values = total_weights / total_weights.sum(axis=0, keepdims=1)

    #         left_top_bone = model.bones[f'布-{(0):02d}-{(0):02d}-{(0):02d}']
    #         right_top_bone = model.bones[f'布-{(max_cnt):02d}-{(0):02d}-{(0):02d}']
    #         left_bottom_bone = model.bones[f'布-{(0):02d}-{(0):02d}-{(max_cnt):02d}']
    #         right_bottom_bone = model.bones[f'布-{(max_cnt):02d}-{(0):02d}-{(max_cnt):02d}']
    #         left_top_distance = 99999
    #         right_top_distance = 99999
    #         left_bottom_distance = 99999
    #         right_bottom_distance = 99999
    #         for bone in model.bones.values():
    #             distance = bone.position.distanceToPoint(v.position)
    #             if bone.position.x() <= v.position.x() and bone.position.y() >= v.position.y() and distance < left_top_distance:
    #                 left_top_bone = bone
    #                 left_top_distance = distance
    #             if bone.position.x() >= v.position.x() and bone.position.y() >= v.position.y() and distance < right_top_distance:
    #                 right_top_bone = bone
    #                 right_top_distance = distance
    #             if bone.position.x() <= v.position.x() and bone.position.y() <= v.position.y() and distance < left_bottom_distance:
    #                 left_bottom_bone = bone
    #                 left_bottom_distance = distance
    #             if bone.position.x() >= v.position.x() and bone.position.y() <= v.position.y() and distance < right_bottom_distance:
    #                 right_bottom_bone = bone
    #                 right_bottom_distance = distance

    #         weight_names = np.array([left_top_bone.name, right_top_bone.name, left_bottom_bone.name, right_bottom_bone.name])
    #         target_names = weight_names[np.nonzero(weight_values)]

    #         if np.count_nonzero(weight_values) == 1:
    #             v.deform = Bdef1(model.bones[target_names[0]].index)
    #         elif np.count_nonzero(weight_values) == 2:
    #             v.deform = Bdef2(model.bones[target_names[0]].index, model.bones[target_names[1]].index, weight_values[weight_values.nonzero()][0])
    #         else:
    #             v.deform = Bdef4(left_top_bone.index, right_top_bone.index, left_bottom_bone.index, right_bottom_bone.index, \
    #                              weight_values[0], weight_values[1], weight_values[2], weight_values[3])

    model.name = "二重スカート"
    model.comment = f"二重スカート\r\n制作： miu\r\nマネキン素体：ささかや様"

    result_dir = "D:\\MMD\\Blender\\スカート"
    new_file_path = f"{result_dir}\\二重スカート.pmx"
    pmx_writer = PmxWriter()
    pmx_writer.write(model, new_file_path)

    logger.warning(f"出力終了: {new_file_path}")


# 指定された頂点から横方向のINDEXリスト
def get_horizonal_x_idxs(start_y_idx: int, indices_dict: dict):

    # 開始頂点から横に伸ばす
    target_x_idx = start_y_idx
    x_idxs = [start_y_idx]
    duplicate_idxs = []
    # 方向にぐるっと回す
    while len(indices_dict[target_x_idx]["x"]) > 0 and ((len(x_idxs[1:]) > 0 and start_y_idx not in x_idxs[1:]) or len(x_idxs) == 1) and len(x_idxs) < 9999999999:
        # まだ入ってないX軸方向を検出
        next_xs = [v for v in indices_dict[target_x_idx]["x"] if v.index not in x_idxs and v.index not in duplicate_idxs]
        if len(next_xs) == 0:

            # 重複頂点で次に移ってる場合、そのまま移動
            if len(indices_dict[target_x_idx]["duplicate"]) > 0:
                next_xs = [v for v in indices_dict[target_x_idx]["duplicate"] if v.index not in x_idxs and v.index not in duplicate_idxs]
                if len(next_xs) > 0:
                    next_x_v = next_xs[0]
                    duplicate_idxs.append(next_x_v.index)
                    target_x_idx = next_x_v.index
                    continue

            # 横にそのまま移動できない場合、一度斜めに移動して、そこから隣に
            if len(indices_dict[target_x_idx]["diagonal+"]) > 0:
                next_xs = [v for v in indices_dict[target_x_idx]["diagonal+"] if v.index not in x_idxs and v.index not in duplicate_idxs]
                if len(next_xs) > 0:
                    next_x_v = next_xs[0]
                    target_x_idx = next_x_v.index
                    
                    if len(indices_dict[target_x_idx]["y-"]) > 0:
                        next_xs = [v for v in indices_dict[target_x_idx]["y-"] if v.index not in x_idxs and v.index not in duplicate_idxs]
                        if len(next_xs) > 0:
                            next_x_v = next_xs[0]
                            x_idxs.append(next_x_v.index)
                            target_x_idx = next_x_v.index
                            continue
                
            if len(indices_dict[target_x_idx]["diagonal-"]) > 0:
                next_xs = [v for v in indices_dict[target_x_idx]["diagonal-"] if v.index not in x_idxs and v.index not in duplicate_idxs]
                if len(next_xs) > 0:
                    next_x_v = next_xs[0]
                    target_x_idx = next_x_v.index
                    
                    if len(indices_dict[target_x_idx]["y+"]) > 0:
                        next_xs = [v for v in indices_dict[target_x_idx]["y+"] if v.index not in x_idxs and v.index not in duplicate_idxs]
                        if len(next_xs) > 0:
                            next_x_v = next_xs[0]
                            x_idxs.append(next_x_v.index)
                            target_x_idx = next_x_v.index
                            continue
                
        if len(next_xs) == 0:
            break
        
        next_x_v = next_xs[0]
        x_idxs.append(next_x_v.index)
        target_x_idx = next_x_v.index

    return x_idxs

# 約数を求める
def make_divisors(n):
    lower_divisors, upper_divisors = [], []
    i = 1
    while i * i <= n:
        if n % i == 0:
            lower_divisors.append(i)
            if i != n // i:
                upper_divisors.append(n // i)
        i += 1

    return sorted(lower_divisors + upper_divisors[::-1])


if __name__ == '__main__':
    exec()
