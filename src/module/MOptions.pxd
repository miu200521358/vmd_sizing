# -*- coding: utf-8 -*-
#
import os
import sys
import argparse

from libcpp cimport  list, str, dict, float, int

from mmd.PmxData cimport PmxModel, Bone
from mmd.VmdData cimport VmdMotion, VmdBoneFrame
from module.MParams cimport BoneLinks # noqa
from module.MMath cimport MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa

from mmd.PmxReader import PmxReader
from mmd.VmdReader import VmdReader
from mmd.VpdReader import VpdReader
from mmd.PmxData import Vertex, Material, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from utils import MFileUtils
from utils.MException import SizingException
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


cdef class MOptions():
    cdef public str version_name
    cdef public int logging_level
    cdef public int max_workers
    cdef public list data_set_list
    cdef public MArmProcessOptions arm_options
    cdef public VmdMotion camera_motion
    cdef public str camera_output_vmd_path
    cdef public object monitor
    cdef public bint is_file
    cdef public str outout_datetime
    cdef public int total_process
    cdef public int now_process
    cdef public object total_process_ctrl
    cdef public object now_process_ctrl
    cdef public dict tree_process_dict

cdef c_parse(str version_name)

cdef class MOptionsDataSet():
    cdef public VmdMotion motion
    cdef public PmxModel org_model
    cdef public PmxModel rep_model
    cdef public str output_vmd_path
    cdef public bint detail_stance_flg
    cdef public bint twist_flg
    cdef public list morph_list
    cdef public PmxModel camera_org_model
    cdef public float camera_offset_y
    cdef public list selected_stance_details

    cdef public VmdMotion org_motion
    cdef public dict test_params
    cdef public bint full_arms

    # 本来の足IKの比率
    cdef public float original_xz_ratio
    cdef public float original_y_ratio

    # 実際に計算に使う足IKの比率
    cdef public float xz_ratio
    cdef public float y_ratio


cdef class MArmProcessOptions():
    cdef public bint avoidance
    cdef public dict avoidance_target_list
    cdef public bint alignment
    cdef public bint alignment_finger_flg
    cdef public bint alignment_floor_flg
    cdef public float alignment_distance_wrist
    cdef public float alignment_distance_finger
    cdef public float alignment_distance_floor
    cdef public bint arm_check_skip_flg


cdef class MSmoothOptions():
    cdef public str version_name
    cdef public int logging_level
    cdef public int max_workers
    cdef public VmdMotion motion
    cdef public PmxModel model
    cdef public str output_path
    cdef public int loop_cnt
    cdef public int interpolation
    cdef public list bone_list
    cdef public object monitor
    cdef public bint is_file
    cdef public str outout_datetime

cdef c_smooth_parse(str version_name)


