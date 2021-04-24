# -*- coding: utf-8 -*-
#
import hashlib
import re

from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils.MException import MParseException # noqa
from utils.MLogger import MLogger # noqa
from utils.MException import SizingException, MKilledException

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
            logger.test("signature %s", signature)

        model_name_pattern = re.compile(r'(.*)(\.osm;.*)', flags=re.IGNORECASE)

        for n in range(len(lines)):
            # モデル名
            if "// 親ファイル名" in lines[n]:
                m = re.search(model_name_pattern, lines[n])
                if len(m.groups()) > 0:
                    return m.groups()[0]

        return "VPDデータ解析失敗"

    def read_data(self):
        # VPDファイルを通常読み込み
        lines = []

        try:
            with open(self.file_path, "r", encoding=self.get_file_encoding(self.file_path)) as f:
                lines = f.readlines()

            if len(lines) > 0:
                # vpdバージョン
                signature = lines[0]
                logger.test("signature %s", signature)

            motion = VmdMotion()
            # モーション数(常に1)
            motion.motion_cnt = 1
            motion.last_motion_frame = 0

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
                    frame = VmdBoneFrame(0)
                    frame.set_name(bone_name)
                    frame.key = True
                    frame.read = True

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
                        motion.bones[bone_name] = {0: frame}
                        frame = None
                        continue

            # ハッシュを設定
            motion.digest = self.hexdigest()
            logger.test("motion: %s, hash: %s", motion.path, motion.digest)

            return motion
        except MKilledException as ke:
            # 終了命令
            raise ke
        except SizingException as se:
            logger.error("サイジング処理が処理できないデータで終了しました。\n\n%s", se.message)
            return se
        except Exception as e:
            import traceback
            logger.error("サイジング処理が意図せぬエラーで終了しました。\n\n%s", traceback.format_exc())
            raise e

    # 一行を読み込む
    def read_line(self, line, test_pattern, n):
        m = re.search(test_pattern, line)
        if m and len(m.groups()) > 0:
            logger.test("line[%s]: %s, m: %s", n, line, m.groups())
            return m.groups()

        # 正規表現に合致するのが取れなかった場合、None
        return None
 
    def hexdigest(self):
        sha1 = hashlib.sha1()

        with open(self.file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(2048 * sha1.block_size), b''):
                sha1.update(chunk)

        sha1.update(chunk)

        # ファイルパスをハッシュに含める
        sha1.update(self.file_path.encode('utf-8'))

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
                logger.test("%s: encoding: %s", file_path, encoding)
                return encoding
            except Exception:
                pass
                
        raise MParseException("unknown encoding!")
        
