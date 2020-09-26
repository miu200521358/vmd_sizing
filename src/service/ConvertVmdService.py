# -*- coding: utf-8 -*-
#
import csv
import logging
import os
import traceback
from datetime import datetime

from mmd.PmxData import PmxModel # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from mmd.VmdWriter import VmdWriter
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MVmdOptions, MOptionsDataSet
from utils import MFileUtils
from utils.MException import SizingException
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class ConvertVmdService():
    def __init__(self, options: MVmdOptions):
        self.options = options

    def execute(self):
        logging.basicConfig(level=self.options.logging_level, format="%(message)s [%(module_name)s]")

        try:
            service_data_txt = "VMD変換処理実行\n------------------------\nexeバージョン: {version_name}\n".format(version_name=self.options.version_name) \

            service_data_txt = "{service_data_txt}　　ボーンCSV: {bone_csv}\n".format(service_data_txt=service_data_txt,
                                    bone_csv=os.path.basename(self.options.bone_csv_path)) # noqa
            service_data_txt = "{service_data_txt}　　モーフCSV: {morph_csv}\n".format(service_data_txt=service_data_txt,
                                    morph_csv=os.path.basename(self.options.morph_csv_path)) # noqa
            service_data_txt = "{service_data_txt}　　カメラCSV: {camera_csv}\n".format(service_data_txt=service_data_txt,
                                    camera_csv=os.path.basename(self.options.camera_csv_path)) # noqa

            logger.info(service_data_txt, decoration=MLogger.DECORATION_BOX)

            # 処理に成功しているか
            result = self.convert_vmd()

            return result
        except SizingException as se:
            logger.error("VMD変換処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
        except Exception:
            logger.critical("VMD変換処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
        finally:
            logging.shutdown()

    # VMD変換処理実行
    def convert_vmd(self):
        dt_now = datetime.now()

        bone_fpath = None
        bone_motion = VmdMotion()

        if self.options.bone_csv_path and os.path.exists(self.options.bone_csv_path):
            # ボーンモーションCSVディレクトリパス
            motion_csv_dir_path = MFileUtils.get_dir_path(self.options.bone_csv_path)
            # ボーンモーションCSVファイル名・拡張子
            motion_csv_file_name, _ = os.path.splitext(os.path.basename(self.options.bone_csv_path))

            bone_fpath = "{0}\\{1}_bone_{2:%Y%m%d_%H%M%S}.vmd".format(motion_csv_dir_path, motion_csv_file_name, dt_now)

            # ボーンCSV読み込み
            with open(self.options.bone_csv_path, encoding='cp932', mode='r') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーを読み飛ばす

                cnt = 0
                for ridx, row in enumerate(reader):
                    bf = VmdBoneFrame()
                    rno = ridx + 1

                    try:
                        if len(row) < 0 or not row[0]:
                            logger.error("%s行目のボーン名（1列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # ボーン名
                        bf.set_name(row[0])
                    except Exception as e:
                        logger.error("%s行目のボーン名の読み取りに失敗しました\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 1 or not row[1]:
                            logger.error("%s行目のフレーム番号（2列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # フレーム
                        bf.fno = int(float(row[1]))

                        if bf.fno < 0:
                            logger.error("%s行目のフレーム番号（2列目）に負数が設定されています", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                    except Exception as e:
                        logger.error("%s行目のフレーム番号の読み取りに失敗しました\nフレーム番号は半角数字のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 4 or not row[2] or not row[3] or not row[4]:
                            logger.error("%s行目の位置（3-5列目）のいずれかが設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # 位置
                        bf.position = MVector3D(float(row[2]), float(row[3]), float(row[4]))
                    except Exception as e:
                        logger.error("%s行目の位置の読み取りに失敗しました\n位置は半角数字・符号・小数点のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 7 or not row[5] or not row[6] or not row[7]:
                            logger.error("%s行目の回転（6-8列目）のいずれかが設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # 回転
                        bf.rotation = MQuaternion.fromEulerAngles(float(row[5]), float(row[6]) * -1, float(row[7]) * -1)
                    except Exception as e:
                        logger.error("%s行目の回転の読み取りに失敗しました\n位置は半角数字・符号・小数点のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 71:
                            logger.error("%s行目の補間曲線（9-72列目）のいずれかが設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False
                        
                        for cidx in range(8, 72):
                            if not row[cidx]:
                                logger.error("%s行目の補間曲線の%s番目が設定されていません", rno, cidx - 7, decoration=MLogger.DECORATION_BOX)
                                return False

                        # 補間曲線(一旦floatで読み込んで指数等も読み込んだ後、intに変換)
                        bf.interpolation = [int(float(row[8])), int(float(row[9])), int(float(row[10])), int(float(row[11])), int(float(row[12])), int(float(row[13])), \
                                            int(float(row[14])), int(float(row[15])), int(float(row[16])), int(float(row[17])), int(float(row[18])), int(float(row[19])), \
                                            int(float(row[20])), int(float(row[21])), int(float(row[22])), int(float(row[23])), int(float(row[24])), int(float(row[25])), \
                                            int(float(row[26])), int(float(row[27])), int(float(row[28])), int(float(row[29])), int(float(row[30])), int(float(row[31])), \
                                            int(float(row[32])), int(float(row[33])), int(float(row[34])), int(float(row[35])), int(float(row[36])), int(float(row[37])), \
                                            int(float(row[38])), int(float(row[39])), int(float(row[40])), int(float(row[41])), int(float(row[42])), int(float(row[43])), \
                                            int(float(row[44])), int(float(row[45])), int(float(row[46])), int(float(row[47])), int(float(row[48])), int(float(row[49])), \
                                            int(float(row[50])), int(float(row[51])), int(float(row[52])), int(float(row[53])), int(float(row[54])), int(float(row[55])), \
                                            int(float(row[56])), int(float(row[57])), int(float(row[58])), int(float(row[59])), int(float(row[60])), int(float(row[61])), \
                                            int(float(row[62])), int(float(row[63])), int(float(row[64])), int(float(row[65])), int(float(row[66])), int(float(row[67])), \
                                            int(float(row[68])), int(float(row[69])), int(float(row[70])), int(float(row[71]))]
                        
                        for bidx, bi in enumerate(bf.interpolation):
                            if 0 > bi:
                                logger.error("%s行目の補間曲線（%s列目）に負数が設定されています", rno, bidx + 9, decoration=MLogger.DECORATION_BOX)
                                return False

                    except Exception as e:
                        logger.error("%s行目の補間曲線の読み取りに失敗しました\n位置は半角数字のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False
                    
                    bf.read = True
                    bf.key = True

                    if bf.name not in bone_motion.bones:
                        bone_motion.bones[bf.name] = {}

                    bone_motion.bones[bf.name][bf.fno] = bf

                    cnt += 1

                    if cnt % 10000 == 0:
                        logger.info("[ボーン] %sキー目:終了", cnt)

        if self.options.morph_csv_path and os.path.exists(self.options.morph_csv_path):
            # モーフモーションCSVディレクトリパス
            motion_csv_dir_path = MFileUtils.get_dir_path(self.options.morph_csv_path)
            # モーフモーションCSVファイル名・拡張子
            motion_csv_file_name, _ = os.path.splitext(os.path.basename(self.options.morph_csv_path))

            if not bone_fpath:
                bone_fpath = "{0}\\{1}_morph_{2:%Y%m%d_%H%M%S}.vmd".format(motion_csv_dir_path, motion_csv_file_name, dt_now)

            # モーフCSV読み込み
            with open(self.options.morph_csv_path, encoding='cp932', mode='r') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーを読み飛ばす

                cnt = 0
                for ridx, row in enumerate(reader):
                    mf = VmdMorphFrame()
                    rno = ridx + 1

                    try:
                        if len(row) < 0 or not row[0]:
                            logger.error("%s行目のモーフ名（1列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # ボーン名
                        mf.set_name(row[0])
                    except Exception as e:
                        logger.error("%s行目のモーフ名の読み取りに失敗しました\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 1 or not row[1]:
                            logger.error("%s行目のフレーム番号（2列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # フレーム
                        mf.fno = int(float(row[1]))

                        if mf.fno < 0:
                            logger.error("%s行目のフレーム番号（2列目）に負数が設定されています", rno, decoration=MLogger.DECORATION_BOX)
                            return False
                    except Exception as e:
                        logger.error("%s行目のフレーム番号の読み取りに失敗しました\nフレーム番号は半角数字のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 2 or not row[2]:
                            logger.error("%s行目の大きさ（3列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # 値
                        mf.ratio = float(row[2])
                    except Exception as e:
                        logger.error("%s行目の大きさの読み取りに失敗しました\n大きさは半角数字・符号・小数点のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    if mf.name not in bone_motion.morphs:
                        bone_motion.morphs[mf.name] = {}

                    bone_motion.morphs[mf.name][mf.fno] = mf

                    cnt += 1

                    if cnt % 1000 == 0:
                        logger.info("[モーフ] %sキー目:終了", cnt)

        if len(bone_motion.bones.keys()) > 0 or len(bone_motion.morphs.keys()) > 0:
            # ボーンかモーフのキーがある場合、まとめて出力

            model = PmxModel()
            model.name = "CSV Convert Model"
            data_set = MOptionsDataSet(bone_motion, model, model, bone_fpath, False, False, [], None, 0, [])

            VmdWriter(data_set).write()

            logger.info("ボーン・モーフモーションVMD: %s", bone_fpath, decoration=MLogger.DECORATION_BOX)

        if self.options.camera_csv_path and os.path.exists(self.options.camera_csv_path):
            # カメラモーションCSVディレクトリパス
            motion_csv_dir_path = MFileUtils.get_dir_path(self.options.camera_csv_path)
            # カメラモーションCSVファイル名・拡張子
            motion_csv_file_name, _ = os.path.splitext(os.path.basename(self.options.camera_csv_path))

            camera_fpath = "{0}\\{1}_camera_{2:%Y%m%d_%H%M%S}.vmd".format(motion_csv_dir_path, motion_csv_file_name, dt_now)
            camera_motion = VmdMotion()

            # カメラCSV読み込み
            with open(self.options.camera_csv_path, encoding='cp932', mode='r') as f:
                reader = csv.reader(f)
                next(reader)  # ヘッダーを読み飛ばす

                cnt = 0
                for ridx, row in enumerate(reader):
                    cf = VmdCameraFrame()
                    rno = ridx + 1

                    try:
                        if len(row) < 1 or not row[0]:
                            logger.error("%s行目のフレーム番号（1列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # フレーム
                        cf.fno = int(row[0])

                        if cf.fno < 0:
                            logger.error("%s行目のフレーム番号（1列目）に負数が設定されています", rno, decoration=MLogger.DECORATION_BOX)
                            return False
                    except Exception as e:
                        logger.error("%s行目のフレーム番号の読み取りに失敗しました\nフレーム番号は半角数字のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 3 or not row[1] or not row[2] or not row[3]:
                            logger.error("%s行目の位置（2-4列目）のいずれかが設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # 位置
                        cf.position = MVector3D(float(row[1]), float(row[2]), float(row[3]))
                    except Exception as e:
                        logger.error("%s行目の位置の読み取りに失敗しました\n位置は半角数字・符号・小数点のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 6 or not row[4] or not row[5] or not row[6]:
                            logger.error("%s行目の回転（5-7列目）のいずれかが設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # 回転（オイラー角）
                        cf.euler = MVector3D(float(row[4]), float(row[5]), float(row[6]))
                    except Exception as e:
                        logger.error("%s行目の回転の読み取りに失敗しました\n回転は半角数字・符号・小数点のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 7 or not row[7]:
                            logger.error("%s行目の距離（8列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # 距離
                        cf.length = -(float(row[7]))
                    except Exception as e:
                        logger.error("%s行目の距離の読み取りに失敗しました\n距離は半角数字・符号・小数点のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 8 or not row[8]:
                            logger.error("%s行目の視野角（9列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # 視野角
                        cf.angle = int(row[8])

                        if cf.angle < 0:
                            logger.error("%s行目の視野角（9列目）に負数が設定されています", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                    except Exception as e:
                        logger.error("%s行目の視野角の読み取りに失敗しました\n視野角は半角数字のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 8 or not row[9]:
                            logger.error("%s行目のパース（10列目）が設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False

                        # パース
                        cf.perspective = int(row[9])

                        if cf.perspective not in [0, 1]:
                            logger.error("%s行目のパース（10列目）に0, 1以外の値が設定されています", rno, decoration=MLogger.DECORATION_BOX)
                            return False
                    except Exception as e:
                        logger.error("%s行目のパースの読み取りに失敗しました\nパースは0, 1のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False

                    try:
                        if len(row) < 33:
                            logger.error("%s行目の補間曲線（11-34列目）のいずれかが設定されていません", rno, decoration=MLogger.DECORATION_BOX)
                            return False
                        
                        for cidx in range(10, 34):
                            if not row[cidx]:
                                logger.error("%s行目の補間曲線の%s番目が設定されていません", rno, cidx - 9, decoration=MLogger.DECORATION_BOX)
                                return False

                        # 補間曲線(一旦floatで読み込んで指数等も読み込んだ後、intに変換)
                        cf.interpolation = [int(float(row[10])), int(float(row[11])), int(float(row[12])), int(float(row[13])), int(float(row[14])), int(float(row[15])), \
                                            int(float(row[16])), int(float(row[17])), int(float(row[18])), int(float(row[19])), int(float(row[20])), int(float(row[21])), \
                                            int(float(row[22])), int(float(row[23])), int(float(row[24])), int(float(row[25])), int(float(row[26])), int(float(row[27])), \
                                            int(float(row[28])), int(float(row[29])), int(float(row[30])), int(float(row[31])), int(float(row[32])), int(float(row[33]))]

                        for cidx, ci in enumerate(cf.interpolation):
                            if 0 > ci:
                                logger.error("%s行目の補間曲線（%s列目）に負数が設定されています", rno, cidx + 11, decoration=MLogger.DECORATION_BOX)
                                return False

                    except Exception as e:
                        logger.error("%s行目の補間曲線の読み取りに失敗しました\n位置は半角数字のみ入力可能です。\n%s", rno, e, decoration=MLogger.DECORATION_BOX)
                        return False
                   
                    camera_motion.cameras[cf.fno] = cf

                    cnt += 1

                    if cnt % 500 == 0:
                        logger.info("[カメラ] %sキー目:終了", cnt)

            if len(camera_motion.cameras) > 0:
                # ボーンかモーフのキーがある場合、まとめて出力

                model = PmxModel()
                model.name = "カメラ・照明"
                data_set = MOptionsDataSet(camera_motion, model, model, camera_fpath, False, False, [], None, 0, [])

                VmdWriter(data_set).write()

                logger.info("カメラモーションVMD: %s", camera_fpath, decoration=MLogger.DECORATION_BOX)

        return True



