# -*- coding: utf-8 -*-
#
from datetime import datetime
import sys
import pathlib
# このソースのあるディレクトリの絶対パスを取得
current_dir = pathlib.Path(__file__).resolve().parent
# モジュールのあるパスを追加
sys.path.append(str(current_dir) + '/../')
sys.path.append(str(current_dir) + '/../src/')

from mmd.PmxReader import PmxReader # noqa
from mmd.VmdReader import VmdReader # noqa
from mmd.VmdWriter import VmdWriter # noqa
from mmd.PmxWriter import PmxWriter # noqa
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint, Bdef1 # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptionsDataSet # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils, MServiceUtils # noqa
from utils.MException import SizingException # noqa
from utils.MLogger import MLogger # noqa


MLogger.initialize(level=MLogger.DEBUG_INFO, is_file=True)
logger = MLogger(__name__, level=MLogger.DEBUG_INFO)


def calc_global_pos():
    model = PmxReader("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\VOCALOID\\初音ミク\\ISAO式ミク\\I_ミクv4\\Miku_V4.pmx", is_check=False).read_data()
    # model = PmxReader("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Model\\VOCALOID\\初音ミク\\Tda式初音ミク_盗賊つばき流Ｍトレースモデル配布 v1.07\\Tda式初音ミク_盗賊つばき流Mトレースモデルv1.07_layer.pmx", is_check=False).read_data()
    motion = VmdReader("D:\\MMD\\MikuMikuDance_v926x64\\UserFile\\Motion\\ダンス_1人\\エゴロック 粉ふきスティック\\egorock_miku.vmd").read_data()
    result_motion = VmdMotion()
    result_pmx = PmxModel()
    result_pmx.name = f"Result {model.name}"
    prepare_bone(result_pmx)

    target_links = [model.create_link_2_top_one("左人指先実体", "左手首"), model.create_link_2_top_one("右人指先実体", "右手首")]

    for fno in range(0, 10, 10):
        for links in target_links:
            result_3ds, result_mats = MServiceUtils.calc_global_pos(model, links, motion, fno, return_matrix=True, is_local_x=False, is_calc_ik=True)
            logger.debug_info("%s [%s] -----------------------------", fno, links.last_name())
            for (link_name, result_pos), result_mat in zip(result_3ds.items(), result_mats.values()):
                create_bone(model, result_pmx, link_name)

                if link_name != "全ての親":
                    bf = motion.calc_bf(link_name, fno).copy()
                    bf.position = result_pos
                    result_motion.regist_bf(bf, bf.name, fno)

                # all_ik_links = links.get_ik_links(link_name)
                # if all_ik_links:
                #     for ik_links in all_ik_links:
                #         result_ik_3ds = MServiceUtils.calc_global_pos(model, ik_links["target"], motion, fno, is_calc_ik=False)

                #         for ik_link_name, result_ik_pos in result_ik_3ds.items():
                #             if ik_link_name not in result_pmx.bones:
                #                 create_bone(model, result_pmx, ik_link_name)

                #                 if ik_link_name != "全ての親":
                #                     bf = motion.calc_bf(ik_link_name, fno).copy()
                #                     bf.position = result_ik_pos
                #                     result_motion.regist_bf(bf, bf.name, fno)

        logger.warning(fno)

    result_dir = "D:\\MMD\\MikuMikuDance_v926x64\\Work\\x003_VMDサイジング\\ver5.02\\test"
    new_file_path = f"{result_dir}\\pos_{datetime.now():%Y%m%d_%H%M%S}.vmd"

    data_set = MOptionsDataSet(result_motion, model, model, new_file_path)
    writer = VmdWriter(data_set)
    writer.write()

    for bidx, b in enumerate(result_pmx.bones.values()):
        try:
            if bidx > 0:
                b.tail_index = result_pmx.bones[model.bone_indexes[model.bones[b.name].parent_index]].index
                b.flag |= 0x0001
        except:
            pass

    pmx_writer = PmxWriter()
    pmx_writer.write(result_pmx, f"{result_dir}\\model_{datetime.now():%Y%m%d_%H%M%S}.pmx")

    logger.warning(f"出力終了: {new_file_path}")


def prepare_bone(model: PmxModel):
    model.vertices["vertices"] = []
    # 空テクスチャを登録
    model.textures.append("")

    # 全ての親 ------------------------
    model.bones["全ての親"] = Bone("全ての親", "Root", MVector3D(), -1, 0, 0x0000 | 0x0002 | 0x0004 | 0x0008 | 0x0010)
    model.bones["全ての親"].index = 0
    model.bone_indexes[0] = "全ての親"
    model.display_slots["Root"] = DisplaySlot("Root", "Root", 1, 0)
    model.display_slots["Root"].references.append(model.bones["全ての親"].index)

    # モーフの表示枠
    model.display_slots["表情"] = DisplaySlot("表情", "Exp", 1, 1)

    # その他
    for display_name in ["ALL"]:
        model.display_slots[display_name] = DisplaySlot(display_name, display_name, 0, 0)
    

def create_bone(org_model: PmxModel, model: PmxModel, mname: str):
    if mname in model.bones:
        return
    
    local_x_axis = org_model.get_local_x_axis(mname)
    local_x_qq = MQuaternion.rotationTo(MVector3D(0, 1, 0), local_x_axis)
    
    bone = Bone(mname, mname, MVector3D(0, 0, 0), 0, 0, 0x0000 | 0x0002 | 0x0004 | 0x0008 | 0x0010)
    bone.index = len(list(model.bones.keys()))

    # ボーンINDEX
    model.bone_indexes[bone.index] = bone.name

    color_list = [MVector3D(255, 0, 0), MVector3D(0, 255, 0), MVector3D(0, 0, 255), MVector3D(255, 127, 0), MVector3D(255, 0, 127), MVector3D(127, 255, 0),
                  MVector3D(255, 127, 0), MVector3D(0, 127, 255), MVector3D(0, 255, 127), MVector3D(127, 127, 0), MVector3D(255, 51, 51), MVector3D(51, 255, 51),
                  MVector3D(51, 51, 255), MVector3D(255, 127, 51), MVector3D(255, 51, 127), MVector3D(127, 255, 51), MVector3D(255, 127, 51), MVector3D(51, 127, 255),
                  MVector3D(51, 255, 127), MVector3D(127, 127, 51)]
    color = color_list[bone.index % len(color_list)] / 255

    # ボーン
    model.bones[bone.name] = bone
    # 表示枠
    model.display_slots["ALL"].references.append(model.bones[bone.name].index)
    # 材質
    model.materials[bone.name] = Material(bone.name, bone.name, color, 1, 0, MVector3D(), color, 0x02 | 0x08, MVector4D(0, 0, 0, 1), 1, 0, 0, 0, 0, 0)
    model.materials[bone.name].vertex_count = 32 * 3
    start_vidx = len(model.vertices["vertices"])

    for vidx, vpos in enumerate([MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 1, -0.00000002980232)),
                                MVector3D(local_x_qq * MVector3D(0, 0.6666665, 0.16666665)),
                                MVector3D(local_x_qq * MVector3D(0.16666665, 0.6666665, -0.00000001721934)),
                                MVector3D(local_x_qq * MVector3D(-0.000000014570465, 0.6666665, -0.16666665)),
                                MVector3D(local_x_qq * MVector3D(-0.16666665, 0.6666665, -0.000000007946625)),
                                MVector3D(local_x_qq * MVector3D(0, 0.33333335, 0.33333335)),
                                MVector3D(local_x_qq * MVector3D(0.33333335, 0.3333333, -0.0000000046363535)),
                                MVector3D(local_x_qq * MVector3D(-0.000000029140925, 0.3333333, -0.3333333)),
                                MVector3D(local_x_qq * MVector3D(-0.33333335, 0.3333333, 0.00000001390907)),
                                MVector3D(local_x_qq * MVector3D(0, 0.00000005960465, 0.5)),
                                MVector3D(local_x_qq * MVector3D(0.5, 0.00000002980232, 0.00000000794663)),
                                MVector3D(local_x_qq * MVector3D(-0.00000004371139, 0, -0.49999995)),
                                MVector3D(local_x_qq * MVector3D(-0.5, 0.00000002980232, 0.000000035764765)),
                                MVector3D(local_x_qq * MVector3D(0, 0.00000005960465, 0.5)),
                                MVector3D(local_x_qq * MVector3D(0.5, 0.00000002980232, 0.00000000794663)),
                                MVector3D(local_x_qq * MVector3D(-0.00000004371139, 0, -0.49999995)),
                                MVector3D(local_x_qq * MVector3D(-0.5, 0.00000002980232, 0.000000035764765)),
                                MVector3D(local_x_qq * MVector3D(0, 0.00000002980232, 0.00000002980232))]):
        v1 = Vertex(start_vidx + vidx, vpos, MVector3D(0, 0, -1), MVector2D(), [], Bdef1(bone.index), 1)
        model.vertices["vertices"].append(v1)
    
    for iidx1, iidx2, iidx3 in [(0, 1, 2), (0, 2, 3), (0, 3, 4), (0, 4, 1), (5, 9, 6), (6, 9, 10), (6, 10, 7), (7, 10, 11), (7, 11, 8), (8, 11, 12), (8, 12, 5),
                                (5, 12, 9), (9, 13, 10), (10, 13, 14), (10, 14, 11), (11, 14, 15), (11, 15, 12), (12, 15, 16), (12, 16, 9), (9, 16, 13), (13, 17, 14),
                                (14, 17, 18), (14, 18, 15), (15, 18, 19), (15, 19, 16), (16, 19, 20), (16, 20, 13), (13, 20, 17), (21, 25, 22), (22, 25, 23), (23, 25, 24),
                                (24, 25, 21)]:
        model.indices.append(start_vidx + iidx1)
        model.indices.append(start_vidx + iidx2)
        model.indices.append(start_vidx + iidx3)

if __name__ == '__main__':
    calc_global_pos()

