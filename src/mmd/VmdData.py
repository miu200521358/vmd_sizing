# -*- coding: utf-8 -*-
#
import copy
import struct
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MBezierUtils # noqa
from utils.MLogger import MLogger

logger = MLogger(__name__)


# https://blog.goo.ne.jp/torisu_tetosuki/e/bc9f1c4d597341b394bd02b64597499d
# https://w.atwiki.jp/kumiho_k/pages/15.html
class VmdMotion():
    def __init__(self):
        self.path = ''
        self.signature = ''
        self.model_name = ''
        self.last_motion_frame = 0
        self.motion_cnt = 0
        # ボーン名：VmdBoneFrameの辞書(key:ボーン名)
        self.frames = {}
        self.morph_cnt = 0
        # モーフ名：VmdMorphFrameの辞書(key:モーフ名)
        self.morphs = {}
        self.camera_cnt = 0
        # カメラ：VmdCameraFrameの配列
        self.cameras = {}
        self.light_cnt = 0
        # 照明：VmdLightFrameの配列
        self.lights = []
        self.shadow_cnt = 0
        # セルフ影：VmdShadowFrameの配列
        self.shadows = []
        self.ik_cnt = 0
        # モデル表示・IK on/off：VmdShowIkFrameの配列
        self.showiks = []
        # ハッシュ値
        self.digest = None

    # 補間曲線を考慮した指定フレーム番号の位置
    # https://www55.atwiki.jp/kumiho_k/pages/15.html
    # https://harigane.at.webry.info/201103/article_1.html
    def calc_bone_by_interpolation(self, bone_name, frameno, is_only, is_exist, is_key=False, is_read=False):
        fill_bf = VmdBoneFrame(frame=frameno, name=bone_name)

        if bone_name not in self.frames:
            self.frames[bone_name] = {}
            self.frames[bone_name][frameno] = fill_bf

        now_framenos = [x for x in sorted(self.frames[bone_name].keys()) if x == frameno]
        
        if len(now_framenos) == 1:
            if is_read:
                if self.frames[bone_name][frameno].read:
                    return self.frames[bone_name][frameno]
                else:
                    pass
            else:
                # キー指定がある場合、キーが有効である場合のみ返す
                if is_key:
                    if self.frames[bone_name][frameno].key:
                        return self.frames[bone_name][frameno]
                    else:
                        pass
                else:
                    # 指定フレームがある場合、それを返す
                    if is_exist:
                        # 存在しているものの場合、コピーしないでそのもの
                        return self.frames[bone_name][frameno]
                    else:
                        return copy.deepcopy(self.frames[bone_name][frameno])
        elif is_only and is_exist:
            # 指定フレームがなく、かつそれ固定指定で、既存の場合、None
            return None

        after_framenos = [x for x in sorted(self.frames[bone_name].keys()) if x > frameno]
        
        if len(after_framenos) == 0:
            if is_exist:
                # 存在固定で、最後までいっても見つからなければ、None
                return None
            elif is_only:
                # 最後まで行っても見つからなければ、最終項目を該当フレーム用に設定して返す
                last_frameno = [x for x in sorted(self.frames[bone_name].keys())][-1]
                fill_bf = copy.deepcopy(self.frames[bone_name][last_frameno])
                return fill_bf

        if is_read:
            # キーONの場合、有効なのを返す
            for af in after_framenos:
                if self.frames[bone_name][af].read:
                    return self.frames[bone_name][af]
        elif is_key:
            # キーONの場合、有効なのを返す
            for af in after_framenos:
                if self.frames[bone_name][af].key:
                    return self.frames[bone_name][af]
        elif is_exist:
            # 既存指定の場合、自身のフレーム（指定フレームの直後のフレーム）
            return copy.deepcopy(self.frames[bone_name][after_framenos[0]])

        # 前フレーム
        prev_framenos = [x for x in sorted(self.frames[bone_name].keys()) if x < fill_bf.frame]
        prev_bf = None

        # 指定されたフレーム直前の有効キー(数が多いのからチェック)
        for p in reversed(prev_framenos):
            if self.frames[bone_name][p].key:
                prev_bf = self.frames[bone_name][p]
                break
        if not prev_bf:
            # 有効な前キーが取れない場合、暫定的に現在フレームの値を保持する
            prev_bf = copy.deepcopy(fill_bf)

        # 計算対象フレーム
        calc_bf = None

        # 次フレーム
        next_next_framenos = [x for x in sorted(self.frames[bone_name].keys()) if x > fill_bf.frame]
        next_bf = None

        # 指定されたフレーム直後のキー
        for p in next_next_framenos:
            next_bf = self.frames[bone_name][p]
            break
        
        if next_bf:
            # 次がある場合、次を採用
            calc_bf = copy.deepcopy(next_bf)
        else:
            if len(now_framenos) > 0:
                # 現在がある場合、現在キー
                calc_bf = copy.deepcopy(self.frames[bone_name][now_framenos[0]])
            else:
                # 現在も次もない場合、過去を計算対象とする
                calc_bf = copy.deepcopy(prev_bf)

            calc_bf.frame = frameno
        
        # 補間曲線を元に間を埋める
        fill_bf.rotation = self.calc_bone_by_interpolation_rot(prev_bf, calc_bf, fill_bf)
        fill_bf.position = self.calc_bone_by_interpolation_pos(prev_bf, calc_bf, fill_bf)
        
        return fill_bf

    # 補間曲線を元に、回転ボーンの値を求める
    def calc_bone_by_interpolation_rot(self, prev_bf, calc_bf, fill_bf):
        if prev_bf.rotation != calc_bf.rotation:
            # 回転補間曲線
            _, _, rn = MBezierUtils.calc_interpolate_bezier(calc_bf.interpolation[MBezierUtils.R_x1_idxs[3]], calc_bf.interpolation[MBezierUtils.R_y1_idxs[3]], \
                                                            calc_bf.interpolation[MBezierUtils.R_x2_idxs[3]], calc_bf.interpolation[MBezierUtils.R_y2_idxs[3]], \
                                                            prev_bf.frame, calc_bf.frame, fill_bf.frame)
            return MQuaternion.slerp(prev_bf.rotation, calc_bf.rotation, rn)

        return copy.deepcopy(prev_bf.rotation)

    # 補間曲線を元に移動ボーンの値を求める
    def calc_bone_by_interpolation_pos(self, prev_bf, calc_bf, fill_bf):

        # 補間曲線を元に間を埋める
        if prev_bf.position != calc_bf.position:
            # http://rantyen.blog.fc2.com/blog-entry-65.html
            # X移動補間曲線
            _, _, xn = MBezierUtils.calc_interpolate_bezier(calc_bf.interpolation[MBezierUtils.MX_x1_idxs[3]], calc_bf.interpolation[MBezierUtils.MX_y1_idxs[3]], \
                                                            calc_bf.interpolation[MBezierUtils.MX_x2_idxs[3]], calc_bf.interpolation[MBezierUtils.MX_y2_idxs[3]], \
                                                            prev_bf.frame, calc_bf.frame, fill_bf.frame)
            # Y移動補間曲線
            _, _, yn = MBezierUtils.calc_interpolate_bezier(calc_bf.interpolation[MBezierUtils.MY_x1_idxs[3]], calc_bf.interpolation[MBezierUtils.MX_y1_idxs[3]], \
                                                            calc_bf.interpolation[MBezierUtils.MY_x2_idxs[3]], calc_bf.interpolation[MBezierUtils.MY_y2_idxs[3]], \
                                                            prev_bf.frame, calc_bf.frame, fill_bf.frame)
            # Z移動補間曲線
            _, _, zn = MBezierUtils.calc_interpolate_bezier(calc_bf.interpolation[MBezierUtils.MZ_x1_idxs[3]], calc_bf.interpolation[MBezierUtils.MZ_y1_idxs[3]], \
                                                            calc_bf.interpolation[MBezierUtils.MZ_x2_idxs[3]], calc_bf.interpolation[MBezierUtils.MZ_y2_idxs[3]], \
                                                            prev_bf.frame, calc_bf.frame, fill_bf.frame)

            fill_pos = MVector3D()
            fill_pos.setX(prev_bf.position.x() + ((calc_bf.position.x() - prev_bf.position.x()) * xn))
            fill_pos.setY(prev_bf.position.y() + ((calc_bf.position.y() - prev_bf.position.y()) * yn))
            fill_pos.setZ(prev_bf.position.z() + ((calc_bf.position.z() - prev_bf.position.z()) * zn))
            
            return fill_pos
        
        return copy.deepcopy(prev_bf.position)

    # ボーンモーション：フレーム番号リスト
    def get_bone_frame_nos(self, bone_name):
        if not self.frames or self.motion_cnt == 0 or bone_name not in self.frames:
            return []
        
        return sorted([fno for fno in self.frames[bone_name].keys()])

    # モーフモーション：フレーム番号リスト
    def get_morph_frame_nos(self, morph_name):
        if not self.morphs or self.morph_cnt == 0 or morph_name not in self.morphs:
            return []
        
        return sorted([fno for fno in self.morphs[morph_name].keys()])
    
    # ボーンモーション：一次元配列
    def get_bone_frames(self):
        total_bone_frames = []

        for bone_name, bone_frames in self.frames.items():
            # キーフレを逆順で取得
            fnos = reversed(self.get_bone_frame_nos(bone_name))

            for fno in fnos:
                total_bone_frames.append(bone_frames[fno])
        
        return total_bone_frames
    
    # モーフモーション：一次元配列
    def get_morph_frames(self):
        total_morph_frames = []

        for morph_name, morph_frames in self.morphs.items():
            # キーフレを逆順で取得
            fnos = reversed(self.get_morph_frame_nos(morph_name))

            for fno in fnos:
                total_morph_frames.append(morph_frames[fno])
        
        return total_morph_frames


class VmdMorphFrame():
    def __init__(self, frame=0):
        self.name = ''
        self.bname = ''
        self.frame = frame
        self.ratio = 0
    
    def write(self, fout):
        fout.write(self.bname)
        fout.write(bytearray([0 for i in range(len(self.name), 15)]))  # ボーン名15Byteの残りを\0で埋める
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('<f', self.ratio))

    def __str__(self):
        return "<VmdMorphFrame name:{0}, frame:{1}, ratio:{2}".format(self.name, self.frame, self.ratio)


class VmdBoneFrame():
    def __init__(self, frame=0, name=''):
        self.name = name
        self.bname = name.encode('cp932').decode('shift_jis').encode('shift_jis')
        self.frame = frame
        self.position = MVector3D(0, 0, 0)
        self.rotation = MQuaternion()
        self.org_position = MVector3D(0, 0, 0)
        self.org_rotation = MQuaternion()
        self.interpolation = [20, 20, 0, 0, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 20, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 0] # noqa
        self.org_interpolation = [20, 20, 0, 0, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 20, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 0] # noqa
        # 登録対象であるか否か
        self.key = False
        # VMD読み込み処理で読み込んだキーか
        self.read = False
        # 補間曲線の分割で追加したキーか
        self.split_interpolation = False

    def __str__(self):
        return "<VmdBoneFrame bname:{0}, frame:{1}, position:{2}, rotation:{3}, interpolation: {4}, key:{5}".format( \
            self.bname, self.frame, self.position, self.rotation, self.interpolation, self.key)

    def write(self, fout):
        fout.write(self.bname)
        fout.write(bytearray([0 for i in range(len(self.name), 15)]))  # ボーン名15Byteの残りを\0で埋める
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('<f', self.position.x()))
        fout.write(struct.pack('<f', self.position.y()))
        fout.write(struct.pack('<f', self.position.z()))
        v = self.rotation.toVector4D()
        fout.write(struct.pack('<f', v.x()))
        fout.write(struct.pack('<f', v.y()))
        fout.write(struct.pack('<f', v.z()))
        fout.write(struct.pack('<f', v.w()))
        fout.write(bytearray([int(x) for x in self.interpolation]))


class VmdCameraFrame():
    def __init__(self):
        self.frame = 0
        self.length = 0
        self.position = MVector3D(0, 0, 0)
        self.euler = MVector3D(0, 0, 0)
        self.interpolation = [20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107]
        self.angle = 0
        self.perspective = 0

    def write(self, fout):
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('<f', self.length))
        fout.write(struct.pack('<f', self.position.x()))
        fout.write(struct.pack('<f', self.position.y()))
        fout.write(struct.pack('<f', self.position.z()))
        fout.write(struct.pack('<f', self.euler.x()))
        fout.write(struct.pack('<f', self.euler.y()))
        fout.write(struct.pack('<f', self.euler.z()))
        fout.write(bytearray([int(x) for x in self.interpolation]))
        fout.write(struct.pack('<L', self.angle))
        fout.write(struct.pack('b', self.perspective))


class VmdLightFrame():
    def __init__(self):
        self.frame = 0
        self.color = MVector3D(0, 0, 0)
        self.position = MVector3D(0, 0, 0)

    def write(self, fout):
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('<f', self.color.x()))
        fout.write(struct.pack('<f', self.color.y()))
        fout.write(struct.pack('<f', self.color.z()))
        fout.write(struct.pack('<f', self.position.x()))
        fout.write(struct.pack('<f', self.position.y()))
        fout.write(struct.pack('<f', self.position.z()))


class VmdShadowFrame():
    def __init__(self):
        self.frame = 0
        self.type = 0
        self.distance = 0

    def write(self, fout):
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('<f', self.type))
        fout.write(struct.pack('<f', self.distance))


# VmdShowIkFrame のikの中の要素
class VmdInfoIk():
    def __init__(self, name='', onoff=0):
        self.name = name
        self.onoff = onoff


class VmdShowIkFrame():
    def __init__(self):
        self.frame = 0
        self.show = 0
        self.ik_count = 0
        self.ik = []

    def write(self, fout):
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('b', self.show))
        fout.write(struct.pack('<L', len(self.ik)))
        for k in (self.ik):
            fout.write(k.name)
            fout.write(bytearray([0 for i in range(len(k.name), 20)]))  # IKボーン名20Byteの残りを\0で埋める
            fout.write(struct.pack('b', k.onoff))
        
        