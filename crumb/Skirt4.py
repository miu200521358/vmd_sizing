# -*- coding: utf-8 -*-
#
from datetime import datetime
from logging import root
import os
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
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint, Bdef1, Bdef2, Bdef4, RigidBodyParam, IkLink, Ik # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MFileUtils # noqa
from utils.MException import SizingException # noqa
from utils.MLogger import MLogger # noqa


MLogger.initialize(level=MLogger.DEBUG_INFO, is_file=True)
logger = MLogger(__name__, level=MLogger.DEBUG_INFO)


def exec():
    model = PmxReader("D:\\MMD\\Blender\\スカート\\cloak.pmx", is_check=False, is_sizing=False).read_data()
    # model = PmxReader("D:\\MMD\\Blender\\スカート\\skirt_single.pmx", is_check=False, is_sizing=False).read_data()
    # model = PmxReader("D:\\MMD\\Blender\\スカート\\skirt_double.pmx", is_check=False, is_sizing=False).read_data()
    # model = PmxReader("D:\\MMD\\Blender\\スカート\\pleats.pmx", is_check=False, is_sizing=False).read_data()
    # model = PmxReader("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\ゲーム\\Fate\\ジャンヌ・ダルク・オルタ・サンタ・リリィ[配布用]ver1.0 潮井イタチ\\ジャンヌ・ダルク・オルタ・サンタ・リリィ[ランサー]_スカート.pmx", is_check=False, is_sizing=False).read_data()

    model.comment += "\r\n\r\n物理: PmxTailor"

    logger.info("頂点位置チェック")
    
    # 全ボーンを登録するか
    is_full_regist = True

    tailor_type = 0  # スカート
    tailor_type = 1  # マント

    # target_bone_name: 処理対象ボーン名
    # target_material_name: 処理対象材質名
    # parent_bone_name: 親ボーン名
    # start_vertex_idx: 起点頂点IDX
    # y_density: 縦方向のボーン密度（面をいくつごとにボーンを配置するか：最小1）
    # x_density: 横方向のボーン密度（面をいくつごとにボーンを配置するか：最小1）
    # collision_group_idx: 自身の剛体グループ（0始まり）
    # rigidbody_param_to: 末端剛体パラ(質量, 移動減衰, 回転減衰, 反発力, 摩擦力)
    # min_vertical_limit_rot: 縦ジョイント回転制限MIN
    # max_vertical_limit_rot: 縦ジョイント回転制限MAX
    # min_horizonal_limit_rot: 横ジョイント回転制限MIN
    # max_horizonal_limit_rot: 横ジョイント回転制限MAX
    for target_bone_name, target_material_name, parent_bone_name, start_vertex_idx, y_density, x_density, collision_group_idx, rigidbody_param_to, \
        min_vertical_limit_rot, max_vertical_limit_rot, min_horizonal_limit_rot, max_horizonal_limit_rot in \
            [("mt", "マント", "首", 5837, 3, 2, 1, RigidBodyParam(0.2, 0.99, 0.99, 0, 0.5), 15, 30, 20, 40)]:
    # for target_bone_name, target_material_name, parent_bone_name, start_vertex_idx, y_density, x_density, collision_group_idx, rigidbody_param_to, \
    #     min_vertical_limit_rot, max_vertical_limit_rot, min_horizonal_limit_rot, max_horizonal_limit_rot in \
    #         [("内sk", "内スカート", "下半身", None, 3, 2, 1, RigidBodyParam(0.5, 0.9999, 0.9999, 0, 0.5), 10, 20, 40, 60), \
    #          ("外sk", "外スカート", "下半身", None, 4, 3, 2, RigidBodyParam(0.3, 0.99, 0.99, 0, 0.5), 10, 20, 60, 80)]:
    # for target_bone_name, target_material_name, parent_bone_name, start_vertex_idx, y_density, x_density, collision_group_idx, rigidbody_param_to, \
    #     min_vertical_limit_rot, max_vertical_limit_rot, min_horizonal_limit_rot, max_horizonal_limit_rot in \
    #         [("sk", "内スカート", "下半身", 94, 2, 2, 1, RigidBodyParam(0.5, 0.9999, 0.9999, 0, 0.5), 10, 20, 40, 60)]:
    # for target_bone_name, target_material_name, parent_bone_name, start_vertex_idx, y_density, x_density, collision_group_idx, rigidbody_param_to, \
    #     min_vertical_limit_rot, max_vertical_limit_rot, min_horizonal_limit_rot, max_horizonal_limit_rot in \
    #         [("sk", "プリーツ", "下半身", None, 2, 2, 1, RigidBodyParam(0.5, 0.9999, 0.9999, 0, 0.5), 10, 20, 40, 60)]:

        # 表示枠定義
        model.display_slots[target_bone_name] = DisplaySlot(target_bone_name, target_bone_name, 0, 0)

        root_bone = Bone(f'{target_bone_name}中心', f'{target_bone_name}中心', model.bones[parent_bone_name].position, model.bones[parent_bone_name].index, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
        root_bone.index = len(list(model.bones.keys()))

        # ボーン
        model.bones[root_bone.name] = root_bone
        model.bone_indexes[root_bone.index] = root_bone.name
        # 表示枠
        model.display_slots[target_bone_name].references.append((0, model.bones[root_bone.name].index))

        root_right_bone_name = ""
        root_left_bone_name = ""
        root_right_bone = root_left_bone = None
        # 左右ボーン
        if tailor_type == 1:
            root_right_bone_name = f'{target_bone_name}中心右'
            root_right_bone = Bone(root_right_bone_name, root_right_bone_name, model.bones[root_bone.name].position, model.bones["右肩"].index, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
            root_right_bone.index = len(list(model.bones.keys()))
            model.bones[root_right_bone.name] = root_right_bone
            model.bone_indexes[root_right_bone.index] = root_right_bone.name

            root_left_bone_name = f'{target_bone_name}中心左'
            root_left_bone = Bone(root_left_bone_name, root_left_bone_name, model.bones[root_bone.name].position, model.bones["左肩"].index, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
            root_left_bone.index = len(list(model.bones.keys()))
            model.bones[root_left_bone.name] = root_left_bone
            model.bone_indexes[root_left_bone.index] = root_left_bone.name

            model.display_slots[target_bone_name].references.append((0, model.bones[root_right_bone.name].index))
            model.display_slots[target_bone_name].references.append((0, model.bones[root_left_bone.name].index))

        logger.info(f"{target_bone_name}: 頂点チェック")

        vertices_dict = {}
        vertex_idxs_dict = {}
        indices_dict = {}
        added_vertices = []
        vertex_vecs = {}
        for ik, index_idx in enumerate(model.material_indices[target_material_name]):
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

                    # 一旦ウェイトをクリアする
                    v.deform = None
            
            v0 = model.vertex_dict[model.indices[index_idx][0]]
            v1 = model.vertex_dict[model.indices[index_idx][1]]
            v2 = model.vertex_dict[model.indices[index_idx][2]]

            v10_diff = (v1.position - v0.position)
            v20_diff = (v2.position - v0.position)
            v02_diff = (v0.position - v2.position)
            v12_diff = (v1.position - v2.position)
            v01_diff = (v0.position - v1.position)
            v21_diff = (v2.position - v1.position)

            # もっとも対角線の角度が大きいのが斜め方向とみなす
            diagonal_idx = np.argmax([MQuaternion.rotationTo(v02_diff, v12_diff).toDegree(), \
                MQuaternion.rotationTo(v10_diff, v20_diff).toDegree(), MQuaternion.rotationTo(v01_diff, v21_diff).toDegree()])  # noqa
            # もっとも内積が小さいのが垂直方向と見なす
            y_idx = np.argmin(np.abs([MVector3D.dotProduct(v10_diff, v20_diff), \
                MVector3D.dotProduct(v01_diff, v21_diff), MVector3D.dotProduct(v02_diff, v12_diff)]))  # noqa
            # 残りが水平方向と見なす
            xz_idx = list({0, 1, 2} - {y_idx, diagonal_idx})[0]

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
        
        logger.info(f"{target_bone_name}: 重複頂点チェック")

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

        logger.info(f"{target_bone_name}: 辺走査")

        if not start_vertex_idx:
            # Yの昇順ソート
            sorted_ys = np.sort(list(vertices_dict.keys()))
            # 一番上の最後頂点
            sorted_top_vertex_poses = sorted(vertices_dict[sorted_ys[-1]], key=lambda x: [-round(x[2], 3), round(abs(x[0]), 3)])
            # 最後頂点のINDEX
            start_vertex_idx = [i for i in vertex_idxs_dict[sorted_ys[-1]] if model.vertex_dict[i].position == MVector3D(sorted_top_vertex_poses[0])][0]

        # 開始頂点から縦に伸ばす
        target_y_idx = start_vertex_idx
        # 該当Yの開始頂点INDEX
        start_y_idxs = [start_vertex_idx]
        start_ys = [model.vertex_dict[start_vertex_idx].position.y()]
        if len(indices_dict[target_y_idx]["y-"]) == 0 and len(indices_dict[target_y_idx]["duplicate"]) > 0:
            for yv in indices_dict[target_y_idx]["duplicate"]:
                if len(indices_dict[yv.index]["y-"]) > 0:
                    target_y_idx = yv.index
                    break
        while len(indices_dict[target_y_idx]["y-"]) > 0:
            next_y_v = indices_dict[target_y_idx]["y-"][0]
            start_y_idxs.append(next_y_v.index)
            start_ys.append(model.vertex_dict[next_y_v.index].position.y())
            if len(indices_dict[target_y_idx]["y-"]) == 0 and len(indices_dict[target_y_idx]["duplicate"]) > 0:
                for yv in indices_dict[target_y_idx]["duplicate"]:
                    if len(indices_dict[yv.index]["y-"]) > 0:
                        target_y_idx = yv.index
                        break
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
        # YINDEXとXIDEXの対応表
        mesh_xy_map = {}

        max_y_cnt = math.ceil(len(start_ys) / y_density) + 1
        # 円周か否か
        is_circles = {}

        # Y軸に等間隔にボーンを配置する
        for yidx, now_y in enumerate([start_ys[0]] + np.linspace(start_ys[1], start_ys[-1], max_y_cnt - 1).tolist()):
            # 等分割したYに最も近い頂点のY値
            now_y_idx = np.abs(np.asarray(start_ys) - now_y).argmin()
            # 登録対象頂点INDEX
            start_y_idx = start_y_idxs[now_y_idx]

            # 指定された頂点から横方向のINDEXリストを取得
            x_idxs = get_horizonal_x_idxs(start_y_idx, indices_dict)
            mesh_xy_map[yidx] = x_idxs
            is_circles[yidx] = x_idxs[0] == x_idxs[:-1]

            # メッシュ状のYINDEXを取得
            mesh_yidx = now_y_idx

            if is_circles[yidx]:
                # 円周の場合
                target_x_idxs = x_idxs[:-1] if is_full_regist else x_idxs[:] + [x_idxs[0]]
            else:
                # 一枚の場合
                target_x_idxs = x_idxs
            max_x_cnt = 0
            for xidx, now_x_idx in enumerate(target_x_idxs):
                # ボーン登録
                bone_name = f'{target_bone_name}-{(yidx + 1):03d}-{(xidx + 1):03d}'

                # 親ボーン
                parent_bone_name = f'{target_bone_name}-{(yidx):03d}-{(xidx + 1):03d}'
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
                    max_x_cnt = xidx

                # メッシュ状のXINDEXを取得
                mesh_xidx = [xi for xi, x in enumerate(x_idxs) if x == now_x_idx][0]

                # 対応表に追記
                # 頂点リストは重複頂点含めて保持
                bone_vertex_map[bone_name] = {"xidx": mesh_xidx, "yidx": mesh_yidx, \
                                              "vertex_idxs": [now_x_idx] + [i.index for i in indices_dict[now_x_idx]["duplicate"]]}

        end_left_top_bone_name = f'{target_bone_name}-{(max_y_cnt - 1):03d}-{(1):03d}'
        end_left_bottom_bone_name = f'{target_bone_name}-{(max_y_cnt):03d}-{(1):03d}'
        end_right_top_bone_name = f'{target_bone_name}-{(max_y_cnt - 1):03d}-{(1 + x_density):03d}'
        end_right_bottom_bone_name = f'{target_bone_name}-{(max_y_cnt):03d}-{(1 + x_density):03d}'

        # 末端表示枠の最大値
        end_length = np.mean([
            target_bones[end_left_top_bone_name].position.distanceToPoint(target_bones[end_right_top_bone_name].position), \
            target_bones[end_left_bottom_bone_name].position.distanceToPoint(target_bones[end_right_bottom_bone_name].position)
        ])

        # 前処理ボーン
        prev_bone_name = None
        parent_bones = {}
        end_x_idxs = []

        # 高密度ボーンをを排除して登録
        for yidx in range(1, max_y_cnt + 1):
            for xidx in range(0, max_x_cnt + 1):
                # 処理対象ボーン名
                bone_name = f'{target_bone_name}-{(yidx):03d}-{(xidx + 1):03d}'
                # 親ボーン名
                parent_bone_name = f'{target_bone_name}-{(yidx - 1):03d}-{(xidx + 1):03d}'

                is_regist = False

                if xidx == 0:
                    if parent_bone_name not in model.bones:
                        if tailor_type == 1 and root_right_bone and root_left_bone:
                            for direction in ["右", "左"]:
                                shoulder_bone = model.bones[f"{direction}肩"]
                                arm_bone = model.bones[f"{direction}腕"]
                                elbow_bone = model.bones[f"{direction}ひじ"]

                                distance = arm_bone.position.distanceToPoint(elbow_bone.position) / 2

                                bone = target_bones[bone_name]
                                if bone.position.distanceToPoint(shoulder_bone.position) <= distance:
                                    # 肩に近い場合、左右ボーンに割り振る
                                    parent_bone_name = root_bone.name + direction
                                    break

                        if parent_bone_name not in model.bones:
                            parent_bone_name = root_bone.name
                    is_regist = True
                elif not is_circles[yidx - 1] and xidx == max_x_cnt:
                    # 一枚物の場合、最後は常に登録する
                    if yidx == 1:
                        if parent_bone_name not in model.bones:
                            if tailor_type == 1 and root_right_bone and root_left_bone:
                                for direction in ["右", "左"]:
                                    shoulder_bone = model.bones[f"{direction}肩"]
                                    arm_bone = model.bones[f"{direction}腕"]
                                    elbow_bone = model.bones[f"{direction}ひじ"]

                                    distance = arm_bone.position.distanceToPoint(elbow_bone.position) / 2

                                    bone = target_bones[bone_name]
                                    if bone.position.distanceToPoint(shoulder_bone.position) <= distance:
                                        # 肩に近い場合、左右ボーンに割り振る
                                        parent_bone_name = root_bone.name + direction
                                        break

                        if parent_bone_name not in model.bones:
                            parent_bone_name = root_bone.name
                    else:
                        parent_bone_name = f'{target_bone_name}-{(yidx - 1):03d}-{(max_x_cnt + 1):03d}'
                    is_regist = True
                else:
                    # 指定された頂点から横方向のINDEXリストを取得
                    x_vertex_idxs = vertices_map[bone_vertex_map[bone_name]["yidx"]]

                    # 隣のボーンとの距離
                    prev_brother_lengths = []
                    prev_brother_length = 0
                    next_brother_lengths = []
                    next_brother_length = 0

                    # 隣ボーンとの距離
                    prev_vidxs = x_vertex_idxs[(bone_vertex_map[prev_bone_name]["xidx"]):(xidx + 1)]
                    next_vidxs = x_vertex_idxs[(xidx):]

                    for pvidx, nvidx in zip(prev_vidxs[:-1], prev_vidxs[1:]):
                        prev_brother_lengths.append(model.vertex_dict[pvidx].position.distanceToPoint(model.vertex_dict[nvidx].position))

                    for pvidx, nvidx in zip(next_vidxs[:-1], next_vidxs[1:]):
                        next_brother_lengths.append(model.vertex_dict[pvidx].position.distanceToPoint(model.vertex_dict[nvidx].position))

                    prev_brother_length = np.sum(prev_brother_lengths)
                    next_brother_length = np.sum(next_brother_lengths)
                    
                    if (is_full_regist and xidx % x_density == 0) \
                        or (end_length * 0.8 < prev_brother_length and end_length * 0.8 < next_brother_length):     # noqa
                        # 全登録か、表示先より隣の方が遠い場合、対象ボーン登録
                        is_regist = True

                        if yidx == 1:
                            if parent_bone_name not in model.bones:
                                if tailor_type == 1 and root_right_bone and root_left_bone:
                                    for direction in ["右", "左"]:
                                        shoulder_bone = model.bones[f"{direction}肩"]
                                        arm_bone = model.bones[f"{direction}腕"]
                                        elbow_bone = model.bones[f"{direction}ひじ"]

                                        distance = arm_bone.position.distanceToPoint(elbow_bone.position) / 2

                                        bone = target_bones[bone_name]
                                        if bone.position.distanceToPoint(shoulder_bone.position) <= distance:
                                            # 肩に近い場合、左右ボーンに割り振る
                                            parent_bone_name = root_bone.name + direction
                                            break

                            if parent_bone_name not in model.bones:
                                parent_bone_name = root_bone.name
                        else:
                            # 親ボーンを探す
                            is_parent = False
                            byidx = yidx - 1
                            parent_bone_name = f'{target_bone_name}-{(byidx):03d}-{(xidx + 1):03d}'
                            if parent_bone_name in model.bones:
                                is_parent = True

                            if not is_parent:
                                for bxidx in range(xidx, max(0, int(prev_bone_name.split('-')[-1])), -1):
                                    parent_bone_name = f'{target_bone_name}-{(byidx):03d}-{(bxidx):03d}'
                                    if parent_bone_name in model.bones:
                                        is_parent = True
                                        break

                                if not is_parent:
                                    for bxidx in range(xidx + 2, max_x_cnt + 1):
                                        parent_bone_name = f'{target_bone_name}-{(byidx):03d}-{(bxidx):03d}'
                                        if parent_bone_name in model.bones:
                                            is_parent = True
                                            break

                            if not is_parent:
                                if is_circles[yidx - 1]:
                                    # 最後までいって見つからなければ最初
                                    parent_bone_name = f'{target_bone_name}-{(yidx - 1):03d}-{(1):03d}'
                                else:
                                    # 一枚物の場合、最後
                                    parent_bone_name = f'{target_bone_name}-{(yidx - 1):03d}-{(max_x_cnt + 1):03d}'
                
                if is_regist:
                    if parent_bone_name not in parent_bones.keys():
                        parent_bones[parent_bone_name] = []
                    parent_bones[parent_bone_name].append(bone_name)

                    if yidx == max_y_cnt:
                        end_x_idxs.append(xidx)

                    bone = target_bones[bone_name]
                    bone.parent_index = model.bones[parent_bone_name].index
                    bone.index = len(list(model.bones.keys()))

                    model.bones[bone.name] = bone
                    model.bone_indexes[bone.index] = bone.name

                    # 表示枠
                    model.display_slots[target_bone_name].references.append((0, bone.index))

                    prev_bone_name = bone.name

        # 表示先を定義
        for parent_bone_name, bone_names in parent_bones.items():
            if parent_bone_name in [root_bone.name, root_right_bone_name, root_left_bone_name]:
                continue

            sorted_bone_names = sorted(bone_names, key=lambda x: [abs(int(parent_bone_name.split('-')[2]) - int(x.split('-')[2])), -int(x.split('-')[1])])
            for tail_bone_name in sorted_bone_names:
                if tail_bone_name in model.bones:
                    break
            model.bones[parent_bone_name].tail_index = model.bones[tail_bone_name].index
            model.bones[parent_bone_name].flag |= 0x0001

        logger.info(f"{target_bone_name}: ボーン完了")

        # if tailor_type == 1:
        #     # マントタイプのIK
        #     for direction in ["右", "左"]:
        #         shoulder_bone = model.bones[f"{direction}肩"]
        #         arm_bone = model.bones[f"{direction}腕"]
        #         elbow_bone = model.bones[f"{direction}ひじ"]

        #         distance = arm_bone.position.distanceToPoint(elbow_bone.position) / 2

        #         yidx = 1
        #         max_x_cnt = len(end_x_idxs)
        #         head_bone_name = f'{target_bone_name}-{(yidx):03d}-{(1):03d}'
        #         while head_bone_name in model.bones:
        #             head_bone = model.bones[head_bone_name]
        #             if head_bone.position.distanceToPoint(shoulder_bone.position) <= distance:
        #                 # 腕の半分くらいの距離ならIK生成
        #                 cloak_ik_bone = Bone(f'{head_bone_name}_IK', f'{head_bone_name}_IK', head_bone.position, arm_bone.index, 0, 0x0000 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0020)
        #                 cloak_ik_bone.index = len(list(model.bones.keys()))
        #                 model.bones[cloak_ik_bone.name] = cloak_ik_bone
        #                 model.bone_indexes[cloak_ik_bone.index] = cloak_ik_bone.name
        #                 model.display_slots[target_bone_name].references.append(model.bones[cloak_ik_bone.name].index)

        #                 cloak_ik = Ik(model.bones[parent_bones[head_bone_name][0]].index, 2, 1, [IkLink(head_bone.index, 0)])

        #                 cloak_ik_bone.ik = cloak_ik

        #             if model.bone_indexes[model.bones[head_bone_name].index + 1].split('-')[1] != head_bone_name.split('-')[1]:
        #                 break

        #             head_bone_name = model.bone_indexes[model.bones[head_bone_name].index + 1]

        rigidbody_param_from = RigidBodyParam(rigidbody_param_to.mass * ((max_y_cnt + 1) ** 2), 0.9, 0.9, 0, 0.5)

        created_rigidbodies = {}

        vertex_vertical_lengths = np.zeros(vertices_map.shape)
        vertex_horizonal_lengths = np.zeros(vertices_map.shape)
        for ridx, row_range in enumerate(vertices_map):
            for widx, wvidx in enumerate(row_range):
                if widx > 0:
                    vertex_horizonal_lengths[ridx, widx] = model.vertex_dict[vertices_map[ridx, widx]].position.distanceToPoint(model.vertex_dict[vertices_map[ridx, widx - 1]].position)
                if ridx > 0:
                    vertex_vertical_lengths[ridx, widx] = model.vertex_dict[vertices_map[ridx, widx]].position.distanceToPoint(model.vertex_dict[vertices_map[ridx - 1, widx]].position)

        rigidbody_limit_thicks = np.linspace(0.1, 0.3, max_y_cnt)

        yidx = max_y_cnt
        max_x_cnt = len(end_x_idxs)
        while yidx > 1:
            xidx = 1
            left_bottom_bone_name = f'{target_bone_name}-{(yidx):03d}-{(xidx):03d}'
            right_bottom_bone_name = model.bone_indexes[model.bones[left_bottom_bone_name].index + 1]
            left_top_bone_name = model.bone_indexes[model.bones[left_bottom_bone_name].parent_index]
            right_top_bone_name = model.bone_indexes[model.bones[right_bottom_bone_name].parent_index]

            while xidx <= max_x_cnt:
                # 各ボーンに対応する頂点情報
                left_top_bone_map = bone_vertex_map[left_top_bone_name]
                left_bottom_bone_map = bone_vertex_map[left_bottom_bone_name]

                if int(left_bottom_bone_name.split('-')[1]) == max_y_cnt:
                    if int(right_bottom_bone_name.split('-')[2]) == 1:
                        # 下段最後まで
                        vertices_range = \
                            vertices_map[left_top_bone_map["yidx"]:, left_top_bone_map["xidx"]:]
                        vertex_horizonal_length_range = \
                            vertex_horizonal_lengths[left_top_bone_map["yidx"]:, left_top_bone_map["xidx"]:]
                        vertex_vertical_length_range = \
                            vertex_vertical_lengths[left_top_bone_map["yidx"]:, left_top_bone_map["xidx"]:]
                    else:
                        # 全部がある場合はそこまで
                        right_top_bone_map = bone_vertex_map[right_top_bone_name]
                        right_bottom_bone_map = bone_vertex_map[right_bottom_bone_name]
                        # 一旦最大値
                        max_xidx = max(left_top_bone_map["xidx"], left_bottom_bone_map["xidx"], right_top_bone_map["xidx"], right_bottom_bone_map["xidx"])

                        vertices_range = \
                            vertices_map[left_top_bone_map["yidx"]:, \
                                         left_top_bone_map["xidx"]:(max_xidx + 1)]
                        vertex_horizonal_length_range = \
                            vertex_horizonal_lengths[left_top_bone_map["yidx"]:, \
                                                     left_top_bone_map["xidx"]:(max_xidx + 1)]
                        vertex_vertical_length_range = \
                            vertex_vertical_lengths[left_top_bone_map["yidx"]:, \
                                                    left_top_bone_map["xidx"]:(max_xidx + 1)]
                elif (is_circles[yidx - 1] and (int(right_top_bone_name.split('-')[2]) == 1 or int(right_bottom_bone_name.split('-')[2]) == 1)):
                    # 最後まで
                    max_xidx = 0

                    # 右端がない場合、最後まで
                    vertices_range = \
                        vertices_map[left_top_bone_map["yidx"]:(left_bottom_bone_map["yidx"] + 1), \
                                     left_top_bone_map["xidx"]:]
                    vertex_horizonal_length_range = \
                        vertex_horizonal_lengths[left_top_bone_map["yidx"]:(left_bottom_bone_map["yidx"] + 1), \
                                                 left_top_bone_map["xidx"]:]
                    vertex_vertical_length_range = \
                        vertex_vertical_lengths[left_top_bone_map["yidx"]:(left_bottom_bone_map["yidx"] + 1), \
                                                left_top_bone_map["xidx"]:]
                else:
                    # 全部がある場合はそこまで
                    right_top_bone_map = bone_vertex_map[right_top_bone_name]
                    right_bottom_bone_map = bone_vertex_map[right_bottom_bone_name]
                    # 一旦最大値
                    max_xidx = max(left_top_bone_map["xidx"], left_bottom_bone_map["xidx"], right_top_bone_map["xidx"], right_bottom_bone_map["xidx"])

                    vertices_range = \
                        vertices_map[left_top_bone_map["yidx"]:(left_bottom_bone_map["yidx"] + 1), \
                                     left_top_bone_map["xidx"]:(max_xidx + 1)]
                    vertex_horizonal_length_range = \
                        vertex_horizonal_lengths[left_top_bone_map["yidx"]:(left_bottom_bone_map["yidx"] + 1), \
                                                 left_top_bone_map["xidx"]:(max_xidx + 1)]
                    vertex_vertical_length_range = \
                        vertex_vertical_lengths[left_top_bone_map["yidx"]:(left_bottom_bone_map["yidx"] + 1), \
                                                left_top_bone_map["xidx"]:(max_xidx + 1)]
                
                for hi, h_vertices in enumerate(vertices_range):
                    for vi, vertex_idx in enumerate(h_vertices):
                        v = model.vertex_dict[vertex_idx]

                        horizonal_length = np.sum(vertex_horizonal_length_range[hi, :])
                        v_horizonal_length = np.sum(vertex_horizonal_length_range[hi, :(vi + 1)])
                        vertical_length = np.sum(vertex_vertical_length_range[:, vi])
                        v_vertical_length = np.sum(vertex_vertical_length_range[:(hi + 1), vi])

                        left_top_weight = max(0, ((horizonal_length - v_horizonal_length) / horizonal_length) * \
                                              ((vertical_length - v_vertical_length) / vertical_length))    # * 1.9
                        left_bottom_weight = max(0, ((horizonal_length - v_horizonal_length) / horizonal_length) * \
                                                 ((v_vertical_length) / vertical_length))   # * 0.1
                        right_top_weight = max(0, ((v_horizonal_length) / horizonal_length) * \
                                               ((vertical_length - v_vertical_length) / vertical_length))   # * 1.9
                        right_bottom_weight = max(0, ((v_horizonal_length) / horizonal_length) * \
                                                  ((v_vertical_length) / vertical_length))   # * 0.1
                        
                        if int(left_bottom_bone_name.split('-')[1]) == max_y_cnt:
                            # 最下段は末端ボーンにウェイトを振らない
                            # 処理対象全ボーン名
                            weight_names = np.array([left_top_bone_name, right_top_bone_name])
                            # ウェイト
                            total_weights = np.array([left_top_weight + left_bottom_weight, right_top_weight + right_bottom_weight])
                        else:
                            # 処理対象全ボーン名
                            weight_names = np.array([left_top_bone_name, right_top_bone_name, left_bottom_bone_name, right_bottom_bone_name])
                            # ウェイト
                            total_weights = np.array([left_top_weight, right_top_weight, left_bottom_weight, right_bottom_weight])

                        if len(np.nonzero(total_weights)[0]) > 0:
                            weights = total_weights / total_weights.sum(axis=0, keepdims=1)
                            weight_idxs = np.argsort(weights)

                            for vv in [v] + indices_dict[v.index]["duplicate"]:
                                # 重複頂点にも同じウェイトを割り当てる
                                if not vv.deform:
                                    if np.count_nonzero(weights) == 1:
                                        vv.deform = Bdef1(model.bones[weight_names[weight_idxs[-1]]].index)
                                    elif np.count_nonzero(weights) == 2:
                                        vv.deform = Bdef2(model.bones[weight_names[weight_idxs[-1]]].index, model.bones[weight_names[weight_idxs[-2]]].index, weights[weight_idxs[-1]])
                                    else:
                                        vv.deform = Bdef4(model.bones[weight_names[weight_idxs[-1]]].index, model.bones[weight_names[weight_idxs[-2]]].index, \
                                                          model.bones[weight_names[weight_idxs[-3]]].index, model.bones[weight_names[weight_idxs[-4]]].index, \
                                                          weights[weight_idxs[-1]], weights[weight_idxs[-2]], weights[weight_idxs[-3]], weights[weight_idxs[-4]])
            
                # 剛体登録 ---------------------
                if left_top_bone_name not in created_rigidbodies:
                    # 左上の段と列
                    yi = int(left_top_bone_name.split("-")[1])

                    # 剛体計算用ボーン
                    rigidbody_xis = np.array([int(left_top_bone_name.split("-")[-1]), int(left_bottom_bone_name.split("-")[-1]), \
                                              int(right_top_bone_name.split("-")[-1]), int(right_bottom_bone_name.split("-")[-1]), \
                                              int(model.bone_indexes[model.bones[left_top_bone_name].index + 1].split("-")[-1])])
                    if int(left_top_bone_name.split("-")[-1]) == 1:
                        rigidbody_left_top_bone_name = left_top_bone_name
                    else:
                        rigidbody_left_top_bone_name = f'{target_bone_name}-{(yi):03d}-{(np.min(rigidbody_xis[np.where(rigidbody_xis > 1)])):03d}'

                    if is_circles[yidx - 1] and (int(right_top_bone_name.split("-")[-1]) == 1 or int(right_bottom_bone_name.split("-")[-1]) == 1):
                        rigidbody_right_top_bone_name = f'{target_bone_name}-{(yi):03d}-{(1):03d}'
                    else:
                        rigidbody_right_top_bone_name = f'{target_bone_name}-{(yi):03d}-{(np.max(rigidbody_xis)):03d}'
                    
                    if int(left_bottom_bone_name.split("-")[-1]) == 1:
                        rigidbody_left_bottom_bone_name = left_bottom_bone_name
                    else:
                        rigidbody_left_bottom_bone_name = f'{target_bone_name}-{(yi + 1):03d}-{(np.min(rigidbody_xis[np.where(rigidbody_xis > 1)])):03d}'

                    if (is_circles[yidx - 1] and (int(right_bottom_bone_name.split("-")[-1]) == 1 or int(right_bottom_bone_name.split("-")[-1]) == 1)):
                        rigidbody_right_bottom_bone_name = f'{target_bone_name}-{(yi + 1):03d}-{(1):03d}'
                    else:
                        rigidbody_right_bottom_bone_name = f'{target_bone_name}-{(yi + 1):03d}-{(np.max(rigidbody_xis)):03d}'

                    # 剛体処理対象ボーン名リスト
                    # 剛体設定
                    rigidbody_bone = model.bones[left_top_bone_name]

                    # 衝突剛体
                    for yidx in range(max_y_cnt + 1):
                        rigidbody_no_collisions = 0
                        for nc in range(16):
                            # 最上部はボディとの剛体非接触
                            # 以降は剛体接触判定あり
                            if nc not in ([0, 1, collision_group_idx] if yidx == 1 else [collision_group_idx]):
                                rigidbody_no_collisions |= 1 << nc

                    # 質量：末端からの二乗
                    # 減衰：根元から末端の線形補間
                    # 反発・摩擦：根元一定
                    # mass = rigidbody_param_to.mass * ((max_y_cnt - yi) ** 2) / 2
                    mass = rigidbody_param_to.mass * (max_y_cnt - yi)
                    linear_damping = rigidbody_param_from.linear_damping + ((rigidbody_param_to.linear_damping - rigidbody_param_from.linear_damping) * (yi / max_y_cnt))
                    angular_damping = rigidbody_param_from.angular_damping + ((rigidbody_param_to.angular_damping - rigidbody_param_from.angular_damping) * (yi / max_y_cnt))
                    
                    # 剛体の傾き
                    if int(rigidbody_right_top_bone_name.split("-")[-1]) == 1:
                        slope_xidx = int(int(rigidbody_left_top_bone_name.split("-")[-1]) + (((end_x_idxs[-1] + 2) - int(rigidbody_left_top_bone_name.split("-")[-1])) / 2))
                    else:
                        slope_xidx = int(int(rigidbody_left_top_bone_name.split("-")[-1]) + \
                            ((int(rigidbody_right_top_bone_name.split("-")[-1]) - int(rigidbody_left_top_bone_name.split("-")[-1])) / 2))   # noqa
                    left_above_bone_name = f'{target_bone_name}-{(yi):03d}-{slope_xidx:03d}'
                    left_below_bone_name = f'{target_bone_name}-{(yi + 1):03d}-{slope_xidx:03d}'
                    shape_rotation_radians = MVector3D()
                    shape_axis = (target_bones[left_below_bone_name].position - target_bones[left_above_bone_name].position).normalized()
                    shape_axis_up = MVector3D(shape_axis.x(), 0, shape_axis.z())
                    shape_axis_cross = MVector3D.crossProduct(shape_axis, shape_axis_up).normalized()

                    # if round(shape_axis.x(), 3) == 0 and (end_x_idxs[-1] / 2) - x_density <= min(rigidbody_xis) <= (end_x_idxs[-1] / 2) + x_density:
                    #     shape_rotation_qq = MQuaternion.fromEulerAngles(0, 180, 0)
                    # else:
                    shape_rotation_qq = MQuaternion.fromDirection(shape_axis, shape_axis_cross)
                    shape_rotation_qq *= MQuaternion.fromEulerAngles(0, 0, -90)
                    shape_rotation_qq *= MQuaternion.fromEulerAngles(-90, 0, 0)
                    # shape_rotation_qq = MQuaternion.rotationTo(MVector3D(0, -1, 0), MVector3D(shape_axis.x(), 0, shape_axis.z()))
                    # # 正面の傾き
                    # if yi == max_y_cnt - 1 and xidx == 1:
                    #     shape_slope = MQuaternion.rotationTo(MVector3D(0, -1, 0), shape_rotation_qq * shape_axis)
                    # shape_rotation_qq *= shape_slope
                    shape_rotation_euler = shape_rotation_qq.toEulerAngles()
                    shape_rotation_radians = MVector3D(math.radians(shape_rotation_euler.x()), math.radians(shape_rotation_euler.y()), math.radians(shape_rotation_euler.z()))
                    
                    # 剛体の大きさ
                    x_size = np.max(
                        [target_bones[rigidbody_right_top_bone_name].position.distanceToPoint(target_bones[rigidbody_left_top_bone_name].position), \
                         target_bones[rigidbody_right_bottom_bone_name].position.distanceToPoint(target_bones[rigidbody_left_bottom_bone_name].position)])
                    y_size = np.max(
                        [target_bones[rigidbody_right_top_bone_name].position.distanceToPoint(target_bones[rigidbody_right_bottom_bone_name].position), \
                         target_bones[rigidbody_left_top_bone_name].position.distanceToPoint(target_bones[rigidbody_left_bottom_bone_name].position)])
                    shape_size = MVector3D(max(0.25, x_size * 0.5), max(0.25, y_size * 0.5), rigidbody_limit_thicks[yi])

                    # 剛体の位置
                    shape_position = (target_bones[left_above_bone_name].position + target_bones[left_below_bone_name].position) / 2 - rigidbody_limit_thicks[yi] / 2
                    
                    # if yi in [1, 2]:
                    #     # 先頭と次はボーン追従の球剛体
                    #     ball_size = max(0.25, np.mean([x_size * 0.5, y_size * 0.5]))
                    #     shape_size = MVector3D(ball_size, ball_size, ball_size)
                    #     shape_type = 0
                    #     mode = 0 if yi == 1 else 1
                    # else:
                    #     # それ以降は板の物理剛体
                    #     shape_type = 1
                    #     mode = 1
                    shape_type = 1
                    mode = 0 if yi == 1 else 1
                    rigidbody = RigidBody(rigidbody_bone.name, rigidbody_bone.english_name, rigidbody_bone.index, collision_group_idx, rigidbody_no_collisions, \
                                          shape_type, shape_size, shape_position, shape_rotation_radians, \
                                          mass, linear_damping, angular_damping, rigidbody_param_from.restitution, rigidbody_param_from.friction, mode)

                    # 別途保持しておく
                    created_rigidbodies[rigidbody.name] = rigidbody

                xidx += 1
                left_bottom_bone_name = right_bottom_bone_name
                if len(model.bones) == model.bones[right_bottom_bone_name].index + 1:
                    # 最後の場合クリア
                    right_bottom_bone_name = f'{target_bone_name}-{(yidx):03d}-{(1):03d}'
                else:
                    right_bottom_bone_name = model.bone_indexes[model.bones[right_bottom_bone_name].index + 1]
                    if left_bottom_bone_name.split('-')[1] != right_bottom_bone_name.split('-')[1]:
                        # 段が違う場合クリア
                        right_bottom_bone_name = f'{target_bone_name}-{left_bottom_bone_name.split("-")[1]}-{(1):03d}'
                left_top_bone_name = model.bone_indexes[model.bones[left_bottom_bone_name].parent_index]
                right_top_bone_name = model.bone_indexes[model.bones[right_bottom_bone_name].parent_index]
                logger.debug(f"({xidx}:{yidx}) {left_bottom_bone_name}, {right_bottom_bone_name}, {left_top_bone_name}, {right_top_bone_name}")
        
            yidx -= 1
            left_bottom_bone_name = left_top_bone_name
            right_bottom_bone_name = right_top_bone_name
            left_top_bone_name = model.bone_indexes[model.bones[left_bottom_bone_name].parent_index]
            right_top_bone_name = model.bone_indexes[model.bones[right_bottom_bone_name].parent_index]
            logger.debug(f"({xidx}:{yidx}) {left_bottom_bone_name}, {right_bottom_bone_name}, {left_top_bone_name}, {right_top_bone_name}")

        for rigidbody_name in sorted(created_rigidbodies.keys()):
            # 剛体を登録
            rigidbody = created_rigidbodies[rigidbody_name]
            rigidbody.index = len(model.rigidbodies)
            model.rigidbodies[rigidbody.name] = rigidbody

        vertical_limit_min_rots = np.linspace(-min_vertical_limit_rot, -max_vertical_limit_rot, max_y_cnt - 1)
        vertical_limit_max_rots = np.linspace(min_vertical_limit_rot, max_vertical_limit_rot, max_y_cnt - 1)
        horizonal_limit_min_rots = np.linspace(-min_horizonal_limit_rot, -max_horizonal_limit_rot, max_x_cnt)
        horizonal_limit_max_rots = np.linspace(min_horizonal_limit_rot, max_horizonal_limit_rot, max_x_cnt)
        vertical_limit_min_movs = np.linspace(0, 0, max_y_cnt - 1)
        vertical_limit_max_movs = np.linspace(0, 0, max_y_cnt - 1)
        horizonal_limit_min_movs = np.linspace(0, 0, max_x_cnt)
        horizonal_limit_max_movs = np.linspace(0, 0, max_x_cnt)
        created_joints = {}

        yidx = max_y_cnt
        max_x_cnt = len(end_x_idxs)
        while yidx > 1:
            xidx = 1
            left_bottom_bone_name = f'{target_bone_name}-{(yidx):03d}-{(xidx):03d}'
            right_bottom_bone_name = model.bone_indexes[model.bones[left_bottom_bone_name].index + 1]
            left_top_bone_name = model.bone_indexes[model.bones[left_bottom_bone_name].parent_index]
            right_top_bone_name = model.bone_indexes[model.bones[right_bottom_bone_name].parent_index]

            while (xidx <= max_x_cnt and is_circles[yidx - 1]) or (xidx < max_x_cnt and not is_circles[yidx - 1]):
                target_vertex_joints = [(left_top_bone_name, left_bottom_bone_name, right_bottom_bone_name)]
                # if int(left_bottom_bone_name.split('-')[-1]) < int(right_top_bone_name.split('-')[-1]) < int(right_bottom_bone_name.split('-')[-1]):
                #     target_vertex_joints += [(right_top_bone_name, left_bottom_bone_name, right_bottom_bone_name)]
                for joint_src_bone_name, joint_dest_bone_name, joint_horizonal_name in target_vertex_joints:    # noqa
                    # 縦ジョイント
                    joint_name = f'↓|{joint_src_bone_name}|{joint_dest_bone_name}'

                    if joint_name in created_joints or joint_src_bone_name not in model.rigidbodies or joint_dest_bone_name not in model.rigidbodies:
                        # 登録済みはスルー
                        continue

                    joint_src_bone = model.bones[joint_src_bone_name]
                    joint_dest_bone = model.bones[joint_dest_bone_name]
                    joint_horizonal_bone = model.bones[joint_horizonal_name]
                    
                    # 縦ジョイント
                    joint_horizonal_vec = ((joint_horizonal_bone.position - joint_dest_bone.position) / 2)
                    joint_vec = joint_dest_bone.position + MVector3D(joint_horizonal_vec.x(), 0, joint_horizonal_vec.z())

                    # 回転量
                    joint_src_radians = created_rigidbodies[joint_src_bone.name].shape_rotation
                    joint_dest_radians = created_rigidbodies[joint_dest_bone.name].shape_rotation
                    joint_src_qq = MQuaternion.fromEulerAngles(math.degrees(joint_src_radians.x()), math.degrees(joint_src_radians.y()), math.degrees(joint_src_radians.z()))
                    joint_dest_qq = MQuaternion.fromEulerAngles(math.degrees(joint_dest_radians.x()), math.degrees(joint_dest_radians.y()), math.degrees(joint_dest_radians.z()))
                    joint_euler = MQuaternion.slerp(joint_src_qq, joint_dest_qq, 0.5).toEulerAngles()
                    joint_radians = MVector3D(math.radians(joint_euler.x()), math.radians(joint_euler.y()), math.radians(joint_euler.z()))

                    yi = int(joint_src_bone.name.split('-')[1]) - 1

                    joint = Joint(joint_name, joint_name, 0, model.rigidbodies[joint_src_bone.name].index, model.rigidbodies[joint_dest_bone.name].index,
                                  joint_vec, joint_radians, MVector3D(vertical_limit_min_movs[yi], vertical_limit_min_movs[yi], vertical_limit_min_movs[yi]), \
                                  MVector3D(vertical_limit_max_movs[yi], vertical_limit_max_movs[yi], vertical_limit_max_movs[yi]),
                                  MVector3D(math.radians(vertical_limit_min_rots[yi]), math.radians(vertical_limit_min_rots[yi]), math.radians(vertical_limit_min_rots[yi])),
                                  MVector3D(math.radians(vertical_limit_max_rots[yi]), math.radians(vertical_limit_max_rots[yi]), math.radians(vertical_limit_max_rots[yi])),
                                  MVector3D(), MVector3D())
                    created_joints[joint.name] = joint

                for joint_src_bone_name, joint_dest_bone_name, joint_bottom_bone_name in ([(left_top_bone_name, right_top_bone_name, left_bottom_bone_name), \
                        (left_bottom_bone_name, right_bottom_bone_name, left_top_bone_name)]):    # noqa
                    # 横ジョイント
                    joint_name = f'→|{joint_src_bone_name}|{joint_dest_bone_name}'

                    if joint_name in created_joints or joint_dest_bone_name not in model.rigidbodies:
                        # 登録済みはスルー
                        continue

                    joint_src_bone = model.bones[joint_src_bone_name]
                    joint_dest_bone = model.bones[joint_dest_bone_name]
                    joint_bottom_bone = model.bones[joint_bottom_bone_name]
                    
                    joint_vertical_vec = ((joint_bottom_bone.position - joint_src_bone.position) / 2)
                    joint_center_vec = ((joint_dest_bone.position - joint_src_bone.position) / 2)
                    joint_vec = joint_dest_bone.position + MVector3D(joint_vertical_vec.x(), joint_vertical_vec.y() + joint_center_vec.y(), joint_vertical_vec.z())
                    
                    # 回転量
                    joint_src_radians = created_rigidbodies[joint_src_bone.name].shape_rotation
                    joint_dest_radians = created_rigidbodies[joint_dest_bone.name].shape_rotation
                    joint_src_qq = MQuaternion.fromEulerAngles(math.degrees(joint_src_radians.x()), math.degrees(joint_src_radians.y()), math.degrees(joint_src_radians.z()))
                    joint_dest_qq = MQuaternion.fromEulerAngles(math.degrees(joint_dest_radians.x()), math.degrees(joint_dest_radians.y()), math.degrees(joint_dest_radians.z()))
                    joint_euler = MQuaternion.slerp(joint_src_qq, joint_dest_qq, 0.5).toEulerAngles()
                    joint_radians = MVector3D(math.radians(joint_euler.x()), math.radians(joint_euler.y()), math.radians(joint_euler.z()))
                    
                    xi = xidx - 1
                    yi = int(joint_src_bone.name.split('-')[1]) - 1

                    joint = Joint(joint_name, joint_name, 0, model.rigidbodies[joint_src_bone.name].index, model.rigidbodies[joint_dest_bone.name].index,
                                  joint_vec, joint_radians, MVector3D(horizonal_limit_min_movs[xi], horizonal_limit_min_movs[xi], horizonal_limit_min_movs[xi]), \
                                  MVector3D(horizonal_limit_max_movs[xi], horizonal_limit_max_movs[xi], horizonal_limit_max_movs[xi]),
                                  MVector3D(math.radians(horizonal_limit_min_rots[xi]), math.radians(horizonal_limit_min_rots[xi]), math.radians(horizonal_limit_min_rots[xi])),
                                  MVector3D(math.radians(horizonal_limit_max_rots[xi]), math.radians(horizonal_limit_max_rots[xi]), math.radians(horizonal_limit_max_rots[xi])),
                                  MVector3D(), MVector3D())
                    created_joints[joint.name] = joint
                            
                xidx += 1
                left_bottom_bone_name = right_bottom_bone_name
                if len(model.bones) == model.bones[right_bottom_bone_name].index + 1:
                    # 最後の場合クリア
                    right_bottom_bone_name = f'{target_bone_name}-{(yidx):03d}-{(1):03d}'
                else:
                    right_bottom_bone_name = model.bone_indexes[model.bones[right_bottom_bone_name].index + 1]
                    if left_bottom_bone_name.split('-')[1] != right_bottom_bone_name.split('-')[1]:
                        # 段が違う場合クリア
                        right_bottom_bone_name = f'{target_bone_name}-{left_bottom_bone_name.split("-")[1]}-{(1):03d}'
                left_top_bone_name = model.bone_indexes[model.bones[left_bottom_bone_name].parent_index]
                right_top_bone_name = model.bone_indexes[model.bones[right_bottom_bone_name].parent_index]
                logger.debug(f"({xidx}:{yidx}) {left_bottom_bone_name}, {right_bottom_bone_name}, {left_top_bone_name}, {right_top_bone_name}")
        
            yidx -= 1
            left_bottom_bone_name = left_top_bone_name
            right_bottom_bone_name = right_top_bone_name
            left_top_bone_name = model.bone_indexes[model.bones[left_bottom_bone_name].parent_index]
            right_top_bone_name = model.bone_indexes[model.bones[right_bottom_bone_name].parent_index]
            logger.debug(f"({xidx}:{yidx}) {left_bottom_bone_name}, {right_bottom_bone_name}, {left_top_bone_name}, {right_top_bone_name}")

        for joint_name in sorted(created_joints.keys()):
            # ジョイントを登録
            joint = created_joints[joint_name]
            joint.index = len(model.joints)
            model.joints[joint.name] = joint

        logger.info(f"{target_bone_name}: ウェイト・剛体・ジョイント完了")

        model.comment += "\r\n材質： {0} ----------------------------------".format(
            target_material_name
        )
        model.comment += "\r\n　　ボーン: {0}\r\nボーン密度: X方向: {1}, Y方向: {2}".format(
            "間引きなし" if is_full_regist else "間引きあり", x_density, y_density
        )
        model.comment += "\r\n　　末端剛体: 質量: {0}, 移動減衰: {1}, 回転減衰: {2}, 反発力: {3}, 摩擦力: {4}".format(
            round(rigidbody_param_to.mass), round(rigidbody_param_to.linear_damping, 6), round(rigidbody_param_to.angular_damping, 6), \
            round(rigidbody_param_to.restitution, 6), round(rigidbody_param_to.friction, 6)
        )
        model.comment += "\r\n　　縦ジョイント: 最小回転制限: {0}, 最大回転制限: {1}, 最小移動制限: {2}, 最大移動制限: {3}".format(
            min_vertical_limit_rot, max_vertical_limit_rot, 0, 0
        )
        model.comment += "\r\n　　横ジョイント: 最小回転制限: {0}, 最大回転制限: {1}, 最小移動制限: {2}, 最大移動制限: {3}".format(
            min_horizonal_limit_rot, max_horizonal_limit_rot, 0, 0
        )

    new_file_path = os.path.join(MFileUtils.get_dir_path(model.path), "{0}_{1:%Y%m%d_%H%M%S}{2}".format(os.path.basename(model.path.split('.')[0]), datetime.now(), ".pmx"))

    pmx_writer = PmxWriter()
    pmx_writer.write(model, new_file_path)

    logger.warning(f"出力終了: {new_file_path}")


def get_edge_bone_names(model: PmxModel, target_bone_name: str, max_x_cnt: int, yidx1: int, yidx2: int, xidx1: int, xidx2: int):
    # 処理対象ボーン名
    org_left_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):03d}-{(xidx1 + 1):03d}'
    org_left_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):03d}-{(xidx1 + 1):03d}'
    org_right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):03d}-{(xidx2 + 1):03d}'
    org_right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):03d}-{(xidx2 + 1):03d}'

    left_top_bone_name = None
    left_bottom_bone_name = None
    right_top_bone_name = None
    right_bottom_bone_name = None

    if org_left_top_bone_name in model.bones:
        left_top_bone_name = org_left_top_bone_name
    else:
        for bxidx in range(xidx1, -1, -1):
            brother_bone_name = f'{target_bone_name}-{(yidx1 + 1):03d}-{(bxidx):03d}'
            if brother_bone_name not in model.bones:
                # 隣がない場合、もうひとつ前をチェック
                continue
            else:
                # あったら抜ける(下端は同じ位置)
                left_top_bone_name = brother_bone_name
                org_left_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):03d}-{(bxidx):03d}'
                org_right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):03d}-{(bxidx + 1):03d}'
                break

    if org_left_bottom_bone_name in model.bones:
        left_bottom_bone_name = org_left_bottom_bone_name
    else:
        for bxidx in range(xidx1, -1, -1):
            brother_bone_name = f'{target_bone_name}-{(yidx2 + 1):03d}-{(bxidx):03d}'
            if brother_bone_name not in model.bones:
                # 隣がない場合、もうひとつ前をチェック
                continue
            else:
                # あったら抜ける
                left_bottom_bone_name = brother_bone_name
                break
    
    if org_right_top_bone_name in model.bones:
        right_top_bone_name = org_right_top_bone_name
    else:
        for bxidx in range(xidx2 + 2, max_x_cnt + 1):
            brother_bone_name = f'{target_bone_name}-{(yidx1 + 1):03d}-{(bxidx):03d}'
            if brother_bone_name not in model.bones:
                # 隣がない場合、もうひとつ前をチェック
                continue
            else:
                # あったら抜ける
                right_top_bone_name = brother_bone_name
                org_right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):03d}-{(bxidx):03d}'
                break

    if right_top_bone_name not in model.bones:
        right_top_bone_name = f'{target_bone_name}-{(yidx1 + 1):03d}-{(1):03d}'
        right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):03d}-{(1):03d}'
    
    bxidx = xidx2 + 2
    if right_bottom_bone_name not in model.bones:
        if org_right_bottom_bone_name in model.bones:
            right_bottom_bone_name = org_right_bottom_bone_name
        else:
            for bxidx in range(xidx2 + 2, max_x_cnt + 1):
                brother_bone_name = f'{target_bone_name}-{(yidx2 + 1):03d}-{(bxidx):03d}'
                if brother_bone_name not in model.bones:
                    # 隣がない場合、もうひとつ前をチェック
                    continue
                else:
                    # あったら抜ける
                    right_bottom_bone_name = brother_bone_name
                    break

    if right_bottom_bone_name not in model.bones:
        right_bottom_bone_name = f'{target_bone_name}-{(yidx2 + 1):03d}-{(1):03d}'

    return org_left_top_bone_name, org_right_top_bone_name, org_left_bottom_bone_name, org_right_bottom_bone_name, \
        left_top_bone_name, right_top_bone_name, left_bottom_bone_name, right_bottom_bone_name


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
                next_xs = [v for v in indices_dict[target_x_idx]["duplicate"] if v.index not in x_idxs and v.index not in duplicate_idxs and len(indices_dict[v.index]["x"]) > 0]
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
