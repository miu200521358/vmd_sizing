# -*- coding: utf-8 -*-
#
import hashlib
import re
from mmd import VmdMotion
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MLogger import MLogger # noqa
from utils import MParseException # noqa

logger = MLogger(__name__)


class VpdReader():
    def __init__(self, file_path):
        self.encoding = None
        self.file_path = file_path

    # モデル名だけ取得
    def read_model_name(self):
        # VPDファイルを通常読み込み
        lines = []

        with open(self.file_path, "r", encoding=self.get_file_encoding(self.file_path)) as f:
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

    def read_vpd_file(self):
        # VPDファイルを通常読み込み
        lines = []

        with open(self.file_path, "r", encoding=self.get_file_encoding(self.file_path)) as f:
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
                frame = VmdMotion.VmdBoneFrame()
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
                    frame.position = MVector3D(float(result_values[0]), float(result_values[1]), float(result_values[2]))
                    continue
                
                # 角度
                result_values = self.read_line(lines[n], bone_rot_pattern, n)
                if result_values:
                    # 回転scalar,X,Y,Z
                    frame.rotation = MQuaternion(float(result_values[3]), float(result_values[0]), float(result_values[1]), float(result_values[2]))
                    continue

                # 括弧終了
                result_values = self.read_line(lines[n], bone_end_pattern, n)
                if result_values:
                    motion.frames[bone_name] = [frame]
                    frame = None
                    continue

        # ハッシュを設定
        motion.digest = self.hexdigest(self.file_path)
        logger.debug("motion: %s, hash: %s", motion.path, motion.digest)

        return motion

    # 一行を読み込む
    def read_line(self, line, test_pattern, n):
        m = re.search(test_pattern, line)
        if m and len(m.groups()) > 0:
            logger.debug("line[%s]: %s, m: %s", n, line, m.groups())
            return m.groups()

        # 正規表現に合致するのが取れなかった場合、None
        return None
 
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
        except Exception:
            raise MParseException("unknown encoding!")
            
        codelst = ('shift-jis', 'utf_8')
        
        for encoding in codelst:
            try:
                fstr = fbytes.decode(encoding)  # bytes文字列から指定文字コードの文字列に変換
                fstr = fstr.encode('utf-8')  # uft-8文字列に変換
                # 問題なく変換できたらエンコードを返す
                logger.debug("%s: encoding: %s", file_path, encoding)
                return encoding
            except Exception:
                pass
                
        raise MParseException("unknown encoding!")
        
