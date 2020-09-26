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




