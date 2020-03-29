# -*- coding: utf-8 -*-
#
import copy
from collections import OrderedDict
from mmd.VmdData import VmdMotion, VmdBoneFrame


class BoneLinks():
    def __init__(self):
        self.__links = OrderedDict()
    
    def get(self, bone_name: str, offset=0):
        if bone_name not in self.__links:
            return None
        if offset == 0:
            # オフセットなしの場合、そのまま返す
            return self.__links[bone_name]
        else:
            # オフセットありの場合、その分ずらす
            target_bone_index = self.index(bone_name)
            
            # オフセット加味して、該当INDEXを探す
            for lidx, lkey in enumerate(self.__links.keys()):
                if lidx == target_bone_index + offset:
                    return self.__links[lkey]
        
        return VmdBoneFrame()
    
    def all(self):
        return self.__links

    # リンクに追加
    def append(self, bone: VmdBoneFrame):
        self.__links[bone.name] = bone
    
    # リンクの反転
    def reversed(self):
        return reversed(self.__links)
    
    # リンクの大きさ
    def size(self):
        return len(self.__links.keys())
    
    # 指定されたボーン名を削除する
    def delete(self, bone_name: str):
        copy_links = copy.deepcopy(self.__links)
        del copy_links["bone_name"]
    
    # 指定されたボーン名までのインデックス
    def index(self, bone_name: str):
        for lidx, lkey in enumerate(self.__links.keys()):
            if lkey == bone_name:
                return lidx
        return -1

    # 指定されたボーン名までのリンクを取得
    def from_links(self, bone_name: str):
        new_links = BoneLinks()
        for lidx, lkey in enumerate(self.__links.keys()):
            new_links.append(self.__links[lkey])
            if lkey == bone_name:
                break
        return new_links
    
    # 指定されたボーン名までのフレームを取得
    # それ以上は初期値のボーンを追加する
    def take_out_frames(self, motion: VmdMotion, bone_name: str, fno: int):
        new_motion = VmdMotion()
        for lidx, lkey in enumerate(self.__links.keys()):
            if lidx <= self.index(bone_name):
                calc_bone = motion.calc_bf(self.__links[lkey].name, fno)
                new_motion.bones[calc_bone.name] = {fno: calc_bone}
            else:
                calc_bone = VmdBoneFrame(fno=fno, name=lkey)
                new_motion.bones[calc_bone.name] = {fno: calc_bone}
        
        return new_motion

    def __str__(self):
        return "<BoneLinks links:{0}".format(self.__links)



