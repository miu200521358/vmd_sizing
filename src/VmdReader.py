# -*- coding: utf-8 -*-

import struct
import logging
import re
import copy
from PyQt5.QtGui import QQuaternion, QVector3D
from VmdWriter import VmdBoneFrame, VmdMorphFrame, VmdCameraFrame, VmdLightFrame, VmdShadowFrame, VmdShowIkFrame, VmdInfoIk
from PmxModel import ParseException

logger = logging.getLogger("__main__").getChild(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class VmdMotion():
    def __init__(self):
        self.path = ''
        self.signature = ''
        self.model_name = ''
        self.last_motion_frame = 0
        self.motion_cnt = 0
        # ボーン名：VmdBoneFrameの配列
        self.frames = {}
        self.morph_cnt = 0
        # モーフ名：VmdMorphFrameの配列
        self.morphs = {}
        self.camera_cnt = 0
        # カメラ：VmdCameraFrameの配列
        self.cameras = []
        self.light_cnt = 0
        # 照明：VmdLightFrameの配列
        self.lights = []
        self.shadow_cnt = 0
        # セルフ影：VmdShadowFrameの配列
        self.shadows = []
        self.ik_cnt = 0
        # モデル表示・IK on/off：VmdShowIkFrameの配列
        self.showiks = []

class VmdReader():
    def __init__(self):
        self.offset = 0
        self.buffer = None
        self.encoding = None

    # モデル名だけ取得
    def read_vmd_file_modelname(self, filename):
        # VMDファイルをバイナリ読み込み
        self.buffer = open(filename, "rb").read()
        
        # vmdバージョン
        signature = self.unpack(30, "30s")
        logger.debug("signature %s", signature)

        # モデル名
        model_bname, model_name = self.read_text(20)
        logger.debug("model_bname %s, model_name: %s", model_bname, model_name)

        return model_name

    def read_vmd_file(self, filename):
        # VMDファイルをバイナリ読み込み
        self.buffer = open(filename, "rb").read()
        
        # vmdバージョン
        signature = self.unpack(30, "30s")
        logger.debug("signature %s", signature)

        motion = VmdMotion()
        
        # モーションパス
        motion.path = filename

        # モデル名
        model_bname, model_name = self.read_text(20)
        logger.debug("model_bname %s, model_name: %s", model_bname, model_name)
        motion.model_name = model_name

        # モーション数
        motion.motion_cnt = self.read_uint(4)
        logger.debug("motion.motion_cnt %s", motion.motion_cnt)
        
        # モーションのあるキーのINDEX
        motion_indexes = {}
        
        # 1F分のモーション情報
        for n in range(motion.motion_cnt):
            frame = VmdBoneFrame()
            frame.key = True
            
            # ボーン ----------------------
            # ボーン名
            bone_bname, bone_name = self.read_text(15)

            frame.name = bone_bname
            frame.format_name = bone_name
            logger.debug("name: %s, format_name %s", bone_bname, bone_name)
            
            # フレームIDX
            frame.frame = self.read_uint(4)
            logger.debug("frame.frame %s", frame.frame)            
            
            # 位置X,Y,Z
            frame.position = self.read_Vector3D()
            logger.debug("frame.position %s", frame.position)            
            
            # 回転X,Y,Z,scalar
            frame.rotation = self.read_Quaternion()
            logger.debug("frame.rotation %s", frame.rotation)            
            logger.debug("frame.rotation.euler %s", frame.rotation.toEulerAngles())            
            
            # 補間曲線
            frame.complement = list(self.unpack(64, "64B", True))
            logger.debug("complement %s", frame.complement)
            # オリジナルの補間曲線を保持しておく
            frame.org_complement = copy.deepcopy(frame.complement)
            logger.debug("org_complement %s", frame.org_complement)
            
            if bone_name not in motion.frames:
                # まだ辞書にない場合、配列追加
                motion.frames[bone_name] = []
                motion_indexes[bone_name] = {}

            is_not_existed = True
            if frame.frame in motion_indexes[bone_name]:
                is_not_existed = False

            # 辞書の該当部分にボーンフレームを追加
            if is_not_existed == True:
                motion.frames[bone_name].append(frame)
                motion_indexes[bone_name][frame.frame] = frame.frame

            if frame.frame > motion.last_motion_frame:
                # 最終フレームを記録
                motion.last_motion_frame = frame.frame
            
            if n % 10000 == 0:
                print("VMDモーション読み込み キー: %s" % n)
                
        # ソート
        for k, v in motion.frames.items():
            motion.frames[k] = sorted(v, key=lambda u: u.frame)

        # モーフ数
        motion.morph_cnt = self.read_uint(4)
        logger.debug("motion.morph_cnt %s", motion.morph_cnt)
                
        # モーションのあるキーのINDEX
        morph_indexes = {}

        # 1F分のモーフ情報
        for n in range(motion.morph_cnt):
            morph = VmdMorphFrame()
            
            # ボーン ----------------------
            # ボーン名
            morph_bname, morph_name = self.read_text(15)

            morph.name = morph_bname
            morph.format_name = morph_name
            logger.debug("name: %s, format_name %s", morph_bname, morph_name)
            
            # フレームIDX
            morph.frame = self.read_uint(4)
            logger.debug("morph.frame %s", morph.frame)            
            
            # 度数
            morph.ratio = self.read_float(4)
            logger.debug("morph.ratio %s", morph.ratio)

            if morph_name not in motion.morphs:
                # まだ辞書にない場合、配列追加
                motion.morphs[morph_name] = []
                morph_indexes[morph_name] = {}

            is_not_existed = True
            if morph.frame in morph_indexes[morph_name]:
                is_not_existed = False

            if is_not_existed == True:
                # まだなければ辞書の該当部分にモーフフレームを追加
                motion.morphs[morph_name].append(morph)
                morph_indexes[morph_name][morph.frame] = morph.frame
        
            if n % 1000 == 0:
                print("VMDモーション読み込み モーフ: %s" % n)
                
        # ソート
        for k, v in motion.morphs.items():
            motion.morphs[k] = sorted(v, key=lambda u: u.frame)

        # カメラ数
        motion.camera_cnt = self.read_uint(4)
        logger.debug("motion.camera_cnt %s", motion.camera_cnt)
        
        # 1F分のカメラ情報
        for _ in range(motion.camera_cnt):
            camera = VmdCameraFrame()
                        
            # フレームIDX
            camera.frame = self.read_uint(4)
            logger.debug("camera.frame %s", camera.frame)            
            
            # 距離
            camera.length = self.read_float(4)
            logger.debug("camera.length %s", camera.length)            
            
            # 位置X,Y,Z
            camera.position = self.read_Vector3D()
            logger.debug("camera.position %s", camera.position)
            
            # 角度（オイラー角）
            camera.euler = self.read_Vector3D()
            logger.debug("camera.euler %s", camera.euler)
            
            # 補間曲線
            camera.complement = self.unpack(24, "24B", True)
            logger.debug("camera.complement %s", camera.complement)
            
            # 視野角
            camera.angle = self.read_uint(4)
            logger.debug("camera.angle %s", camera.angle)
            
            # パース有無
            camera.perspective = self.unpack(1, "B")

            # カメラを追加
            motion.cameras.append(camera)
        
        # ソート
        motion.cameras = sorted(motion.cameras, key=lambda u: u.frame)

        # 照明数
        try:
            motion.light_cnt = self.read_uint(4)
            logger.debug("motion.light_cnt %s", motion.light_cnt)
        except Exception as e:
            # 情報がない場合、catchして握りつぶす
            motion.light_cnt = 0
        
        # 1F分の照明情報
        for _ in range(motion.light_cnt):
            light = VmdLightFrame()
                        
            # フレームIDX
            light.frame = self.read_uint(4)
            logger.debug("light.frame %s", light.frame)     

            # 照明色(RGBだが、下手に数値が変わるのも怖いのでV3D)
            light.color = self.read_Vector3D()
            logger.debug("light.color %s", light.color)            

            # 照明位置
            light.position = self.read_Vector3D()
            logger.debug("light.position %s", light.position) 

            # 追加
            motion.lights.append(light)           
            
        # セルフシャドウ数
        try:
            motion.shadow_cnt = self.read_uint(4)
            logger.debug("motion.shadow_cnt %s", motion.shadow_cnt)

            # 1F分のシャドウ情報
            for _ in range(motion.shadow_cnt):
                shadow = VmdShadowFrame()
                            
                # フレームIDX
                shadow.frame = self.read_uint(4)
                logger.debug("shadow.frame %s", shadow.frame)     

                # シャドウ種別
                shadow.type = self.read_uint(1)
                logger.debug("shadow.type %s", shadow.type)            

                # 距離
                shadow.distance = self.read_float()
                logger.debug("shadow.distance %s", shadow.distance)            
                
                # 追加
                motion.shadows.append(shadow)

        except Exception as e:
            # 情報がない場合、catchして握りつぶす
            motion.shadow_cnt = 0
        
        # IK数
        try:
            motion.ik_cnt = self.read_uint(4)
            logger.debug("motion.ik_cnt %s", motion.ik_cnt)

            # 1F分のIK情報
            for _ in range(motion.ik_cnt):
                ik = VmdShowIkFrame()
                            
                # フレームIDX
                ik.frame = self.read_uint(4)
                logger.debug("ik.frame %s", ik.frame)     

                # モデル表示, 0:OFF, 1:ON
                ik.show = self.read_uint(1)
                logger.debug("ik.show %s", ik.show)            

                # 記録するIKの数
                ik.ik_count = self.read_uint(4)
                logger.debug("ik.ik_count %s", ik.ik_count)     

                for _ in range(ik.ik_count):
                    ik_info = VmdInfoIk()

                    # IK名
                    ik_bname, ik_name = self.read_text(20)
                    ik_info.name = ik_bname
                    logger.debug("ik_info.name %s", ik_name)            

                    # モデル表示, 0:OFF, 1:ON
                    ik_info.onoff = self.read_uint(1)
                    logger.debug("ik_info.onoff %s", ik_info.onoff)            

                    ik.ik.append(ik_info)  

                # 追加
                motion.showiks.append(ik)       
                            
        except Exception as e:
            # 昔のMMD（MMDv7.39.x64以前）はIK情報がないため、catchして握りつぶす
            motion.ik_cnt = 0
        
        return motion            
                    
    
    
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
                fstr = self.decode_text(fbytes, encoding, True) # bytes文字列から指定文字コードの文字列に変換
                fstr = fstr.encode('utf-8') # uft-8文字列に変換
                # 問題なく変換できたらエンコードを返す
                logger.debug("%s: encoding: %s", fstr, encoding)
                return encoding
            except Exception as e:
                logger.debug("get_encoding failure: %s", encoding)
                logger.error(e)
                pass
        
        # 変換に失敗したらとりあえずNone
        return None
    
    # 文字列デコード
    def decode_text(self, fbytes, encoding, is_raise=True):
        logger.debug("decode_text: %s", encoding)
        
        if not encoding:
            # エンコードがない場合はNone
            return None
        
        fbytes2 = re.sub(b'\x00.*$', b'', fbytes)
        logger.debug("decode_text %s -> %s", fbytes, fbytes2)

        if is_raise == True:
            try:
                return fbytes2.decode(encoding)
            except Exception as e:
                # エラーを投げる場合はそのまま投げる
                raise e
        else:
            # エラーを投げない場合
            try:
                # 変換できなかった文字は「?」に変換する
                return fbytes2.decode(encoding=encoding, errors='replace')
            except Exception as e:
                # 投げない場合はとりあえずNone
                return None
    
    def read_Vector3D(self):
        return QVector3D(self.read_float(), self.read_float(), self.read_float())

    def read_Quaternion(self):
        x = self.read_float()
        y = self.read_float()
        z = self.read_float()
        scalar = self.read_float()
        return QQuaternion(scalar, x, y, z)

    # 整数の解凍
    def read_int(self, format_size):
        if format_size == 1:
            format_type = "b"
        elif format_size == 2:
            format_type = "h"
        elif format_size == 4:
            format_type = "i"
        else:
            raise ParseException("read_int format_sizeエラー {0}".format(format_size))

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
            raise ParseException("read_uint format_sizeエラー {0}".format(format_size))

        return self.unpack(format_size, format_type)

    # 小数の解凍
    def read_float(self, format_size=4):
        if format_size == 4:
            format_type = "f"
        elif format_size == 8:
            format_type = "d"
        else:
            raise ParseException("read_float format_sizeエラー {0}".format(format_size))

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
    