# -*- coding: utf-8 -*-

import struct
import re
from PyQt5.QtGui import QQuaternion, QVector3D, QColor

class VmdMorphFrame():
    def __init__(self, frame=0):
        self.name = ''
        self.frame = frame
        self.ratio = 0
    
    def write(self, fout):
        fout.write(self.name)
        fout.write(bytearray([0 for i in range(len(self.name), 15)])) # ボーン名15Byteの残りを\0で埋める
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('<f', self.ratio))

    def __str__(self):
        return "<VmdMorphFrame name:{0}, frame:{1}, ratio:{2}".format(
                self.name, self.frame, self.ratio
    )

class VmdBoneFrame():
    def __init__(self, frame=0):
        self.name = ''
        self.format_name = ''
        self.frame = frame
        self.position = QVector3D(0, 0, 0)
        self.rotation = QQuaternion()
        self.complement = [20, 20, 0, 0, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 20, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 0]
        self.org_complement = [20, 20, 0, 0, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 20, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 20, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 20, 20, 20, 20, 20, 107, 107, 107, 107, 107, 107, 107, 107, 0, 0, 0]
        self.key = True

    def __str__(self):
        return "<VmdBoneFrame format_name:{0}, frame:{1}, position:{2}, rotation:{3}, complement: {4}, key:{5}".format(
                self.format_name, self.frame, self.position, self.rotation, self.complement, self.key
    )

    def write(self, fout):
        fout.write(self.name)
        fout.write(bytearray([0 for i in range(len(self.name), 15)])) # ボーン名15Byteの残りを\0で埋める
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('<f', self.position.x()))
        fout.write(struct.pack('<f', self.position.y()))
        fout.write(struct.pack('<f', self.position.z()))
        v = self.rotation.toVector4D()
        fout.write(struct.pack('<f', v.x()))
        fout.write(struct.pack('<f', v.y()))
        fout.write(struct.pack('<f', v.z()))
        fout.write(struct.pack('<f', v.w()))

        # print(self.complement)
        # print(b''.join(self.complement))
        # print([ c.encode() for c in self.complement ])

        # s = struct.Struct("64s")
        # packed_value = struct.pack("64s", [ c.encode() for c in self.complement ])
        # fout.write(packed_value)
        # fout.write(struct.pack('64s', self.complement))

        # fout.write([ c.encode('unicode_escape') for c in self.complement ])

        # c = b''.join([ c.encode('unicode_escape') for c in self.complement ])
        # print(c)
        # print([ c.encode('unicode_escape') for c in self.complement ])
        # fout.write(struct.pack('=64s', c))
        # fout.write(struct.pack('=64s', [ c.encode('unicode_escape') for c in self.complement ][0]))
        fout.write(bytearray(self.complement))

        # for c in self.complement:
        #     # print(c.encode('unicode_escape'))
        #     fout.write(struct.pack('=64s', c.encode('unicode_escape')))
        #     break

        # fout.write(bytearray([i for i in self.complement])) # 補間パラメータ(64Byte)

class VmdCameraFrame():
    def __init__(self):
        self.frame = 0
        self.length = 0
        self.position = QVector3D(0, 0, 0)
        self.euler = QVector3D(0, 0, 0)
        self.complement=[20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107, 20, 107]
        self.angle = 0
        self.perspective = 1

    def write(self, fout):
        fout.write(struct.pack('<L', self.frame))
        fout.write(struct.pack('<f', self.length))
        fout.write(struct.pack('<f', self.position.x()))
        fout.write(struct.pack('<f', self.position.y()))
        fout.write(struct.pack('<f', self.position.z()))
        fout.write(struct.pack('<f', self.euler.x()))
        fout.write(struct.pack('<f', self.euler.y()))
        fout.write(struct.pack('<f', self.euler.z()))
        fout.write(bytearray(self.complement))
        fout.write(struct.pack('<L', self.angle))
        fout.write(struct.pack('b', self.perspective))

class VmdLightFrame():
    def __init__(self):
        self.frame = 0
        self.color = QVector3D(0, 0, 0)
        self.position = QVector3D(0, 0, 0)

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
            fout.write(bytearray([0 for i in range(len(k.name), 20)])) # IKボーン名20Byteの残りを\0で埋める
            fout.write(struct.pack('b', k.onoff))
        
class VmdWriter():
    def __init__(self):
        pass

    def write_vmd_file(self, filename, model_name, bone_frames, morph_frames, camera_frames, light_frames, shadow_frames, showik_frames):
        """Write VMD data to a file"""
        fout = open(filename, "wb")

        # header
        fout.write(b'Vocaloid Motion Data 0002\x00\x00\x00\x00\x00')
            
        if len(bone_frames) > 0 or len(morph_frames) > 0 or len(showik_frames) > 0:
            
            # モデル名を20byteで切る
            model_bname = model_name.ljust(100).encode('shift-jis')[:20]
            # 空白は \x00で埋める
            model_bname = re.sub(b' ', b'\x00', model_bname)

            # # モデル名をバイト変換して設定
            # model_name_parts = ""
            # count = 0
            # for c in model_name:
            #     if east_asian_width(c) in 'FWA':
            #         # 2バイト文字は2換算
            #         count += 2
            #     else:
            #         count += 1

            #     model_name_parts += c

            #     # 20文字だと2バイト文字入れたら溢れるので、19でカット
            #     if count >= 19:
            #         break

            # model_bname = model_name_parts.encode('shift-jis')

            # for _ in range(20 - count):
            #     # 最後までパディング
            #     model_bname += b'\x00'
                
            # print("VMD出力: model_name: %s, model_bname: %s" % (model_name, model_bname))
            fout.write(model_bname)
        else:
            # カメラ・照明
            fout.write(b'\x83J\x83\x81\x83\x89\x81E\x8f\xc6\x96\xbe\x00on Data')

        # bone frames
        fout.write(struct.pack('<L', len(bone_frames))) # ボーンフレーム数
        for bf in bone_frames:
            bf.write(fout)
        fout.write(struct.pack('<L', len(morph_frames))) # 表情キーフレーム数
        for mf in morph_frames:
            mf.write(fout)
        fout.write(struct.pack('<L', len(camera_frames))) # カメラキーフレーム数
        for cf in camera_frames:
            cf.write(fout)
        fout.write(struct.pack('<L', len(light_frames))) # 照明キーフレーム数
        for cf in light_frames:
            cf.write(fout)
        fout.write(struct.pack('<L', len(shadow_frames))) # セルフ影キーフレーム数
        for cf in shadow_frames:
            cf.write(fout)
        fout.write(struct.pack('<L', len(showik_frames))) # モデル表示・IK on/offキーフレーム数
        for sf in showik_frames:
            sf.write(fout)
        
        fout.close()
