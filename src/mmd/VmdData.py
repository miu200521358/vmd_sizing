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
        self.bname = ''
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
        return "<VmdBoneFrame name:{0}, fno:{1}, position:{2}, rotation:{3}, euler:{4}, interpolation: {5}, key:{6}".format( \
            self.name, self.fno, self.position, self.rotation, self.rotation.toEulerAngles4MMD(), self.interpolation, self.key)

    def write(self, fout):
        if not self.bname:
            self.bname = self.name.encode('cp932').decode('shift_jis').encode('shift_jis')[:15].ljust(15, b'\x00')   # 15文字制限
        fout.write(self.bname)
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
        if not self.bname:
            self.bname = self.name.encode('cp932').decode('shift_jis').encode('shift_jis')[:15].ljust(15, b'\x00')   # 15文字制限
        fout.write(self.bname)
        fout.write(struct.pack('<L', int(self.fno)))
        fout.write(struct.pack('<f', float(self.ratio)))

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
    def calc_bf(self, bone_name: str, fno: int, is_key=False, is_read=False):
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
            if is_key or is_read:
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
        fill_bf.rotation = self.calc_bf_rot(prev_bf, fill_bf, after_bf)
        fill_bf.position = self.calc_bf_pos(prev_bf, fill_bf, after_bf)
        
        return fill_bf

    # 補間曲線を元に、回転ボーンの値を求める
    def calc_bf_rot(self, prev_bf: VmdBoneFrame, fill_bf: VmdBoneFrame, after_bf: VmdBoneFrame):
        if prev_bf.rotation != after_bf.rotation:
            # 回転補間曲線
            rx, ry, rt = MBezierUtils.evaluate(after_bf.interpolation[MBezierUtils.R_x1_idxs[3]], after_bf.interpolation[MBezierUtils.R_y1_idxs[3]], \
                                               after_bf.interpolation[MBezierUtils.R_x2_idxs[3]], after_bf.interpolation[MBezierUtils.R_y2_idxs[3]], \
                                               prev_bf.fno, fill_bf.fno, after_bf.fno)
            return MQuaternion.slerp(prev_bf.rotation, after_bf.rotation, ry)

        return copy.deepcopy(prev_bf.rotation)

    # 補間曲線を元に移動ボーンの値を求める
    def calc_bf_pos(self, prev_bf: VmdBoneFrame, fill_bf: VmdBoneFrame, after_bf: VmdBoneFrame):

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
    
    def reset_interpolation_all(self, bone_name: str, prev_bf: VmdBoneFrame, now_bf: VmdBoneFrame, next_bf: VmdBoneFrame):
        self.reset_interpolation_by_rot(bone_name, prev_bf, now_bf, next_bf)
        self.reset_interpolation_by_move_x(bone_name, prev_bf, now_bf, next_bf)
        self.reset_interpolation_by_move_y(bone_name, prev_bf, now_bf, next_bf)
        self.reset_interpolation_by_move_z(bone_name, prev_bf, now_bf, next_bf)

    # 回転による補間曲線の再設定
    def reset_interpolation_by_rot(self, bone_name: str, prev_bf: VmdBoneFrame, now_bf: VmdBoneFrame, next_bf: VmdBoneFrame):
        x1_idxs = MBezierUtils.R_x1_idxs
        y1_idxs = MBezierUtils.R_y1_idxs
        x2_idxs = MBezierUtils.R_x2_idxs
        y2_idxs = MBezierUtils.R_y2_idxs
        next_x1v = next_bf.interpolation[x1_idxs[3]]
        next_y1v = next_bf.interpolation[y1_idxs[3]]
        next_x2v = next_bf.interpolation[x2_idxs[3]]
        next_y2v = next_bf.interpolation[y2_idxs[3]]

        self.reset_interpolation(bone_name, prev_bf, now_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)

    # X移動による補間曲線の再設定
    def reset_interpolation_by_move_x(self, bone_name: str, prev_bf: VmdBoneFrame, now_bf: VmdBoneFrame, next_bf: VmdBoneFrame):
        x1_idxs = MBezierUtils.MX_x1_idxs
        y1_idxs = MBezierUtils.MX_y1_idxs
        x2_idxs = MBezierUtils.MX_x2_idxs
        y2_idxs = MBezierUtils.MX_y2_idxs
        next_x1v = next_bf.interpolation[x1_idxs[3]]
        next_y1v = next_bf.interpolation[y1_idxs[3]]
        next_x2v = next_bf.interpolation[x2_idxs[3]]
        next_y2v = next_bf.interpolation[y2_idxs[3]]

        self.reset_interpolation(bone_name, prev_bf, now_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)

    # Y移動による補間曲線の再設定
    def reset_interpolation_by_move_y(self, bone_name: str, prev_bf: VmdBoneFrame, now_bf: VmdBoneFrame, next_bf: VmdBoneFrame):
        x1_idxs = MBezierUtils.MY_x1_idxs
        y1_idxs = MBezierUtils.MY_y1_idxs
        x2_idxs = MBezierUtils.MY_x2_idxs
        y2_idxs = MBezierUtils.MY_y2_idxs
        next_x1v = next_bf.interpolation[x1_idxs[3]]
        next_y1v = next_bf.interpolation[y1_idxs[3]]
        next_x2v = next_bf.interpolation[x2_idxs[3]]
        next_y2v = next_bf.interpolation[y2_idxs[3]]

        self.reset_interpolation(bone_name, prev_bf, now_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)

    # Z移動による補間曲線の再設定
    def reset_interpolation_by_move_z(self, bone_name: str, prev_bf: VmdBoneFrame, now_bf: VmdBoneFrame, next_bf: VmdBoneFrame):
        x1_idxs = MBezierUtils.MZ_x1_idxs
        y1_idxs = MBezierUtils.MZ_y1_idxs
        x2_idxs = MBezierUtils.MZ_x2_idxs
        y2_idxs = MBezierUtils.MZ_y2_idxs
        next_x1v = next_bf.interpolation[x1_idxs[3]]
        next_y1v = next_bf.interpolation[y1_idxs[3]]
        next_x2v = next_bf.interpolation[x2_idxs[3]]
        next_y2v = next_bf.interpolation[y2_idxs[3]]

        self.reset_interpolation(bone_name, prev_bf, now_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)

    # 補間曲線の再設定
    def reset_interpolation(self, bone_name, prev_bf, now_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs):
        # 区切りキー位置
        before_fill_bf = after_fill_bf = None
        
        # ベジェ曲線を分割して新しい制御点を求める
        x, y, t, bresult, aresult, before_bz, after_bz = MBezierUtils.split_bezier_mmd(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.fno, now_bf.fno, next_bf.fno)

        # 分割（今回キー）の始点は、前半のB
        now_bf.interpolation[x1_idxs[0]] = now_bf.interpolation[x1_idxs[1]] = now_bf.interpolation[x1_idxs[2]] = now_bf.interpolation[x1_idxs[3]] = before_bz[1].x()
        now_bf.interpolation[y1_idxs[0]] = now_bf.interpolation[y1_idxs[1]] = now_bf.interpolation[y1_idxs[2]] = now_bf.interpolation[y1_idxs[3]] = before_bz[1].y()

        # 分割（今回キー）の終点は、後半のC
        now_bf.interpolation[x2_idxs[0]] = now_bf.interpolation[x2_idxs[1]] = now_bf.interpolation[x2_idxs[2]] = now_bf.interpolation[x2_idxs[3]] = before_bz[2].x()
        now_bf.interpolation[y2_idxs[0]] = now_bf.interpolation[y2_idxs[1]] = now_bf.interpolation[y2_idxs[2]] = now_bf.interpolation[y2_idxs[3]] = before_bz[2].y()

        # 次回読み込みキーの始点は、後半のB
        next_bf.interpolation[x1_idxs[0]] = next_bf.interpolation[x1_idxs[1]] = next_bf.interpolation[x1_idxs[2]] = next_bf.interpolation[x1_idxs[3]] = after_bz[1].x()
        next_bf.interpolation[y1_idxs[0]] = next_bf.interpolation[y1_idxs[1]] = next_bf.interpolation[y1_idxs[2]] = next_bf.interpolation[y1_idxs[3]] = after_bz[1].y()

        # 次回読み込みキーの終点は、後半のC
        next_bf.interpolation[x2_idxs[0]] = next_bf.interpolation[x2_idxs[1]] = next_bf.interpolation[x2_idxs[2]] = next_bf.interpolation[x2_idxs[3]] = after_bz[2].x()
        next_bf.interpolation[y2_idxs[0]] = next_bf.interpolation[y2_idxs[1]] = next_bf.interpolation[y2_idxs[2]] = next_bf.interpolation[y2_idxs[3]] = after_bz[2].y()

        if bresult and aresult:
            # nowとnextをモーションに再設定

            self.bones[now_bf.name][prev_bf.fno] = prev_bf
            prev_bf.key = True
            self.bones[now_bf.name][now_bf.fno] = now_bf
            now_bf.key = True
            self.bones[next_bf.name][next_bf.fno] = next_bf
            next_bf.key = True

            return
        else:
            # 分割に失敗している場合、さらに分割する

            if not bresult:
                # 前半用補間曲線
                next_x1v = now_bf.interpolation[x1_idxs[3]]
                next_y1v = now_bf.interpolation[y1_idxs[3]]
                next_x2v = now_bf.interpolation[x2_idxs[3]]
                next_y2v = now_bf.interpolation[y2_idxs[3]]

                # 前半を区切る位置を求める(t=0.5で曲線を半分に分割する位置)
                new_fill_fno, _ = MBezierUtils.evaluate_by_t(next_x1v, next_y1v, next_x2v, next_y2v, prev_bf.fno, now_bf.fno, 0.5)
                # logger.test("%s, 【前半】, now: %s", indent, now)

                if new_fill_fno > prev_bf.fno:
                    # ちゃんとキーが打てるような状態の場合、前半を再分割
                    before_fill_bf = self.calc_bf(bone_name, new_fill_fno)

                if before_fill_bf:
                    # 分割キーが取得できた場合、前半の補間曲線を分割して求めなおす
                    self.reset_interpolation(bone_name, prev_bf, before_fill_bf, now_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)
                else:
                    # 分割キーが取得できなかった場合、念のため補間曲線を0-127の間に収め直す
                    # 分割（今回キー）の始点は、前半のB
                    r_x1 = 0 if 0 > before_bz[1].x() else MBezierUtils.INTERPOLATION_MMD_MAX if MBezierUtils.INTERPOLATION_MMD_MAX < before_bz[1].x() else int(before_bz[1].x())
                    now_bf.interpolation[x1_idxs[0]] = now_bf.interpolation[x1_idxs[1]] = now_bf.interpolation[x1_idxs[2]] = now_bf.interpolation[x1_idxs[3]] = r_x1
                    r_y1 = 0 if 0 > before_bz[1].y() else MBezierUtils.INTERPOLATION_MMD_MAX if MBezierUtils.INTERPOLATION_MMD_MAX < before_bz[1].y() else int(before_bz[1].y())
                    now_bf.interpolation[y1_idxs[0]] = now_bf.interpolation[y1_idxs[1]] = now_bf.interpolation[y1_idxs[2]] = now_bf.interpolation[y1_idxs[3]] = r_y1

                    # 分割（今回キー）の終点は、後半のC
                    r_x2 = 0 if 0 > before_bz[2].x() else MBezierUtils.INTERPOLATION_MMD_MAX if MBezierUtils.INTERPOLATION_MMD_MAX < before_bz[2].x() else int(before_bz[2].x())
                    now_bf.interpolation[x2_idxs[0]] = now_bf.interpolation[x2_idxs[1]] = now_bf.interpolation[x2_idxs[2]] = now_bf.interpolation[x2_idxs[3]] = r_x2
                    r_y2 = 0 if 0 > before_bz[2].y() else MBezierUtils.INTERPOLATION_MMD_MAX if MBezierUtils.INTERPOLATION_MMD_MAX < before_bz[2].y() else int(before_bz[2].y())
                    now_bf.interpolation[y2_idxs[0]] = now_bf.interpolation[y2_idxs[1]] = now_bf.interpolation[y2_idxs[2]] = now_bf.interpolation[y2_idxs[3]] = r_y2

                    self.bones[now_bf.name][now_bf.fno] = now_bf
                    now_bf.key = True

            if not aresult:
                # 後半用補間曲線
                next_x1v = next_bf.interpolation[x1_idxs[3]]
                next_y1v = next_bf.interpolation[y1_idxs[3]]
                next_x2v = next_bf.interpolation[x2_idxs[3]]
                next_y2v = next_bf.interpolation[y2_idxs[3]]

                # 後半を区切る位置を求める
                new_fill_fno, _ = MBezierUtils.evaluate_by_t(next_x1v, next_y1v, next_x2v, next_y2v, now_bf.fno, next_bf.fno, 0.5)
                # logger.test("%s, 【後半】, now: %s", indent, now)

                if new_fill_fno > now_bf.fno:
                    # ちゃんとキーが打てるような状態の場合、後半を再分割
                    after_fill_bf = self.calc_bf(bone_name, new_fill_fno)

                if after_fill_bf:
                    # 分割キーが取得できた場合、後半の補間曲線を分割して求めなおす
                    self.reset_interpolation(bone_name, now_bf, after_fill_bf, next_bf, next_x1v, next_y1v, next_x2v, next_y2v, x1_idxs, y1_idxs, x2_idxs, y2_idxs)
                else:
                    # 分割キーが取得できなかった場合、念のため補間曲線を0-127の間に収め直す

                    # 次回読み込みキーの始点は、後半のB
                    r_x1 = 0 if 0 > after_bz[1].x() else MBezierUtils.INTERPOLATION_MMD_MAX if MBezierUtils.INTERPOLATION_MMD_MAX < after_bz[1].x() else int(after_bz[1].x())
                    next_bf.interpolation[x1_idxs[0]] = next_bf.interpolation[x1_idxs[1]] = next_bf.interpolation[x1_idxs[2]] = next_bf.interpolation[x1_idxs[3]] = r_x1
                    r_y1 = 0 if 0 > after_bz[1].y() else MBezierUtils.INTERPOLATION_MMD_MAX if MBezierUtils.INTERPOLATION_MMD_MAX < after_bz[1].y() else int(after_bz[1].y())
                    next_bf.interpolation[y1_idxs[0]] = next_bf.interpolation[y1_idxs[1]] = next_bf.interpolation[y1_idxs[2]] = next_bf.interpolation[y1_idxs[3]] = r_y1

                    # 次回読み込みキーの終点は、後半のC
                    r_x2 = 0 if 0 > after_bz[2].x() else MBezierUtils.INTERPOLATION_MMD_MAX if MBezierUtils.INTERPOLATION_MMD_MAX < after_bz[2].x() else int(after_bz[2].x())
                    next_bf.interpolation[x2_idxs[0]] = next_bf.interpolation[x2_idxs[1]] = next_bf.interpolation[x2_idxs[2]] = next_bf.interpolation[x2_idxs[3]] = r_x2
                    r_y2 = 0 if 0 > after_bz[2].y() else MBezierUtils.INTERPOLATION_MMD_MAX if MBezierUtils.INTERPOLATION_MMD_MAX < after_bz[2].y() else int(after_bz[2].y())
                    next_bf.interpolation[y2_idxs[0]] = next_bf.interpolation[y2_idxs[1]] = next_bf.interpolation[y2_idxs[2]] = next_bf.interpolation[y2_idxs[3]] = r_y2

                    self.bones[next_bf.name][next_bf.fno] = next_bf
                    next_bf.key = True

            return
        return

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
            fnos = self.get_bone_fnos(bone_name)
            
            if len(fnos) > 0:
                # 各ボーンの最終キーだけ先に登録
                total_bone_frames.append(bone_frames[fnos[-1]])
        
        for bone_name, bone_frames in self.bones.items():
            fnos = self.get_bone_fnos(bone_name)

            if len(fnos) > 1:
                # キーフレを最後の一つ手前まで登録
                for fno in fnos[:-1]:
                    total_bone_frames.append(bone_frames[fno])
        
        return total_bone_frames
    
    # モーフモーション：一次元配列
    def get_morph_frames(self):
        total_morph_frames = []

        for morph_name, morph_frames in self.morphs.items():
            fnos = self.get_morph_fnos(morph_name)
            
            if len(fnos) > 0:
                # 各モーフの最終キーだけ先に登録
                total_morph_frames.append(morph_frames[fnos[-1]])
        
        for morph_name, morph_frames in self.morphs.items():
            fnos = self.get_morph_fnos(morph_name)

            if len(fnos) > 1:
                # キーフレを最後の一つ手前まで登録
                for fno in fnos[:-1]:
                    total_morph_frames.append(morph_frames[fno])
        
        return total_morph_frames

    # ボーンキーフレを追加
    def append_bone_frame(self, frame: VmdBoneFrame):
        if frame.name not in self.bones:
            # まだ該当ボーン名がない場合、追加
            self.bones[frame.name] = {}
        
        self.bones[frame.name][frame.fno] = frame

    # モーフキーフレを追加
    def append_morph_frame(self, frame: VmdMorphFrame):
        if frame.name not in self.morphs:
            # まだ該当モーフ名がない場合、追加
            self.morphs[frame.name] = {}
        
        self.morphs[frame.name][frame.fno] = frame



