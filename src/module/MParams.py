# -*- coding: utf-8 -*-
#
from collections import OrderedDict
from mmd.VmdData import VmdMotion


class BoneLinks():
    def __init__(self):
        self.links = OrderedDict()
    
    # リンクに追加
    def append(self, bone):
        self.links.append(bone)
    
    # リンクの反転
    def reversed(self):
        return reversed(self.links)
    
    # リンクの大きさ
    def size(self):
        return len(self.links.keys())
    
    # 指定されたボーン名までのインデックス
    def index(self, bone_name):
        for lidx, lkey in enumerate(self.links.keys()):
            if lkey == self.links[bone_name]:
                return lidx
        return -1

    # 指定されたボーン名までのリンクを取得
    def from_links(self, bone_name):
        new_links = BoneLinks()
        for lidx, lkey in enumerate(self.links.keys()):
            new_links.append(self.links[lkey])
        return new_links
    
    # 指定されたINDEXまでのフレームを取得
    def take_out_frames(self, motion: VmdMotion, index, fno):
        new_frames = {}
        for lidx, lkey in enumerate(self.links.keys()):
            if lidx <= index:
                lbone = self.links[lkey]
                calc_bone = motion.calc_bone_by_interpolation(lbone.name, fno, is_only=True, is_exist=True, is_key=False, is_read=False)
                new_frames[calc_bone.name] = [calc_bone]
            else:
                calc_bone = VmdMotion.VmdBoneFrame(frame=fno, name=lkey)
                new_frames[calc_bone.name] = [calc_bone]
        return new_frames



