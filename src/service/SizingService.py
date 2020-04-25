# -*- coding: utf-8 -*-
#

import logging
import os
from pathlib import Path
from multiprocessing_logging import install_mp_handler
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

from mmd.VmdWriter import VmdWriter
from module.MOptions import MOptions
from service.parts.MoveService import MoveService
from service.parts.StanceService import StanceService
from service.parts.ArmAlignmentService import ArmAlignmentService
from service.parts.MorphService import MorphService
from utils import MServiceUtils
from utils.MException import SizingException
from utils.MLogger import MLogger # noqa

install_mp_handler()
logger = MLogger(__name__)


class SizingService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        logging.basicConfig(level=self.options.logging_level, format="%(message)s [%(module_name)s]")

        try:
            service_data_txt = "VMDサイジング処理実行\n------------------------\nexeバージョン: {version_name}\n".format(version_name=self.options.version_name) \

            for data_set_idx, data_set in enumerate(self.options.data_set_list):
                service_data_txt = "{service_data_txt}\n【No.{no}】 --------- \n".format(service_data_txt=service_data_txt, no=(data_set_idx+1)) # noqa
                service_data_txt = "{service_data_txt}　　モーション: {motion}\n".format(service_data_txt=service_data_txt,
                                        motion=os.path.basename(data_set.motion.path)) # noqa
                service_data_txt = "{service_data_txt}　　作成元モデル: {trace_model} ({model_name})\n".format(service_data_txt=service_data_txt,
                                        trace_model=os.path.basename(data_set.org_model.path), model_name=data_set.org_model.name) # noqa
                service_data_txt = "{service_data_txt}　　変換先モデル: {replace_model} ({model_name})\n".format(service_data_txt=service_data_txt,
                                        replace_model=os.path.basename(data_set.rep_model.path), model_name=data_set.rep_model.name) # noqa
                service_data_txt = "{service_data_txt}　　スタンス追加補正有無: {detail_stance_flg}\n".format(service_data_txt=service_data_txt,
                                        detail_stance_flg=data_set.detail_stance_flg) # noqa
                service_data_txt = "{service_data_txt}　　捩り分散有無: {twist_flg}\n".format(service_data_txt=service_data_txt,
                                        twist_flg=data_set.twist_flg) # noqa

            service_data_txt = "{service_data_txt}\n--------- \n".format(service_data_txt=service_data_txt) # noqa

            if self.options.arm_options.avoidance:
                service_data_txt = "{service_data_txt}剛体接触回避: {avoidance}\n".format(service_data_txt=service_data_txt,
                                        avoidance=self.options.arm_options.avoidance) # noqa
                service_data_txt = "{service_data_txt}対象剛体名: {avoidance_target}\n".format(service_data_txt=service_data_txt,
                                        avoidance=",".join(self.options.arm_options.avoidance_target_list)) # noqa

            if self.options.arm_options.alignment:
                service_data_txt = "{service_data_txt}手首位置合わせ: {alignment} ({distance})\n".format(service_data_txt=service_data_txt,
                                        alignment=self.options.arm_options.alignment, distance=self.options.arm_options.alignment_distance_wrist) # noqa
                service_data_txt = "{service_data_txt}指位置合わせ: {alignment} ({distance})\n".format(service_data_txt=service_data_txt,
                                        alignment=self.options.arm_options.alignment_finger_flg, distance=self.options.arm_options.alignment_distance_finger) # noqa
                service_data_txt = "{service_data_txt}床位置合わせ: {alignment} ({distance})\n".format(service_data_txt=service_data_txt,
                                        alignment=self.options.arm_options.alignment_floor_flg, distance=self.options.arm_options.alignment_distance_floor) # noqa

            service_data_txt = "{service_data_txt}腕チェックスキップ: {arm_check_skip}\n".format(service_data_txt=service_data_txt,
                                    arm_check_skip=self.options.arm_options.arm_check_skip_flg) # noqa

            service_data_txt = "{service_data_txt}------------------------".format(service_data_txt=service_data_txt) # noqa

            logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

            for data_set_idx, data_set in enumerate(self.options.data_set_list):
                # 足IKのXYZの比率
                data_set.original_xz_ratio, data_set.original_y_ratio = MServiceUtils.calc_leg_ik_ratio(data_set)
            
            # 足IKの比率再計算
            self.options.calc_leg_ratio()

            # 処理に成功しているか
            result = True

            # 移動補正
            result = MoveService(self.options).execute() and result

            # スタンス補正
            result = StanceService(self.options).execute() and result

            # if self.options.arm_options.avoidance:
            #     # 剛体接触回避
            #     pass
            # elif self.options.arm_options.alignment:
            #     # 手首位置合わせ
            #     result = ArmAlignmentService(self.options).execute() and result

            # モーフ置換
            result = MorphService(self.options).execute() and result

            for data_set_idx, data_set in enumerate(self.options.data_set_list):
                # 実行後、出力ファイル存在チェック
                try:
                    # 出力
                    VmdWriter(data_set).write()

                    Path(data_set.output_vmd_path).resolve(True)

                    if result:
                        logger.info("【No.%s】 変換出力終了: %s", (data_set_idx + 1), os.path.basename(data_set.output_vmd_path), decoration=MLogger.DECORATION_BOX, title="サイジング成功")
                    else:
                        logger.warning("【No.%s】 変換出力終了: %s\n※サイジングに失敗している箇所があります。", (data_set_idx + 1), os.path.basename(data_set.output_vmd_path), decoration=MLogger.DECORATION_BOX, title="サイジング成功")

                except FileNotFoundError as fe:
                    logger.error("【No.%s】出力VMDファイルが正常に作成されなかったようです。\nパスを確認してください。%s\n\n%s", (data_set_idx + 1), data_set.output_vmd_path, fe.message, decoration=MLogger.DECORATION_BOX)

            return result
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception as e:
            logger.critical("サイジング処理が意図せぬエラーで終了しました。", e, decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()
