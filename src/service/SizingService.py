# -*- coding: utf-8 -*-
#

import time
import os
import copy
from utils.MLogger import MLogger # noqa
from service.parts.MoveService import MoveService

logger = MLogger(__name__)


class SizingService():
    def __init__(self, options):
        self.options = options

    def execute(self):
        logger.info(
            "exeバージョン: {version_name}\n".format(version_name=self.options.version_name) \
            + "モーション: {motion}\n".format(motion=os.path.basename(self.options.motion_vmd_data.path)) \
            + "作成元モデル: {trace_model} ({model_name})\n".format(trace_model=os.path.basename(self.options.org_model_data.path), model_name=self.options.org_model_data.name) \
            + "変換先モデル: {replace_model} ({model_name})\n".format(replace_model=os.path.basename(self.options.rep_model_data.path), model_name=self.options.rep_model_data.name) \
            + "代替モデル有無: {alternative_model_flg}\n".format(alternative_model_flg=self.options.alternative_model_flg) \
            + "捩り分散有無: {twist_flg}".format(twist_flg=self.options.twist_flg), decoration=MLogger.DECORATION_BOX) # noqa

        # 変換前のオリジナルモーションを保持
        org_motion_frames = copy.deepcopy(self.options.motion_vmd_data.frames)

        # 処理に成功しているか
        is_success = True

        # 移動系ボーン縮尺処理
        is_success = MoveService.execute(self.options, org_motion_frames) and is_success

