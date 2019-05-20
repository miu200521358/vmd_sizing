# -*- coding: utf-8 -*-

import struct
import logging
import re
from PyQt5.QtGui import QQuaternion, QVector3D
from VmdWriter import VmdBoneFrame, VmdMorphFrame

logger = logging.getLogger("__main__").getChild(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class VmdMotion():
    def __init__(self):
        self.signature = ''
        self.model_name = ''
        self.last_motion_frame = 0
        self.motion_cnt = 0
        # ボーン名：VmdBoneFrameの配列
        self.frames = {}
        self.morph_cnt = 0
        # モーフ名：VmdMorphFrameの配列
        self.morphs = {}

class VmdReader():
    def __init__(self):
        pass

    def read_vmd_file(self, filename):
        """Read VMD data to a file"""
        fin = open(filename, "rb").read()
        
        motion = VmdMotion()

        # vmdバージョン
        signature = struct.unpack_from("30s", fin, 0)
        # vmdバージョンは英語だけなので、とりあえずutf-8変換
        motion.signature = byte_decode(signature[0], "utf-8")
        logger.debug("signature %s", motion.signature)

        # モデル名
        model_name = struct.unpack_from("20s", fin, 30)

        try:
            # 文字コードが取れた場合、それでモデル名取得
            encoding = get_encoding(model_name[0])
            motion.model_name = byte_decode(model_name[0], encoding, False)
            logger.debug("model_name %s", motion.model_name)
        except Exception:
            encoding = None
        
        # モーション数
        motion_cnt = struct.unpack_from("I", fin, 50)
        motion.motion_cnt = motion_cnt[0]
        logger.debug("motion_cnt %s", motion.motion_cnt)

        # 1F分の情報
        for n in range(motion.motion_cnt):
            frame = VmdBoneFrame()
            
            # ボーン ----------------------
            # ボーン名
            bone_bname = struct.unpack_from("15s", fin, 54 + (n * 111))

            # ボーン名はそのまま追加
            frame.name = bone_bname[0]

            if encoding == None:
                # モデル名でエンコードが取れなかった場合、ボーン名で取得
                encoding = get_encoding(bone_bname[0])
                
            # ボーン名を分かる形に変換(キー用)
            bone_name = byte_decode(bone_bname[0], encoding, False)
            
            logger.debug("frame.name %s", bone_name)

            frame.format_name = bone_name

            # フレームIDX
            frame.frame = struct.unpack_from("I", fin, 69 + (n * 111))[0]
            logger.debug("frame.frame %s", frame.frame)

            # 位置X,Y,Z
            frame.position.setX(struct.unpack_from("f", fin, 73 + (n * 111))[0])
            frame.position.setY(struct.unpack_from("f", fin, 77 + (n * 111))[0])
            frame.position.setZ(struct.unpack_from("f", fin, 81 + (n * 111))[0])
            logger.debug("frame.position %s", frame.position)
            
            # 回転X,Y,Z,scalar
            frame.rotation.setX(struct.unpack_from("f", fin, 85 + (n * 111))[0])
            frame.rotation.setY(struct.unpack_from("f", fin, 89 + (n * 111))[0])
            frame.rotation.setZ(struct.unpack_from("f", fin, 93 + (n * 111))[0])
            frame.rotation.setScalar(struct.unpack_from("f", fin, 97 + (n * 111))[0])
            logger.debug("frame.rotation %s", frame.rotation)
            logger.debug("frame.rotation.toEulerAngles() %s", frame.rotation.toEulerAngles())

            # 補間曲線
            # logger.info(struct.unpack_from("64B", fin, 101 + (n * 111)))
            frame.complement = struct.unpack_from("64B", fin, 101 + (n * 111))
            # frame.complement=['%x' % x for x in range(struct.unpack_from("64B", fin, 101 + (n * 111))[0]) ]
            logger.debug("frame.complement %s: %s %s", frame.frame, bone_name, frame.complement)

            if bone_name not in motion.frames:
                # まだ辞書にない場合、配列追加
                motion.frames[bone_name] = []

            # 辞書の該当部分にボーンフレームを追加
            motion.frames[bone_name].append(frame)

            if frame.frame > motion.last_motion_frame:
                # 最終フレームを記録
                motion.last_motion_frame = frame.frame
        
        # ソート
        for k, v in motion.frames.items():
            motion.frames[k] = sorted(v, key=lambda u: u.frame)

        # モーフ数
        morph_cnt = struct.unpack_from("I", fin, 54 + ((n + 1) * 111))
        motion.morph_cnt = morph_cnt[0]
        logger.debug("morph_cnt %s", motion.morph_cnt)

        # 1F分の情報
        for m in range(motion.morph_cnt):
            # モーフ -------------------------------------
            morph = VmdMorphFrame()

            # モーフ名
            morph_bname = struct.unpack_from("15s", fin, 58 + ((n + 1) * 111) + (m * 23))

            # モーフ名はそのまま追加
            morph.name = morph_bname[0]

            # モーフ名を分かる形に変換(キー用)
            morph_name = byte_decode(morph_bname[0], encoding, False)
            
            logger.debug("morph.name %s", morph_name)

            # フレームIDX
            morph.frame = struct.unpack_from("I", fin, 73 + ((n + 1) * 111) + (m * 23))[0]
            logger.debug("morph.frame %s", morph.frame)

            # 度数
            morph.ratio = struct.unpack_from("f", fin, 77 + ((n + 1) * 111) + (m * 23))[0]
            logger.debug("morph.ratio %s", morph.ratio)

            if morph_name not in motion.morphs:
                # まだ辞書にない場合、配列追加
                motion.morphs[morph_name] = []

            # 辞書の該当部分にモーフフレームを追加
            motion.morphs[morph_name].append(morph)
        
        # ソート
        for k, v in motion.morphs.items():
            motion.morphs[k] = sorted(v, key=lambda u: u.frame)

        return motion


# ファイルのエンコードを取得する
def get_encoding(fbytes, is_raise=True):        
    codelst = ('shift-jis', 'utf-8')
    
    for encoding in codelst:
        try:
            fstr = byte_decode(fbytes, encoding, True) # bytes文字列から指定文字コードの文字列に変換
            fstr = fstr.encode('utf-8') # uft-8文字列に変換
            # 問題なく変換できたらエンコードを返す
            logger.debug("%s: encoding: %s", fstr, encoding)
            return encoding
        except:
            pass

    print("■■■■■■■■■■■■■■■■■")
    print("■　**ERROR**　")
    print("■　2バイト文字の変換処理に失敗しました。")
    print("■　モーションデータを別名保存して再実行すると直る可能性があります。")
    print("■■■■■■■■■■■■■■■■■")

    raise Exception("unknown encoding!: ", fbytes)

def byte_decode(fbytes, encoding, is_raise=True):
    fbytes2 = re.sub(b'\x00.*$', b'', fbytes)
    logger.debug("byte_decode %s -> %s", fbytes, fbytes2)

    if is_raise == True:
        try:
            return fbytes2.decode(encoding)
        except Exception as e:
            # # loggerだと二重出力されるので、とりあえずprint
            # print("fbytes: %s" % fbytes)
            # print("%s" % e)
            # print("■■■■■■■■■■■■■■■■■")
            # print("■　**ERROR**　")
            # print("■　2バイト文字の変換処理に失敗しました。")
            # print("■　モーションデータを別名保存して再実行すると直る可能性があります。")
            # print("■■■■■■■■■■■■■■■■■")

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

