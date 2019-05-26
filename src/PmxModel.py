# -*- coding: utf-8 -*-
#

import logging
import copy
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QColor

logger = logging.getLogger("__main__").getChild(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class PmxModel():
    def __init__(self):
        self.name = ''
        self.english_name = ''
        self.comment = ''
        self.english_comment = ''
        # 頂点データ
        self.vertices = []
        # 面データ
        self.indices = []
        # テクスチャデータ
        self.textures = []
        # 材質データ
        self.materials = {}
        # ボーンデータ
        self.bones = {}
        # ボーンINDEXデータ
        self.bone_indexes = {}
        # モーフデータ
        self.morphs = {}
        # 表示枠データ
        self.display_slots = {}
        # 剛体データ
        self.rigidbodies = {}
        # ジョイントデータ
        self.joints = {}

    # 上半身の頂点を取得する
    def get_upper_vertices(self, head_links):
        upper_vertices = []

        min_upper_y = 99999
        for l in head_links:
            # if l.name == "首":
            #     min_upper_y = l.position.y()
            #     break
            if l.position.y() < min_upper_y and l.name not in ["センター", "グルーブ"]:
                min_upper_y = l.position.y()
        
        for v in self.vertices:
            for l in head_links:
                if v.deform.index0 == l.index and v.position.y() > min_upper_y:
                    # 上半身系のボーンにウェイトが乗っていて、かつウェイトボーンのY位置より上の場合、頂点追加
                    upper_vertices.append(v)

                    break

        return upper_vertices

    def create_ik_link_2_top(self, start_bone, ik_links):
        if start_bone not in self.bones or start_bone == "全ての親":
            # 開始ボーン名がなければ終了
            # すべての親も見ない。
            return
        
        # 自分をリンクに登録
        ik_links.append( self.bones[start_bone] )
        
        if self.bones[start_bone].parent_index not in self.bone_indexes:
            # 親ボーンがボーンインデックスリストになければ終了
            return

        # 親をたどる
        self.create_ik_link_2_top(self.bone_indexes[self.bones[start_bone].parent_index], ik_links )    

    # 頂点構造 ----------------------------
    class Vertex():
        def __init__(self, position, normal, uv, extended_uvs, deform, edge_factor):
            self.position = position
            self.normal = normal
            self.uv = uv
            self.extended_uvs = extended_uvs or []
            self.deform = deform
            self.edge_factor = edge_factor
            
        def __str__(self):
            return "<Vertex position:{0}, normal:{1}, uv:{2}, extended_uv: {3}, deform:{4}, edge:{5}".format(
                    self.position, self.normal, self.uv, len(self.extended_uvs), self.deform, self.edge_factor
        )

        def is_deform_index(self, target_idx):
            if type(self.deform) is PmxModel.Bdef1:
                return self.deform.index0 == target_idx
            elif type(self.deform) is PmxModel.Bdef2:
                return self.deform.index0 == target_idx or self.deform.index1 == target_idx
            elif type(self.deform) is PmxModel.Bdef4:
                return self.deform.index0 == target_idx or self.deform.index1 == target_idx \
                    or self.deform.index2 == target_idx or self.deform.index3 == target_idx
            elif type(self.deform) is PmxModel.Sdef:
                return self.deform.index0 == target_idx or self.deform.index1 == target_idx
            elif type(self.deform) is PmxModel.Qdef:
                return self.deform.index0 == target_idx or self.deform.index1 == target_idx

            return False
        
        # 最もウェイトが乗っているボーンINDEX
        def get_max_deform_index(self, head_links_indexes):
            if type(self.deform) is PmxModel.Bdef2 or type(self.deform) is PmxModel.Sdef or type(self.deform) is PmxModel.Qdef:
                if self.deform.weight0 >= 0.5 and self.deform.index0 in head_links_indexes.keys():
                    return self.deform.index0
                else:
                    if self.deform.index1 in head_links_indexes.keys():
                        return self.deform.index1
                    else:
                        return self.deform.index0

            elif type(self.deform) is PmxModel.Bdef4:
                
                # 上半身系INDEXにウェイトが乗っているボーンのみ対象
                target_weights = []
                if self.deform.index0 in head_links_indexes.keys():
                    target_weights.append(self.deform.weight0)
                if self.deform.index1 in head_links_indexes.keys():
                    target_weights.append(self.deform.weight1)
                if self.deform.index2 in head_links_indexes.keys():
                    target_weights.append(self.deform.weight2)
                if self.deform.index3 in head_links_indexes.keys():
                    target_weights.append(self.deform.weight3)
                        
                max_weight = max(target_weights)

                if max_weight == self.deform.weight1:
                    return self.deform.index1
                elif max_weight == self.deform.weight2:
                    return self.deform.index2
                elif max_weight == self.deform.weight3:
                    return self.deform.index3
                else:
                    return self.deform.index0

            return self.deform.index0
            
    class Bdef1():
        def __init__(self, index0):
            self.index0 = index0
            
        def __str__(self):
            return "<Bdef1 {0}>".format(self.index0)

    class Bdef2():
        def __init__(self, index0, index1, weight0):
            self.index0 = index0
            self.index1 = index1
            self.weight0 = weight0
            
        def __str__(self):
            return "<Bdef2 {0}, {1}, {2}>".format(self.index0, self.index1, self.weight0)

    class Bdef4():
        def __init__(self, index0, index1, index2, index3, weight0, weight1, weight2, weight3):
            self.index0 = index0
            self.index1 = index1
            self.index2 = index2
            self.index3 = index3
            self.weight0 = weight0
            self.weight1 = weight1
            self.weight2 = weight2
            self.weight3 = weight3
            
        def __str__(self):
            return "<Bdef4 {0}:{1}, {2}:{3}, {4}:{5}, {6}:{7}>".format(
                    self.index0, self.index1, self.index2, self.index3,
                    self.weight0, self.weight1, self.weight2, self.weight3)
            
    class Sdef():
        def __init__(self, index0, index1, weight0, sdef_c, sdef_r0, sdef_r1):
            self.index0 = index0
            self.index1 = index1
            self.weight0 = weight0
            self.sdef_c = sdef_c
            self.sdef_r0 = sdef_r0
            self.sdef_r1 = sdef_r1        
            
        def __str__(self):
            return "<Sdef {0}, {1}, {2}, {3} {4} {5}>".format(
                    self.index0, self.index1, self.weight0, 
                    self.sdef_c, self.sdef_r0, self.sdef_r1)
     
    class Qdef():
        def __init__(self, index0, index1, weight0, sdef_c, sdef_r0, sdef_r1):
            self.index0 = index0
            self.index1 = index1
            self.weight0 = weight0
            self.sdef_c = sdef_c
            self.sdef_r0 = sdef_r0
            self.sdef_r1 = sdef_r1        
            
        def __str__(self):
            return "<Sdef {0}, {1}, {2}, {3} {4} {5}>".format(
                    self.index0, self.index1, self.weight0, 
                    self.sdef_c, self.sdef_r0, self.sdef_r1)
    
    # 材質構造-----------------------
    
    class Material():
        def __init__(self,
                name,
                english_name,
                diffuse_color,
                alpha,
                specular_factor,
                specular_color,
                ambient_color,
                flag,
                edge_color,
                edge_size,
                texture_index,
                sphere_texture_index,
                sphere_mode,
                toon_sharing_flag,
                toon_texture_index=0,
                comment="",
                vertex_count=0,
                ):
            self.name=name
            self.english_name=english_name
            self.diffuse_color=diffuse_color
            self.alpha=alpha
            self.specular_color=specular_color
            self.specular_factor=specular_factor
            self.ambient_color=ambient_color
            self.flag=flag
            self.edge_color=edge_color
            self.edge_size=edge_size
            self.texture_index=texture_index
            self.sphere_texture_index=sphere_texture_index
            self.sphere_mode=sphere_mode
            self.toon_sharing_flag=toon_sharing_flag
            self.toon_texture_index=toon_texture_index
            self.comment=comment
            self.vertex_count=vertex_count

        def __str__(self):
            return "<Material name:{0}, english_name:{1}, diffuse_color:{2}, alpha:{3}, specular_color:{4}, " \
                    "ambient_color: {5}, flag: {6}, edge_color: {7}, edge_size: {8}, texture_index: {9}, " \
                    "sphere_texture_index: {10}, sphere_mode: {11}, toon_sharing_flag: {12}, " \
                    "toon_texture_index: {13}, comment: {14}, vertex_count: {15}".format(
                        self.name, self.english_name, self.diffuse_color, self.alpha, self.specular_color,
                        self.ambient_color, self.flag, self.edge_color, self.edge_size, self.texture_index,
                        self.sphere_texture_index, self.sphere_mode, self.toon_sharing_flag,
                        self.toon_texture_index, self.comment, self.vertex_count
                    )
        
    # ボーン構造-----------------------
    
    class Bone():
        def __init__(self,
                name,
                english_name,
                position,
                parent_index,
                layer,
                flag,
                tail_position=None,
                tail_index=-1,
                effect_index=-1,
                effect_factor=0.0,
                fixed_axis=None,
                local_x_vector=None,
                local_z_vector=None,
                external_key=-1,
                ik=None
                ):
            self.name=name
            self.english_name=english_name
            self.position=position
            self.parent_index=parent_index
            self.layer=layer
            self.flag=flag
            self.tail_position=tail_position or QVector3D()
            self.tail_index=tail_index
            self.effect_index=effect_index
            self.effect_factor=effect_factor
            self.fixed_axis=fixed_axis or QVector3D()
            self.local_x_vector=local_x_vector or QVector3D()
            self.local_z_vector=local_z_vector or QVector3D()
            self.external_key=external_key
            self.ik=ik
            self.index=-1

            # 親ボーンからの長さ(計算して求める）
            self.len = 0
            
            self.BONEFLAG_TAILPOS_IS_BONE=0x0001
            self.BONEFLAG_CAN_ROTATE=0x0002
            self.BONEFLAG_CAN_TRANSLATE=0x0004
            self.BONEFLAG_IS_VISIBLE=0x0008
            self.BONEFLAG_CAN_MANIPULATE=0x0010
            self.BONEFLAG_IS_IK=0x0020
            self.BONEFLAG_IS_EXTERNAL_ROTATION=0x0100
            self.BONEFLAG_IS_EXTERNAL_TRANSLATION=0x0200
            self.BONEFLAG_HAS_FIXED_AXIS=0x0400
            self.BONEFLAG_HAS_LOCAL_COORDINATE=0x0800
            self.BONEFLAG_IS_AFTER_PHYSICS_DEFORM=0x1000
            self.BONEFLAG_IS_EXTERNAL_PARENT_DEFORM=0x2000

        def hasFlag(self, flag):
            return (self.flag & flag)!=0

        def setFlag(self, flag, enable):
            if enable:
                self.flag |= flag
            else:
                self.flag &= ~flag

        def getConnectionFlag(self):
            return self.hasFlag(self.BONEFLAG_TAILPOS_IS_BONE)

        def getRotatable(self):
            return self.hasFlag(self.BONEFLAG_CAN_ROTATE)

        def getTranslatable(self):
            return self.hasFlag(self.BONEFLAG_CAN_TRANSLATE)

        def getVisibleFlag(self):
            return self.hasFlag(self.BONEFLAG_IS_VISIBLE)

        def getManipulatable(self):
            return self.hasFlag(self.BONEFLAG_CAN_MANIPULATE)

        def getIkFlag(self):
            return self.hasFlag(self.BONEFLAG_IS_IK)

        def getExternalRotationFlag(self):
            return self.hasFlag(self.BONEFLAG_IS_EXTERNAL_ROTATION)

        def getExternalTranslationFlag(self):
            return self.hasFlag(self.BONEFLAG_IS_EXTERNAL_TRANSLATION)

        def getFixedAxisFlag(self):
            return self.hasFlag(self.BONEFLAG_HAS_FIXED_AXIS)

        def getLocalCoordinateFlag(self):
            return self.hasFlag(self.BONEFLAG_HAS_LOCAL_COORDINATE)

        def getAfterPhysicsDeformFlag(self):
            return self.hasFlag(self.BONEFLAG_IS_AFTER_PHYSICS_DEFORM)

        def getExternalParentDeformFlag(self):
            return self.hasFlag(self.BONEFLAG_IS_EXTERNAL_PARENT_DEFORM)

        def __str__(self):
            return "<Bone name:{0}, english_name:{1}, position:{2}, parent_index:{3}, layer:{4}, " \
                    "flag: {5}, tail_position: {6}, tail_index: {7}, effect_index: {8}, effect_factor: {9}, " \
                    "fixed_axis: {10}, local_x_vector: {11}, local_z_vector: {12}, " \
                    "external_key: {13}, ik: {14}, index: {15}".format(
                        self.name, self.english_name, self.position, self.parent_index, self.layer,
                        self.flag, self.tail_position, self.tail_index, self.effect_index, self.effect_factor,
                        self.fixed_axis, self.local_x_vector, self.local_z_vector,
                        self.external_key, self.ik, self.index
                    )

    class Ik():
        def __init__(self, target_index, loop, limit_radian, link=None):
            self.target_index=target_index
            self.loop=loop
            self.limit_radian=limit_radian
            self.link=link or []

        def __str__(self):
            return "<Ik target_index:{0}, loop:{1}, limit_radian:{2}, link:{3}".format(
                        self.target_index, self.loop, self.limit_radian, self.link
                    )
            
    class IkLink():

        def __init__(self, bone_index, limit_angle, limit_min=None, limit_max=None):
            self.bone_index=bone_index
            self.limit_angle=limit_angle
            self.limit_min=limit_min or QVector3D()
            self.limit_max=limit_max or QVector3D()

        def __str__(self):
            return "<IkLink bone_index:{0}, limit_angle:{1}, limit_min:{2}, limit_max:{3}".format(
                        self.bone_index, self.limit_angle, self.limit_min, self.limit_max
                    )
            
        
    # モーフ構造-----------------------
    
    class Morph():
        def __init__(self, name, english_name, panel, morph_type, offsets=None):
            self.name=name
            self.english_name=english_name
            self.panel=panel
            self.morph_type=morph_type
            self.offsets=offsets or []

        def __str__(self):
            return "<Morph name:{0}, english_name:{1}, panel:{2}, morph_type:{3}, offsets(len): {4}".format(
                        self.name, self.english_name, self.panel, self.morph_type, len(self.offsets)
                    )
            
    class GroupMorphData():
        def __init__(self, morph_index, value):
            self.morph_index=morph_index
            self.value=value

    class VertexMorphOffset():
        def __init__(self, vertex_index, position_offset):
            self.vertex_index=vertex_index
            self.position_offset=position_offset

    class BoneMorphData():
        def __init__(self, bone_index, position, rotation):
            self.bone_index=bone_index
            self.position=position
            self.rotation=rotation

    class UVMorphData():
        def __init__(self, vertex_index, uv):
            self.vertex_index=vertex_index
            self.uv=uv

    class MaterialMorphData():
        def __init__(self, material_index, calc_mode, 
                diffuse, specular, specular_factor,
                ambient, edge_color, edge_size, 
                texture_factor, sphere_texture_factor, toon_texture_factor):
            self.material_index=material_index
            self.calc_mode=calc_mode
            self.diffuse=diffuse
            self.specular=specular
            self.specular_factor=specular_factor
            self.ambient=ambient
            self.edge_color=edge_color
            self.edge_size=edge_size
            self.texture_factor=texture_factor
            self.sphere_texture_factor=sphere_texture_factor
            self.toon_texture_factor=toon_texture_factor

    # 表示枠構造-----------------------

    class DisplaySlot():
        def __init__(self, name, english_name, special_flag, references=None):
            self.name=name
            self.english_name=english_name
            self.special_flag=special_flag
            self.references=references or []

        def __str__(self):
            return "<DisplaySlots name:{0}, english_name:{1}, special_flag:{2}, references(len):{3}".format(
                        self.name, self.english_name, self.special_flag, len(self.references)
                    )

    # 剛体構造-----------------------

    class RigidBody():        
        def __init__(self,
                name,
                english_name,
                bone_index,
                collision_group,
                no_collision_group,
                shape_type,
                shape_size,
                shape_position,
                shape_rotation,
                mass,
                linear_damping,
                angular_damping,
                restitution,
                friction,
                mode
                ):
            self.name=name
            self.english_name=english_name
            self.bone_index=bone_index
            self.collision_group=collision_group
            self.no_collision_group=no_collision_group
            self.shape_type=shape_type
            self.shape_size=shape_size
            self.shape_position=shape_position
            self.shape_rotation=shape_rotation
            self.param=PmxModel.RigidBodyParam(mass,
                    linear_damping, angular_damping,
                    restitution, friction)
            self.mode=mode

            self.SHAPE_SPHERE=0
            self.SHAPE_BOX=1
            self.SHAPE_CAPSULE=2

        def __str__(self):
            return "<RigidBody name:{0}, english_name:{1}, bone_index:{2}, collision_group:{3}, no_collision_group:{4}, " \
                    "shape_type: {5}, shape_size: {6}, shape_position: {7}, shape_rotation: {8}, param: {9}, " \
                    "mode: {10}".format(
                        self.name, self.english_name, self.bone_index, self.collision_group, self.no_collision_group,
                        self.shape_type, self.shape_size, self.shape_position, self.shape_rotation, self.param,
                        self.mode
                    )

    class RigidBodyParam():
        def __init__(self, mass, linear_damping, angular_damping, restitution, friction):
            self.mass=mass
            self.linear_damping=linear_damping
            self.angular_damping=angular_damping
            self.restitution=restitution
            self.friction=friction

        def __str__(self):
            return "<RigidBodyParam mass:{0}, linear_damping:{1}, angular_damping:{2}, restitution:{3}, friction: {4}".format(
                        self.mass, self.linear_damping, self.angular_damping, self.restitution, self.friction
                    )
            
    # ジョイント構造-----------------------

    class Joint():
        def __init__(self, name, english_name,
                joint_type,
                rigidbody_index_a,
                rigidbody_index_b,
                position,
                rotation,
                translation_limit_min,
                translation_limit_max,
                rotation_limit_min,
                rotation_limit_max,
                spring_constant_translation,
                spring_constant_rotation
                ):
            self.name=name
            self.english_name=english_name
            self.joint_type=joint_type
            self.rigidbody_index_a=rigidbody_index_a
            self.rigidbody_index_b=rigidbody_index_b
            self.position=position
            self.rotation=rotation
            self.translation_limit_min=translation_limit_min
            self.translation_limit_max=translation_limit_max
            self.rotation_limit_min=rotation_limit_min
            self.rotation_limit_max=rotation_limit_max
            self.spring_constant_translation=spring_constant_translation
            self.spring_constant_rotation=spring_constant_rotation

        def __str__(self):
            return "<RigidBody name:{0}, english_name:{1}, joint_type:{2}, rigidbody_index_a:{3}, rigidbody_index_b:{4}, " \
                    "position: {5}, rotation: {6}, translation_limit_min: {7}, translation_limit_max: {8}, " \
                    "spring_constant_translation: {9}, spring_constant_rotation: {10}".format(
                        self.name, self.english_name, self.joint_type, self.rigidbody_index_a, self.rigidbody_index_b,
                        self.position, self.rotation, self.translation_limit_min, self.translation_limit_max,
                        self.spring_constant_translation, self.spring_constant_rotation
                    )













class ParseException(Exception):
    def __init__(self, message):
        self.message=message

