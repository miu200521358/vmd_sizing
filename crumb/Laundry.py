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
    max_cnt = 16

    model = PmxReader("D:\\MMD\\Blender\\Laundry\\Laundry04.pmx", is_check=False, is_sizing=False).read_data()

    vertices_xs = []
    vertices_ys = []
    vertices_zs = []
    vertices_vec = []
    for k, vs in model.vertices.items():
        for v in vs:
            vertices_vec.append(v.position.data())
            vertices_xs.append(v.position.x())
            vertices_xs.append(v.position.y())
            vertices_zs.append(v.position.z())
    
    vertices_xs = np.sort(np.unique(vertices_xs))
    vertices_ys = np.sort(np.unique(vertices_ys))
    vertices_zs = np.sort(np.unique(vertices_zs))

    max_vec = MVector3D(np.max(vertices_vec, axis=0))
    min_vec = MVector3D(np.min(vertices_vec, axis=0))
    size = (max_vec - min_vec)

    model.bones["センター"].position = MVector3D(0, max_vec.y(), 0)

    display_pole_name = "布支"
    model.display_slots[display_pole_name] = DisplaySlot(display_pole_name, display_pole_name, 0, 0)

    display_name = "布"
    model.display_slots[display_name] = DisplaySlot(display_name, display_name, 0, 0)

    bone_xs = np.append(np.arange(min_vec.x(), max_vec.x(), (size.x() / max_cnt)), max_vec.x())
    bone_ys = np.append(np.arange(max_vec.y(), min_vec.y(), -(size.y() / max_cnt)), min_vec.y())

    r_size = MVector3D(abs(bone_xs[1] - bone_xs[0]), abs(bone_ys[1] - bone_ys[0]), abs(max_vec.z() - min_vec.z()))

    # まず横にボーンを伸ばす
    for xidx in range(max_cnt + 1):
        x = bone_xs[xidx]
        pole_bone_name = f'布-{(xidx):02d}-00-00'
        parent_bone_name = "センター" if xidx == 0 else f'布-{(xidx - 1):02d}-00-00'

        pole_bone = Bone(pole_bone_name, pole_bone_name, MVector3D(x, max_vec.y(), 0), model.bones[parent_bone_name].index, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
        pole_bone.index = len(list(model.bones.keys()))

        # ボーン
        model.bones[pole_bone.name] = pole_bone
        
        # 表示枠
        model.display_slots[display_pole_name].references.append(pole_bone.index)

        for zidx, z_direction in enumerate([min_vec.z(), max_vec.z()]):
            for yi, yidx in enumerate(range(max_cnt + 1)):
                if yi == 0:
                    continue
            
                y = bone_ys[yidx]

                # もっとも近い頂点のZ値を取得
                distance = 99999
                min_distance = 99999
                min_distance_z = 0
                for k, vs in model.vertices.items():
                    for v in vs:
                        distance = v.position.distanceToPoint(MVector3D(x, y, z_direction))

                        if distance < min_distance:
                            min_distance = distance
                            min_distance_z = v.position.z()

                bone_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}'

                parent_index = pole_bone.index if yi == 1 else len(list(model.bones.keys())) - 1

                bone = Bone(bone_name, bone_name, MVector3D(x, y, min_distance_z), parent_index, 0, 0x0000 | 0x0002 | 0x0008 | 0x0010)
                bone.index = len(list(model.bones.keys()))

                # ボーン
                model.bones[bone.name] = bone
                
                # 表示枠
                model.display_slots[display_name].references.append(model.bones[bone.name].index)

    logger.info("ボーン完了")

    rigidbody_param_to = RigidBodyParam(0.5, 0.9999, 0.9999, 0, 0.5)
    rigidbody_param_from = RigidBodyParam(rigidbody_param_to.mass * ((max_cnt + 1) ** 2), 0.9, 0.9, 0, 0.5)

    # 剛体
    for xidx in range(max_cnt + 1):
        rigidbody_no_collisions = 0
        for nc in range(16):
            if nc not in [0, 13, 14]:
                rigidbody_no_collisions |= 1 << nc

        x = bone_xs[xidx]
        pole_bone_name = f'布-{(xidx):02d}-00-00'

        left_top_name = f'布-{(xidx):02d}-00-00'
        right_top_name = f'布-{(xidx + 1):02d}-00-00'

        target_poses = []
        for target_name in [left_top_name, right_top_name]:
            if target_name in model.bones:
                target_poses.append(model.bones[target_name].position.data())
        center_pos = MVector3D(np.mean(target_poses, axis=0)) + MVector3D(-r_size.x() / 2, 0, 0)
        if right_top_name not in model.bones:
            center_pos.setX(center_pos.x() + (r_size.x() / 2))

        # 剛体
        mode = 0
        rigidbody = RigidBody(model.bones[pole_bone_name].name, model.bones[pole_bone_name].english_name, model.bones[pole_bone_name].index, 14, rigidbody_no_collisions, \
                              0, MVector3D(r_size.x() / 2, r_size.y() / 2, 0.1), center_pos, MVector3D(), \
                              rigidbody_param_from.mass, rigidbody_param_from.linear_damping, rigidbody_param_from.angular_damping, \
                              rigidbody_param_from.restitution, rigidbody_param_from.friction, mode)
        rigidbody.index = len(model.rigidbodies)
        model.rigidbodies[rigidbody.name] = rigidbody

        for zidx, z_direction in enumerate([min_vec.z(), max_vec.z()]):
            
            collision_idx = 13 if zidx == 0 else 14
            rigidbody_no_collisions = 0
            for nc in range(16):
                if nc not in [0, collision_idx]:
                    rigidbody_no_collisions |= 1 << nc

            for yi, yidx in enumerate(range(max_cnt + 1)):
                if yi == 0:
                    continue

                bone_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}'
                bone = model.bones[bone_name]
                left_top_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}'
                right_top_name = f'布-{(xidx + 1):02d}-{(zidx):02d}-{(yidx):02d}'
                left_bottom_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx + 1):02d}'
                right_bottom_name = f'布-{(xidx + 1):02d}-{(zidx):02d}-{(yidx + 1):02d}'

                target_poses = []
                for target_name in [left_top_name, right_top_name, left_bottom_name, right_bottom_name]:
                    if target_name in model.bones:
                        target_poses.append(model.bones[target_name].position.data())
                center_pos = MVector3D(np.mean(target_poses, axis=0)) + MVector3D(-r_size.x() / 2, r_size.y() / 2, 0)
                if right_top_name not in model.bones:
                    center_pos.setX(center_pos.x() + (r_size.x() / 2))
                if left_bottom_name not in model.bones:
                    center_pos.setY(center_pos.y() - (r_size.y() / 2))

                # 質量：末端からの二乗
                # 減衰：根元から末端の線形補間
                # 反発・摩擦：根元一定
                mass = rigidbody_param_to.mass * ((max_cnt - yi + 1) ** 2)
                linear_damping = rigidbody_param_from.linear_damping + ((rigidbody_param_to.linear_damping - rigidbody_param_from.linear_damping) * (yi / max_cnt))
                angular_damping = rigidbody_param_from.angular_damping + ((rigidbody_param_to.angular_damping - rigidbody_param_from.angular_damping) * (yi / max_cnt))

                # 剛体
                mode = 1
                rigidbody = RigidBody(bone.name, bone.english_name, bone.index, collision_idx, rigidbody_no_collisions, \
                                      1, MVector3D(r_size.x() / 2, r_size.y() / 2, 0.1), center_pos, MVector3D(), \
                                      mass, linear_damping, angular_damping, rigidbody_param_from.restitution, rigidbody_param_from.friction, mode)
                rigidbody.index = len(model.rigidbodies)
                model.rigidbodies[rigidbody.name] = rigidbody

    logger.info("剛体完了")
        
    for xidx in range(max_cnt + 1):
        for zidx, z_direction in enumerate([min_vec.z(), max_vec.z()]):
            for yi, yidx in enumerate(range(max_cnt + 1)):
                bone_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}' if yi > 0 else f'布-{(xidx):02d}-00-00'
                vertical_joint_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx + 1):02d}'

                if vertical_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
                    joint = Joint(vertical_joint_name, vertical_joint_name, 0, model.rigidbodies[bone_name].index, model.rigidbodies[vertical_joint_name].index,
                                  model.bones[vertical_joint_name].position + MVector3D(0, r_size.y() / 2, 0), MVector3D(), MVector3D(), MVector3D(),
                                  MVector3D(math.radians(-15), math.radians(-2), math.radians(-25)),
                                  MVector3D(math.radians(135), math.radians(2), math.radians(25)), MVector3D(), MVector3D())

                    model.joints[joint.name] = joint
                else:
                    logger.debug("%s -> %s", bone_name, vertical_joint_name)

    logger.info("縦ジョイント完了")

    for xidx in range(max_cnt + 1):
        for zidx, z_direction in enumerate([min_vec.z(), max_vec.z()]):
            for yi, yidx in enumerate(range(max_cnt + 1)):
                if yi == 0:
                    continue

                bone_name = f'布-{(xidx):02d}-{(zidx):02d}-{(yidx):02d}' if yi > 0 else f'布-{(xidx):02d}-00-00'
                right_joint_name = f'布-{(xidx + 1):02d}-{(zidx):02d}-{(yidx):02d}'

                if right_joint_name in model.rigidbodies and bone_name in model.rigidbodies:
                    joint = Joint(f'{bone_name}_横', f'{bone_name}_横', 0, model.rigidbodies[bone_name].index, model.rigidbodies[right_joint_name].index,
                                  model.bones[bone_name].position + MVector3D(r_size.x() / 2, 0, 0), MVector3D(), MVector3D(), MVector3D(),
                                  MVector3D(math.radians(1), math.radians(1), math.radians(1)),
                                  MVector3D(math.radians(0), math.radians(0), math.radians(0)), MVector3D(), MVector3D())

                    model.joints[joint.name] = joint
                else:
                    logger.debug("%s -> %s", bone_name, right_joint_name)

    logger.info("横ジョイント完了")

    for k, vs in model.vertices.items():
        for v in vs:
            target_xs = {}
            target_ys = {}
            target_zs = {}

            for zi, z in enumerate([min_vec.z(), max_vec.z()]):
                if z - (r_size.z()) < v.position.z() < z + (r_size.z()):
                    target_zs[z] = zi
            for yi, y in enumerate(bone_ys):
                if y - (r_size.y()) < v.position.y() < y + (r_size.y()):
                    target_ys[y] = yi
            for xi, x in enumerate(bone_xs):
                if x - (r_size.x()) < v.position.x() < x + (r_size.x()):
                    target_xs[x] = xi
            
            r_min_vec = MVector3D(list(target_xs.keys())[0], list(target_ys.keys())[-1], list(target_zs.keys())[0])
            r_max_vec = MVector3D(list(target_xs.keys())[-1], list(target_ys.keys())[0], list(target_zs.keys())[-1])

            left_top_weight = max(0, ((r_size.x() - (v.position.x() - r_min_vec.x())) / r_size.x()) * (((v.position.y() - r_min_vec.y())) / r_size.y()))
            left_bottom_weight = max(0, ((r_size.x() - (v.position.x() - r_min_vec.x())) / r_size.x()) * (r_size.y() - (v.position.y() - r_min_vec.y())) / r_size.y())
            right_bottom_weight = max(0, (((v.position.x() - r_min_vec.x())) / r_size.x()) * (r_size.y() - (v.position.y() - r_min_vec.y())) / r_size.y())
            right_top_weight = max(0, (((v.position.x() - r_min_vec.x())) / r_size.x()) * (((v.position.y() - r_min_vec.y())) / r_size.y()))

            total_weights = np.array([left_top_weight, right_top_weight, left_bottom_weight, right_bottom_weight])
            weight_values = total_weights / total_weights.sum(axis=0, keepdims=1)

            left_top_bone = model.bones[f'布-{(0):02d}-{(0):02d}-{(0):02d}']
            right_top_bone = model.bones[f'布-{(max_cnt):02d}-{(0):02d}-{(0):02d}']
            left_bottom_bone = model.bones[f'布-{(0):02d}-{(0):02d}-{(max_cnt):02d}']
            right_bottom_bone = model.bones[f'布-{(max_cnt):02d}-{(0):02d}-{(max_cnt):02d}']
            left_top_distance = 99999
            right_top_distance = 99999
            left_bottom_distance = 99999
            right_bottom_distance = 99999
            for bone in model.bones.values():
                distance = bone.position.distanceToPoint(v.position)
                if bone.position.x() <= v.position.x() and bone.position.y() >= v.position.y() and distance < left_top_distance:
                    left_top_bone = bone
                    left_top_distance = distance
                if bone.position.x() >= v.position.x() and bone.position.y() >= v.position.y() and distance < right_top_distance:
                    right_top_bone = bone
                    right_top_distance = distance
                if bone.position.x() <= v.position.x() and bone.position.y() <= v.position.y() and distance < left_bottom_distance:
                    left_bottom_bone = bone
                    left_bottom_distance = distance
                if bone.position.x() >= v.position.x() and bone.position.y() <= v.position.y() and distance < right_bottom_distance:
                    right_bottom_bone = bone
                    right_bottom_distance = distance

            weight_names = np.array([left_top_bone.name, right_top_bone.name, left_bottom_bone.name, right_bottom_bone.name])
            target_names = weight_names[np.nonzero(weight_values)]

            if np.count_nonzero(weight_values) == 1:
                v.deform = Bdef1(model.bones[target_names[0]].index)
            elif np.count_nonzero(weight_values) == 2:
                v.deform = Bdef2(model.bones[target_names[0]].index, model.bones[target_names[1]].index, weight_values[weight_values.nonzero()][0])
            else:
                v.deform = Bdef4(left_top_bone.index, right_top_bone.index, left_bottom_bone.index, right_bottom_bone.index, \
                                 weight_values[0], weight_values[1], weight_values[2], weight_values[3])

    logger.info("ウェイト完了")
    
    model.name = "たなびく洗濯物（大）"
    model.comment = f"たなびく洗濯物\r\n制作： miu\r\n偽重力プラグイン： 千成様"

    result_dir = "D:\\MMD\\Blender\\Laundry\\たなびく洗濯物 v1.00"
    new_file_path = f"{result_dir}\\たなびく洗濯物大_v1.00.pmx"
    pmx_writer = PmxWriter()
    pmx_writer.write(model, new_file_path)

    logger.warning(f"出力終了: {new_file_path}")


if __name__ == '__main__':
    exec()
