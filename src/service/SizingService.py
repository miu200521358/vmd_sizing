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
                service_data_txt = "{service_data_txt}　　捩り分散有無: {twist_flg}".format(service_data_txt=service_data_txt,
                                        twist_flg=data_set.twist_flg) # noqa

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

            # モーフ置換
            result = MorphService(self.options).execute() and result

            # 最後に全キーフレで繋げるのを除去
            if self.options.logging_level != MLogger.FULL and self.options.logging_level != MLogger.DEBUG_FULL:
                futures = []
                with ThreadPoolExecutor(thread_name_prefix="smooth") as executor:
                    for data_set_idx, data_set in enumerate(self.options.data_set_list):
                        if data_set.full_arms:
                            logger.info("不要キー削除【No.%s】", (data_set_idx + 1), decoration=MLogger.DECORATION_LINE)
                            
                            for bone_name in ["左腕", "左腕捩", "左ひじ", "左手捩", "左手首", "右腕", "右腕捩", "右ひじ", "右手捩", "右手首"]:
                                # 読み込んだ時のキーフレのみを対象とする
                                fnos = data_set.motion.get_bone_fnos(bone_name, is_read=True)
                                if len(fnos) < 2:
                                    # 前後がない場合、全件キーフレ
                                    all_fnos = data_set.motion.get_bone_fnos(bone_name)
                                    fnos = [all_fnos[0], all_fnos[-1]]

                                prev_sep_fno = 0
                                log_target_idxs = []
                                for fno_idx, fno in enumerate(data_set.motion.get_bone_fnos(bone_name)):
                                    if fno // 500 > prev_sep_fno:
                                        log_target_idxs.append(fno)
                                        prev_sep_fno = fno // 500
                                log_target_idxs.append(fnos[-1])

                                for start_fno, end_fno in zip(fnos[:-1], fnos[1:]):
                                    futures.append(executor.submit(self.remove_unnecessary_bf_pool_parts, data_set_idx, bone_name, start_fno, end_fno, log_target_idxs))
                concurrent.futures.wait(futures, timeout=None, return_when=concurrent.futures.FIRST_EXCEPTION)

                for f in futures:
                    result = f.result() and result
                
                for data_set_idx, data_set in enumerate(self.options.data_set_list):
                    if data_set.full_arms:
                        logger.info(" 不要キー削除:終了【No.%s】", data_set_idx + 1)

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

    def remove_unnecessary_bf_pool_parts(self, data_set_idx: int, bone_name: str, start_fno: int, end_fno: int, log_target_idxs: list):
        try:
            data_set = self.options.data_set_list[data_set_idx]
            data_set.motion.remove_unnecessary_bf(data_set_idx + 1, bone_name, start_fno, end_fno, \
                                                  data_set.rep_model.bones[bone_name].getRotatable(), data_set.rep_model.bones[bone_name].getTranslatable(), \
                                                  (end_fno in log_target_idxs))

            return True
        except SizingException:
            return False
        except Exception as e:
            logger.error("サイジング処理が意図せぬエラーで終了しました。", e)
            return False

