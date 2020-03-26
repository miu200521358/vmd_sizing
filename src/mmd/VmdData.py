# -*- coding: utf-8 -*-
#
import copy
import struct
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MBezierUtils # noqa
from utils.MLogger import MLogger

logger = MLogger(__name__)


class VmdBoneFrame():
    def __init__(self, fno=0, name=''):
        self.name = name
        self.bname = name.encode('cp932').decode('shift_jis').encode('shift_jis')
        self.fno = fno
        self.position = MVector3D()
        self.rotation = MQuaternion()
        self.org_position = MVector3D()
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
        return "<VmdBoneFrame name:{0}, fno:{1}, position:{2}, rotation:{3}, interpolation: {4}, key:{5}".format( \
            self.name, self.fno, self.position, self.rotation, self.interpolation, self.key)

    def write(self, fout):
        fout.write(self.bname)
        fout.write(bytearray([0 for i in range(len(self.bname), 15)]))  # ボーン名15Byteの残りを\0で埋める
        fout.write(struct.pack('<L', int(self.fno)))
        fout.write(struct.pack('<f', float(self.position.x())))
        fout.write(struct.pack('<f', float(self.position.y())))
        fout.write(struct.pack('<f', float(self.position.z())))
        v = self.rotation.toVector4D()
        fout.write(struct.pack('<f', float(v.x())))
        fout.write(struct.pack('<f', float(v.y())))
        fout.write(struct.pack('<f', float(v.z())))
        fout.write(struct.pack('<f', float(v.w())))
        fout.write(bytearray([int(x) for x in self.interpolation]))


class VmdMorphFrame():
    def __init__(self, fno=0):
        self.name = ''
        self.bname = ''
        self.fno = fno
        self.ratio = 0
    
    def write(self, fout):
        fout.write(self.bname)
        fout.write(bytearray([0 for i in range(len(self.bname), 15)]))  # ボーン名15Byteの残りを\0で埋める
        fout.write(struct.pack('<L', self.fno))
        fout.write(struct.pack('<f', self.ratio))

    def __str__(self):
        return "<VmdMorphFrame name:{0}, fno:{1}, ratio:{2}".format(self.name, self.fno, self.ratio)


class VmdCameraFrame():
    def __init__(self):
        self.fno = 0
        self.length = 0
        self.position = MVector3D(0, 0, 0)
        self.euler = MVector3D(0, 0, 0)
        self.interpolation = [20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107]
        self.angle = 0
        self.perspective = 0

    def write(self, fout):
        fout.write(struct.pack('<L', int(self.fno)))
        fout.write(struct.pack('<f', float(self.length)))
        fout.write(struct.pack('<f', float(self.position.x())))
        fout.write(struct.pack('<f', float(self.position.y())))
        fout.write(struct.pack('<f', float(self.position.z())))
        fout.write(struct.pack('<f', float(self.euler.x())))
        fout.write(struct.pack('<f', float(self.euler.y())))
        fout.write(struct.pack('<f', float(self.euler.z())))
        fout.write(bytearray([int(x) for x in self.interpolation]))
        fout.write(struct.pack('<L', int(self.angle)))
        fout.write(struct.pack('b', self.perspective))


class VmdLightFrame():
    def __init__(self):
        self.fno = 0
        self.color = MVector3D(0, 0, 0)
        self.position = MVector3D(0, 0, 0)

    def write(self, fout):
        fout.write(struct.pack('<L', self.fno))
        fout.write(struct.pack('<f', self.color.x()))
        fout.write(struct.pack('<f', self.color.y()))
        fout.write(struct.pack('<f', self.color.z()))
        fout.write(struct.pack('<f', self.position.x()))
        fout.write(struct.pack('<f', self.position.y()))
        fout.write(struct.pack('<f', self.position.z()))


class VmdShadowFrame():
    def __init__(self):
        self.fno = 0
        self.type = 0
        self.distance = 0

    def write(self, fout):
        fout.write(struct.pack('<L', self.fno))
        fout.write(struct.pack('<f', self.type))
        fout.write(struct.pack('<f', self.distance))


# VmdShowIkFrame のikの中の要素
class VmdInfoIk():
    def __init__(self, name='', onoff=0):
        self.name = name
        self.onoff = onoff


class VmdShowIkFrame():
    def __init__(self):
        self.fno = 0
        self.show = 0
        self.ik_count = 0
        self.ik = []

    def write(self, fout):
        fout.write(struct.pack('<L', self.fno))
        fout.write(struct.pack('b', self.show))
        fout.write(struct.pack('<L', len(self.ik)))
        for k in (self.ik):
            fout.write(k.name)
            fout.write(bytearray([0 for i in range(len(k.name), 20)]))  # IKボーン名20Byteの残りを\0で埋める
            fout.write(struct.pack('b', k.onoff))
        

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
        self.bones = {}
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
    def calc_bone_by_interpolation(self, bone_name: str, fno: int, is_existed=False, is_key=False, is_read=False):
        fill_bf = VmdBoneFrame(fno=fno, name=bone_name)

        if bone_name not in self.bones:
            self.bones[bone_name] = {}
            self.bones[bone_name][fno] = fill_bf
        
        # 条件に合致するフレーム番号を探す
        # is_key: 登録対象のキーを探す
        # is_read: データ読み込み時のキーを探す
        fnos = [x for x in sorted(self.bones[bone_name].keys()) if (x == fno) and (not is_key or (is_key and self.bones[x].key)) and (not is_read or (is_read and self.bones[x].read))]
        
        if len(fnos) > 0:
            # 合致するキーが見つかった場合、それを返す
            return self.bones[bone_name][fnos[0]]
        else:
            # 合致するキーが見つからなかった場合
            if is_existed:
                # 既存キーのみ探している場合はNone
                return None

        # 番号より前のフレーム番号
        before_fnos = [x for x in sorted(self.bones[bone_name].keys()) if (x < fno)]
        # 番号より後のフレーム番号
        after_fnos = [x for x in sorted(self.bones[bone_name].keys()) if (x > fno)]

        if len(after_fnos) == 0:
            if len(before_fnos) == 0:
                # 番号の前後もない場合、新規キーを返す
                return fill_bf
            else:
                # 番号より前があって、後のがない場合、前のをコピーして返す
                fill_bf = copy.deepcopy(self.bones[bone_name][before_fnos[-1]])
                fill_bf.fno = fno
                return fill_bf

        prev_bf = self.bones[bone_name][before_fnos[-1]]
        after_bf = self.bones[bone_name][after_fnos[0]]

        # 補間曲線を元に間を埋める
        fill_bf.rotation = self.calc_bone_by_interpolation_rot(prev_bf, fill_bf, after_bf)
        fill_bf.position = self.calc_bone_by_interpolation_pos(prev_bf, fill_bf, after_bf)
        
        return fill_bf

    # 補間曲線を元に、回転ボーンの値を求める
    def calc_bone_by_interpolation_rot(self, prev_bf: VmdBoneFrame, fill_bf: VmdBoneFrame, after_bf: VmdBoneFrame):
        if prev_bf.rotation != after_bf.rotation:
            # 回転補間曲線
            rx, ry, rt = MBezierUtils.evaluate(after_bf.interpolation[MBezierUtils.R_x1_idxs[3]], after_bf.interpolation[MBezierUtils.R_y1_idxs[3]], \
                                               after_bf.interpolation[MBezierUtils.R_x2_idxs[3]], after_bf.interpolation[MBezierUtils.R_y2_idxs[3]], \
                                               prev_bf.fno, fill_bf.fno, after_bf.fno)
            return MQuaternion.slerp(prev_bf.rotation, after_bf.rotation, ry)

        return copy.deepcopy(prev_bf.rotation)

    # 補間曲線を元に移動ボーンの値を求める
    def calc_bone_by_interpolation_pos(self, prev_bf: VmdBoneFrame, fill_bf: VmdBoneFrame, after_bf: VmdBoneFrame):

        # 補間曲線を元に間を埋める
        if prev_bf.position != after_bf.position:
            # http://rantyen.blog.fc2.com/blog-entry-65.html
            # X移動補間曲線
            xx, xy, xt = MBezierUtils.evaluate(after_bf.interpolation[MBezierUtils.MX_x1_idxs[3]], after_bf.interpolation[MBezierUtils.MX_y1_idxs[3]], \
                                               after_bf.interpolation[MBezierUtils.MX_x2_idxs[3]], after_bf.interpolation[MBezierUtils.MX_y2_idxs[3]], \
                                               prev_bf.fno, fill_bf.fno, after_bf.fno)
            # Y移動補間曲線
            yx, yy, yt = MBezierUtils.evaluate(after_bf.interpolation[MBezierUtils.MY_x1_idxs[3]], after_bf.interpolation[MBezierUtils.MY_y1_idxs[3]], \
                                               after_bf.interpolation[MBezierUtils.MY_x2_idxs[3]], after_bf.interpolation[MBezierUtils.MY_y2_idxs[3]], \
                                               prev_bf.fno, fill_bf.fno, after_bf.fno)
            # Z移動補間曲線
            zx, zy, zt = MBezierUtils.evaluate(after_bf.interpolation[MBezierUtils.MZ_x1_idxs[3]], after_bf.interpolation[MBezierUtils.MZ_y1_idxs[3]], \
                                               after_bf.interpolation[MBezierUtils.MZ_x2_idxs[3]], after_bf.interpolation[MBezierUtils.MZ_y2_idxs[3]], \
                                               prev_bf.fno, fill_bf.fno, after_bf.fno)

            fill_pos = MVector3D()
            fill_pos.setX(prev_bf.position.x() + ((after_bf.position.x() - prev_bf.position.x()) * xy))
            fill_pos.setY(prev_bf.position.y() + ((after_bf.position.y() - prev_bf.position.y()) * yy))
            fill_pos.setZ(prev_bf.position.z() + ((after_bf.position.z() - prev_bf.position.z()) * zy))
            
            return fill_pos
        
        return copy.deepcopy(prev_bf.position)

    # ボーンモーション：フレーム番号リスト
    def get_bone_fnos(self, bone_name: str):
        if not self.bones or self.motion_cnt == 0 or bone_name not in self.bones:
            return []
        
        return sorted([fno for fno in self.bones[bone_name].keys()])

    # モーフモーション：フレーム番号リスト
    def get_morph_fnos(self, morph_name: str):
        if not self.morphs or self.morph_cnt == 0 or morph_name not in self.morphs:
            return []
        
        return sorted([fno for fno in self.morphs[morph_name].keys()])
    
    # ボーンモーション：一次元配列
    def get_bone_frames(self):
        total_bone_frames = []

        for bone_name, bone_frames in self.bones.items():
            # キーフレを逆順で取得
            for fno in reversed(self.get_bone_fnos(bone_name)):
                total_bone_frames.append(bone_frames[fno])
        
        return total_bone_frames
    
    # モーフモーション：一次元配列
    def get_morph_frames(self):
        total_morph_frames = []

        for morph_name, morph_frames in self.morphs.items():
            # キーフレを逆順で取得
            for fno in reversed(self.get_morph_fnos(morph_name)):
                total_morph_frames.append(morph_frames[fno])
        
        return total_morph_frames
    
    def append_bone_frame(self, frame: VmdBoneFrame):
        if frame.name not in self.bones:
            # まだ該当ボーン名がない場合、追加
            self.bones[frame.name] = {}
        
        self.bones[frame.name][frame.fno] = frame

    def append_morph_frame(self, frame: VmdMorphFrame):
        if frame.name not in self.morphs:
            # まだ該当モーフ名がない場合、追加
            self.morphs[frame.name] = {}
        
        self.morphs[frame.name][frame.fno] = frame



