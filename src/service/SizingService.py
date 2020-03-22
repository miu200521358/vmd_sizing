# -*- coding: utf-8 -*-
#

import logging
import os
import traceback
import _pickle as cPickle
from pathlib import Path

from mmd.VmdWriter import VmdWriter
from module.MOptions import MOptions
from service.parts.MoveService import MoveService
from service.parts.StanceService import StanceService
from utils.MException import SizingException
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class SizingService():
    def __init__(self, options: MOptions):
        self.options = options

    def execute(self):
        logging.basicConfig(level=self.options.logging_level, format="%(message)s [%(module_name)s]")

        try:
            logger.info(
                "VMDサイジング処理実行\n------------------------\n" \
                + "exeバージョン: {version_name}\n".format(version_name=self.options.version_name) \
                + "モーション: {motion}\n".format(motion=os.path.basename(self.options.motion_vmd_data.path)) \
                + "作成元モデル: {trace_model} ({model_name})\n".format(trace_model=os.path.basename(self.options.org_model_data.path), model_name=self.options.org_model_data.name) \
                + "変換先モデル: {replace_model} ({model_name})\n".format(replace_model=os.path.basename(self.options.rep_model_data.path), model_name=self.options.rep_model_data.name) \
                + "代替モデル有無: {substitute_model_flg}\n".format(substitute_model_flg=self.options.substitute_model_flg) \
                + "捩り分散有無: {twist_flg}".format(twist_flg=self.options.twist_flg), decoration=MLogger.DECORATION_BOX) # noqa

            # 変換前のオリジナルモーションを保持
            org_motion = cPickle.loads(cPickle.dumps(self.options.motion_vmd_data, -1))

            # 処理に成功しているか
            result = True

            # 移動補正
            result = MoveService(self.options).execute(org_motion) and result

            # スタンス補正
            result = StanceService(self.options).execute(org_motion) and result

            # 出力
            VmdWriter(self.options).write()

            # 実行後、出力ファイル存在チェック
            try:
                Path(self.options.output_vmd_path).resolve(True)

                if result:
                    logger.info("変換出力完了: %s", os.path.basename(self.options.output_vmd_path), decoration=MLogger.DECORATION_BOX, title="サイジング成功")
                else:
                    logger.warning("変換出力完了: %s\n※サイジングに失敗している箇所があります。", os.path.basename(self.options.output_vmd_path), decoration=MLogger.DECORATION_BOX, title="サイジング成功")

            except FileNotFoundError as fe:
                logger.error("出力VMDファイルが正常に作成されなかったようです。\nパスを確認してください。%s\n\n%s", self.options.output_vmd_path, fe.message, decoration=MLogger.DECORATION_BOX)

            return result
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception:
            logger.critical("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

