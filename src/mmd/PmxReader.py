# -*- coding: utf-8 -*-
#
import struct
import hashlib
from collections import OrderedDict

from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MException import MParseException # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class PmxReader():
    def __init__(self, file_path):
        self.file_path = file_path
        self.offset = 0
        self.buffer = None
        self.vertex_index_size = 0
        self.texture_index_size = 0
        self.material_index_size = 0
        self.bone_index_size = 0
        self.morph_index_size = 0
        self.rigidbody_index_size = 0

    def read_model_name(self):
        model_name = ""
        with open(self.file_path, "rb") as f:
            # PMXファイルをバイナリ読み込み
            self.buffer = f.read()
            # logger.test("hashlib.algorithms_available: %s", hashlib.algorithms_available)

            # pmx宣言
            signature = self.unpack(4, "4s")
            logger.test("signature: %s (%s)", signature, self.offset)

            # pmxバージョン
            version = self.read_float()
            logger.test("version: %s (%s)", version, self.offset)

            if signature[:3] != b"PMX" or (version != 2.0 and version != 2.1):
                # 整合性チェック
                raise MParseException("PMX2.0/2.1形式外のデータです。signature: {0}, version: {1} ".format(signature, version))

            # flag
            flag_bytes = self.read_int(1)
            logger.test("flag_bytes: %s (%s)", flag_bytes, self.offset)

            # エンコード方式
            text_encoding = self.read_int(1)
            logger.test("text_encoding: %s (%s)", text_encoding, self.offset)
            # エンコードに基づいて文字列解凍処理を定義
            self.read_text = self.define_read_text(text_encoding)

            # 追加UV数
            self.extended_uv = self.read_int(1)
            logger.test("extended_uv: %s (%s)", self.extended_uv, self.offset)

            # 頂点Indexサイズ
            self.vertex_index_size = self.read_int(1)
            logger.test("vertex_index_size: %s (%s)", self.vertex_index_size, self.offset)
            self.read_vertex_index_size = lambda: self.read_int(self.vertex_index_size)

            # テクスチャIndexサイズ
            self.texture_index_size = self.read_int(1)
            logger.test("texture_index_size: %s (%s)", self.texture_index_size, self.offset)
            self.read_texture_index_size = lambda: self.read_int(self.texture_index_size)

            # 材質Indexサイズ
            self.material_index_size = self.read_int(1)
            logger.test("material_index_size: %s (%s)", self.material_index_size, self.offset)
            self.read_material_index_size = lambda: self.read_int(self.material_index_size)

            # ボーンIndexサイズ
            self.bone_index_size = self.read_int(1)
            logger.test("bone_index_size: %s (%s)", self.bone_index_size, self.offset)
            self.read_bone_index_size = lambda: self.read_int(self.bone_index_size)

            # モーフIndexサイズ
            self.morph_index_size = self.read_int(1)
            logger.test("morph_index_size: %s (%s)", self.morph_index_size, self.offset)
            self.read_morph_index_size = lambda: self.read_int(self.morph_index_size)

            # 剛体Indexサイズ
            self.rigidbody_index_size = self.read_int(1)
            logger.test("rigidbody_index_size: %s (%s)", self.rigidbody_index_size, self.offset)
            self.read_rigidbody_index_size = lambda: self.read_int(self.rigidbody_index_size)

            # モデル名（日本語）
            model_name = self.read_text()
            logger.test("name: %s (%s)", model_name, self.offset)

        return model_name

    def read_data(self):
        # Pmxモデル生成
        pmx = PmxModel()
        pmx.path = self.file_path

        # PMXファイルをバイナリ読み込み
        with open(self.file_path, "rb") as f:
            self.buffer = f.read()
            # logger.test("hashlib.algorithms_available: %s", hashlib.algorithms_available)

            # pmx宣言
            signature = self.unpack(4, "4s")
            logger.test("signature: %s (%s)", signature, self.offset)

            # pmxバージョン
            version = self.read_float()
            logger.test("version: %s (%s)", version, self.offset)

            if signature[:3] != b"PMX" or (version != 2.0 and version != 2.1):
                # 整合性チェック
                raise MParseException("PMX2.0/2.1形式外のデータです。signature: {0}, version: {1} ".format(signature, version))

            # flag
            flag_bytes = self.read_int(1)
            logger.test("flag_bytes: %s (%s)", flag_bytes, self.offset)

            # エンコード方式
            text_encoding = self.read_int(1)
            logger.test("text_encoding: %s (%s)", text_encoding, self.offset)
            # エンコードに基づいて文字列解凍処理を定義
            self.read_text = self.define_read_text(text_encoding)

            # 追加UV数
            self.extended_uv = self.read_int(1)
            logger.test("extended_uv: %s (%s)", self.extended_uv, self.offset)

            # 頂点Indexサイズ
            self.vertex_index_size = self.read_int(1)
            logger.test("vertex_index_size: %s (%s)", self.vertex_index_size, self.offset)
            self.read_vertex_index_size = lambda: self.read_int(self.vertex_index_size)

            # テクスチャIndexサイズ
            self.texture_index_size = self.read_int(1)
            logger.test("texture_index_size: %s (%s)", self.texture_index_size, self.offset)
            self.read_texture_index_size = lambda: self.read_int(self.texture_index_size)

            # 材質Indexサイズ
            self.material_index_size = self.read_int(1)
            logger.test("material_index_size: %s (%s)", self.material_index_size, self.offset)
            self.read_material_index_size = lambda: self.read_int(self.material_index_size)

            # ボーンIndexサイズ
            self.bone_index_size = self.read_int(1)
            logger.test("bone_index_size: %s (%s)", self.bone_index_size, self.offset)
            self.read_bone_index_size = lambda: self.read_int(self.bone_index_size)

            # モーフIndexサイズ
            self.morph_index_size = self.read_int(1)
            logger.test("morph_index_size: %s (%s)", self.morph_index_size, self.offset)
            self.read_morph_index_size = lambda: self.read_int(self.morph_index_size)

            # 剛体Indexサイズ
            self.rigidbody_index_size = self.read_int(1)
            logger.test("rigidbody_index_size: %s (%s)", self.rigidbody_index_size, self.offset)
            self.read_rigidbody_index_size = lambda: self.read_int(self.rigidbody_index_size)

            # モデル名（日本語）
            pmx.name = self.read_text()
            logger.test("name: %s (%s)", pmx.name, self.offset)

            # モデル名（英語）
            pmx.english_name = self.read_text()
            logger.test("english_name: %s (%s)", pmx.english_name, self.offset)

            # コメント（日本語）
            pmx.comment = self.read_text()
            logger.test("comment: %s (%s)", pmx.comment, self.offset)

            # コメント（英語）
            pmx.english_comment = self.read_text()
            logger.test("english_comment: %s (%s)", pmx.english_comment, self.offset)

            # 頂点データリスト
            for vertex_idx in range(self.read_int(4)):
                position = self.read_Vector3D()
                normal = self.read_Vector3D()
                uv = self.read_Vector2D()

                extended_uvs = []
                if self.extended_uv > 0:
                    # 追加UVがある場合
                    for _ in range(self.extended_uv):
                        extended_uvs.append(self.read_Vector4D())

                deform = self.read_deform()
                edge_factor = self.read_float()

                # 頂点をウェイトボーンごとに分けて保持する
                vertex = Vertex(vertex_idx, position, normal, uv, extended_uvs, deform, edge_factor)
                for bone_idx in vertex.deform.get_idx_list():
                    if bone_idx not in pmx.vertices:
                        pmx.vertices[bone_idx] = []
                    pmx.vertices[bone_idx].append(vertex)

            logger.test("len(vertices): %s", len(pmx.vertices))
            logger.test("vertices.keys: %s", pmx.vertices.keys())
            logger.info("-- PMX 頂点読み込み完了")

            # 面データリスト
            for _ in range(self.read_int(4)):
                if self.vertex_index_size <= 2:
                    # 頂点サイズが2以下の場合、符号なし
                    pmx.indices.append(self.read_uint(self.vertex_index_size))
                else:
                    pmx.indices.append(self.read_int(self.vertex_index_size))
            logger.test("len(indices): %s", len(pmx.indices))
            
            logger.info("-- PMX 面読み込み完了")

            # テクスチャデータリスト
            for _ in range(self.read_int(4)):
                pmx.textures.append(self.read_text())
            logger.test("len(textures): %s", len(pmx.textures))

            logger.info("-- PMX テクスチャ読み込み完了")

            # 材質データリスト
            for material_idx in range(self.read_int(4)):
                material = Material(
                    name=self.read_text(),
                    english_name=self.read_text(),
                    diffuse_color=self.read_RGB(),
                    alpha=self.read_float(),
                    specular_color=self.read_RGB(),
                    specular_factor=self.read_float(),
                    ambient_color=self.read_RGB(),
                    flag=self.read_int(1),
                    edge_color=self.read_RGBA(),
                    edge_size=self.read_float(),
                    texture_index=self.read_texture_index_size(),
                    sphere_texture_index=self.read_texture_index_size(),
                    sphere_mode=self.read_int(1),
                    toon_sharing_flag=self.read_int(1)
                )
                material.index = material_idx

                if material.toon_sharing_flag == 0:
                    material.toon_texture_index = self.read_texture_index_size()
                elif material.toon_sharing_flag == 1:
                    material.toon_texture_index = self.read_int(1)
                else:
                    raise MParseException("unknown toon_sharing_flag {0}".format(material.toon_sharing_flag))
                material.comment = self.read_text()
                material.vertex_count = self.read_int(4)

                pmx.materials[material.name] = material
                pmx.material_indexes[material.index] = material.name
            logger.test("len(materials): %s", len(pmx.materials))

            logger.info("-- PMX 材質読み込み完了")

            # サイジング用ルートボーン
            sizing_root_bone = Bone("SIZING_ROOT_BONE", "SIZING_ROOT_BONE", MVector3D(), -1, 0, 0)
            sizing_root_bone.index = -999

            pmx.bones[sizing_root_bone.name] = sizing_root_bone
            # インデックス逆引きも登録
            pmx.bone_indexes[sizing_root_bone.index] = sizing_root_bone.name

            # ボーンデータリスト
            for bone_idx in range(self.read_int(4)):
                bone = Bone(
                    name=self.read_text(),
                    english_name=self.read_text(),
                    position=self.read_Vector3D(),
                    parent_index=self.read_bone_index_size(),
                    layer=self.read_int(4),
                    flag=self.read_int(2)
                )

                if not bone.getConnectionFlag():
                    bone.tail_position = self.read_Vector3D()
                elif bone.getConnectionFlag():
                    bone.tail_index = self.read_bone_index_size()
                else:
                    raise MParseException("unknown bone conenction flag: {0}".format(bone.getConnectionFlag()))

                if bone.getExternalRotationFlag() or bone.getExternalTranslationFlag():
                    bone.effect_index = self.read_bone_index_size()
                    bone.effect_factor = self.read_float()

                if bone.getFixedAxisFlag():
                    bone.fixed_axis = self.read_Vector3D()

                if bone.getLocalCoordinateFlag():
                    bone.local_x_vector = self.read_Vector3D()
                    bone.local_z_vector = self.read_Vector3D()

                if bone.getExternalParentDeformFlag():
                    bone.external_key = self.read_int(4)

                if bone.getIkFlag():
                    bone.ik = Bone.Ik(
                        target_index=self.read_bone_index_size(),
                        loop=self.read_int(4),
                        limit_radian=self.read_float()
                    )

                    # IKリンク取得
                    for _ in range(self.read_int(4)):

                        link = Bone.IkLink(
                            self.read_bone_index_size(),
                            self.read_int(1)
                        )

                        if link.limit_angle == 0:
                            pass
                        elif link.limit_angle == 1:
                            link.limit_min = self.read_Vector3D()
                            link.limit_max = self.read_Vector3D()
                        else:
                            raise MParseException("invalid ik link limit_angle: {0}".format(link.limit_angle))

                        bone.ik.link.append(link)

                # ボーンのINDEX
                bone.index = bone_idx

                if bone.name not in pmx.bones:
                    # まだ未登録の名前のボーンの場合のみ登録
                    pmx.bones[bone.name] = bone
                    # インデックス逆引きも登録
                    pmx.bone_indexes[bone.index] = bone.name
            
            # サイジング用ボーン ---------
            # 頭頂ボーン
            head_top_vertex = pmx.get_head_top_vertex()
            pmx.head_top_vertex = head_top_vertex
            head_top_bone = Bone("頭頂実体", "head_top", head_top_vertex.position.copy(), -1, 0, 0)
            head_top_bone.index = len(pmx.bones.keys())
            pmx.bones[head_top_bone.name] = head_top_bone
            pmx.bone_indexes[head_top_bone.index] = head_top_bone.name

            if "右足ＩＫ" in pmx.bones or "右つま先ＩＫ" in pmx.bones:
                # 右つま先ボーン
                right_toe_vertex = pmx.get_toe_vertex("右")
                if right_toe_vertex:
                    pmx.right_toe_vertex = right_toe_vertex
                    right_toe_bone = Bone("右つま先実体", "right toe entity", right_toe_vertex.position.copy(), -1, 0, 0)
                    right_toe_bone.index = len(pmx.bones.keys())
                    pmx.bones[right_toe_bone.name] = right_toe_bone
                    pmx.bone_indexes[right_toe_bone.index] = right_toe_bone.name

            if "左足ＩＫ" in pmx.bones or "左つま先ＩＫ" in pmx.bones:
                # 左つま先ボーン
                left_toe_vertex = pmx.get_toe_vertex("左")
                if left_toe_vertex:
                    pmx.left_toe_vertex = left_toe_vertex
                    left_toe_bone = Bone("左つま先実体", "left toe entity", left_toe_vertex.position.copy(), -1, 0, 0)
                    left_toe_bone.index = len(pmx.bones.keys())
                    pmx.bones[left_toe_bone.name] = left_toe_bone
                    pmx.bone_indexes[left_toe_bone.index] = left_toe_bone.name

            if "右足先EX" in pmx.bones or "右足ＩＫ" in pmx.bones:
                # 右足底実体ボーン
                if "右足先EX" in pmx.bones:
                    right_sole_vertex = Vertex(-1, MVector3D(pmx.bones["右足先EX"].position.x(), 0, pmx.bones["右足先EX"].position.z()), MVector3D(), [], [], Vertex.Bdef1(-1), -1)
                elif "右足ＩＫ" in pmx.bones:
                    right_sole_vertex = pmx.get_sole_vertex("右")
                
                if right_sole_vertex:
                    pmx.right_sole_vertex = right_sole_vertex
                    right_sole_bone = Bone("右足底実体", "right sole entity", right_sole_vertex.position.copy(), -1, 0, 0)
                    right_sole_bone.index = len(pmx.bones.keys())
                    pmx.bones[right_sole_bone.name] = right_sole_bone
                    pmx.bone_indexes[right_sole_bone.index] = right_sole_bone.name

            if "左足先EX" in pmx.bones or "左足ＩＫ" in pmx.bones:
                # 左足底実体ボーン
                if "左足先EX" in pmx.bones:
                    left_sole_vertex = Vertex(-1, MVector3D(pmx.bones["左足先EX"].position.x(), 0, pmx.bones["左足先EX"].position.z()), MVector3D(), [], [], Vertex.Bdef1(-1), -1)
                elif "左足ＩＫ" in pmx.bones:
                    left_sole_vertex = pmx.get_sole_vertex("左")
                
                if left_sole_vertex:
                    pmx.left_sole_vertex = left_sole_vertex
                    left_sole_bone = Bone("左足底実体", "left sole entity", left_sole_vertex.position.copy(), -1, 0, 0)
                    left_sole_bone.index = len(pmx.bones.keys())
                    pmx.bones[left_sole_bone.name] = left_sole_bone
                    pmx.bone_indexes[left_sole_bone.index] = left_sole_bone.name

            if "右足ＩＫ" in pmx.bones:
                # 右足ＩＫ底実体ボーン
                right_ik_sole_vertex = Vertex(-1, MVector3D(pmx.bones["右足ＩＫ"].position.x(), 0, pmx.bones["右足ＩＫ"].position.z()), MVector3D(), [], [], Vertex.Bdef1(-1), -1)
                pmx.right_ik_sole_vertex = right_ik_sole_vertex
                right_ik_sole_bone = Bone("右足ＩＫ底実体", "right ik ik_sole entity", right_ik_sole_vertex.position.copy(), -1, 0, 0)
                right_ik_sole_bone.index = len(pmx.bones.keys())
                pmx.bones[right_ik_sole_bone.name] = right_ik_sole_bone
                pmx.bone_indexes[right_ik_sole_bone.index] = right_ik_sole_bone.name

            if "左足ＩＫ" in pmx.bones:
                # 左足ＩＫ底実体ボーン
                left_ik_sole_vertex = Vertex(-1, MVector3D(pmx.bones["左足ＩＫ"].position.x(), 0, pmx.bones["左足ＩＫ"].position.z()), MVector3D(), [], [], Vertex.Bdef1(-1), -1)
                pmx.left_ik_sole_vertex = left_ik_sole_vertex
                left_ik_sole_bone = Bone("左足ＩＫ底実体", "left ik ik_sole entity", left_ik_sole_vertex.position.copy(), -1, 0, 0)
                left_ik_sole_bone.index = len(pmx.bones.keys())
                pmx.bones[left_ik_sole_bone.name] = left_ik_sole_bone
                pmx.bone_indexes[left_ik_sole_bone.index] = left_ik_sole_bone.name

            if "右足IK親" in pmx.bones:
                # 右足IK親底実体ボーン
                right_ik_sole_vertex = Vertex(-1, MVector3D(pmx.bones["右足IK親"].position.x(), 0, pmx.bones["右足IK親"].position.z()), MVector3D(), [], [], Vertex.Bdef1(-1), -1)
                pmx.right_ik_sole_vertex = right_ik_sole_vertex
                right_ik_sole_bone = Bone("右足IK親底実体", "right ik ik_sole entity", right_ik_sole_vertex.position.copy(), -1, 0, 0)
                right_ik_sole_bone.index = len(pmx.bones.keys())
                pmx.bones[right_ik_sole_bone.name] = right_ik_sole_bone
                pmx.bone_indexes[right_ik_sole_bone.index] = right_ik_sole_bone.name

            if "左足IK親" in pmx.bones:
                # 左足IK親底実体ボーン
                left_ik_sole_vertex = Vertex(-1, MVector3D(pmx.bones["左足IK親"].position.x(), 0, pmx.bones["左足IK親"].position.z()), MVector3D(), [], [], Vertex.Bdef1(-1), -1)
                pmx.left_ik_sole_vertex = left_ik_sole_vertex
                left_ik_sole_bone = Bone("左足IK親底実体", "left ik ik_sole entity", left_ik_sole_vertex.position.copy(), -1, 0, 0)
                left_ik_sole_bone.index = len(pmx.bones.keys())
                pmx.bones[left_ik_sole_bone.name] = left_ik_sole_bone
                pmx.bone_indexes[left_ik_sole_bone.index] = left_ik_sole_bone.name

            # 首根元ボーン
            if "左肩" in pmx.bones and "右肩" in pmx.bones:
                neck_base_vertex = Vertex(-1, (pmx.bones["左肩"].position + pmx.bones["右肩"].position) / 2, MVector3D(), [], [], Vertex.Bdef1(-1), -1)
                neck_base_vertex.position.setX(0)
                neck_base_bone = Bone("首根元", "base of neck", neck_base_vertex.position.copy(), -1, 0, 0)

                if "上半身2" in pmx.bones:
                    # 上半身2がある場合、表示先は、上半身2
                    neck_base_bone.parent_index = pmx.bones["上半身2"].index
                    neck_base_bone.tail_index = pmx.bones["上半身2"].index
                elif "上半身" in pmx.bones:
                    neck_base_bone.parent_index = pmx.bones["上半身"].index
                    neck_base_bone.tail_index = pmx.bones["上半身"].index

                neck_base_bone.index = len(pmx.bones.keys())
                pmx.bones[neck_base_bone.name] = neck_base_bone
                pmx.bone_indexes[neck_base_bone.index] = neck_base_bone.name

            if "右肩" in pmx.bones:
                # 右肩下延長ボーン
                right_shoulder_under_pos = pmx.bones["右肩"].position.copy()
                right_shoulder_under_pos.setY(right_shoulder_under_pos.y() - 1)
                right_shoulder_under_bone = Bone("右肩下延長", "", right_shoulder_under_pos, -1, 0, 0)
                right_shoulder_under_bone.index = len(pmx.bones.keys())
                pmx.bones[right_shoulder_under_bone.name] = right_shoulder_under_bone
                pmx.bone_indexes[right_shoulder_under_bone.index] = right_shoulder_under_bone.name

            if "左肩" in pmx.bones:
                # 左肩下延長ボーン
                left_shoulder_under_pos = pmx.bones["左肩"].position.copy()
                left_shoulder_under_pos.setY(left_shoulder_under_pos.y() - 1)
                left_shoulder_under_bone = Bone("左肩下延長", "", left_shoulder_under_pos, -1, 0, 0)
                left_shoulder_under_bone.index = len(pmx.bones.keys())
                pmx.bones[left_shoulder_under_bone.name] = left_shoulder_under_bone
                pmx.bone_indexes[left_shoulder_under_bone.index] = left_shoulder_under_bone.name

            if "右ひじ" in pmx.bones and "右手首" in pmx.bones:
                # 右ひじ手首中間ボーン
                right_elbow_middle_pos = (pmx.bones["右ひじ"].position + pmx.bones["右手首"].position) / 2
                right_elbow_middle_bone = Bone("右ひじ手首中間", "", right_elbow_middle_pos, -1, 0, 0)
                right_elbow_middle_bone.index = len(pmx.bones.keys())
                pmx.bones[right_elbow_middle_bone.name] = right_elbow_middle_bone
                pmx.bone_indexes[right_elbow_middle_bone.index] = right_elbow_middle_bone.name

            if "左ひじ" in pmx.bones and "左手首" in pmx.bones:
                # 左ひじ手首中間ボーン
                left_elbow_middle_pos = (pmx.bones["左ひじ"].position + pmx.bones["左手首"].position) / 2
                left_elbow_middle_bone = Bone("左ひじ手首中間", "", left_elbow_middle_pos, -1, 0, 0)
                left_elbow_middle_bone.index = len(pmx.bones.keys())
                pmx.bones[left_elbow_middle_bone.name] = left_elbow_middle_bone
                pmx.bone_indexes[left_elbow_middle_bone.index] = left_elbow_middle_bone.name

            if "右ひじ" in pmx.bones and "右腕" in pmx.bones:
                # 右腕ひじ中間ボーン
                right_arm_middle_pos = (pmx.bones["右ひじ"].position + pmx.bones["右腕"].position) / 2
                right_arm_middle_bone = Bone("右腕ひじ中間", "", right_arm_middle_pos, -1, 0, 0)
                right_arm_middle_bone.index = len(pmx.bones.keys())
                pmx.bones[right_arm_middle_bone.name] = right_arm_middle_bone
                pmx.bone_indexes[right_arm_middle_bone.index] = right_arm_middle_bone.name

            if "左ひじ" in pmx.bones and "左腕" in pmx.bones:
                # 左腕ひじ中間ボーン
                left_arm_middle_pos = (pmx.bones["左ひじ"].position + pmx.bones["左腕"].position) / 2
                left_arm_middle_bone = Bone("左腕ひじ中間", "", left_arm_middle_pos, -1, 0, 0)
                left_arm_middle_bone.index = len(pmx.bones.keys())
                pmx.bones[left_arm_middle_bone.name] = left_arm_middle_bone
                pmx.bone_indexes[left_arm_middle_bone.index] = left_arm_middle_bone.name

            # センター実体
            center_entity_bone = Bone("センター実体", "", MVector3D(), -1, 0, 0)
            center_entity_bone.index = len(pmx.bones.keys())
            pmx.bones[center_entity_bone.name] = center_entity_bone
            pmx.bone_indexes[center_entity_bone.index] = center_entity_bone.name

            # 指先ボーンがない場合、代替で挿入
            for direction in ["左", "右"]:
                for (finger_name, end_joint_name) in [("親指", "２"), ("人指", "３"), ("中指", "３"), ("薬指", "３"), ("小指", "３")]:
                    end_joint_name = "{0}{1}{2}".format(direction, finger_name, end_joint_name)
                    to_joint_name = "{0}{1}{2}".format(direction, finger_name, "先")

                    if end_joint_name in pmx.bones and to_joint_name not in pmx.bones:
                        # 指先端があって、指先がない場合挿入
                        to_pos = self.calc_tail_pos(pmx, end_joint_name)
                        to_bone = Bone(to_joint_name, None, to_pos, -1, 0, 0)

                        # ボーンのINDEX
                        to_bone.index = len(pmx.bones.keys())
                        pmx.bones[to_bone.name] = to_bone
                        # インデックス逆引きも登録
                        pmx.bone_indexes[to_bone.index] = to_bone.name

            logger.test("len(bones): %s", len(pmx.bones))

            logger.info("-- PMX ボーン読み込み完了")

            # ボーンの長さを計算する
            self.calc_bone_length(pmx.bones, pmx.bone_indexes)

            # 操作パネル (PMD:カテゴリ) 1:眉(左下) 2:目(左上) 3:口(右上) 4:その他(右下)
            morphs_by_panel = OrderedDict()
            morphs_by_panel[2] = []  # 目
            morphs_by_panel[1] = []  # 眉
            morphs_by_panel[3] = []  # 口
            morphs_by_panel[4] = []  # 他
            morphs_by_panel[0] = []  # システム予約

            # モーフデータリスト
            for morph_idx in range(self.read_int(4)):
                morph = Morph(
                    name=self.read_text(),
                    english_name=self.read_text(),
                    panel=self.read_int(1),
                    morph_type=self.read_int(1)
                )

                offset_size = self.read_int(4)

                if morph.morph_type == 0:
                    # group
                    morph.offsets = [self.read_group_morph_data() for _ in range(offset_size)]
                elif morph.morph_type == 1:
                    # vertex
                    morph.offsets = [self.read_vertex_position_morph_offset() for _ in range(offset_size)]
                elif morph.morph_type == 2:
                    # bone
                    morph.offsets = [self.read_bone_morph_data() for _ in range(offset_size)]
                elif morph.morph_type == 3:
                    # uv
                    morph.offsets = [self.read_uv_morph_data() for _ in range(offset_size)]
                elif morph.morph_type == 4:
                    # uv extended1
                    morph.offsets = [self.read_uv_morph_data() for _ in range(offset_size)]
                elif morph.morph_type == 5:
                    # uv extended2
                    morph.offsets = [self.read_uv_morph_data() for _ in range(offset_size)]
                elif morph.morph_type == 6:
                    # uv extended3
                    morph.offsets = [self.read_uv_morph_data() for _ in range(offset_size)]
                elif morph.morph_type == 7:
                    # uv extended4
                    morph.offsets = [self.read_uv_morph_data() for _ in range(offset_size)]
                elif morph.morph_type == 8:
                    # material
                    morph.data = [self.read_material_morph_data() for _ in range(offset_size)]
                else:
                    raise MParseException("unknown morph type: {0}".format(morph.morph_type))

                # モーフのINDEXは、先頭から順番に設定
                morph.index = morph_idx

                if morph.panel not in morphs_by_panel.keys():
                    # ないと思うが念のためパネル情報がなければ追加
                    morphs_by_panel[morph.panel] = 0

                morphs_by_panel[morph.panel].append(morph)

            # モーフのパネル順に並び替えてモーフを登録していく
            for _, mlist in morphs_by_panel.items():
                for m in mlist:
                    pmx.morphs[m.name] = m

            logger.test("len(morphs): %s", len(pmx.morphs))

            logger.info("-- PMX モーフ読み込み完了")

            # 表示枠データリスト
            for _ in range(self.read_int(4)):
                display_slot = DisplaySlot(
                    name=self.read_text(),
                    english_name=self.read_text(),
                    special_flag=self.read_int(1)
                )

                display_count = self.read_int(4)

                for _ in range(display_count):
                    display_type = self.read_int(1)
                    if display_type == 0:
                        born_idx = self.read_bone_index_size()
                        display_slot.references.append((display_type, born_idx))
                        # ボーン表示ON
                        for v in pmx.bones.values():
                            if v.index == born_idx:
                                v.display = True
                    elif display_type == 1:
                        morph_idx = self.read_morph_index_size()
                        display_slot.references.append((display_type, morph_idx))
                        # モーフ表示ON
                        for v in pmx.morphs.values():
                            if v.index == morph_idx:
                                v.display = True
                            # logger.test("v: %s, display: %s", v.name, v.display)
                    else:
                        raise MParseException("unknown display_type: {0}".format(display_type))

                pmx.display_slots[display_slot.name] = display_slot

            logger.test("len(display_slots): %s", len(pmx.display_slots))

            logger.info("-- PMX 表示枠読み込み完了")

            # 剛体データリスト
            for rigidbody_idx in range(self.read_int(4)):
                rigidbody = RigidBody(
                    name=self.read_text(),
                    english_name=self.read_text(),
                    bone_index=self.read_bone_index_size(),
                    collision_group=self.read_int(1),
                    no_collision_group=self.read_int(2),
                    shape_type=self.read_int(1),
                    shape_size=self.read_Vector3D(),
                    shape_position=self.read_Vector3D(),
                    shape_rotation=self.read_Vector3D(),
                    mass=self.read_float(),
                    linear_damping=self.read_float(),
                    angular_damping=self.read_float(),
                    restitution=self.read_float(),
                    friction=self.read_float(),
                    mode=self.read_int(1)
                )

                # ボーンのINDEX
                rigidbody.index = rigidbody_idx

                pmx.rigidbodies[rigidbody.name] = rigidbody
                # インデックス逆引きも登録
                pmx.rigidbody_indexes[rigidbody.index] = rigidbody.name

            logger.test("len(rigidbodies): %s", len(pmx.rigidbodies))

            logger.info("-- PMX 剛体読み込み完了")

            # ジョイントデータリスト
            for joint_idx in range(self.read_int(4)):
                joint = Joint(
                    name=self.read_text(),
                    english_name=self.read_text(),
                    joint_type=self.read_int(1),
                    rigidbody_index_a=self.read_rigidbody_index_size(),
                    rigidbody_index_b=self.read_rigidbody_index_size(),
                    position=self.read_Vector3D(),
                    rotation=self.read_Vector3D(),
                    translation_limit_min=self.read_Vector3D(),
                    translation_limit_max=self.read_Vector3D(),
                    rotation_limit_min=self.read_Vector3D(),
                    rotation_limit_max=self.read_Vector3D(),
                    spring_constant_translation=self.read_Vector3D(),
                    spring_constant_rotation=self.read_Vector3D()
                )

                pmx.joints[joint.name] = joint

            logger.test("len(joints): %s", len(pmx.joints))

            logger.info("-- PMX ジョイント読み込み完了")

        # ハッシュを設定
        pmx.digest = self.hexdigest()
        logger.test("pmx: %s, hash: %s", pmx.name, pmx.digest)

        # 腕がサイジング可能かチェック
        pmx.can_arm_sizing = pmx.check_arm_bone_can_sizing()
        logger.test("pmx: %s, can_arm_sizing: %s", pmx.name, pmx.can_arm_sizing)

        # # 上半身がサイジング可能かチェック
        # pmx.can_upper_sizing = pmx.check_upper_bone_can_sizing()
        # logger.test("pmx: %s, can_upper_sizing: %s", pmx.name, pmx.can_upper_sizing)

        return pmx

    def hexdigest(self):
        sha1 = hashlib.sha1()

        with open(self.file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(2048 * sha1.block_size), b''):
                sha1.update(chunk)

        sha1.update(chunk)

        # ファイルパスをハッシュに含める
        sha1.update(self.file_path.encode('utf-8'))

        return sha1.hexdigest()

    def calc_bone_length(self, bones, bone_indexes):
        for k, v in bones.items():
            if k in ["左足ＩＫ", "右足ＩＫ", "右足ＩＫ親", "左足ＩＫ親"] and v.getIkFlag():
                #   足IKの場合、ひざボーンの位置を採用する
                knee_pos = MVector3D(0, 0, 0)
                for l in v.ik.link:
                    logger.test("k %s, link %s", k, l)
                    if l.bone_index in bone_indexes and "ひざ" in bones[bone_indexes[l.bone_index]].name:
                        # 存在するボーンで、大きい方を採用
                        knee_pos = bones[bone_indexes[l.bone_index]].position
                v.len = knee_pos.length()

            elif k in ["左つま先ＩＫ", "右つま先ＩＫ"] and v.getIkFlag():
                # IKの場合、リンクボーンの離れている方を採用する
                farer_pos = MVector3D(0, 0, 0)
                for l in v.ik.link:
                    logger.test("k %s, link %s", k, l)
                    if l.bone_index in bone_indexes and farer_pos.length() < bones[bone_indexes[l.bone_index]].position.length():
                        # 存在するボーンで、大きい方を採用
                        farer_pos = bones[bone_indexes[l.bone_index]].position
                        logger.test("farer: %s", bones[bone_indexes[l.bone_index]].position)
                # 最も大きな値（離れている）のを採用
                v.len = farer_pos.length()

            elif k in ["グルーブ", "センター", "腰"]:
                # 親がグルーブの場合、センターとの連動は行わない
                v.len = v.position.length()
                if k == "センター":
                    v.len_3d = MVector3D(1, v.position.length(), 1)
                else:
                    v.len_3d = MVector3D(1, 1, 1)
            else:
                # IK以外の場合、親ボーンとの間の長さを「親ボーン」に設定する
                if v.parent_index is not None and v.parent_index in bone_indexes and not bone_indexes[v.parent_index] in ["腰", "グルーブ", "センター", "左足ＩＫ", "右足ＩＫ", "左つま先ＩＫ", "右つま先ＩＫ", "右足ＩＫ親", "左足ＩＫ親"]:
                    # 親ボーンを採用
                    pos = v.position - bones[bone_indexes[v.parent_index]].position
                    if v.len > 0:
                        # 既にある場合、平均値を求めて設定する
                        bones[bone_indexes[v.parent_index]].len = (v.len + pos.length()) / 2
                        bones[bone_indexes[v.parent_index]].len_3d = (v.len_3d + pos) / 2
                    else:
                        # 0の場合はそのまま追加
                        bones[bone_indexes[v.parent_index]].len = pos.length()
                        bones[bone_indexes[v.parent_index]].len_3d = pos

                    logger.test("bone: %s, len_3d: %s", bone_indexes[v.parent_index], bones[bone_indexes[v.parent_index]].len_3d)
                else:
                    # 自分が最親の場合、そのまま長さ
                    v.len = v.position.length()
                    v.len_3d = v.position

                    logger.test("bone: %s, len_3d: %s", v.name, v.len_3d)

    def read_group_morph_data(self):
        return Morph.GroupMorphData(
            self.read_morph_index_size(),
            self.read_float()
        )

    def read_vertex_position_morph_offset(self):
        return Morph.VertexMorphOffset(
            self.read_vertex_index_size(), self.read_Vector3D())

    def read_bone_morph_data(self):
        return Morph.BoneMorphData(
            self.read_bone_index_size(),
            self.read_Vector3D(),
            self.read_Quaternion()
        )

    def read_uv_morph_data(self):
        return Morph.UVMorphData(
            self.read_vertex_index_size(),
            self.read_Vector4D(),
        )

    def read_material_morph_data(self):
        # 材質モーフはRGB(A)に負数が入る場合があるので、Vector型で保持
        return Morph.MaterialMorphData(
            self.read_material_index_size(),
            self.read_int(1),
            self.read_Vector4D(),
            self.read_Vector3D(),
            self.read_float(),
            self.read_Vector3D(),
            self.read_Vector4D(),
            self.read_float(),
            self.read_Vector4D(),
            self.read_Vector4D(),
            self.read_Vector4D()
        )

    def read_RGB(self):
        return MVector3D(int(self.read_float()), int(self.read_float()), int(self.read_float()))

    def read_RGBA(self):
        return MVector4D(int(self.read_float()), int(self.read_float()), int(self.read_float()), int(self.read_float()))

    def read_Vector4D(self):
        return MVector4D(self.read_float(), self.read_float(), self.read_float(), self.read_float())

    def read_Vector3D(self):
        return MVector3D(self.read_float(), self.read_float(), self.read_float())

    def read_Vector2D(self):
        return [self.read_float(), self.read_float()]

    def read_Quaternion(self):
        x = self.read_float()
        y = self.read_float()
        z = self.read_float()
        scalar = self.read_float()
        return MQuaternion(scalar, x, y, z)

    def read_deform(self):
        deform_type = self.read_int(1)

        if deform_type == 0:
            # BDEF1
            return Vertex.Bdef1(self.read_bone_index_size())
        elif deform_type == 1:
            # BDEF2
            return Vertex.Bdef2(
                self.read_bone_index_size(),
                self.read_bone_index_size(),
                self.read_float()
            )
        elif deform_type == 2:
            # BDEF4
            return Vertex.Bdef4(
                self.read_bone_index_size(),
                self.read_bone_index_size(),
                self.read_bone_index_size(),
                self.read_bone_index_size(),
                self.read_float(),
                self.read_float(),
                self.read_float(),
                self.read_float()
            )
        elif deform_type == 3:
            # SDEF
            return Vertex.Sdef(
                self.read_bone_index_size(),
                self.read_bone_index_size(),
                self.read_float(),
                self.read_Vector3D(),
                self.read_Vector3D(),
                self.read_Vector3D()
            )
        elif deform_type == 4:
            # QDEF
            return Vertex.Qdef(
                self.read_bone_index_size(),
                self.read_bone_index_size(),
                self.read_float(),
                self.read_Vector3D(),
                self.read_Vector3D(),
                self.read_Vector3D()
            )
        else:
            raise MParseException("unknown deform_type: {0}".format(deform_type))

    # 文字列の解凍（エンコーディングに基づく）
    def define_read_text(self, text_encoding):
        if text_encoding == 0:
            def read_text():
                format_size = self.read_int(4)
                bresult = self.unpack(format_size, "{0}s".format(format_size))
                return bresult.decode("utf-16-le")
            return read_text
        elif text_encoding == 1:
            def read_text():
                format_size = self.read_int(4)
                bresult = self.unpack(format_size, "{0}s".format(format_size))
                return bresult.decode("UTF8")
            return read_text
        else:
            raise MParseException("define_read_text 定義エラー {0}".format(text_encoding))

    # 整数の解凍
    def read_int(self, format_size):
        if format_size == 1:
            format_type = "b"
        elif format_size == 2:
            format_type = "h"
        elif format_size == 4:
            format_type = "i"
        else:
            raise MParseException("read_int format_sizeエラー {0}".format(format_size))

        return self.unpack(format_size, format_type)

    # 整数の解凍
    def read_uint(self, format_size):
        if format_size == 1:
            format_type = "B"
        elif format_size == 2:
            format_type = "H"
        elif format_size == 4:
            format_type = "I"
        else:
            raise MParseException("read_uint format_sizeエラー {0}".format(format_size))

        return self.unpack(format_size, format_type)

    # 小数の解凍
    def read_float(self, format_size=4):
        if format_size == 4:
            format_type = "f"
        elif format_size == 8:
            format_type = "d"
        else:
            raise MParseException("read_float format_sizeエラー {0}".format(format_size))

        return self.unpack(format_size, format_type)

    # 解凍して、offsetを更新する
    def unpack(self, format_size, format):
        bresult = struct.unpack_from(format, self.buffer, self.offset)

        # オフセットを更新する
        self.offset += format_size

        if bresult:
            result = bresult[0]
        else:
            result = None

        return result

    # 指定されたボーンの先を取得する
    def calc_tail_pos(self, model, bone_name: str):
        if bone_name not in model.bones:
            return MVector3D()
        
        bone = model.bones[bone_name]
        to_pos = MVector3D()

        from_pos = model.bones[bone.name].position
        if bone.tail_position != MVector3D():
            # 表示先が相対パスの場合、保持
            to_pos = from_pos + bone.tail_position
        elif bone.tail_index >= 0 and bone.tail_index in model.bone_indexes and model.bones[model.bone_indexes[bone.tail_index]].position != bone.position:
            # 表示先が指定されているの場合、保持
            to_pos = model.bones[model.bone_indexes[bone.tail_index]].position
        else:
            # 表示先がない場合、とりあえず子ボーンのどれかを選択
            for b in model.bones.values():
                if b.parent_index == bone.index and model.bones[model.bone_indexes[b.index]].position != bone.position:
                    to_pos = model.bones[model.bone_indexes[b.index]].position
                    break

        return to_pos
