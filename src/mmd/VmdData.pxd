# -*- coding: utf-8 -*-
#
from module.MMath cimport MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa

cdef class VmdBoneFrame:
    cdef public str name
    cdef public bytes bname
    cdef public int fno
    cdef public MVector3D position
    cdef public MQuaternion rotation
    cdef public MVector3D org_position
    cdef public MQuaternion org_rotation
    cdef public list interpolation
    cdef public list org_interpolation
    cdef public bint key
    cdef public bint read
    cdef public str avoidance

cdef class VmdMotion:
    cdef public str path
    cdef public str signature
    cdef public str model_name
    cdef public int last_motion_frame
    cdef public int motion_cnt
    cdef public dict bones
    cdef public int morph_cnt
    cdef public dict morphs
    cdef public int camera_cnt
    cdef public dict cameras
    cdef public int light_cnt
    cdef public list lights
    cdef public int shadow_cnt
    cdef public list shadows
    cdef public int ik_cnt
    cdef public list showiks
    cdef public str digest

    cdef c_regist_full_bf(self, int data_set_no, list bone_name_list, int offset)

    cdef list c_get_differ_fnos(self, int data_set_no, list bone_name_list, double limit_degrees, double limit_length)

    cdef c_smooth_bf(self, int data_set_no, str bone_name, bint is_rot, bint is_mov, double limit_degrees, int start_fno, int end_fno, bint is_show_log)

    cdef c_smooth_filter_bf(self, int data_set_no, str bone_name, bint is_rot, bint is_mov, int loop, dict config, int start_fno, int end_fno, bint is_show_log)
    
    cdef c_remove_unnecessary_bf(self, int data_set_no, str bone_name, bint is_rot, bint is_mov, \
                                 double offset, double rot_diff_limit, double mov_diff_limit, int start_fno, int end_fno, bint is_show_log, bint is_force)

    cdef c_regist_bf(self, VmdBoneFrame bf, str bone_name, int fno, bint copy_interpolation)

    cdef VmdBoneFrame c_calc_bf(self, str bone_name, int fno, bint is_key, bint is_read, bint is_reset_interpolation)

    cdef MQuaternion calc_bf_rot(self, VmdBoneFrame prev_bf, VmdBoneFrame fill_bf, VmdBoneFrame next_bf)

    cdef MVector3D calc_bf_pos(self, VmdBoneFrame prev_bf, VmdBoneFrame fill_bf, VmdBoneFrame next_bf)

    cdef bint split_bf_by_fno(self, str target_bone_name, VmdBoneFrame prev_bf, VmdBoneFrame next_bf, int fill_fno)

    cdef bint split_bf(self, str target_bone_name, VmdBoneFrame prev_bf, VmdBoneFrame next_bf)

    cdef int get_split_fill_fno(self, str target_bone_name, VmdBoneFrame prev_bf, VmdBoneFrame next_bf, \
                                 list x1_idxs, list y1_idxs, list x2_idxs, list y2_idxs)

    cdef reset_interpolation(self, str target_bone_name, VmdBoneFrame prev_bf, VmdBoneFrame now_bf, VmdBoneFrame next_bf, \
                              list before_bz, list after_bz, list x1_idxs, list y1_idxs, list x2_idxs, list y2_idxs)

    cdef copy_interpolation(self, VmdBoneFrame org_bf, VmdBoneFrame rep_bf, str bz_type)

    cdef reset_interpolation_parts(self, str target_bone_name, VmdBoneFrame bf, list bzs, list x1_idxs, list y1_idxs, list x2_idxs, list y2_idxs)

    cpdef bint is_active_bones(self, str bone_name)





