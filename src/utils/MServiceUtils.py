# -*- coding: utf-8 -*-
#

import copy
import math
from collections import OrderedDict

from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions, MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


# グローバル位置算出
def calc_global_pos_dic(model: PmxModel, links: BoneLinks, motion: VmdMotion, fno: int):
    trans_vs = calc_relative_position(model, links, motion, fno)
    add_qs = calc_relative_rotation(model, links, motion, fno)

    # 行列
    matrixs = [MMatrix4x4() for i in range(links.size())]

    for n, (lname, v, q) in enumerate(zip(links.all().keys(), trans_vs, add_qs)):
        # 行列を生成
        matrixs[n] = MMatrix4x4()
        # 初期化
        matrixs[n].setToIdentity()
        # 移動
        matrixs[n].translate(v)
        # 回転
        matrixs[n].rotate(q)

    total_mat = [MMatrix4x4() for i in range(links.size())]
    global_3ds_dic = OrderedDict()

    for n, (lname, v) in enumerate(zip(links.all().keys(), trans_vs)):
        for m in range(n):
            # 最後のひとつ手前までループ
            if m == 0:
                # 0番目の位置を初期値とする
                total_mat[n] = copy.deepcopy(matrixs[0])
            else:
                # 自分より前の行列結果を掛け算する
                total_mat[n] *= copy.deepcopy(matrixs[m])
        
        # 自分は、位置だけ掛ける
        global_3ds_dic[lname] = total_mat[n] * trans_vs[n]

    return global_3ds_dic


# 指定された方向に向いた場合の位置情報を返す
def calc_global_pos_dic_by_direction(direction_qq: MQuaternion, target_pos_3ds_dic: OrderedDict):
    direction_pos_dic = OrderedDict()

    for bone_name, target_pos in target_pos_3ds_dic.items():
        mat = MMatrix4x4()
        mat.rotate(direction_qq)

        direction_pos_dic[bone_name] = mat.mapVector(target_pos)
    
    return direction_pos_dic


# 各ボーンの相対位置情報
def calc_relative_position(model: PmxModel, links: BoneLinks, motion: VmdMotion, fno: int):
    trans_vs = []

    for link_idx, link_bone_name in enumerate(links.all()):
        link_bone = links.get(link_bone_name)

        # キー情報を取得
        fill_bf = motion.calc_bone_by_interpolation(link_bone.name, fno)

        # 位置
        if link_idx == 0:
            # 一番親は、グローバル座標を考慮
            trans_vs.append(link_bone.position + fill_bf.position)
        else:
            # 位置：自身から親の位置を引いた相対位置
            trans_vs.append(link_bone.position + fill_bf.position - links.get(link_bone_name, offset=1).position)

    return trans_vs


# 各ボーンの相対回転情報
def calc_relative_rotation(model: PmxModel, links: BoneLinks, motion: VmdMotion, fno: int):
    add_qs = []

    for link_idx, link_bone_name in enumerate(links.all()):
        link_bone = links.get(link_bone_name)

        # キー情報を取得
        fill_bf = motion.calc_bone_by_interpolation(link_bone.name, fno)
        
        # 回転量
        rot = fill_bf.rotation

        if link_bone.fixed_axis != MVector3D():
            # 回転角度を求める
            if rot == MQuaternion():
                # 回転なしの場合、角度なし
                degree = 0
            else:
                # 回転補正
                if "右" in link_bone.name and rot.x() > 0 and link_bone.fixed_axis.x() <= 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                elif "左" in link_bone.name and rot.x() < 0 and link_bone.fixed_axis.x() >= 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                # 回転補正（コロン式ミクさん等軸反転パターン）
                elif "右" in link_bone.name and rot.x() < 0 and link_bone.fixed_axis.x() > 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                elif "左" in link_bone.name and rot.x() > 0 and link_bone.fixed_axis.x() < 0:
                    rot.setX(rot.x() * -1)
                    rot.setScalar(rot.scalar() * -1)
                
                rot.normalize()

                degree = math.degrees(2 * math.acos(min(1, max(0, rot.scalar()))))
            
            # 軸固定の場合、回転を制限する
            rot = MQuaternion.fromAxisAndAngle(link_bone.fixed_axis, degree)
        
        if link_bone.getExternalRotationFlag() and link_bone.effect_index in model.bone_indexes:
            # 該当する付与親の回転を取得する
            effect_bf = motion.calc_bone_by_interpolation(model.bone_indexes[link_bone.effect_index], fno)

            # 自身の回転量に付与親の回転量を付与率を加味して付与する
            rot = rot * effect_bf.rotation
            rot.setX(rot.x() * link_bone.effect_factor)
            rot.setY(rot.y() * link_bone.effect_factor)
            rot.setZ(rot.z() * link_bone.effect_factor)

        add_qs.append(rot)

    return add_qs


# 指定されたボーンまでの回転量
def calc_direction_qq(model: PmxModel, links: BoneLinks, motion: VmdMotion, fno: int):
    add_qs = calc_relative_rotation(model, links, motion, fno)

    total_qq = MQuaternion()
    for qq in add_qs:
        total_qq *= qq

    return total_qq


# 上半身のスタンスの違い
def calc_upper_stance_diff(model: PmxModel, from_bone_name: str, to_bone_name=None):
    return calc_stance_diff(model, from_bone_name, to_bone_name, MVector3D(0, 1, 0))


# 腕のスタンスの違い
def calc_arm_stance_diff(model: PmxModel, from_bone_name: str, to_bone_name=None):
    default_pos = MVector3D(1, 0, 0) if "左" in from_bone_name else MVector3D(-1, 0, 0)
    return calc_stance_diff(model, from_bone_name, to_bone_name, default_pos)


# 指定ボーンのスタンスの違い
def calc_stance_diff(model: PmxModel, from_bone_name: str, to_bone_name: str, default_pos: MVector3D):
    from_pos = MVector3D()
    to_pos = MVector3D()

    if from_bone_name in model.bones:
        fv = model.bones[from_bone_name]
        from_pos = fv.position
        
        if to_bone_name in model.bones:
            # TOが指定されている場合、ボーン位置を保持
            to_pos = model.bones[to_bone_name].position
        else:
            # TOの明示が無い場合、表示先からボーン位置取得
            if fv.tail_position != MVector3D():
                # 表示先が相対パスの場合、保持
                to_pos = from_pos + fv.tail_position
            elif fv.tail_index >= 0:
                # 表示先がボーンの場合、ボーン位置保持
                to_pos = model.bones[model.bone_indexes[fv.tail_index]].position
            else:
                # ここまで来たらデフォルト加算
                to_pos = from_pos + default_pos

    from_qq = MQuaternion()
    if from_pos != MVector3D() and to_pos != MVector3D():
        logger.test("from_pos: %s", from_pos)
        logger.test("to_pos: %s", to_pos)

        diff_pos = to_pos - from_pos
        diff_pos.normalize()
        logger.test("diff_pos: %s", diff_pos)

        from_qq = MQuaternion.rotationTo(default_pos, diff_pos)
        logger.test("[z] from_bone_name: %s, from_qq: %s", from_bone_name, from_qq.toEulerAngles())

    return diff_pos, from_qq


# 足IKに基づく身体比率
def calc_leg_ik_ratio(data_set: MOptionsDataSet):
    target_bones = ["左足", "左ひざ", "左足首", "センター"]

    if set(target_bones).issubset(data_set.org_model_data.bones) and set(target_bones).issubset(data_set.rep_model_data.bones):
        # XZ比率(足の長さ)
        org_leg_length = ((data_set.org_model_data.bones["左足首"].position - data_set.org_model_data.bones["左ひざ"].position) \
                          + (data_set.org_model_data.bones["左ひざ"].position - data_set.org_model_data.bones["左足"].position)).length()
        rep_leg_length = ((data_set.rep_model_data.bones["左足首"].position - data_set.rep_model_data.bones["左ひざ"].position) \
                          + (data_set.rep_model_data.bones["左ひざ"].position - data_set.rep_model_data.bones["左足"].position)).length()
        logger.test("xz_ratio rep_leg_length: %s, org_leg_length: %s", rep_leg_length, org_leg_length)
        xz_ratio = 1 if org_leg_length == 0 else (rep_leg_length / org_leg_length)

        # Y比率(股下のY差)
        rep_leg_length = (data_set.rep_model_data.bones["左足首"].position - data_set.rep_model_data.bones["左足"].position).y()
        org_leg_length = (data_set.org_model_data.bones["左足首"].position - data_set.org_model_data.bones["左足"].position).y()
        logger.test("y_ratio rep_leg_length: %s, org_leg_length: %s", rep_leg_length, org_leg_length)
        y_ratio = 1 if org_leg_length == 0 else (rep_leg_length / org_leg_length)

        return xz_ratio, y_ratio
    
    logger.warning("「左足」「左ひざ」「左足首」「センター」のいずれかのボーンが不足しているため、足の長さの比率が測れませんでした。", decoration=MLogger.DECORATION_IN_BOX)

    return 1, 1


