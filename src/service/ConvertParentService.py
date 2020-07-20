# -*- coding: utf-8 -*-
#
import math
import numpy as np
import logging
import os
import traceback
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from module.MOptions import MParentOptions, MOptionsDataSet
from mmd.PmxData import PmxModel # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from mmd.VmdWriter import VmdWriter
import module.MMath as MMath
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MUtils, MServiceUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException

logger = MLogger(__name__, level=1)


class ConvertParentService():
    def __init__(self, options: MParentOptions):
        self.options = options

    def execute(self):
        logging.basicConfig(level=self.options.logging_level, format="%(message)s [%(module_name)s]")

        try:
            service_data_txt = "全親移植処理実行\n------------------------\nexeバージョン: {version_name}\n".format(version_name=self.options.version_name) \

            service_data_txt = "{service_data_txt}　VMD: {vmd}\n".format(service_data_txt=service_data_txt,
                                    vmd=os.path.basename(self.options.motion.path)) # noqa
            service_data_txt = "{service_data_txt}　モデル: {model}({model_name})\n".format(service_data_txt=service_data_txt,
                                    model=os.path.basename(self.options.motion.path), model_name=self.options.model.name) # noqa

            logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

            # 処理に成功しているか
            result = self.convert_parent()

            # 最後に出力
            VmdWriter(MOptionsDataSet(self.options.motion, None, self.options.model, self.options.output_path, False, False, [], None, 0, [])).write()

            logger.info("出力終了: %s", os.path.basename(self.options.output_path), decoration=MLogger.DECORATION_BOX, title="成功")

            return result
        except SizingException as se:
            logger.error("全親移植処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception:
            logger.critical("全親移植処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

    # 全親移植処理実行
    def convert_parent(self):
        motion = self.options.motion
        model = self.options.model

        parent_bone_name = "全ての親"

        for bone_name in ["センター", "右足ＩＫ", "左足ＩＫ"]:
            links = model.create_link_2_top_one(bone_name)
            fnos = motion.get_bone_fnos(bone_name)
            for fno in fnos:
                bf = motion.calc_bf(bone_name, fno)
                global_3ds_dic = MServiceUtils.calc_global_pos(model, links, motion, fno)
                bone_global_pos = global_3ds_dic[bone_name]

                bf.position = bone_global_pos - model.bones[bone_name].position
                motion.regist_bf(bf, bone_name, fno)
        
        for bone_name in ["上半身", "下半身", "右足ＩＫ", "左足ＩＫ"]:
            links = model.create_link_2_top_one(bone_name)
            fnos = motion.get_bone_fnos(bone_name)
            for fno in fnos:
                parent_bf = motion.calc_bf(parent_bone_name, fno)
                bf = motion.calc_bf(bone_name, fno)
                bf.rotation = parent_bf.rotation * bf.rotation
                motion.regist_bf(bf, bone_name, fno)

        # 全ての親削除
        del motion.bones[parent_bone_name]


