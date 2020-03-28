# -*- coding: utf-8 -*-
#

import logging
import os
import traceback
from datetime import datetime

from module.MOptions import MCsvOptions
from utils import MFileUtils
from utils.MException import SizingException
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class ConvertCsvService():
    def __init__(self, options: MCsvOptions):
        self.options = options

    def execute(self):
        logging.basicConfig(level=self.options.logging_level, format="%(message)s [%(module_name)s]")

        try:
            service_data_txt = "CSV変換処理実行\n------------------------\nexeバージョン: {version_name}\n".format(version_name=self.options.version_name) \

            service_data_txt = "{service_data_txt}　　VMD: {vmd}\n".format(service_data_txt=service_data_txt,
                                    vmd=os.path.basename(self.options.motion.path)) # noqa

            logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

            # 処理に成功しているか
            result = self.convert_csv()

            return result
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception:
            logger.critical("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

    # CSV変換処理実行
    def convert_csv(self):
        # モーションVMDディレクトリパス
        motion_vmd_dir_path = MFileUtils.get_dir_path(self.options.motion.path)
        # モーションVMDファイル名・拡張子
        motion_vmd_file_name, motion_vmd_ext = os.path.splitext(os.path.basename(self.options.motion.path))

        if self.options.motion.motion_cnt > 0:
            # ボーンモーションがある場合、ボーンモーション出力

            bone_fpath = "{0}\\{1}_bone_{2:%Y%m%d_%H%M%S}.csv".format(motion_vmd_dir_path, motion_vmd_file_name, datetime.now())

            # Excel等で読めるよう、cp932限定
            with open(bone_fpath, encoding='cp932', mode='w') as f:
                
                s = "ボーン名,フレーム,位置X,位置Y,位置Z,回転X,回転Y,回転Z,【X_x1】,Y_x1,Z_x1,R_x1,【X_y1】,Y_y1,Z_y1,R_y1,【X_x2】,Y_x2,Z_x2,R_x2,【X_y2】,Y_y2,Z_y2,R_y2,【Y_x1】,Z_x1,R_x1,X_y1,【Y_y1】,Z_y1,R_y1,X_x2,【Y_x2】,Z_x2,R_x2,X_y2,【Y_y2】,Z_y2,R_y2,1,【Z_x1】,R_x1,X_y1,Y_y1,【Z_y1】,R_y1,X_x2,Y_x2,【Z_x2】,R_x2,X_y2,Y_y2,【Z_y2】,R_y2,1,0,【R_x1】,X_y1,Y_y1,Z_y1,【R_y1】,X_x2,Y_x2,Z_x2,【R_x2】,X_y2,Y_y2,Z_y2,【R_y2】,01,00,00"
                f.write(s)
                f.write("\n")

                for bone_name in self.options.motion.bones:
                    for fno in self.options.motion.get_bone_fnos(bone_name):
                        bf = self.options.motion.bones[bone_name][fno]
                        s = "{0},{1},{2},{3},{4},{5},{6},{7},{8}".format(bf.name, bf.fno, \
                                                                         bf.position.x(), bf.position.y(), bf.position.z(), bf.rotation.toEulerAngles4MMD().x(), \
                                                                         bf.rotation.toEulerAngles4MMD().y(), bf.rotation.toEulerAngles4MMD().z(), ','.join([str(i) for i in bf.interpolation]))
                        f.write(s)
                        f.write("\n")

        return True



