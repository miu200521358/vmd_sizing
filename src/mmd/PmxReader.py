# -*- coding: utf-8 -*-
#
import struct
import hashlib
import random
import string

from mmd.PmxData import PmxModel, Bone, RigidBody, Vertex, Material, Morph, DisplaySlot, RigidBody, Joint, Ik, IkLink, Bdef1, Bdef2, Bdef4, Sdef, Qdef, MaterialMorphData, UVMorphData, BoneMorphData, VertexMorphOffset, GroupMorphData # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException, MKilledException, MParseException

logger = MLogger(__name__, level=1)


class PmxReader:
    def __init__(self, file_path, is_check=True, is_sizing=True):
        self.file_path = file_path
        self.is_check = is_check
        self.is_sizing = is_sizing
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
            extended_uv = self.read_int(1)
            logger.test("extended_uv: %s (%s)", extended_uv, self.offset)

            # 頂点Indexサイズ
            self.vertex_index_size = self.read_int(1)
            logger.test("vertex_index_size: %s (%s)", self.vertex_index_size, self.offset)
            # サイズに基づいて頂点INDEX解凍処理を定義
            self.read_vertex_index_size = self.define_read_vertex_idx(self.vertex_index_size)

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

        try:
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
                pmx.extended_uv = self.read_int(1)
                logger.test("extended_uv: %s (%s)", pmx.extended_uv, self.offset)

                # 頂点Indexサイズ
                self.vertex_index_size = self.read_int(1)
                logger.test("vertex_index_size: %s (%s)", self.vertex_index_size, self.offset)
                # サイズに基づいて頂点INDEX解凍処理を定義
                self.read_vertex_index_size = self.define_read_vertex_idx(self.vertex_index_size)

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
                    if pmx.extended_uv > 0:
                        # 追加UVがある場合
                        for _ in range(pmx.extended_uv):
                            extended_uvs.append(self.read_Vector4D())

                    deform = self.read_deform()
                    edge_factor = self.read_float()

                    # 頂点をウェイトボーンごとに分けて保持する
                    vertex = Vertex(vertex_idx, position, normal, uv, extended_uvs, deform, edge_factor)
                    for bone_idx in vertex.deform.get_idx_list():
                        if bone_idx not in pmx.vertices:
                            pmx.vertices[bone_idx] = []
                        pmx.vertices[bone_idx].append(vertex)
                    
                    # 全頂点データとしても保持
                    pmx.vertex_dict[vertex.index] = vertex
                    
                logger.test("len(vertices): %s", len(pmx.vertices))
                logger.test("vertices.keys: %s", pmx.vertices.keys())
                logger.info("-- PMX 頂点読み込み完了")

                # 面データリスト
                for iidx in range(self.read_int(4)):
                    index_idx = iidx // 3
                    if index_idx not in pmx.indices.keys():
                        pmx.indices[index_idx] = []

                    pmx.indices[index_idx].append(self.read_vertex_index_size(self.vertex_index_size))
                    
                logger.test("len(indices): %s", len(pmx.indices))
                
                logger.info("-- PMX 面読み込み完了")

                # テクスチャデータリスト
                for _ in range(self.read_int(4)):
                    pmx.textures.append(self.read_text())
                logger.test("len(textures): %s", len(pmx.textures))

                logger.info("-- PMX テクスチャ読み込み完了")

                # 全面データの件数
                total_index_count = 0

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

                    # 頂点を材質の頂点数を元に割り振る
                    if material.name not in pmx.material_indices:
                        pmx.material_indices[material.name] = []
                        
                    if material.name not in pmx.material_vertices:
                        pmx.material_vertices[material.name] = []
                    
                    logger.test("material.vertex_count: %s: %s total: %s", material.name, material.vertex_count, total_index_count)

                    for iidx in range(total_index_count, total_index_count + (material.vertex_count // 3)):
                        pmx.material_indices[material.name].append(iidx)
                        for iiidx in pmx.indices[iidx]:
                            pmx.material_vertices[material.name].append(iiidx)
                
                    # 全面数加算
                    total_index_count += (material.vertex_count // 3)

                    pmx.materials[material.name] = material
                    pmx.material_indices[material.index] = material.name
                logger.test("len(materials): %s", len(pmx.materials))

                logger.info("-- PMX 材質読み込み完了")
                
                pmx.bones = {}
                pmx.bone_indexes = {}

                if self.is_sizing:
                    # サイジング用ルートボーン
                    sizing_root_bone = Bone("SIZING_ROOT_BONE", "SIZING_ROOT_BONE", MVector3D(), -1, 0, 0, is_sizing=True)
                    sizing_root_bone.index = -1
                    sizing_root_bone.is_sizing = True
                    pmx.bones[sizing_root_bone.name] = sizing_root_bone
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
                        bone.ik = Ik(
                            target_index=self.read_bone_index_size(),
                            loop=self.read_int(4),
                            limit_radian=self.read_float()
                        )

                        # IKリンク取得
                        for _ in range(self.read_int(4)):

                            link = IkLink(
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
                    else:
                        # 既に同じボーン名がある場合、処理がおかしくなるので乱数追加
                        logger.warning("ボーン名が重複しているため、後のボーンを無視します。\nモデル: %s\n重複ボーン名: %s(%s - %s)" % (pmx.name, bone.name, pmx.bones[bone.name].index, bone_idx), decoration=MLogger.DECORATION_BOX)     # noqa
                        # 乱数追加してボーンリストにだけ追加
                        pmx.bones[bone.name + randomname(3)] = bone
                        # INDEX逆引きは登録しない（同名のを優先させる）
                
                if self.is_sizing:
                    # サイジング用ボーン ---------
                    if "頭" in pmx.bones:
                        # 頭頂ボーン
                        head_top_vertex = pmx.get_head_top_vertex()
                        pmx.head_top_vertex = head_top_vertex
                        head_top_bone = Bone("頭頂実体", "head_top", head_top_vertex.position.copy(), pmx.bones["頭"].index, pmx.bones["頭"].layer, 0, tail_position=MVector3D(0, -1, 0), is_sizing=True)
                        head_top_bone.index = len(pmx.bones.keys())
                        pmx.bones[head_top_bone.name] = head_top_bone
                        pmx.bone_indexes[head_top_bone.index] = head_top_bone.name

                    if "右足先EX" in pmx.bones or "右足ＩＫ" in pmx.bones:
                        # 右足底実体ボーン
                        right_sole_vertex = None
                        if "右足先EX" in pmx.bones:
                            right_sole_vertex = Vertex(-1, MVector3D(pmx.bones["右足先EX"].position.x(), 0, pmx.bones["右足先EX"].position.z()), MVector3D(), MVector2D(), [], Bdef1(-1), -1)
                        elif "右足ＩＫ" in pmx.bones:
                            right_sole_vertex = pmx.get_sole_vertex("右")
                        
                        if right_sole_vertex:
                            pmx.right_sole_vertex = right_sole_vertex
                            right_sole_bone = Bone("右足底実体", "right sole entity", right_sole_vertex.position.copy(), -1, 0, 0, is_sizing=True)
                            right_sole_bone.index = len(pmx.bones.keys())
                            
                            if "右足先EX" in pmx.bones:
                                right_sole_bone.parent_index = pmx.bones["右足先EX"].index
                                right_sole_bone.layer = pmx.bones["右足先EX"].layer
                            else:
                                right_sole_bone.parent_index = pmx.bones["右足ＩＫ"].index
                                right_sole_bone.layer = pmx.bones["右足ＩＫ"].layer
                            
                            logger.debug("右足底実体: %s, parent: %s(%s)", right_sole_bone.index, right_sole_bone.parent_index, pmx.bone_indexes[right_sole_bone.parent_index])

                            pmx.bones[right_sole_bone.name] = right_sole_bone
                            pmx.bone_indexes[right_sole_bone.index] = right_sole_bone.name

                    if "左足先EX" in pmx.bones or "左足ＩＫ" in pmx.bones:
                        # 左足底実体ボーン
                        left_sole_vertex = None
                        if "左足先EX" in pmx.bones:
                            left_sole_vertex = Vertex(-1, MVector3D(pmx.bones["左足先EX"].position.x(), 0, pmx.bones["左足先EX"].position.z()), MVector3D(), MVector2D(), [], Bdef1(-1), -1)
                        elif "左足ＩＫ" in pmx.bones:
                            left_sole_vertex = pmx.get_sole_vertex("左")
                        
                        if left_sole_vertex:
                            pmx.left_sole_vertex = left_sole_vertex
                            left_sole_bone = Bone("左足底実体", "left sole entity", left_sole_vertex.position.copy(), -1, 0, 0, is_sizing=True)
                            left_sole_bone.index = len(pmx.bones.keys())
                            
                            if "左足先EX" in pmx.bones:
                                left_sole_bone.parent_index = pmx.bones["左足先EX"].index
                                left_sole_bone.layer = pmx.bones["左足先EX"].layer
                            else:
                                left_sole_bone.parent_index = pmx.bones["左足ＩＫ"].index
                                left_sole_bone.layer = pmx.bones["左足ＩＫ"].layer

                            logger.debug("左足底実体: %s, parent: %s(%s)", left_sole_bone.index, left_sole_bone.parent_index, pmx.bone_indexes[left_sole_bone.parent_index])

                            pmx.bones[left_sole_bone.name] = left_sole_bone
                            pmx.bone_indexes[left_sole_bone.index] = left_sole_bone.name

                    if "右足ＩＫ" in pmx.bones or "右つま先ＩＫ" in pmx.bones:
                        # 右つま先ボーン
                        right_toe_vertex = pmx.get_toe_vertex("右")
                        if right_toe_vertex:
                            pmx.right_toe_vertex = right_toe_vertex
                            right_toe_pos = right_toe_vertex.position.copy()
                            right_toe_pos.setY(0)
                            right_toe_bone = Bone("右つま先実体", "right toe entity", right_toe_pos, -1, 0, 0, is_sizing=True)
                            right_toe_bone.index = len(pmx.bones.keys())

                            if "右足底実体" in pmx.bones:
                                right_toe_bone.parent_index = pmx.bones["右足底実体"].index
                                right_toe_bone.layer = pmx.bones["右足底実体"].layer
                            else:
                                right_toe_bone.parent_index = pmx.bones["右つま先ＩＫ"].index
                                right_toe_bone.layer = pmx.bones["右つま先ＩＫ"].layer

                            logger.debug("右つま先実体: %s, parent: %s(%s)", right_toe_bone.index, right_toe_bone.parent_index, pmx.bone_indexes[right_toe_bone.parent_index])

                            pmx.bones[right_toe_bone.name] = right_toe_bone
                            pmx.bone_indexes[right_toe_bone.index] = right_toe_bone.name

                    if "左足ＩＫ" in pmx.bones or "左つま先ＩＫ" in pmx.bones:
                        # 左つま先ボーン
                        left_toe_vertex = pmx.get_toe_vertex("左")
                        if left_toe_vertex:
                            pmx.left_toe_vertex = left_toe_vertex
                            left_toe_pos = left_toe_vertex.position.copy()
                            left_toe_pos.setY(0)
                            left_toe_bone = Bone("左つま先実体", "left toe entity", left_toe_pos, -1, 0, 0, is_sizing=True)
                            left_toe_bone.index = len(pmx.bones.keys())

                            if "左足底実体" in pmx.bones:
                                left_toe_bone.parent_index = pmx.bones["左足底実体"].index
                                left_toe_bone.layer = pmx.bones["左足底実体"].layer
                            else:
                                left_toe_bone.parent_index = pmx.bones["左つま先ＩＫ"].index
                                left_toe_bone.layer = pmx.bones["左つま先ＩＫ"].layer

                            logger.debug("左つま先実体: %s, parent: %s(%s)", left_toe_bone.index, left_toe_bone.parent_index, pmx.bone_indexes[left_toe_bone.parent_index])

                            pmx.bones[left_toe_bone.name] = left_toe_bone
                            pmx.bone_indexes[left_toe_bone.index] = left_toe_bone.name

                    # 首根元ボーン
                    if "左肩" in pmx.bones and "右肩" in pmx.bones:
                        neck_base_vertex = Vertex(-1, (pmx.bones["左肩"].position + pmx.bones["右肩"].position) / 2, MVector3D(), MVector2D(), [], Bdef1(-1), -1)
                        neck_base_vertex.position.setX(0)
                        neck_base_bone = Bone("首根元", "base of neck", neck_base_vertex.position.copy(), -1, 0, 0, is_sizing=True)

                        if "上半身2" in pmx.bones:
                            # 上半身2がある場合、表示先は、上半身2
                            neck_base_bone.parent_index = pmx.bones["上半身2"].index
                            neck_base_bone.tail_index = pmx.bones["上半身2"].index
                            neck_base_bone.layer = pmx.bones["上半身2"].layer
                        elif "上半身" in pmx.bones:
                            neck_base_bone.parent_index = pmx.bones["上半身"].index
                            neck_base_bone.tail_index = pmx.bones["上半身"].index
                            neck_base_bone.layer = pmx.bones["上半身"].layer

                        neck_base_bone.index = len(pmx.bones.keys())
                        pmx.bones[neck_base_bone.name] = neck_base_bone
                        pmx.bone_indexes[neck_base_bone.index] = neck_base_bone.name
                        
                        if "左肩P" in pmx.bones:
                            pmx.bones["左肩P"].parent_index = neck_base_bone.index
                        else:
                            pmx.bones["左肩"].parent_index = neck_base_bone.index
                        
                        if "右肩P" in pmx.bones:
                            pmx.bones["右肩P"].parent_index = neck_base_bone.index
                        else:
                            pmx.bones["右肩"].parent_index = neck_base_bone.index
                        
                    # 首根元2ボーン
                    if "左腕" in pmx.bones and "右腕" in pmx.bones:
                        neck_base2_vertex = Vertex(-1, (pmx.bones["左腕"].position + pmx.bones["右腕"].position) / 2, MVector3D(), MVector2D(), [], Bdef1(-1), -1)
                        neck_base2_vertex.position.setX(0)
                        neck_base2_bone = Bone("首根元2", "base of neck", neck_base2_vertex.position.copy(), -1, 0, 0, is_sizing=True)

                        if "首根元" in pmx.bones:
                            # 首根元が既にある場合は首根元
                            neck_base2_bone.parent_index = pmx.bones["首根元"].index
                            neck_base2_bone.tail_index = pmx.bones["首根元"].index
                            neck_base2_bone.layer = pmx.bones["首根元"].layer
                        elif "上半身2" in pmx.bones:
                            # 上半身2がある場合、表示先は、上半身2
                            neck_base2_bone.parent_index = pmx.bones["上半身2"].index
                            neck_base2_bone.tail_index = pmx.bones["上半身2"].index
                            neck_base2_bone.layer = pmx.bones["上半身2"].layer
                        elif "上半身" in pmx.bones:
                            neck_base2_bone.parent_index = pmx.bones["上半身"].index
                            neck_base2_bone.tail_index = pmx.bones["上半身"].index
                            neck_base2_bone.layer = pmx.bones["上半身"].layer

                        neck_base2_bone.index = len(pmx.bones.keys())
                        pmx.bones[neck_base2_bone.name] = neck_base2_bone
                        pmx.bone_indexes[neck_base2_bone.index] = neck_base2_bone.name

                    if "右肩" in pmx.bones:
                        # 右肩下延長ボーン
                        right_shoulder_under_pos = pmx.bones["右肩"].position.copy()
                        right_shoulder_under_pos.setY(right_shoulder_under_pos.y() - 1)
                        right_shoulder_under_bone = Bone("右肩下延長", "", right_shoulder_under_pos, pmx.bones["右肩"].index, pmx.bones["右肩"].layer, 0, is_sizing=True)
                        right_shoulder_under_bone.index = len(pmx.bones.keys())
                        pmx.bones[right_shoulder_under_bone.name] = right_shoulder_under_bone
                        pmx.bone_indexes[right_shoulder_under_bone.index] = right_shoulder_under_bone.name

                    if "左肩" in pmx.bones:
                        # 左肩下延長ボーン
                        left_shoulder_under_pos = pmx.bones["左肩"].position.copy()
                        left_shoulder_under_pos.setY(left_shoulder_under_pos.y() - 1)
                        left_shoulder_under_bone = Bone("左肩下延長", "", left_shoulder_under_pos, pmx.bones["左肩"].index, pmx.bones["左肩"].layer, 0, is_sizing=True)
                        left_shoulder_under_bone.index = len(pmx.bones.keys())
                        pmx.bones[left_shoulder_under_bone.name] = left_shoulder_under_bone
                        pmx.bone_indexes[left_shoulder_under_bone.index] = left_shoulder_under_bone.name

                    if "右ひじ" in pmx.bones and "右腕" in pmx.bones:
                        # 右腕ひじ中間ボーン
                        right_arm_middle_pos = (pmx.bones["右ひじ"].position + pmx.bones["右腕"].position) / 2
                        right_arm_middle_bone = Bone("右腕ひじ中間", "", right_arm_middle_pos, -1, 0, 0, is_sizing=True)
                        right_arm_middle_bone.index = len(pmx.bones.keys())
                        pmx.bones[right_arm_middle_bone.name] = right_arm_middle_bone
                        pmx.bone_indexes[right_arm_middle_bone.index] = right_arm_middle_bone.name

                        if "右腕捩" in pmx.bones:
                            right_arm_middle_bone.parent_index = pmx.bones["右腕捩"].index
                            right_arm_middle_bone.layer = pmx.bones["右腕捩"].layer
                        else:
                            right_arm_middle_bone.parent_index = pmx.bones["右腕"].index
                            right_arm_middle_bone.layer = pmx.bones["右腕"].layer

                        right_arm_middle_bone.tail_index = pmx.bones["右ひじ"].index
                        pmx.bones["右ひじ"].parent_index = right_arm_middle_bone.index

                    if "左ひじ" in pmx.bones and "左腕" in pmx.bones:
                        # 左腕ひじ中間ボーン
                        left_arm_middle_pos = (pmx.bones["左ひじ"].position + pmx.bones["左腕"].position) / 2
                        left_arm_middle_bone = Bone("左腕ひじ中間", "", left_arm_middle_pos, -1, 0, 0, is_sizing=True)
                        left_arm_middle_bone.index = len(pmx.bones.keys())
                        pmx.bones[left_arm_middle_bone.name] = left_arm_middle_bone
                        pmx.bone_indexes[left_arm_middle_bone.index] = left_arm_middle_bone.name

                        if "左腕捩" in pmx.bones:
                            left_arm_middle_bone.parent_index = pmx.bones["左腕捩"].index
                            left_arm_middle_bone.layer = pmx.bones["左腕捩"].layer
                        else:
                            left_arm_middle_bone.parent_index = pmx.bones["左腕"].index
                            left_arm_middle_bone.layer = pmx.bones["左腕"].layer

                        left_arm_middle_bone.tail_index = pmx.bones["左ひじ"].index
                        pmx.bones["左ひじ"].parent_index = left_arm_middle_bone.index

                    if "右ひじ" in pmx.bones and "右手首" in pmx.bones:
                        # 右ひじ手首中間ボーン
                        right_elbow_middle_pos = (pmx.bones["右ひじ"].position + pmx.bones["右手首"].position) / 2
                        right_elbow_middle_bone = Bone("右ひじ手首中間", "", right_elbow_middle_pos, -1, 0, 0, is_sizing=True)
                        right_elbow_middle_bone.index = len(pmx.bones.keys())
                        pmx.bones[right_elbow_middle_bone.name] = right_elbow_middle_bone
                        pmx.bone_indexes[right_elbow_middle_bone.index] = right_elbow_middle_bone.name

                        if "右手捩" in pmx.bones:
                            right_elbow_middle_bone.parent_index = pmx.bones["右手捩"].index
                            right_elbow_middle_bone.layer = pmx.bones["右手捩"].layer
                        else:
                            right_elbow_middle_bone.parent_index = pmx.bones["右ひじ"].index
                            right_elbow_middle_bone.layer = pmx.bones["右ひじ"].layer
                        right_elbow_middle_bone.tail_index = pmx.bones["右手首"].index
                        pmx.bones["右手首"].parent_index = right_elbow_middle_bone.index

                    if "左ひじ" in pmx.bones and "左手首" in pmx.bones:
                        # 左ひじ手首中間ボーン
                        left_elbow_middle_pos = (pmx.bones["左ひじ"].position + pmx.bones["左手首"].position) / 2
                        left_elbow_middle_bone = Bone("左ひじ手首中間", "", left_elbow_middle_pos, -1, 0, 0, is_sizing=True)
                        left_elbow_middle_bone.index = len(pmx.bones.keys())
                        pmx.bones[left_elbow_middle_bone.name] = left_elbow_middle_bone
                        pmx.bone_indexes[left_elbow_middle_bone.index] = left_elbow_middle_bone.name

                        if "左手捩" in pmx.bones:
                            left_elbow_middle_bone.parent_index = pmx.bones["左手捩"].index
                            left_elbow_middle_bone.layer = pmx.bones["左手捩"].layer
                        else:
                            left_elbow_middle_bone.parent_index = pmx.bones["左ひじ"].index
                            left_elbow_middle_bone.layer = pmx.bones["左ひじ"].layer
                        left_elbow_middle_bone.tail_index = pmx.bones["左手首"].index
                        pmx.bones["左手首"].parent_index = left_elbow_middle_bone.index

                    if "右つま先" in pmx.bones or "右つま先ＩＫ" in pmx.bones:
                        toe_bone_name = "右つま先" if "右つま先" in pmx.bones else pmx.bone_indexes[pmx.bones["右つま先ＩＫ"].ik.target_index]

                        right_big_toe_bone = Bone("右足親指", "", pmx.bones[toe_bone_name].position + MVector3D(0.5, 0, 0), -1, 0, 0, is_sizing=True)
                        right_big_toe_bone.parent_index = pmx.bones[toe_bone_name].index
                        right_big_toe_bone.index = len(pmx.bones.keys())
                        pmx.bones[right_big_toe_bone.name] = right_big_toe_bone
                        pmx.bone_indexes[right_big_toe_bone.index] = right_big_toe_bone.name

                        right_small_toe_bone = Bone("右足小指", "", pmx.bones[toe_bone_name].position + MVector3D(-0.5, 0, 0), -1, 0, 0, is_sizing=True)
                        right_small_toe_bone.parent_index = pmx.bones[toe_bone_name].index
                        right_small_toe_bone.index = len(pmx.bones.keys())
                        pmx.bones[right_small_toe_bone.name] = right_small_toe_bone
                        pmx.bone_indexes[right_small_toe_bone.index] = right_small_toe_bone.name

                    if "右足首" in pmx.bones:
                        right_heel_bone = Bone("右かかと", "", MVector3D(pmx.bones["右足首"].position.x(), 0, pmx.bones["右足首"].position.z()), -1, 0, 0, is_sizing=True)
                        if "右足小指" in pmx.bones:
                            right_heel_bone.parent_index = pmx.bones["右足小指"].index
                            right_heel_bone.layer = pmx.bones["右足小指"].layer
                        else:
                            right_heel_bone.parent_index = pmx.bones["右足首"].index
                            right_heel_bone.layer = pmx.bones["右足首"].layer
                        right_heel_bone.index = len(pmx.bones.keys())
                        pmx.bones[right_heel_bone.name] = right_heel_bone
                        pmx.bone_indexes[right_heel_bone.index] = right_heel_bone.name

                    if "左つま先" in pmx.bones or "左つま先ＩＫ" in pmx.bones:
                        toe_bone_name = "左つま先" if "左つま先" in pmx.bones else pmx.bone_indexes[pmx.bones["左つま先ＩＫ"].ik.target_index]

                        left_big_toe_bone = Bone("左足親指", "", pmx.bones[toe_bone_name].position + MVector3D(0.5, 0, 0), -1, 0, 0, is_sizing=True)
                        left_big_toe_bone.parent_index = pmx.bones[toe_bone_name].index
                        left_big_toe_bone.layer = pmx.bones[toe_bone_name].layer
                        left_big_toe_bone.index = len(pmx.bones.keys())
                        pmx.bones[left_big_toe_bone.name] = left_big_toe_bone
                        pmx.bone_indexes[left_big_toe_bone.index] = left_big_toe_bone.name

                        left_small_toe_bone = Bone("左足小指", "", pmx.bones[toe_bone_name].position + MVector3D(-0.5, 0, 0), -1, 0, 0, is_sizing=True)
                        left_small_toe_bone.parent_index = pmx.bones[toe_bone_name].index
                        left_small_toe_bone.index = len(pmx.bones.keys())
                        pmx.bones[left_small_toe_bone.name] = left_small_toe_bone
                        pmx.bone_indexes[left_small_toe_bone.index] = left_small_toe_bone.name

                    if "左足首" in pmx.bones:
                        left_heel_bone = Bone("左かかと", "", MVector3D(pmx.bones["左足首"].position.x(), 0, pmx.bones["左足首"].position.z()), -1, 0, 0, is_sizing=True)
                        if "左足小指" in pmx.bones:
                            left_heel_bone.parent_index = pmx.bones["左足小指"].index
                            left_heel_bone.layer = pmx.bones["左足小指"].layer
                        else:
                            left_heel_bone.parent_index = pmx.bones["左足首"].index
                            left_heel_bone.layer = pmx.bones["左足首"].layer
                        left_heel_bone.index = len(pmx.bones.keys())
                        pmx.bones[left_heel_bone.name] = left_heel_bone
                        pmx.bone_indexes[left_heel_bone.index] = left_heel_bone.name

                    # 指先ボーンがない場合、代替で挿入
                    for direction in ["左", "右"]:
                        for (finger_name, end_joint_name) in [("親指", "２"), ("人指", "３"), ("中指", "３"), ("薬指", "３"), ("小指", "３")]:
                            end_joint_name = "{0}{1}{2}".format(direction, finger_name, end_joint_name)

                            if end_joint_name not in pmx.bones:
                                continue

                            to_joint_name = "{0}{1}{2}".format(direction, finger_name, "先実体")

                            finger_tail_vertex = pmx.get_finger_tail_vertex(end_joint_name, to_joint_name)
                            if finger_tail_vertex:
                                pmx.finger_tail_vertex = finger_tail_vertex
                                finger_tail_pos = finger_tail_vertex.position.copy()
                                finger_tail_bone = Bone(to_joint_name, "", finger_tail_pos, -1, 0, 0, is_sizing=True)
                                finger_tail_bone.index = len(pmx.bones.keys())
                                finger_tail_bone.parent_index = pmx.bones[end_joint_name].index
                                finger_tail_bone.layer = pmx.bones[end_joint_name].layer
                                pmx.bones[finger_tail_bone.name] = finger_tail_bone
                                pmx.bone_indexes[finger_tail_bone.index] = finger_tail_bone.name

                    # 足中間ボーン
                    if "左足" in pmx.bones and "右足" in pmx.bones:
                        leg_center_vertex = Vertex(-1, (pmx.bones["左足"].position + pmx.bones["右足"].position) / 2, MVector3D(), MVector2D(), [], Bdef1(-1), -1)
                        leg_center_vertex.position.setX(0)
                        leg_center_bone = Bone("足中間", "base of neck", leg_center_vertex.position.copy(), -1, 0, 0, is_sizing=True)

                        if "下半身" in pmx.bones:
                            leg_center_bone.parent_index = pmx.bones["下半身"].index
                            leg_center_bone.tail_index = pmx.bones["下半身"].index
                            leg_center_bone.layer = pmx.bones["下半身"].layer

                        leg_center_bone.index = len(pmx.bones.keys())
                        pmx.bones[leg_center_bone.name] = leg_center_bone
                        pmx.bone_indexes[leg_center_bone.index] = leg_center_bone.name
                    
                    # # ボーンの並び替え
                    # tmp_bones = {}
                    # tmp_bone_indexes = {}
                    # for k, v in pmx.bones.items():
                    #     tmp_bones[k] = v.copy()
                    #     tmp_bone_indexes[v.index] = k

                    # root_bone = (list(pmx.bones.values())[0]).copy()
                    # root_bone.index = -1
                    # root_bone.is_sizing = True

                    # pmx.bones = {}
                    # pmx.bone_indexes = {}
                    # pmx.bones[root_bone.name] = root_bone
                    # pmx.bone_indexes[root_bone.index] = root_bone.name
                    # index = -2
                    # for is_ik in [False, True]:
                    #     index = self.sort_bones(pmx, tmp_bones, tmp_bone_indexes, root_bone.index, is_ik, index)

                    # for bv in pmx.bones.values():
                    #     if bv.tail_index >= 0:
                    #         bv.tail_index = pmx.bones[tmp_bone_indexes[bv.tail_index]].index
                    #     if bv.effect_index >= 0:
                    #         bv.effect_index = pmx.bones[tmp_bone_indexes[bv.effect_index]].index
                    #     if bv.ik:
                    #         bv.ik.target_index = pmx.bones[tmp_bone_indexes[bv.ik.target_index]].index
                    #         for n in range(len(bv.ik.link)):
                    #             bv.ik.link[n].bone_index = pmx.bones[tmp_bone_indexes[bv.ik.link[n].bone_index]].index

                    logger.debug_info("bones: %s", ", ".join([f"{b.index:04d}-{b.parent_index:04d}[{b.name}]" for b in pmx.bones.values()]))

                    # ボーンの長さを計算する
                    self.calc_bone_length(pmx.bones, pmx.bone_indexes)

                logger.info("-- PMX ボーン読み込み完了")

                # 操作パネル (PMD:カテゴリ) 1:眉(左下) 2:目(左上) 3:口(右上) 4:その他(右下)
                morphs_by_panel = {}
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
                        morph.offsets = [self.read_material_morph_data() for _ in range(offset_size)]
                    else:
                        raise MParseException("unknown morph type: {0}".format(morph.morph_type))

                    # モーフのINDEXは、先頭から順番に設定
                    morph.index = morph_idx
                    # インデックス逆引きも登録
                    pmx.morph_indexes[morph.index] = morph.name
                    # そのままで保持
                    pmx.org_morphs[morph.name] = morph

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
                            bone_idx = self.read_bone_index_size()
                            display_slot.references.append((display_type, bone_idx))
                            # ボーン表示ON
                            for v in pmx.bones.values():
                                if v.index == bone_idx:
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
                        no_collision_group=self.read_uint(2),
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

                    # if rigidbody.no_collision_group < 0:
                    #     rigidbody.no_collision_group = 0
                    #     for nc in range(16):
                    #         rigidbody.no_collision_group |= 1 << nc

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

            if self.is_check:
                # 腕がサイジング可能かチェック
                pmx.can_arm_sizing = pmx.check_arm_bone_can_sizing()
                logger.test("pmx: %s, can_arm_sizing: %s", pmx.name, pmx.can_arm_sizing)

            # # 上半身がサイジング可能かチェック
            # pmx.can_upper_sizing = pmx.check_upper_bone_can_sizing()
            # logger.test("pmx: %s, can_upper_sizing: %s", pmx.name, pmx.can_upper_sizing)

            return pmx
        except MKilledException as ke:
            # 終了命令
            raise ke
        except SizingException as se:
            logger.error("Pmx読み込み処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
            return se
        except Exception as e:
            import traceback
            logger.error("Pmx読み込み処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
            raise e
    
    def sort_bones(self, pmx, tmp_bones, tmp_bone_indexes, bone_index, is_ik, index):
        for bk, bv in tmp_bones.items():
            if bv.getIkFlag() == is_ik and (bv.parent_index == bone_index or bv.name not in pmx.bones):
                index = self.regist_bone(pmx, tmp_bones, tmp_bone_indexes, bk, is_ik, index + 1)
        return index

    def regist_bone(self, pmx, tmp_bones, tmp_bone_indexes, bone_name, is_ik, index):
        bv = tmp_bones[bone_name]
        index, parent_index = self.get_bone_parent(pmx, tmp_bones, tmp_bone_indexes, bv.parent_index, is_ik, index)

        # 実データは改めてINDEXを計算
        bone = bv.copy()
        bone.index = index
        bone.parent_index = parent_index
        pmx.bones[bv.name] = bone
        pmx.bone_indexes[bone.index] = bv.name

        logger.test("regist_bone: %s, index: %s, parent: %s", bone_name, index, parent_index)

        return index

    def get_bone_parent(self, pmx, tmp_bones, tmp_bone_indexes, parent_index, is_ik, index):
        if index <= 0:
            return index, parent_index

        if tmp_bone_indexes[parent_index] not in pmx.bones:
            parent_index = self.regist_bone(pmx, tmp_bones, tmp_bone_indexes, tmp_bone_indexes[parent_index], is_ik, index)
            return index + 1, parent_index
        else:
            return index, pmx.bones[tmp_bone_indexes[parent_index]].index

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
                for lk in v.ik.link:
                    logger.test("k %s, link %s", k, lk)
                    if lk.bone_index in bone_indexes and "ひざ" in bones[bone_indexes[lk.bone_index]].name:
                        # 存在するボーンで、大きい方を採用
                        knee_pos = bones[bone_indexes[lk.bone_index]].position
                v.len_1d = knee_pos.length()

            elif k in ["左つま先ＩＫ", "右つま先ＩＫ"] and v.getIkFlag():
                # IKの場合、リンクボーンの離れている方を採用する
                farer_pos = MVector3D(0, 0, 0)
                for lk in v.ik.link:
                    logger.test("k %s, link %s", k, lk)
                    if lk.bone_index in bone_indexes and farer_pos.length() < bones[bone_indexes[lk.bone_index]].position.length():
                        # 存在するボーンで、大きい方を採用
                        farer_pos = bones[bone_indexes[lk.bone_index]].position
                        logger.test("farer: %s", bones[bone_indexes[lk.bone_index]].position)
                # 最も大きな値（離れている）のを採用
                v.len_1d = farer_pos.length()

            elif k in ["グルーブ", "センター", "腰"]:
                # 親がグルーブの場合、センターとの連動は行わない
                v.len_1d = v.position.length()
                if k == "センター":
                    v.len_3d = MVector3D(1, v.position.length(), 1)
                else:
                    v.len_3d = MVector3D(1, 1, 1)
            else:
                # IK以外の場合、親ボーンとの間の長さを「親ボーン」に設定する
                if v.parent_index is not None and v.parent_index in bone_indexes and not bone_indexes[v.parent_index] in ["腰", "グルーブ", "センター", "左足ＩＫ", "右足ＩＫ", "左つま先ＩＫ", "右つま先ＩＫ", "右足ＩＫ親", "左足ＩＫ親"]:
                    # 親ボーンを採用
                    pos = v.position - bones[bone_indexes[v.parent_index]].position
                    if v.len_1d > 0:
                        # 既にある場合、平均値を求めて設定する
                        bones[bone_indexes[v.parent_index]].len_1d = (v.len_1d + pos.length()) / 2
                        bones[bone_indexes[v.parent_index]].len_3d = (v.len_3d + pos) / 2
                    else:
                        # 0の場合はそのまま追加
                        bones[bone_indexes[v.parent_index]].len_1d = pos.length()
                        bones[bone_indexes[v.parent_index]].len_3d = pos

                    logger.test("bone: %s, len_3d: %s", bone_indexes[v.parent_index], bones[bone_indexes[v.parent_index]].len_3d)
                else:
                    # 自分が最親の場合、そのまま長さ
                    v.len_1d = v.position.length()
                    v.len_3d = v.position

                    logger.test("bone: %s, len_3d: %s", v.name, v.len_3d)

    def read_group_morph_data(self):
        return GroupMorphData(
            self.read_morph_index_size(),
            self.read_float()
        )

    def read_vertex_position_morph_offset(self):
        return VertexMorphOffset(
            self.read_vertex_index_size(self.vertex_index_size), self.read_Vector3D())

    def read_bone_morph_data(self):
        return BoneMorphData(
            self.read_bone_index_size(),
            self.read_Vector3D(),
            self.read_Quaternion()
        )

    def read_uv_morph_data(self):
        return UVMorphData(
            self.read_vertex_index_size(self.vertex_index_size),
            self.read_Vector4D(),
        )

    def read_material_morph_data(self):
        # 材質モーフはRGB(A)に負数が入る場合があるので、Vector型で保持
        return MaterialMorphData(
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
        return MVector3D(abs(self.read_float()), abs(self.read_float()), abs(self.read_float()))

    def read_RGBA(self):
        return MVector4D(abs(self.read_float()), abs(self.read_float()), abs(self.read_float()), abs(self.read_float()))

    def read_Vector4D(self):
        return MVector4D(self.read_float(), self.read_float(), self.read_float(), self.read_float())

    def read_Vector3D(self):
        return MVector3D(self.read_float(), self.read_float(), self.read_float())

    def read_Vector2D(self):
        return MVector2D(self.read_float(), self.read_float())

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
            return Bdef1(self.read_bone_index_size())
        elif deform_type == 1:
            # BDEF2
            return Bdef2(
                self.read_bone_index_size(),
                self.read_bone_index_size(),
                self.read_float()
            )
        elif deform_type == 2:
            # BDEF4
            return Bdef4(
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
            return Sdef(
                self.read_bone_index_size(),
                self.read_bone_index_size(),
                self.read_float(),
                self.read_Vector3D(),
                self.read_Vector3D(),
                self.read_Vector3D()
            )
        elif deform_type == 4:
            # QDEF
            return Qdef(
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

    # 頂点INDEXの解凍（サイズに基づく）
    def define_read_vertex_idx(self, vertex_size):
        if vertex_size <= 2:
            def read_vertex_idx(vertex_size):
                return self.read_uint(vertex_size)
            return read_vertex_idx
        elif vertex_size == 4:
            def read_vertex_idx(vertex_size):
                return self.read_int(vertex_size)
            return read_vertex_idx
        else:
            raise MParseException("define_read_vertex_idx 定義エラー {0}".format(vertex_size))

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

        return int(self.unpack(format_size, format_type))

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

        return int(self.unpack(format_size, format_type))

    # 小数の解凍
    def read_float(self, format_size=4):
        if format_size == 4:
            format_type = "f"
        elif format_size == 8:
            format_type = "d"
        else:
            raise MParseException("read_float format_sizeエラー {0}".format(format_size))

        return float(self.unpack(format_size, format_type))

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


def randomname(n) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=n))
