# -*- coding: utf-8 -*-
#
from abc import ABCMeta, abstractmethod
from collections import OrderedDict
import math
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa


class PmxModel():
    def __init__(self):
        self.path = ''
        self.name = ''
        self.english_name = ''
        self.comment = ''
        self.english_comment = ''
        # 頂点データ（キー：ボーンINDEX、値：頂点データリスト）
        self.vertices = {}
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
        # モーフデータ(順番保持)
        self.morphs = OrderedDict()
        # 表示枠データ
        self.display_slots = {}
        # 剛体データ
        self.rigidbodies = {}
        # 剛体INDEXデータ
        self.rigidbody_indexes = {}
        # ジョイントデータ
        self.joints = {}
        # ハッシュ値
        self.digest = None
        # 上半身がサイジング可能（標準・準標準ボーン構造）か
        self.can_upper_sizing = True
        # 腕がサイジング可能（標準・準標準ボーン構造）か
        self.can_arm_sizing = True

    # 頂点構造 ----------------------------
    class Vertex():
        def __init__(self, index, position, normal, uv, extended_uvs, deform, edge_factor):
            self.index = index
            self.position = position
            self.normal = normal
            self.uv = uv
            self.extended_uvs = extended_uvs or []
            self.deform = deform
            self.edge_factor = edge_factor
            
        def __str__(self):
            return "<Vertex index:{0}, position:{1}, normal:{2}, uv:{3}, extended_uv: {4}, deform:{5}, edge:{6}".format(
                   self.index, self.position, self.normal, self.uv, len(self.extended_uvs), self.deform, self.edge_factor)

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
            if type(self.deform) is PmxModel.Vertex.Bdef2 or type(self.deform) is PmxModel.Vertex.Sdef or type(self.deform) is PmxModel.Vertex.Qdef:
                if self.deform.weight0 >= 0.5 and self.deform.index0 in head_links_indexes.keys():
                    return self.deform.index0
                else:
                    if self.deform.index1 in head_links_indexes.keys():
                        return self.deform.index1
                    else:
                        return self.deform.index0

            elif type(self.deform) is PmxModel.Vertex.Bdef4:
                
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
            
            def get_idx_list(self):
                return [self.index0]
                
            def __str__(self):
                return "<Bdef1 {0}>".format(self.index0)

        class Bdef2():
            def __init__(self, index0, index1, weight0):
                self.index0 = index0
                self.index1 = index1
                self.weight0 = weight0
                
            def get_idx_list(self):
                return [self.index0, self.index1]
                
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
                
            def get_idx_list(self):
                return [self.index0, self.index1, self.index2, self.index3]

            def __str__(self):
                return "<Bdef4 {0}:{1}, {2}:{3}, {4}:{5}, {6}:{7}>".format(self.index0, self.index1, self.index2, self.index3, self.weight0, self.weight1, self.weight2, self.weight3)
                    
        class Sdef():
            def __init__(self, index0, index1, weight0, sdef_c, sdef_r0, sdef_r1):
                self.index0 = index0
                self.index1 = index1
                self.weight0 = weight0
                self.sdef_c = sdef_c
                self.sdef_r0 = sdef_r0
                self.sdef_r1 = sdef_r1
                
            def get_idx_list(self):
                return [self.index0, self.index1]

            def __str__(self):
                return "<Sdef {0}, {1}, {2}, {3} {4} {5}>".format(self.index0, self.index1, self.weight0, self.sdef_c, self.sdef_r0, self.sdef_r1)
            
        class Qdef():
            def __init__(self, index0, index1, weight0, sdef_c, sdef_r0, sdef_r1):
                self.index0 = index0
                self.index1 = index1
                self.weight0 = weight0
                self.sdef_c = sdef_c
                self.sdef_r0 = sdef_r0
                self.sdef_r1 = sdef_r1
                
            def get_idx_list(self):
                return [self.index0, self.index1]

            def __str__(self):
                return "<Sdef {0}, {1}, {2}, {3} {4} {5}>".format(self.index0, self.index1, self.weight0, self.sdef_c, self.sdef_r0, self.sdef_r1)

    # 材質構造-----------------------

    class Material():
        def __init__(self, name, english_name, diffuse_color, alpha, specular_factor, specular_color, ambient_color, flag, edge_color, edge_size, texture_index,
                     sphere_texture_index, sphere_mode, toon_sharing_flag, toon_texture_index=0, comment="", vertex_count=0):
            self.name = name
            self.english_name = english_name
            self.diffuse_color = diffuse_color
            self.alpha = alpha
            self.specular_color = specular_color
            self.specular_factor = specular_factor
            self.ambient_color = ambient_color
            self.flag = flag
            self.edge_color = edge_color
            self.edge_size = edge_size
            self.texture_index = texture_index
            self.sphere_texture_index = sphere_texture_index
            self.sphere_mode = sphere_mode
            self.toon_sharing_flag = toon_sharing_flag
            self.toon_texture_index = toon_texture_index
            self.comment = comment
            self.vertex_count = vertex_count

        def __str__(self):
            return "<Material name:{0}, english_name:{1}, diffuse_color:{2}, alpha:{3}, specular_color:{4}, " \
                   "ambient_color: {5}, flag: {6}, edge_color: {7}, edge_size: {8}, texture_index: {9}, " \
                   "sphere_texture_index: {10}, sphere_mode: {11}, toon_sharing_flag: {12}, " \
                   "toon_texture_index: {13}, comment: {14}, vertex_count: {15}".format(
                       self.name, self.english_name, self.diffuse_color, self.alpha, self.specular_color,
                       self.ambient_color, self.flag, self.edge_color, self.edge_size, self.texture_index,
                       self.sphere_texture_index, self.sphere_mode, self.toon_sharing_flag,
                       self.toon_texture_index, self.comment, self.vertex_count)

    # ボーン構造-----------------------
    class Bone():
        def __init__(self, name, english_name, position, parent_index, layer, flag, tail_position=None, tail_index=-1, effect_index=-1, effect_factor=0.0, fixed_axis=None,
                     local_x_vector=None, local_z_vector=None, external_key=-1, ik=None):
            self.name = name
            self.english_name = english_name
            self.position = position
            self.parent_index = parent_index
            self.layer = layer
            self.flag = flag
            self.tail_position = tail_position or MVector3D()
            self.tail_index = tail_index
            self.effect_index = effect_index
            self.effect_factor = effect_factor
            self.fixed_axis = fixed_axis or MVector3D()
            self.local_x_vector = local_x_vector or MVector3D()
            self.local_z_vector = local_z_vector or MVector3D()
            self.external_key = external_key
            self.ik = ik
            self.index = -1
            # 表示枠チェック時にONにするので、デフォルトはFalse
            self.display = False

            # 親ボーンからの長さ(計算して求める）
            self.len = 0
            # 親ボーンからの長さ3D版(計算して求める）
            self.len_3d = MVector3D()
            # オフセット(ローカル)
            self.local_offset = MVector3D()
            # IKオフセット(グローバル)
            self.global_ik_offset = MVector3D()
            
            self.BONEFLAG_TAILPOS_IS_BONE = 0x0001
            self.BONEFLAG_CAN_ROTATE = 0x0002
            self.BONEFLAG_CAN_TRANSLATE = 0x0004
            self.BONEFLAG_IS_VISIBLE = 0x0008
            self.BONEFLAG_CAN_MANIPULATE = 0x0010
            self.BONEFLAG_IS_IK = 0x0020
            self.BONEFLAG_IS_EXTERNAL_ROTATION = 0x0100
            self.BONEFLAG_IS_EXTERNAL_TRANSLATION = 0x0200
            self.BONEFLAG_HAS_FIXED_AXIS = 0x0400
            self.BONEFLAG_HAS_LOCAL_COORDINATE = 0x0800
            self.BONEFLAG_IS_AFTER_PHYSICS_DEFORM = 0x1000
            self.BONEFLAG_IS_EXTERNAL_PARENT_DEFORM = 0x2000

        def hasFlag(self, flag):
            return (self.flag & flag) != 0

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
                       self.external_key, self.ik, self.index)

    class Ik():
        def __init__(self, target_index, loop, limit_radian, link=None):
            self.target_index = target_index
            self.loop = loop
            self.limit_radian = limit_radian
            self.link = link or []

        def __str__(self):
            return "<Ik target_index:{0}, loop:{1}, limit_radian:{2}, link:{3}".format(self.target_index, self.loop, self.limit_radian, self.link)
            
    class IkLink():

        def __init__(self, bone_index, limit_angle, limit_min=None, limit_max=None):
            self.bone_index = bone_index
            self.limit_angle = limit_angle
            self.limit_min = limit_min or MVector3D()
            self.limit_max = limit_max or MVector3D()

        def __str__(self):
            return "<IkLink bone_index:{0}, limit_angle:{1}, limit_min:{2}, limit_max:{3}".format(self.bone_index, self.limit_angle, self.limit_min, self.limit_max)
            
    # モーフ構造-----------------------
    class Morph():
        def __init__(self, name, english_name, panel, morph_type, offsets=None):
            self.index = 0
            self.name = name
            self.english_name = english_name
            self.panel = panel
            self.morph_type = morph_type
            self.offsets = offsets or []
            # 表示枠チェック時にONにするので、デフォルトはFalse
            self.display = False

        def __str__(self):
            return "<Morph name:{0}, english_name:{1}, panel:{2}, morph_type:{3}, offsets(len): {4}".format(
                   self.name, self.english_name, self.panel, self.morph_type, len(self.offsets))
        
        # パネルの名称取得
        def get_panel_name(self):
            if self.panel == 1:
                return "眉"
            elif self.panel == 2:
                return "目"
            elif self.panel == 3:
                return "口"
            elif self.panel == 4:
                return "他"
            else:
                return "？"
                
        class GroupMorphData():
            def __init__(self, morph_index, value):
                self.morph_index = morph_index
                self.value = value

        class VertexMorphOffset():
            def __init__(self, vertex_index, position_offset):
                self.vertex_index = vertex_index
                self.position_offset = position_offset

        class BoneMorphData():
            def __init__(self, bone_index, position, rotation):
                self.bone_index = bone_index
                self.position = position
                self.rotation = rotation

        class UVMorphData():
            def __init__(self, vertex_index, uv):
                self.vertex_index = vertex_index
                self.uv = uv

        class MaterialMorphData():
            def __init__(self, material_index, calc_mode, diffuse, specular, specular_factor, ambient, edge_color, edge_size, texture_factor, sphere_texture_factor, toon_texture_factor):
                self.material_index = material_index
                self.calc_mode = calc_mode
                self.diffuse = diffuse
                self.specular = specular
                self.specular_factor = specular_factor
                self.ambient = ambient
                self.edge_color = edge_color
                self.edge_size = edge_size
                self.texture_factor = texture_factor
                self.sphere_texture_factor = sphere_texture_factor
                self.toon_texture_factor = toon_texture_factor

    # 表示枠構造-----------------------
    class DisplaySlot():
        def __init__(self, name, english_name, special_flag, references=None):
            self.name = name
            self.english_name = english_name
            self.special_flag = special_flag
            self.references = references or []

        def __str__(self):
            return "<DisplaySlots name:{0}, english_name:{1}, special_flag:{2}, references(len):{3}".format(self.name, self.english_name, self.special_flag, len(self.references))

    # 剛体構造-----------------------
    class RigidBody():
        def __init__(self, name, english_name, bone_index, collision_group, no_collision_group, shape_type, shape_size, shape_position, shape_rotation, mass, linear_damping, \
                     angular_damping, restitution, friction, mode):
            self.name = name
            self.english_name = english_name
            self.bone_index = bone_index
            self.collision_group = collision_group
            self.no_collision_group = no_collision_group
            self.shape_type = shape_type
            self.shape_size = shape_size
            self.shape_position = shape_position
            self.shape_rotation = shape_rotation
            self.param = PmxModel.RigidBodyParam(mass, linear_damping, angular_damping, restitution, friction)
            self.mode = mode
            self.index = -1

            self.SHAPE_SPHERE = 0
            self.SHAPE_BOX = 1
            self.SHAPE_CAPSULE = 2

        def __str__(self):
            return "<RigidBody name:{0}, english_name:{1}, bone_index:{2}, collision_group:{3}, no_collision_group:{4}, " \
                   "shape_type: {5}, shape_size: {6}, shape_position: {7}, shape_rotation: {8}, param: {9}, " \
                   "mode: {10}".format(self.name, self.english_name, self.bone_index, self.collision_group, self.no_collision_group,
                                       self.shape_type, self.shape_size, self.shape_position, self.shape_rotation, self.param, self.mode)
        
        def get_obb(self, bone_pos, trans_vs, add_qs):
            # 剛体の形状別の衝突判定用
            if self.shape_type == self.SHAPE_SPHERE:
                return PmxModel.RigidBody.Sphere(self.shape_size, self.shape_position, self.shape_rotation, bone_pos, trans_vs, add_qs)
            elif self.shape_type == self.SHAPE_BOX:
                return PmxModel.RigidBody.Box(self.shape_size, self.shape_position, self.shape_rotation, bone_pos, trans_vs, add_qs)
            else:
                return PmxModel.RigidBody.Capsule(self.shape_size, self.shape_position, self.shape_rotation, bone_pos, trans_vs, add_qs)

        # OBB（有向境界ボックス：Oriented Bounding Box）
        class OBB(metaclass=ABCMeta):
            def __init__(self, shape_size, shape_position, shape_rotation, bone_pos, trans_vs, add_qs):
                self.shape_size = shape_size
                self.shape_position = shape_position
                self.shape_rotation = shape_rotation
                self.shape_rotation_qq = MQuaternion.fromEulerAngles(-shape_rotation.x(), shape_rotation.y(), shape_rotation.z())
                self.bone_pos = bone_pos
                self.trans_vs = trans_vs
                self.add_qs = add_qs

                self.matrix = MMatrix4x4()

                # 実際の原点位置
                for v, q in zip(trans_vs, add_qs):
                    # 移動
                    self.matrix.translate(v)
                    # 回転
                    self.matrix.rotate(q)

                # 剛体自体の位置
                self.matrix.translate(self.shape_position - bone_pos)
                # 剛体自体の回転
                self.matrix.rotate(self.shape_rotation_qq)

                # 剛体自体の原点
                self.origin = self.matrix * MVector3D(0, 0, 0)

                self.origin_xyz = {"x": self.origin.x(), "y": self.origin.y(), "z": self.origin.z()}
                self.shape_size_xyz = {"x": self.shape_size.x(), "y": self.shape_size.y(), "z": self.shape_size.z()}

            # 指定軸番号の方向ベクトルを取得
            def get_direct(self, axis):
                if axis == "x":
                    return self.matrix.mapVector(MVector3D(1, 0, 0))
                if axis == "y":
                    return self.matrix.mapVector(MVector3D(0, 1, 0))
                if axis == "z":
                    return self.matrix.mapVector(MVector3D(0, 0, 1))
            
            # 誤差を丸める
            def epsilon(self, v):
                if round(v, 3) == 0:
                    return 0
                else:
                    return v

            # http://marupeke296.com/COL_3D_No12_OBBvsPoint.html
            # http://marupeke296.com/COL_3D_No14_OBBvsPlane.html
            # 3次元OBBと点の最短距離算出関数
            def get_distance_vec(self, point):
                # 最終的に長さを求めるベクトル
                distance_vec = MVector3D()
                
                # 各軸についてはみ出た部分のベクトルを算出
                for axis in ["x", "y", "z"]:
                    length = self.get_length(axis)
                    if length <= 0:
                        continue

                    # pointの位置の場合分け
                    s = MVector3D.dotProduct((point - self.origin), self.get_direct(axis)) / length
                    # sの誤差を丸めた絶対値
                    fs = abs(self.epsilon(s))
                    # はみ出した部分のベクトル算出
                    if fs > 1:
                        distance_vec += (1 - fs) * length * self.get_direct(axis)
                    
                return distance_vec
            
            # 指定軸方向の長さ
            @abstractmethod
            def get_length(self, axis):
                pass
            
            # 衝突判定
            def judge_collision(self, point):
                distance_vec = self.get_distance_vec(point)

                # 衝突判定
                collision = self.get_collistion(distance_vec, point)

                # めり込んだ位置から平面の法線方向に戻し距離だけオフセット
                return_pos = self.get_return_pos(distance_vec, point)

                return collision, return_pos
            
            # # OBBとの衝突判定
            # def get_return_distance(self, distance_vec, distance_proximity):
            #     return_distance = 0
            #     if distance > 0:
            #         return_distance = r - self.epsilon(distance)
            #     else:
            #         return_distance = r + self.epsilon(distance)
            #     return return_distance

            # OBBとの衝突判定
            @abstractmethod
            def get_collistion(self, distance_vec, point):
                pass
            
            # OBBとの衝突判定
            def get_return_pos(self, distance_vec, point):
                # 戻し距離
                return MVector3D.crossProduct(point, self.origin).normalized() * distance_vec

        # 球剛体
        class Sphere(OBB):
            def __init__(self, shape_size, shape_position, shape_rotation, pos, trans_vs, add_qs):
                super().__init__(shape_size, shape_position, shape_rotation, pos, trans_vs, add_qs)

            # 指定軸方向の長さ
            def get_length(self, axis):
                # 半径そのもの
                return self.shape_size.x()

            # 衝突しているか
            def get_collistion(self, distance_vec, point):
                # 半径未満なら衝突
                return 0 < abs(self.epsilon(distance_vec.length())) < self.shape_size.x()

        # 箱剛体
        class Box(OBB):
            def __init__(self, shape_size, shape_position, shape_rotation, pos, trans_vs, add_qs):
                super().__init__(shape_size, shape_position, shape_rotation, pos, trans_vs, add_qs)

            # 指定軸方向の長さ
            def get_length(self, axis):
                # 各軸の長さ
                return self.shape_size_xyz[axis] / 2

            # 衝突しているか（内外判定）
            # https://stackoverflow.com/questions/21037241/how-to-determine-a-point-is-inside-or-outside-a-cube
            def get_collistion(self, distance_vec, point):
                # 立方体の中にある場合、衝突
                # 下辺
                b1 = self.matrix * MVector3D(self.get_length("x"), -self.get_length("y"), -self.get_length("z"))
                b2 = self.matrix * MVector3D(self.get_length("x"), -self.get_length("y"), self.get_length("z"))
                # b3 = self.matrix * MVector3D(-self.get_length("x"), -self.get_length("y"), self.get_length("z"))
                b4 = self.matrix * MVector3D(-self.get_length("x"), -self.get_length("y"), -self.get_length("z"))
                # 上辺
                t1 = self.matrix * MVector3D(self.get_length("x"), self.get_length("y"), -self.get_length("z"))
                # t2 = self.matrix * MVector3D(self.get_length("x"), self.get_length("y"), self.get_length("z"))
                # t3 = self.matrix * MVector3D(-self.get_length("x"), self.get_length("y"), self.get_length("z"))
                # t4 = self.matrix * MVector3D(-self.get_length("x"), self.get_length("y"), -self.get_length("z"))

                d1 = (t1 - b1)
                size1 = d1.lengthSquared()
                dir1 = d1 / size1
                PmxModel.set_effective_value_vec3(dir1)

                d2 = (b2 - b1)
                size2 = d2.lengthSquared()
                dir2 = d2 / size2
                PmxModel.set_effective_value_vec3(dir2)

                d3 = (b4 - b1)
                size3 = d3.lengthSquared()
                dir3 = d3 / size3
                PmxModel.set_effective_value_vec3(dir3)

                dir_vec = point - self.origin
                PmxModel.set_effective_value_vec3(dir_vec)

                res1 = abs(MVector3D.dotProduct(dir_vec, dir1) * 2) < size1
                res2 = abs(MVector3D.dotProduct(dir_vec, dir2) * 2) < size2
                res3 = abs(MVector3D.dotProduct(dir_vec, dir3) * 2) < size3

                return res1 == res2 == res3

        # カプセル剛体
        class Capsule(OBB):
            def __init__(self, shape_size, shape_position, shape_rotation, pos, trans_vs, add_qs):
                super().__init__(shape_size, shape_position, shape_rotation, pos, trans_vs, add_qs)
                                
            # 指定軸方向の長さ
            def get_length(self, axis):
                if axis in ["x", "z"]:
                    # カプセルの横は線分
                    return self.shape_size.y() / 2
                else:
                    # Yは半径を追加する
                    return self.shape_size.y() / 2 + self.shape_size.x()

            # 衝突しているか
            def get_collistion(self, distance_vec, point):
                # 半径未満なら衝突
                return 0 < abs(self.epsilon(distance_vec.length())) < self.shape_size.x()

    class RigidBodyParam():
        def __init__(self, mass, linear_damping, angular_damping, restitution, friction):
            self.mass = mass
            self.linear_damping = linear_damping
            self.angular_damping = angular_damping
            self.restitution = restitution
            self.friction = friction

        def __str__(self):
            return "<RigidBodyParam mass:{0}, linear_damping:{1}, angular_damping:{2}, restitution:{3}, friction: {4}".format(
                self.mass, self.linear_damping, self.angular_damping, self.restitution, self.friction)
            
    # ジョイント構造-----------------------

    class Joint():
        def __init__(self, name, english_name, joint_type, rigidbody_index_a, rigidbody_index_b, position, rotation, \
                     translation_limit_min, translation_limit_max, rotation_limit_min, rotation_limit_max, spring_constant_translation, spring_constant_rotation):
            self.name = name
            self.english_name = english_name
            self.joint_type = joint_type
            self.rigidbody_index_a = rigidbody_index_a
            self.rigidbody_index_b = rigidbody_index_b
            self.position = position
            self.rotation = rotation
            self.translation_limit_min = translation_limit_min
            self.translation_limit_max = translation_limit_max
            self.rotation_limit_min = rotation_limit_min
            self.rotation_limit_max = rotation_limit_max
            self.spring_constant_translation = spring_constant_translation
            self.spring_constant_rotation = spring_constant_rotation

        def __str__(self):
            return "<RigidBody name:{0}, english_name:{1}, joint_type:{2}, rigidbody_index_a:{3}, rigidbody_index_b:{4}, " \
                   "position: {5}, rotation: {6}, translation_limit_min: {7}, translation_limit_max: {8}, " \
                   "spring_constant_translation: {9}, spring_constant_rotation: {10}".format(
                       self.name, self.english_name, self.joint_type, self.rigidbody_index_a, self.rigidbody_index_b,
                       self.position, self.rotation, self.translation_limit_min, self.translation_limit_max,
                       self.spring_constant_translation, self.spring_constant_rotation)

    @classmethod
    def get_effective_value(cls, v):
        if math.isnan(v):
            return 0
        
        if math.isinf(v):
            return 0
        
        return v

    @classmethod
    def set_effective_value_vec3(cls, vec3):
        vec3.setX(cls.get_effective_value(vec3.x()))
        vec3.setY(cls.get_effective_value(vec3.y()))
        vec3.setZ(cls.get_effective_value(vec3.z()))
