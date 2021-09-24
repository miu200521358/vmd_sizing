# -*- coding: utf-8 -*-
#
from datetime import datetime
import sys
import pathlib
import numpy as np
import math
from numpy.core.defchararray import center
# このソースのあるディレクトリの絶対パスを取得
current_dir = pathlib.Path(__file__).resolve().parent
# モジュールのあるパスを追加
sys.path.append(str(current_dir) + '/../')
sys.path.append(str(current_dir) + '/../src/')

from mmd.PmxReader import PmxReader # noqa
from mmd.VmdReader import VmdReader # noqa
from mmd.VmdWriter import VmdWriter # noqa
from mmd.PmxWriter import PmxWriter # noqa
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint, Bdef1, Bdef2, Bdef4 # noqa
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

    for base_file_name in ["揺れる紙A4", "揺れる紙写真"]:
        for prefix, max_cnt in [("3x3", 2), ("5x5", 4), ("7x7", 6), ("9x9", 8)]:
            for physics in [None, "横一列", "縦一列", "一点", "フル"]:
                center_cnt = int(max_cnt / 2)

                model = PmxReader(f"D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Accessory\\文房具\\揺れる紙 miu\\{base_file_name}.pmx", is_check=False, is_sizing=False).read_data()

                vertices_xs = []
                vertices_zs = []
                vertices_vec = []
                for k, vs in model.vertices.items():
                    for v in vs:
                        vertices_vec.append(v.position.data())
                        vertices_xs.append(v.position.x())
                        vertices_zs.append(v.position.z())
                
                vertices_xs = np.sort(np.unique(vertices_xs))
                vertices_zs = np.sort(np.unique(vertices_zs))

                max_vec = MVector3D(np.max(vertices_vec, axis=0))
                min_vec = MVector3D(np.min(vertices_vec, axis=0))
                size = (max_vec - min_vec)

                model.bones["全ての親"].position = MVector3D(min_vec.x(), 0, max_vec.z())
                model.bones["全ての親"].index = 0

                model.bones["センター"].position = size / 2
                model.bones["センター"].index = 1

                edge_display_name = "隅"
                model.display_slots[edge_display_name] = DisplaySlot(edge_display_name, edge_display_name, 0, 0)
                
                display_name = "紙回転"
                model.display_slots[display_name] = DisplaySlot(display_name, display_name, 0, 0)

                bone_xs = np.append(np.arange(min_vec.x(), max_vec.x(), (size.x() / max_cnt)), max_vec.x())
                bone_zs = np.append(np.arange(max_vec.z(), min_vec.z(), -(size.z() / max_cnt)), min_vec.z())

                r_size = MVector3D(abs(bone_xs[1] - bone_xs[0]), 0, abs(bone_zs[1] - bone_zs[0]))

                for zidx in range(max_cnt + 1):
                    for xidx in range(max_cnt + 1):
                        x = bone_xs[xidx]
                        z = bone_zs[zidx]

                        if ((physics == "一点" and xidx in [0] and zidx in [0]) or (physics in ["横一列", "一点"] and xidx in [0, center_cnt, max_cnt] and zidx in [0]) \
                                or (physics == "縦一列" and xidx in [0] and zidx in [0, center_cnt, max_cnt])):
                            edge_bone_name = f'紙-{("左" if xidx == 0 else "右" if xidx == max_cnt else "中")}{("上" if zidx == 0 else "下" if zidx == max_cnt else "中")}'
                            edge_bone = Bone(edge_bone_name, edge_bone_name, MVector3D(x, 0, z), len(list(model.bones.keys())) - 1, 0, 0x0000 | 0x0002 | 0x0004 | 0x0008 | 0x0010)
                            edge_bone.index = len(list(model.bones.keys()))
                            model.bones[edge_bone.name] = edge_bone

                            # 表示枠
                            model.display_slots[edge_display_name].references.append(edge_bone.index)

                if physics and physics == "縦一列":
                    for xidx in range(max_cnt + 1):
                        for zidx in range(max_cnt + 1):
                            x = bone_xs[xidx]
                            z = bone_zs[zidx]
                            bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'

                            bone = Bone(bone_name, bone_name, MVector3D(x, 0, z), len(list(model.bones.keys())) - 1, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
                            bone.index = len(list(model.bones.keys()))

                            # ボーン
                            model.bones[bone.name] = bone
                            
                            # 表示枠
                            model.display_slots[display_name].references.append(model.bones[bone.name].index)
                else:
                    for zidx in range(max_cnt + 1):
                        for xidx in range(max_cnt + 1):
                            x = bone_xs[xidx]
                            z = bone_zs[zidx]
                            bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'

                            bone = Bone(bone_name, bone_name, MVector3D(x, 0, z), len(list(model.bones.keys())) - 1, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
                            bone.index = len(list(model.bones.keys()))

                            # ボーン
                            model.bones[bone.name] = bone
                            
                            # 表示枠
                            model.display_slots[display_name].references.append(model.bones[bone.name].index)

                rigidbody_no_collisions = 0
                for nc in range(16):
                    if nc not in [0, 1, 2, 3, 4, 14]:
                        rigidbody_no_collisions |= 1 << nc

                if physics:
                    if physics == "縦一列":
                        # 剛体
                        for xidx in range(max_cnt + 1):
                            for zidx in range(max_cnt + 1):
                                bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'
                                bone = model.bones[bone_name]
                                left_top_name = f'紙-{xidx:02d}-{zidx:02d}'
                                right_top_name = f'紙-{(xidx + 1):02d}-{zidx:02d}'
                                left_bottom_name = f'紙-{xidx:02d}-{(zidx + 1):02d}'
                                right_bottom_name = f'紙-{(xidx + 1):02d}-{(zidx + 1):02d}'

                                target_poses = []
                                for target_name in [left_top_name, right_top_name, left_bottom_name, right_bottom_name]:
                                    if target_name in model.bones:
                                        target_poses.append(model.bones[target_name].position.data())
                                center_pos = MVector3D(np.mean(target_poses, axis=0)) + MVector3D(-r_size.x() / 2, 0, r_size.z() / 2)
                                if right_top_name not in model.bones:
                                    center_pos.setX(center_pos.x() + (r_size.x() / 2))
                                if left_bottom_name not in model.bones:
                                    center_pos.setZ(center_pos.z() - (r_size.z() / 2))

                                # 剛体
                                mode = 1
                                if (physics in "横一列" and zidx == 0) or (physics == "縦一列" and xidx == 0) or (physics == "一点" and zidx == 0 and xidx == 0):
                                    mode = 0
                                rigidbody = RigidBody(bone.name, bone.english_name, bone.index, 14, rigidbody_no_collisions, \
                                                      1, MVector3D(abs(r_size.x() / 2), 0.1, r_size.z() / 2), center_pos, MVector3D(), \
                                                      0.5, 0.5, 0.5, 0, 1, mode)
                                rigidbody.index = len(model.rigidbodies)
                                model.rigidbodies[rigidbody.name] = rigidbody
                    else:
                        # 剛体
                        for zidx in range(max_cnt + 1):
                            for xidx in range(max_cnt + 1):
                                bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'
                                bone = model.bones[bone_name]
                                left_top_name = f'紙-{xidx:02d}-{zidx:02d}'
                                right_top_name = f'紙-{(xidx + 1):02d}-{zidx:02d}'
                                left_bottom_name = f'紙-{xidx:02d}-{(zidx + 1):02d}'
                                right_bottom_name = f'紙-{(xidx + 1):02d}-{(zidx + 1):02d}'

                                target_poses = []
                                for target_name in [left_top_name, right_top_name, left_bottom_name, right_bottom_name]:
                                    if target_name in model.bones:
                                        target_poses.append(model.bones[target_name].position.data())
                                center_pos = MVector3D(np.mean(target_poses, axis=0)) + MVector3D(-r_size.x() / 2, 0, r_size.z() / 2)
                                if right_top_name not in model.bones:
                                    center_pos.setX(center_pos.x() + (r_size.x() / 2))
                                if left_bottom_name not in model.bones:
                                    center_pos.setZ(center_pos.z() - (r_size.z() / 2))

                                # 剛体
                                mode = 1
                                if (physics in "横一列" and zidx == 0) or (physics == "縦一列" and xidx == 0) or (physics == "一点" and zidx == 0 and xidx == 0):
                                    mode = 0
                                rigidbody = RigidBody(bone.name, bone.english_name, bone.index, 14, rigidbody_no_collisions, \
                                                      1, MVector3D(abs(r_size.x() / 2), 0.1, r_size.z() / 2), center_pos, MVector3D(), \
                                                      0.5, 0.5, 0.5, 0, 1, mode)
                                rigidbody.index = len(model.rigidbodies)
                                model.rigidbodies[rigidbody.name] = rigidbody
                        
                    if physics in ["横一列", "一点", "フル"]:
                        for zidx in range(max_cnt + 1):
                            for xidx in range(max_cnt + 1):
                                vertical_joint_name = f'紙-{(xidx):02d}-{(zidx + 1):02d}'
                                bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'

                                if vertical_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
                                    joint = Joint(bone_name, bone_name, 0, model.rigidbodies[bone_name].index, model.rigidbodies[vertical_joint_name].index,
                                                  model.bones[bone_name].position - MVector3D(0, 0, r_size.z() / 2), MVector3D(), MVector3D(), MVector3D(),
                                                  MVector3D(math.radians(-(max_cnt * 5)), math.radians(0), math.radians(0)),
                                                  MVector3D(math.radians((max_cnt * 3)), math.radians(0), math.radians(0)), MVector3D(100, 100, 100), MVector3D(100, 100, 100))

                                    model.joints[joint.name] = joint

                        for zidx in range(max_cnt + 1):
                            for xidx in range(max_cnt + 1):
                                right_bottom_joint_name = f'紙-{(xidx + 1):02d}-{(zidx + 1):02d}'
                                bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'
                                if right_bottom_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
                                    joint = Joint(f'{bone_name}_右', f'{bone_name}_右', 0, model.rigidbodies[bone_name].index, model.rigidbodies[right_bottom_joint_name].index,
                                                  model.bones[bone_name].position + MVector3D(r_size.x() / 2, 0, 0), MVector3D(), MVector3D(), MVector3D(),
                                                  MVector3D(math.radians(-(max_cnt * 5)), math.radians(0), math.radians(0)),
                                                  MVector3D(math.radians((max_cnt * 3)), math.radians(0), math.radians(0)), MVector3D(100, 100, 100), MVector3D(100, 100, 100))
                                    model.joints[joint.name] = joint

                        for zidx in range(max_cnt + 1):
                            for xidx in range(1, max_cnt + 1):
                                left_bottom_joint_name = f'紙-{(xidx - 1):02d}-{(zidx + 1):02d}'
                                bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'
                                if left_bottom_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
                                    joint = Joint(f'{bone_name}_左', f'{bone_name}_左', 0, model.rigidbodies[bone_name].index, model.rigidbodies[left_bottom_joint_name].index,
                                                  model.bones[bone_name].position + MVector3D(r_size.x() / 2, 0, 0), MVector3D(), MVector3D(), MVector3D(),
                                                  MVector3D(math.radians(-(max_cnt * 5)), math.radians(0), math.radians(0)),
                                                  MVector3D(math.radians((max_cnt * 3)), math.radians(0), math.radians(0)), MVector3D(100, 100, 100), MVector3D(100, 100, 100))
                                    model.joints[joint.name] = joint

                        start_y = 1 if physics == "横一列" else 0
                        for zidx in range(start_y, max_cnt + 1):
                            for xidx in range(max_cnt + 1):
                                horizonal_joint_name = f'紙-{(xidx + 1):02d}-{(zidx):02d}'
                                bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'
                                if horizonal_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
                                    joint = Joint(f'{bone_name}_横', f'{bone_name}_横', 0, model.rigidbodies[bone_name].index, model.rigidbodies[horizonal_joint_name].index,
                                                  model.bones[bone_name].position + MVector3D(r_size.x() / 2, 0, 0), MVector3D(), MVector3D(), MVector3D(),
                                                  MVector3D(), MVector3D(), MVector3D(0, 0, 0), MVector3D(0, 0, 0))
                                    model.joints[joint.name] = joint

                    elif physics in ["縦一列"]:
                        for xidx in range(max_cnt + 1):
                            for zidx in range(max_cnt + 1):
                                vertical_joint_name = f'紙-{(xidx + 1):02d}-{(zidx):02d}'
                                bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'

                                if vertical_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
                                    joint = Joint(bone_name, bone_name, 0, model.rigidbodies[bone_name].index, model.rigidbodies[vertical_joint_name].index,
                                                  model.bones[bone_name].position - MVector3D(0, 0, r_size.z() / 2), MVector3D(), MVector3D(), MVector3D(),
                                                  MVector3D(math.radians(0), math.radians(-(max_cnt * 5)), math.radians(0)),
                                                  MVector3D(math.radians(0), math.radians((max_cnt * 3)), math.radians(0)), MVector3D(100, 100, 100), MVector3D(100, 100, 100))
                                    model.joints[joint.name] = joint

                        for xidx in range(1, max_cnt + 1):
                            for zidx in range(max_cnt + 1):
                                horizonal_joint_name = f'紙-{(xidx):02d}-{(zidx + 1):02d}'
                                bone_name = f'紙-{(xidx):02d}-{(zidx):02d}'
                                if horizonal_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
                                    joint = Joint(f'{bone_name}_横', f'{bone_name}_横', 0, model.rigidbodies[bone_name].index, model.rigidbodies[horizonal_joint_name].index,
                                                  model.bones[bone_name].position - MVector3D(0, 0, r_size.z() / 2), MVector3D(), MVector3D(), MVector3D(),
                                                  MVector3D(), MVector3D(), MVector3D(0, 0, 0), MVector3D(0, 0, 0))
                                    model.joints[joint.name] = joint

                for xidx, (k, vs) in enumerate(model.vertices.items()):
                    for zidx, v in enumerate(vs):
                        
                        target_xs = {}
                        target_zs = {}
                        for yi, y in enumerate(bone_zs):
                            if y - (r_size.z()) < v.position.z() < y + (r_size.z()):
                                target_zs[y] = yi
                        for xi, x in enumerate(bone_xs):
                            if x - (r_size.x()) < v.position.x() < x + (r_size.x()):
                                target_xs[x] = xi
                        
                        r_min_vec = MVector3D(list(target_xs.keys())[0], 0, list(target_zs.keys())[-1])
                        r_max_vec = MVector3D(list(target_xs.keys())[-1], 0, list(target_zs.keys())[0])

                        left_top_weight = max(0, ((r_size.x() - (v.position.x() - r_min_vec.x())) / r_size.x()) * (((v.position.z() - r_min_vec.z())) / r_size.z()))
                        left_bottom_weight = max(0, ((r_size.x() - (v.position.x() - r_min_vec.x())) / r_size.x()) * (r_size.z() - (v.position.z() - r_min_vec.z())) / r_size.z())
                        right_bottom_weight = max(0, (((v.position.x() - r_min_vec.x())) / r_size.x()) * (r_size.z() - (v.position.z() - r_min_vec.z())) / r_size.z())
                        right_top_weight = max(0, (((v.position.x() - r_min_vec.x())) / r_size.x()) * (((v.position.z() - r_min_vec.z())) / r_size.z()))

                        total_weights = np.array([left_top_weight, right_top_weight, left_bottom_weight, right_bottom_weight])
                        weight_values = total_weights / total_weights.sum(axis=0, keepdims=1)

                        left_top_name = f'紙-{(target_xs[r_min_vec.x()]):02d}-{(target_zs[r_max_vec.z()]):02d}'
                        right_top_name = f'紙-{(target_xs[r_max_vec.x()]):02d}-{(target_zs[r_max_vec.z()]):02d}'
                        left_bottom_name = f'紙-{(target_xs[r_min_vec.x()]):02d}-{(target_zs[r_min_vec.z()]):02d}'
                        right_bottom_name = f'紙-{(target_xs[r_max_vec.x()]):02d}-{(target_zs[r_min_vec.z()]):02d}'

                        weight_names = np.array([left_top_name, right_top_name, left_bottom_name, right_bottom_name])
                        target_names = weight_names[np.nonzero(weight_values)]

                        if np.count_nonzero(weight_values) == 1:
                            v.deform = Bdef1(model.bones[target_names[0]].index)
                        elif np.count_nonzero(weight_values) == 2:
                            v.deform = Bdef2(model.bones[target_names[0]].index, model.bones[target_names[1]].index, weight_values[weight_values.nonzero()][0])
                        else:
                            v.deform = Bdef4(model.bones[left_top_name].index, model.bones[right_top_name].index, model.bones[left_bottom_name].index, model.bones[right_bottom_name].index, \
                                             weight_values[0], weight_values[1], weight_values[2], weight_values[3])
                
                model.name = f"{base_file_name}_{prefix}_{(physics if physics else '物理なし')}_v1.00"
                model.comment = f"{base_file_name}: {prefix} {(physics if physics else '物理なし')}\r\nby miu"

                result_dir = "D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Accessory\\文房具\\揺れる紙 miu\\揺れる紙 v1.00"
                new_file_path = f"{result_dir}\\{base_file_name}_{prefix}_{(physics if physics else '物理なし')}_v1.00.pmx"
                pmx_writer = PmxWriter()
                pmx_writer.write(model, new_file_path)

                logger.warning(f"出力終了: {new_file_path}")

if __name__ == '__main__':
    exec()
