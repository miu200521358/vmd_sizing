# -*- coding: utf-8 -*-
#
import struct
import hashlib
import re

from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException, MKilledException, MParseException

logger = MLogger(__name__)


class VmdReader:
    def __init__(self, file_path):
        self.offset = 0
        self.buffer = None
        self.encoding = None
        self.file_path = file_path

    # モデル名だけ取得
    def read_model_name(self):
        model_name = ""
        with open(self.file_path, "rb") as f:
            # VMDファイルをバイナリ読み込み
            self.buffer = f.read()

            # vmdバージョン
            signature = self.unpack(30, "30s")
            logger.test("signature %s", signature)

            # モデル名
            model_bname, model_name = self.read_text(20)
            logger.test("model_bname %s, model_name: %s", model_bname, model_name)

        return model_name

    def read_data(self):
        # モーションパス
        motion = VmdMotion()
        motion.path = self.file_path

        try:
            with open(self.file_path, "rb") as f:
                # VMDファイルをバイナリ読み込み
                self.buffer = f.read()

                # vmdバージョン
                signature = self.unpack(30, "30s")
                logger.test("signature %s", signature)

                # モデル名
                model_bname, model_name = self.read_text(20)
                logger.test("model_bname %s, model_name: %s", model_bname, model_name)
                motion.model_name = model_name

                # モーション数
                motion.motion_cnt = self.read_uint(4)
                logger.test("motion.motion_cnt %s", motion.motion_cnt)

                # 1F分のモーション情報

                prev_n = 0
                for n in range(motion.motion_cnt):
                    frame = VmdBoneFrame(0)
                    frame.key = True
                    frame.read = True

                    # ボーン ----------------------
                    # ボーン名
                    bone_bname, bone_name = self.read_text(15)

                    frame.name = bone_name
                    frame.bname = bone_bname
                    logger.test("name: %s, bname %s", bone_name, bone_bname)

                    # フレームIDX
                    frame.fno = self.read_uint(4)
                    logger.test("frame.fno %s", frame.fno)

                    # 位置X,Y,Z
                    frame.position = self.read_Vector3D()
                    logger.test("frame.position %s", frame.position)

                    # 回転X,Y,Z,scalar
                    frame.rotation = self.read_Quaternion()
                    logger.test("frame.rotation %s", frame.rotation)
                    logger.test("frame.rotation.euler %s", frame.rotation.toEulerAngles())
                    # オリジナルを保持
                    frame.org_rotation = frame.rotation.copy()

                    # 補間曲線
                    frame.interpolation = list(self.unpack(64, "64B", True))
                    logger.test("interpolation %s", frame.interpolation)

                    if bone_name not in motion.bones:
                        # まだ辞書にない場合、配列追加
                        motion.bones[bone_name] = {}

                    # 辞書の該当部分にボーンフレームを追加
                    if frame.fno not in motion.bones[bone_name]:
                        motion.bones[bone_name][frame.fno] = frame

                    if frame.fno > motion.last_motion_frame:
                        # 最終フレームを記録
                        motion.last_motion_frame = frame.fno

                    if n // 10000 > prev_n:
                        prev_n = n // 10000
                        logger.info("-- VMDモーション読み込み キー: %s" % n)

                # モーフ数
                motion.morph_cnt = self.read_uint(4)
                logger.test("motion.morph_cnt %s", motion.morph_cnt)

                # 1F分のモーフ情報
                prev_n = 0
                for n in range(motion.morph_cnt):
                    morph = VmdMorphFrame()
                    morph.key = True
                    morph.read = True

                    # モーフ ----------------------
                    # モーフ名
                    morph_bname, morph_name = self.read_text(15)

                    morph.name = morph_name
                    morph.bname = morph_bname
                    logger.test("name: %s, bname %s", morph_name, morph_bname)

                    # フレームIDX
                    morph.fno = self.read_uint(4)
                    logger.test("morph.fno %s", morph.fno)

                    # 度数
                    morph.ratio = self.read_float(4)
                    logger.test("morph.ratio %s", morph.ratio)

                    if morph_name not in motion.morphs:
                        # まだ辞書にない場合、配列追加
                        motion.morphs[morph_name] = {}

                    if morph.fno not in motion.morphs[morph_name]:
                        # まだなければ辞書の該当部分にモーフフレームを追加
                        motion.morphs[morph_name][morph.fno] = morph

                    if n // 1000 > prev_n:
                        prev_n = n // 1000
                        logger.info("-- VMDモーション読み込み モーフ: %s" % n)

                try:
                    # カメラ数
                    motion.camera_cnt = self.read_uint(4)
                    logger.test("motion.camera_cnt %s", motion.camera_cnt)

                    # 1F分のカメラ情報
                    prev_n = 0
                    for n in range(motion.camera_cnt):
                        camera = VmdCameraFrame()

                        # フレームIDX
                        camera.fno = self.read_uint(4)
                        logger.test("camera.fno %s", camera.fno)

                        # 距離
                        camera.length = self.read_float(4)
                        logger.test("camera.length %s", camera.length)

                        # ０距離の場合、念のため少しだけ距離を入れておく
                        if camera.length == 0:
                            camera.length = -0.00001

                        # 位置X,Y,Z
                        camera.position = self.read_Vector3D()
                        logger.test("camera.position %s", camera.position)

                        # 角度（オイラー角）
                        camera.euler = self.read_Vector3D()
                        logger.test("camera.euler %s", camera.euler)

                        # 補間曲線
                        camera.interpolation = self.unpack(24, "24B", True)
                        logger.test("camera.interpolation %s", camera.interpolation)

                        # 視野角
                        camera.angle = self.read_uint(4)
                        logger.test("camera.angle %s", camera.angle)

                        # パース有無
                        camera.perspective = self.unpack(1, "B")
                        logger.test("camera.perspective %s", camera.perspective)

                        # オリジナルを保持
                        camera.org_length = camera.org_length
                        camera.org_position = camera.org_position.copy()

                        # カメラを追加
                        motion.cameras[camera.fno] = camera

                        if n // 10000 > prev_n:
                            prev_n = n // 10000
                            logger.info("VMDカメラ読み込み キー: %s" % n)

                except Exception:
                    # 情報がない場合、catchして握りつぶす
                    motion.camera_cnt = 0

                # 照明数
                try:
                    motion.light_cnt = self.read_uint(4)
                    logger.test("motion.light_cnt %s", motion.light_cnt)

                    # 1F分の照明情報
                    for _ in range(motion.light_cnt):
                        light = VmdLightFrame()

                        # フレームIDX
                        light.fno = self.read_uint(4)
                        logger.test("light.fno %s", light.fno)

                        # 照明色(RGBだが、下手に数値が変わるのも怖いのでV3D)
                        light.color = self.read_Vector3D()
                        logger.test("light.color %s", light.color)

                        # 照明位置
                        light.position = self.read_Vector3D()
                        logger.test("light.position %s", light.position)

                        # 追加
                        motion.lights.append(light)

                except Exception:
                    # 情報がない場合、catchして握りつぶす
                    motion.light_cnt = 0

                # セルフシャドウ数
                try:
                    motion.shadow_cnt = self.read_uint(4)
                    logger.test("motion.shadow_cnt %s", motion.shadow_cnt)

                    # 1F分のシャドウ情報
                    for _ in range(motion.shadow_cnt):
                        shadow = VmdShadowFrame()

                        # フレームIDX
                        shadow.fno = self.read_uint(4)
                        logger.test("shadow.fno %s", shadow.fno)

                        # シャドウ種別
                        shadow.type = self.read_uint(1)
                        logger.test("shadow.type %s", shadow.type)

                        # 距離
                        shadow.distance = self.read_float()
                        logger.test("shadow.distance %s", shadow.distance)

                        # 追加
                        motion.shadows.append(shadow)

                except Exception:
                    # 情報がない場合、catchして握りつぶす
                    motion.shadow_cnt = 0

                # IK数
                try:
                    motion.ik_cnt = self.read_uint(4)
                    logger.test("motion.ik_cnt %s", motion.ik_cnt)

                    # 1F分のIK情報
                    for _ in range(motion.ik_cnt):
                        show_ik = VmdShowIkFrame()

                        # フレームIDX
                        show_ik.fno = self.read_uint(4)
                        logger.test("ik.fno %s", show_ik.fno)

                        # モデル表示, 0:OFF, 1:ON
                        show_ik.show = self.read_uint(1)
                        logger.test("ik.show %s", show_ik.show)

                        # 記録するIKの数
                        show_ik.ik_count = self.read_uint(4)
                        logger.test("ik.ik_count %s", show_ik.ik_count)

                        for _ in range(show_ik.ik_count):
                            ik_info = VmdInfoIk()

                            # IK名
                            ik_bname, ik_name = self.read_text(20)
                            ik_info.name = ik_name
                            ik_info.bname = ik_bname
                            logger.test("ik_info.name %s", ik_name)

                            # モデル表示, 0:OFF, 1:ON
                            ik_info.onoff = self.read_uint(1)
                            logger.test("ik_info.onoff %s", ik_info.onoff)

                            show_ik.ik.append(ik_info)

                        # 追加
                        motion.showiks.append(show_ik)

                except Exception:
                    # 昔のMMD（MMDv7.39.x64以前）はIK情報がないため、catchして握りつぶす
                    motion.ik_cnt = 0

            # ハッシュを設定
            motion.digest = self.hexdigest()
            logger.test("motion: %s, hash: %s", motion.path, motion.digest)

            return motion
        except MKilledException as ke:
            # 終了命令
            raise ke
        except SizingException as se:
            logger.error("VMD読み込み処理が処理できないデータで終了しました。\n\n%s", se.message, decoration=MLogger.DECORATION_BOX)
            return se
        except Exception as e:
            import traceback
            logger.critical("VMD読み込み処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc(), decoration=MLogger.DECORATION_BOX)
            raise e

    def hexdigest(self):
        sha1 = hashlib.sha1()

        with open(self.file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(2048 * sha1.block_size), b''):
                sha1.update(chunk)

        sha1.update(chunk)

        # ファイルパスをハッシュに含める
        sha1.update(self.file_path.encode('utf-8'))

        return sha1.hexdigest()

    def read_text(self, format_size):
        bresult = self.unpack(format_size, "{0}s".format(format_size))

        if not self.encoding:
            # まだエンコードが確定していない場合、エンコード取得
            self.encoding = self.get_encoding(bresult, False)

        if self.encoding:
            # エンコードが取れた場合、復元
            return bresult, self.decode_text(bresult, self.encoding, False)

        return None, None

    # ファイルのエンコードを取得する
    def get_encoding(self, fbytes, is_raise=True):
        codelst = ('shift-jis', 'utf-8')

        for encoding in codelst:
            try:
                fstr = self.decode_text(fbytes, encoding, False)  # bytes文字列から指定文字コードの文字列に変換
                fstr = fstr.encode('utf-8')  # uft-8文字列に変換
                # 問題なく変換できたらエンコードを返す
                logger.test("%s: encoding: %s", fstr, encoding)
                return encoding
            except Exception as e:
                logger.test("get_encoding failure: %s", encoding)
                logger.error(e)
                pass

        # 変換に失敗したらとりあえずNone
        return None

    # 文字列デコード
    def decode_text(self, fbytes, encoding, is_raise=True):
        logger.test("decode_text: %s", encoding)

        if not encoding:
            # エンコードがない場合はNone
            return None

        fbytes2 = re.sub(b'\x00.*$', b'', fbytes)
        logger.test("decode_text %s -> %s", fbytes, fbytes2)

        if is_raise:
            try:
                return fbytes2.decode(encoding)
            except Exception as e:
                # エラーを投げる場合はそのまま投げる
                raise e
        else:
            # エラーを投げない場合
            try:
                if encoding == 'shift-jis':
                    # shift-jisは一旦cp932に変換してもう一度戻したのでテスト
                    return fbytes2.decode('shift_jis', errors='replace').encode('cp932', errors='replace').decode('cp932', errors='replace')

                # 変換できなかった文字は「?」に変換する
                return fbytes2.decode(encoding=encoding, errors='replace')
            except Exception:
                # 投げない場合はとりあえずNone
                return None

    def read_Vector3D(self):
        return MVector3D(self.read_float(), self.read_float(), self.read_float())

    def read_Quaternion(self):
        x = self.read_float()
        y = self.read_float()
        z = self.read_float()
        scalar = self.read_float()
        return MQuaternion(scalar, x, y, z)

    # 整数の解凍
    def read_int(self, format_size):
        if format_size == 1:
            format_type = "b"
        elif format_size == 2:
            format_type = "h"
        elif format_size == 4:
            format_type = "i"
        else:
            raise MParseException("read_int format_sizeエラー {0}".format(format_size))

        return self.unpack(format_size, format_type)

    # 整数の解凍
    def read_uint(self, format_size):
        if format_size == 1:
            format_type = "B"
        elif format_size == 2:
            format_type = "H"
        elif format_size == 4:
            format_type = "I"
        else:
            raise MParseException("read_uint format_sizeエラー {0}".format(format_size))

        return self.unpack(format_size, format_type)

    # 小数の解凍
    def read_float(self, format_size=4):
        if format_size == 4:
            format_type = "f"
        elif format_size == 8:
            format_type = "d"
        else:
            raise MParseException("read_float format_sizeエラー {0}".format(format_size))

        return self.unpack(format_size, format_type)

    # 解凍して、offsetを更新する
    def unpack(self, format_size, format, is_all=False):
        bresult = struct.unpack_from(format, self.buffer, self.offset)

        # オフセットを更新する
        self.offset += format_size

        if bresult:
            if is_all:
                # 全部を返す場合、配列全部を返す
                result = bresult
            else:
                # 全指定がない場合、先頭のみ返す
                result = bresult[0]
        else:
            result = None

        return result
