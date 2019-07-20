# -*- coding: utf-8 -*-
#

import logging
import copy
from collections import OrderedDict
from PyQt5.QtGui import QQuaternion, QVector3D, QVector2D, QColor, QMatrix4x4

logger = logging.getLogger("__main__").getChild(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class PmxModel():
    def __init__(self):
        self.path = ''
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
        # モーフデータ(順番保持)
        self.morphs = OrderedDict()
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
            if l.name == "首":
                min_upper_y = l.position.y()
                break
            # if l.position.y() < min_upper_y and l.name not in ["センター", "グルーブ"]:
            #     min_upper_y = l.position.y()
            
        for v in self.vertices:
            for l in head_links:
                if v.deform.index0 == l.index and v.position.y() > min_upper_y:
                    # 上半身系のボーンにウェイトが乗っていて、かつウェイトボーンのY位置より上の場合、頂点追加
                    upper_vertices.append(v)

                    break

        return upper_vertices
    
    # 左右の手首の厚みを取得する
    def get_wrist_thickness_lr(self):
        return {
            "左": abs(self.get_wrist_thickness("左")), 
            "右": abs(self.get_wrist_thickness("右"))
        }

    # 手首の厚みを取得する
    def get_wrist_thickness(self, direction):
        arm_qq = self.calc_arm_stance_rotation(direction)
        # print("arm_qq: %s" % arm_qq.toEulerAngles())

        # mat = QMatrix4x4()
        # mat.rotate(arm_qq.inverted())
        # wrist_pos = mat.mapVector(self.bones["{0}手首".format(direction)].position - self.bones["{0}ひじ".format(direction)].position)
        wrist_pos = arm_qq.inverted().rotatedVector(self.bones["{0}手首".format(direction)].position - self.bones["{0}ひじ".format(direction)].position)
        # print("wrist_pos: %s" % wrist_pos)

        # 手首ウェイトの最下頂点
        wrist_upper_pos, wrist_below_pos = self.get_wrist_vertex_position(direction, arm_qq, wrist_pos)
        # print("wrist_upper_pos: %s" % wrist_upper_pos)
        # print("wrist_below_pos: %s" % wrist_below_pos)

        if wrist_upper_pos.y() >= wrist_pos.y() >= wrist_below_pos.y():
            # 手首ボーンの上下にウェイト頂点がある場合、手首の厚みを測って返す
            # 手首位置との差（手首の厚み）
            return abs(wrist_below_pos.y() - wrist_pos.y())

        # ウェイト頂点が手首から外れている場合、手首の厚みは採用しない
        return 0
    
    # 手首ウェイトの最下と最上頂点の位置を取得する
    def get_wrist_vertex_position(self, direction, arm_qq, wrist_pos):
        
        max_wrist_upper_pos = QVector3D(0, -99999, 0)
        min_wrist_below_pos = QVector3D(0, 99999, 0)
        for is_x in [True, False]:
            # X範囲を制限するか否か
            for v in self.vertices:
                # 一旦水平にしたときの頂点位置を算出
                # mat = QMatrix4x4()
                # mat.rotate(arm_qq.inverted())
                # v_pos = mat.mapVector(v.position - self.bones["{0}ひじ".format(direction)].position)
                v_pos = arm_qq.inverted().rotatedVector(v.position - self.bones["{0}ひじ".format(direction)].position)
                # logger.debug("v_pos: %s", v_pos)

                for l in self.bones.values():
                    if "{0}手首".format(direction) in l.name and v.is_deform_index(l.index) and ((is_x and v_pos.x() - 0.1 <= wrist_pos.x() <= v_pos.x() + 0.1) or not is_x):
                        if v_pos.y() < min_wrist_below_pos.y() :
                            # if type(v.deform) is PmxModel.Bdef1:
                            #     logger.debug("Bdef1: idx: %s, target: %s, index0: %s", v.index, l.index, v.deform.index0)
                            # elif type(v.deform) is PmxModel.Bdef2:
                            #     logger.debug("Bdef2: idx: %s, target: %s, index0: %s,  index1: %s", v.index, l.index, v.deform.index0, v.deform.index1)
                            # elif type(v.deform) is PmxModel.Bdef4:
                            #     logger.debug("Bdef4: idx: %s, target: %s, index0: %s,  index1: %s,  index2: %s,  index3: %s", v.index, l.index, v.deform.index0, v.deform.index1, v.deform.index2, v.deform.index3)
                            # elif type(v.deform) is PmxModel.Sdef:
                            #     logger.debug("Sdef: idx: %s, target: %s, index0: %s,  index1: %s", v.index, l.index, v.deform.index0, v.deform.index1)
                            # elif type(v.deform) is PmxModel.Qdef:
                            #     logger.debug("Qdef: idx: %s, target: %s, index0: %s,  index1: %s", v.index, l.index, v.deform.index0, v.deform.index1)

                            # 手首のボーンにウェイトが乗っていて、かつ最下の頂点より下の場合、保持
                            min_wrist_below_pos = v_pos
                            # print("min_wrist_below_pos: %s, %s, %s, %s, %s" % (l.index, l.name, v.index, v.position, v_pos))
                        
                        if v_pos.y() > max_wrist_upper_pos.y():
                            # 手首のボーンにウェイトが乗っていて、かつ最上の頂点より上の場合、保持
                            max_wrist_upper_pos = v_pos
                
            if min_wrist_below_pos == QVector3D(0, 99999, 0) or max_wrist_upper_pos == QVector3D(0, -99999, 0):
                # X制限をして見つからなかった場合、制限しないでチェック
                continue
            else:
                # X制限をして見つかった場合、終了
                break

        return max_wrist_upper_pos, min_wrist_below_pos

    # 自身の腕の角度を算出する
    def calc_arm_stance_rotation(self, direction):
        from_pos = self.bones["{0}ひじ".format(direction)].position
        to_pos = self.bones["{0}手首".format(direction)].position

        from_qq = QQuaternion()
        if from_pos != QVector3D and to_pos != QVector3D:
            logger.debug("from_pos: %s", from_pos)        
            logger.debug("to_pos: %s", to_pos)        

            to_pos = from_pos - to_pos
            to_pos.normalize()
            logger.debug("to_pos: %s", to_pos)        

            # 水平からTOボーンまでの回転量
            direction_x = -1 if direction == "左" else 1
            from_qq = QQuaternion.rotationTo(QVector3D(direction_x, 0, 0), QVector3D(to_pos.x(), to_pos.y(), 0))
            logger.debug("d: %s, from_qq: %s", direction, from_qq.toEulerAngles())
        
        return from_qq

    # 上半身ウェイトの最前頂点の位置を取得する
    def get_upper_front_position(self, from_bone_name, to_bone_name):

        x_from = self.bones["上半身"].position.x() + ((self.bones[from_bone_name].position.x() - self.bones["上半身"].position.x()) / 2) - 0.1
        x_to = self.bones["上半身"].position.x() + ((self.bones[to_bone_name].position.x() - self.bones["上半身"].position.x()) / 2) + 0.1
        # logger.debug("x_from: %s, x_to: %s", x_from, x_to)

        max_upper_front_pos = QVector3D(0, 0, -1)
        min_upper_front_pos = QVector3D(0, 0, 99999)
        for v in self.vertices:
            for l in self.bones.values():
                if l.name in ["上半身", "上半身2"] and v.is_deform_index(l.index) and x_from <= v.position.x() <= x_to:
                    if v.position.z() < self.bones["上半身"].position.z() and v.position.z() < min_upper_front_pos.z():
                        # 上半身か上半身2のボーンにウェイトが乗っていて、かつ最下の頂点より下の場合、保持
                        min_upper_front_pos = v.position
                        logger.debug("min_wrist_below_pos: %s, %s, %s, %s", l.index, l.name, v.index, v.position)
                    if v.position.z() < self.bones["上半身"].position.z() and v.position.z() > max_upper_front_pos.z():
                        # 上半身か上半身2のボーンにウェイトが乗っていて、かつ最下の頂点より上の場合、保持
                        max_upper_front_pos = v.position
                        logger.debug("max_wrist_below_pos: %s, %s, %s, %s", l.index, l.name, v.index, v.position)

        return min_upper_front_pos, max_upper_front_pos

    # 左右のボーンリンクを生成する
    def create_link_2_top_lr(self, start_type_bone, start_type_bone_second=None):

        if "左" + start_type_bone in self.bones and "右" + start_type_bone in self.bones:
            left_links, left_indexes = self.create_link_2_top("左" + start_type_bone)
            right_links, right_indexes = self.create_link_2_top("右" + start_type_bone)
            return { "左": left_links, "右": right_links }, { "左": left_indexes, "右": right_indexes }

        elif start_type_bone_second is not None and "左" + start_type_bone_second in self.bones and "右" + start_type_bone_second in self.bones:
            left_links, left_indexes = self.create_link_2_top("左" + start_type_bone_second)
            right_links, right_indexes = self.create_link_2_top("右" + start_type_bone_second)
            return { "左": left_links, "右": right_links }, { "左": left_indexes, "右": right_indexes }

        print("ボーンリンク生成失敗: start_type_bone: %s, start_type_bone_second: %s", start_type_bone, start_type_bone_second )

        return None

    # 一方向のボーンリンクを生成する
    def create_link_2_top_one(self, start_type_bone, start_type_bone_second=None):

        if start_type_bone in self.bones:
            # logger.debug("first start_type_bone: %s", start_type_bone)
            return self.create_link_2_top(start_type_bone)

        elif start_type_bone_second is not None and start_type_bone_second in self.bones:
            # logger.debug("second start_type_bone: %s", start_type_bone_second)
            return self.create_link_2_top(start_type_bone_second)

        print("ボーンリンク生成失敗: start_type_bone: %s, start_type_bone_second: %s", start_type_bone, start_type_bone_second )

        return None

    # ボーンリンクを生成する
    def create_link_2_top(self, start_bone, ik_links=None, ik_indexes=None):
        if not ik_links:
            # 順番を保持した辞書
            ik_links = []
            ik_indexes = OrderedDict()

        if start_bone not in self.bones:
            # 開始ボーン名がなければ終了
            return ik_links, ik_indexes
        
        start_type_bone = start_bone
        if start_bone.startswith("右") or start_bone.startswith("左"):
            # 左右から始まってたらそれは除く
            start_type_bone = start_bone[1:]
        
        # 自分をリンクに登録
        ik_indexes[start_type_bone] = len(ik_indexes)
        ik_links.append(self.bones[start_bone])

        parent_name = None
        for pname in self.PARENT_BORN_PAIR[start_bone]:
            # 親子関係のボーンリストから親ボーンが存在した場合
            if pname in self.bones:
                parent_name = pname
                break
                
        if not parent_name:
            # 親ボーンがボーンインデックスリストになければ終了
            return ik_links, ik_indexes
        
        logger.debug("start_bone: %s. parent_name: %s, start_type_bone: %s", start_bone, parent_name, start_type_bone)
        
        # 親をたどる
        return self.create_link_2_top(parent_name, ik_links, ik_indexes )    

    # ボーン関係親子のペア
    PARENT_BORN_PAIR = {
        "全ての親": [""]
        , "センター": ["全ての親"]
        , "グルーブ": ["センター"]
        , "腰": ["グルーブ", "センター"]
        , "下半身": ["腰", "センター"]
        , "上半身": ["腰", "センター"]
        , "上半身2": ["上半身"]
        , "首": ["上半身2", "上半身"]
        , "頭": ["首"]
        , "左肩P": ["上半身2", "上半身"]
        , "左肩": ["左肩P", "上半身2", "上半身"]
        , "左腕": ["左肩"]
        , "左腕捩": ["左腕"]
        , "左ひじ": ["左腕捩", "左腕"]
        , "左手捩": ["左ひじ"]
        , "左手首": ["左手捩", "左ひじ"]
        , "左親指０": ["左手首"]
        , "左親指１": ["左親指０", "左手首"]
        , "左親指２": ["左親指１"]
        , "左人指１": ["左手首"]
        , "左人指２": ["左人指１"]
        , "左人指３": ["左人指２"]
        , "左中指１": ["左手首"]
        , "左中指２": ["左中指１"]
        , "左中指３": ["左中指２"]
        , "左薬指１": ["左手首"]
        , "左薬指２": ["左薬指１"]
        , "左薬指３": ["左薬指２"]
        , "左小指１": ["左手首"]
        , "左小指２": ["左小指１"]
        , "左小指３": ["左小指２"]
        , "左足": ["下半身"]
        , "左ひざ": ["左足"]
        , "左足首": ["左ひざ"]
        , "左つま先": ["左足首"]
        , "左足IK親": ["全ての親"]
        , "左足ＩＫ": ["左足IK親", "全ての親"]
        , "左つま先ＩＫ": ["左足ＩＫ"]
        , "右肩P": ["上半身2", "上半身"]
        , "右肩": ["右肩P", "上半身2", "上半身"]
        , "右腕": ["右肩"]
        , "右腕捩": ["右腕"]
        , "右ひじ": ["右腕捩", "右腕"]
        , "右手捩": ["右ひじ"]
        , "右手首": ["右手捩", "右ひじ"]
        , "右親指０": ["右手首"]
        , "右親指１": ["右親指０", "右手首"]
        , "右親指２": ["右親指１"]
        , "右人指１": ["右手首"]
        , "右人指２": ["右人指１"]
        , "右人指３": ["右人指２"]
        , "右中指１": ["右手首"]
        , "右中指２": ["右中指１"]
        , "右中指３": ["右中指２"]
        , "右薬指１": ["右手首"]
        , "右薬指２": ["右薬指１"]
        , "右薬指３": ["右薬指２"]
        , "右小指１": ["右手首"]
        , "右小指２": ["右小指１"]
        , "右小指３": ["右小指２"]
        , "右足": ["下半身"]
        , "右ひざ": ["右足"]
        , "右足首": ["右ひざ"]
        , "右つま先": ["右足首"]
        , "右足IK親": ["全ての親"]
        , "右足ＩＫ": ["右足IK親", "全ての親"]
        , "右つま先ＩＫ": ["右足ＩＫ"]
    }
    
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
                    self.index, self.position, self.normal, self.uv, len(self.extended_uvs), self.deform, self.edge_factor
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
            # 表示枠チェック時にONにするので、デフォルトはFalse
            self.display=False

            # 親ボーンからの長さ(計算して求める）
            self.len = 0
            # 親ボーンからの長さ3D版(計算して求める）
            self.len_3d = QVector3D()
            # センターのZ軸オフセット
            self.offset_z = 0
            
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
            self.index=0
            self.name=name
            self.english_name=english_name
            self.panel=panel
            self.morph_type=morph_type
            self.offsets=offsets or []
            # 表示枠チェック時にONにするので、デフォルトはFalse
            self.display=False

        def __str__(self):
            return "<Morph name:{0}, english_name:{1}, panel:{2}, morph_type:{3}, offsets(len): {4}".format(
                        self.name, self.english_name, self.panel, self.morph_type, len(self.offsets)
                    )
        
        # パネルの名称取得
        def get_panel_name(self):
            if self.panel == 1: return "眉"
            elif self.panel == 2: return "目"
            elif self.panel == 3: return "口"
            elif self.panel == 4: return "他"
            else: return "？"
            
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


class SizingException(Exception):
    def __init__(self, message):
        self.message=message

