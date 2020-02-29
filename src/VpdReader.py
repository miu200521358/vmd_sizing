# -*- coding: utf-8 -*-

import struct
import logging
import re
import copy
import hashlib
from PyQt5.QtGui import QQuaternion, QVector3D
from VmdWriter import VmdBoneFrame
from VmdReader import VmdMotion
from PmxModel import ParseException

logger = logging.getLogger("VmdSizing").getChild(__name__)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.setLevel(logging.INFO)
logger.addHandler(handler)

class VpdMotion():
    def __init__(self):
        self.path = ''
        self.signature = ''
        self.model_name = ''
        self.last_motion_frame = 0
        self.motion_cnt = 0
        # ボーン名：VmdBoneFrameの配列
        self.frames = {}
        # ハッシュ値
        self.digest = None

class VpdReader():
    def __init__(self):
        self.encoding = None

    # モデル名だけ取得
    def read_vpd_file_modelname(self, filepath):
        # VPDファイルを通常読み込み
        lines = []

        with open(filepath, "r", encoding=self.get_file_encoding(filepath)) as f:
            lines = f.readlines()

        if len(lines) > 0:
            # vpdバージョン
            signature = lines[0]
            logger.debug("signature %s", signature)

        model_name_pattern = re.compile(r'(.*)(\.osm;.*)', flags=re.IGNORECASE)

        for n in range(len(lines)):
            # モデル名
            if "// 親ファイル名" in lines[n]:
                m = re.search(model_name_pattern, lines[n])
                if len(m.groups()) > 0:
                    return m.groups()[0]

        return "VPDデータ解析失敗"

    def read_vpd_file(self, filepath):
        # VPDファイルを通常読み込み
        lines = []

        with open(filepath, "r", encoding=self.get_file_encoding(filepath)) as f:
            lines = f.readlines()

        if len(lines) > 0:
            # vpdバージョン
            signature = lines[0]
            logger.debug("signature %s", signature)

        motion = VmdMotion()
        # モーション数(常に1)
        motion.motion_cnt = motion.last_motion_frame = 1

        # 各パターン（括弧はひとつのみ実体として取得する）
        model_name_pattern = re.compile(r'(.*)(?:\.osm;)(?:.*// 親ファイル名.*)', flags=re.IGNORECASE)
        bone_start_pattern = re.compile(r'(?:.*)(?:{)(.*)', flags=re.IGNORECASE)
        bone_pos_pattern = re.compile(r'([+-]?\d+(?:\.\d+))(?:,)([+-]?\d+(?:\.\d+))(?:,)([+-]?\d+(?:\.\d+))(?:;)(?:.*trans.*)', flags=re.IGNORECASE)
        bone_rot_pattern = re.compile(r'([+-]?\d+(?:\.\d+))(?:,)([+-]?\d+(?:\.\d+))(?:,)([+-]?\d+(?:\.\d+))(?:,)([+-]?\d+(?:\.\d+))(?:;)(?:.*Quaternion.*)', flags=re.IGNORECASE)
        bone_end_pattern = re.compile(r'(?:.*)(})(?:.*)', flags=re.IGNORECASE)

        frame = None

        for n in range(len(lines)):
            # モデル名
            result_values = self.read_line(lines[n], model_name_pattern, n)
            if result_values:
                motion.model_name = result_values[0]

                continue
            
            # 括弧開始
            result_values = self.read_line(lines[n], bone_start_pattern, n)
            if result_values:
                bone_name = result_values[0]
                
                # キーフレ生成
                frame = VmdBoneFrame()
                frame.key = True
                frame.read = True

                # ボーン名のエンコード値
                frame.name = bone_name.encode('cp932').decode('shift_jis').encode('shift_jis')
                # ボーン名
                frame.format_name = bone_name

                continue
            
            if frame:
                # 括弧内のチェック
                
                # 位置
                result_values = self.read_line(lines[n], bone_pos_pattern, n)
                if result_values:
                    # 位置X,Y,Z
                    frame.position = QVector3D(float(result_values[0]), float(result_values[1]), float(result_values[2]))
                    continue
                
                # 角度
                result_values = self.read_line(lines[n], bone_rot_pattern, n)
                if result_values:
                    # 回転scalar,X,Y,Z
                    frame.rotation = QQuaternion(float(result_values[3]), float(result_values[0]), float(result_values[1]), float(result_values[2]))
                    continue

                # 括弧終了
                result_values = self.read_line(lines[n], bone_end_pattern, n)
                if result_values:
                    motion.frames[bone_name] = [frame]
                    frame = None
                    continue

        # ハッシュを設定
        motion.digest = self.hexdigest(filepath)
        logger.debug("motion: %s, hash: %s", motion.path, motion.digest)

        return motion            

    # 一行を読み込む
    def read_line(self, line, test_pattern, n):
        m = re.search(test_pattern, line)
        result_values = []
        if m and len(m.groups()) > 0:
            logger.debug("line[%s]: %s, m: %s", n, line, m.groups())
            return m.groups()

        # 正規表現に合致するのが取れなかった場合、None
        return None




        # # VMDファイルをバイナリ読み込み
        # self.buffer = open(filepath, "rb").read()
        
        # # vmdバージョン
        # signature = self.unpack(30, "30s")
        # logger.debug("signature %s", signature)

        
        # # モーションパス
        # motion.path = filepath

        # # モデル名
        # model_bname, model_name = self.read_text(20)
        # logger.debug("model_bname %s, model_name: %s", model_bname, model_name)
        # motion.model_name = model_name

        # # モーション数
        # motion.motion_cnt = self.read_uint(4)
        # logger.debug("motion.motion_cnt %s", motion.motion_cnt)
        
        # # モーションのあるキーのINDEX
        # motion_indexes = {}
        
        # # 1F分のモーション情報
        # for n in range(motion.motion_cnt):
        #     frame = VmdBoneFrame()
        #     frame.key = True
        #     frame.read = True
            
        #     # ボーン ----------------------
        #     # ボーン名
        #     bone_bname, bone_name = self.read_text(15)

        #     frame.name = bone_bname
        #     frame.format_name = bone_name
        #     logger.debug("name: %s, format_name %s", bone_bname, bone_name)
            
        #     # フレームIDX
        #     frame.frame = self.read_uint(4)
        #     logger.debug("frame.frame %s", frame.frame)            
            
        #     # 位置X,Y,Z
        #     frame.position = self.read_Vector3D()
        #     logger.debug("frame.position %s", frame.position)   
        #     # オリジナルを保持
        #     frame.org_position = copy.deepcopy(frame.position)         
            
        #     # 回転X,Y,Z,scalar
        #     frame.rotation = self.read_Quaternion()
        #     logger.debug("frame.rotation %s", frame.rotation)            
        #     logger.debug("frame.rotation.euler %s", frame.rotation.toEulerAngles())            
        #     # オリジナルを保持
        #     frame.org_rotation = copy.deepcopy(frame.rotation)         
            
        #     # 補間曲線
        #     frame.complement = list(self.unpack(64, "64B", True))
        #     logger.debug("complement %s", frame.complement)
        #     # オリジナルの補間曲線を保持しておく
        #     frame.org_complement = copy.deepcopy(frame.complement)
        #     logger.debug("org_complement %s", frame.org_complement)
            
        #     if bone_name not in motion.frames:
        #         # まだ辞書にない場合、配列追加
        #         motion.frames[bone_name] = []
        #         motion_indexes[bone_name] = {}

        #     is_not_existed = True
        #     if frame.frame in motion_indexes[bone_name]:
        #         is_not_existed = False

        #     # 辞書の該当部分にボーンフレームを追加
        #     if is_not_existed == True:
        #         motion.frames[bone_name].append(frame)
        #         motion_indexes[bone_name][frame.frame] = frame.frame

        #     if frame.frame > motion.last_motion_frame:
        #         # 最終フレームを記録
        #         motion.last_motion_frame = frame.frame
            
        #     if n % 10000 == 0:
        #         print("VMDモーション読み込み キー: %s" % n)
                
        # # ソート
        # for k, v in motion.frames.items():
        #     motion.frames[k] = sorted(v, key=lambda u: u.frame)
 

    def hexdigest(self, filepath):
        sha1 = hashlib.sha1()

        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(2048 * sha1.block_size), b''):
                sha1.update(chunk)

        sha1.update(chunk)

        return sha1.hexdigest()      
        
    # ファイルのエンコードを取得する
    def get_file_encoding(self, file_path):
        try: 
            f = open(file_path, "rb")
            fbytes = f.read()
            f.close()
        except:
            raise Exception("unknown encoding!")
            
        codelst = ('shift-jis', 'utf_8')
        
        for encoding in codelst:
            try:
                fstr = fbytes.decode(encoding) # bytes文字列から指定文字コードの文字列に変換
                fstr = fstr.encode('utf-8') # uft-8文字列に変換
                # 問題なく変換できたらエンコードを返す
                logger.debug("%s: encoding: %s", file_path, encoding)
                return encoding
            except:
                pass
                
        raise Exception("unknown encoding!")
        
        