# -*- coding: utf-8 -*-
#
import copy
import math
import logging
import os
import traceback
import itertools
import random
from datetime import datetime

from mmd.VmdWriter import VmdWriter
from mmd.VmdData import VmdMotion, VmdMorphFrame # noqa
from module.MOptions import MCsvOptions, MOptionsDataSet
from utils import MFileUtils
from utils.MException import SizingException
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class MorphBlendService():
    def __init__(self, options: MCsvOptions):
        self.options = options

    def execute(self):
        logging.basicConfig(level=self.options.logging_level, format="%(message)s [%(module_name)s]")

        try:
            service_data_txt = "モーフブレンド処理実行\n------------------------\nexeバージョン: {version_name}\n".format(version_name=self.options.version_name)

            service_data_txt = "{service_data_txt}モデル: {model_path} ({model_name})\n".format(service_data_txt=service_data_txt,
                                    model_path=os.path.basename(self.options.model.path), model_name=self.options.model.name) # noqa
            
            service_data_txt = "{service_data_txt}　　目: {target}\n".format(service_data_txt=service_data_txt, target=",".join(self.options.eye_list)) # noqa
            service_data_txt = "{service_data_txt}　　眉: {target}\n".format(service_data_txt=service_data_txt, target=",".join(self.options.eyebrow_list)) # noqa
            service_data_txt = "{service_data_txt}　　口: {target}\n".format(service_data_txt=service_data_txt, target=",".join(self.options.lip_list)) # noqa
            service_data_txt = "{service_data_txt}　　他: {target}\n".format(service_data_txt=service_data_txt, target=",".join(self.options.other_list)) # noqa
            service_data_txt = "{service_data_txt}　範囲: {min}～{max} ({inc})".format(service_data_txt=service_data_txt, \
                    min=self.options.min_value, max=self.options.max_value, inc=self.options.inc_value) # noqa

            logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

            # 処理に成功しているか
            result = self.blend_morph()

            return result
        except SizingException as se:
            logger.error("モーフブレンド処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception:
            logger.critical("モーフブレンド処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

    # モーフブレンド処理実行
    def blend_morph(self):
        # モーションVMDディレクトリパス
        pmx_dir_path = MFileUtils.get_dir_path(self.options.model.path)
        # モーションVMDファイル名・拡張子
        pmx_file_name, pmx_ext = os.path.splitext(os.path.basename(self.options.model.path))

        dt_now = datetime.now()

        blend_fpath = "{0}\\{1}_blend_{2:%Y%m%d_%H%M%S}.vmd".format(pmx_dir_path, pmx_file_name, dt_now)

        bone_motion = VmdMotion()

        # 処理対象モーフ名（文字列）
        target_morphs = self.options.eye_list + self.options.eyebrow_list + self.options.lip_list + self.options.other_list

        # 処理対象モーフデータ
        all_morphs = []
        for mk, mv in self.options.model.morphs.items():
            if mv.display and mv.name in target_morphs:
                all_morphs.append(mv)
                bone_motion.morphs[mk] = {}

        # 変化量(少ない方のの割合を多くする)
        ratio_values = [self.options.inc_value * x for x in range(math.ceil(self.options.min_value / self.options.inc_value), \
                        math.ceil(self.options.max_value / self.options.inc_value) + 1) if self.options.min_value <= self.options.inc_value * x <= self.options.max_value]
        ratio_lower_values = [self.options.inc_value * x for x in range(math.ceil(self.options.min_value / self.options.inc_value), \
                              math.ceil(self.options.max_value / self.options.inc_value / 2) + 1) if self.options.min_value <= self.options.inc_value * x <= self.options.max_value]
        ratio_zero_values = [0 for x in range(len(all_morphs))]

        # 全体の比率増減量
        ratio_total_values = copy.deepcopy(ratio_values)
        ratio_total_values.extend(ratio_lower_values)
        ratio_total_values.extend(ratio_lower_values)
        ratio_total_values.extend(ratio_zero_values)

        # モーフの組合せ数
        morph_comb_cnt = 1
        # 変化量の組合せ数
        ratio_product_cnt = 1
        for n in range(len(all_morphs), 0, -1):
            morph_comb_cnt *= n
            ratio_product_cnt *= len(ratio_values)

        morph_total_cnt = 0

        if morph_comb_cnt * ratio_product_cnt <= 1000:
            # モーフの組合せ
            morph_comb = list(itertools.combinations(all_morphs, len(all_morphs)))
            logger.debug("morph_comb: %s", len(morph_comb))
            
            # 変化量の直積（同じ値を許容する）
            ratio_product = list(itertools.product(ratio_values, repeat=len(all_morphs)))
            logger.debug("ratio_product: %s", len(ratio_product))

            # 組合せが1000以下なら組合せをそのまま出力
            brend_mr_pairs_list = list(itertools.product(morph_comb, ratio_product))
            logger.debug("brend_mr_pairs_list: %s", len(brend_mr_pairs_list))

            for mframe, (morphs, ratios) in enumerate(brend_mr_pairs_list):
                # 上限までしか登録しない
                if morph_total_cnt > 19000:
                    break

                for morph, ratio in zip(morphs, ratios):
                    vmd_morph = VmdMorphFrame()
                    vmd_morph.fno = mframe
                    vmd_morph.set_name(morph.name)
                    vmd_morph.ratio = ratio
                    vmd_morph.key = True
                    
                    bone_motion.morphs[morph.name][mframe] = vmd_morph
                    logger.test(vmd_morph)

                    morph_total_cnt += 1

        else:
            # 組合せが1000より多い場合、ランダム
            for mframe in range(1000):
                # 上限までしか登録しない
                if morph_total_cnt > 19000:
                    break

                for morph in all_morphs:
                    ratio = ratio_total_values[random.randint(0, len(ratio_values) - 1)]

                    vmd_morph = VmdMorphFrame()
                    vmd_morph.fno = mframe
                    vmd_morph.set_name(morph.name)
                    vmd_morph.ratio = ratio
                    vmd_morph.key = True
                    
                    bone_motion.morphs[morph.name][mframe] = vmd_morph
                    logger.test(vmd_morph)

                    morph_total_cnt += 1
        
        data_set = MOptionsDataSet(bone_motion, None, self.options.model, blend_fpath, False, False, [], None, None, [])

        VmdWriter(data_set).write()

        logger.info("モーフブレンドVMD: %s", blend_fpath, decoration=MLogger.DECORATION_BOX)

        return True

