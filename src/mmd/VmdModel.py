# -*- coding: utf-8 -*-
#
import struct
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MLogger # noqa

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
        # ボーン名：VmdBoneFrameの配列
        self.frames = {}
        self.morph_cnt = 0
        # モーフ名：VmdMorphFrameの配列
        self.morphs = {}
        self.camera_cnt = 0
        # カメラ：VmdCameraFrameの配列
        self.cameras = {}
        self.light_cnt = 0
        # 照明：VmdLightFrameの配列
        self.lights = {}
        self.shadow_cnt = 0
        # セルフ影：VmdShadowFrameの配列
        self.shadows = {}
        self.ik_cnt = 0
        # モデル表示・IK on/off：VmdShowIkFrameの配列
        self.showiks = {}
        # ハッシュ値
        self.digest = None

    def get_bone_frame_nos(self, bone_name):
        if not self.frames or self.motion_cnt == 0 or bone_name not in self.frames:
            return []
        
        return [fno for fno in self.frames[bone_name].keys()]

    def get_morph_frame_nos(self, morph_name):
        if not self.morphs or self.morph_cnt == 0 or morph_name not in self.morphs:
            return []
        
        return [fno for fno in self.morphs[morph_name].keys()]

    class VmdMorphFrame():
        def __init__(self, frame=0):
            self.name = ''
            self.format_name = ''
            self.frame = frame
            self.ratio = 0
        
        def write(self, fout):
            fout.write(self.name)
            fout.write(bytearray([0 for i in range(len(self.name), 15)]))  # ボーン名15Byteの残りを\0で埋める
            fout.write(struct.pack('<L', self.frame))
            fout.write(struct.pack('<f', self.ratio))

        def __str__(self):
            return "<VmdMorphFrame name:{0}, frame:{1}, ratio:{2}".format(self.name, self.frame, self.ratio)

    class VmdBoneFrame():
        def __init__(self, frame=0):
            self.name = ''
            self.format_name = ''
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
            return "<VmdBoneFrame format_name:{0}, frame:{1}, position:{2}, rotation:{3}, interpolation: {4}, key:{5}".format( \
                self.format_name, self.frame, self.position, self.rotation, self.interpolation, self.key)

        def write(self, fout):
            fout.write(self.name)
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
            fout.write(bytearray(self.interpolation))
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
            
            