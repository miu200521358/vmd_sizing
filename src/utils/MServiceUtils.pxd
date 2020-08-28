import math
import numpy as np
cimport numpy as np
cimport libc.math as cmath
from libcpp cimport  list, str

from mmd.PmxData cimport PmxModel, Bone
from mmd.VmdData cimport VmdMotion, VmdBoneFrame
from module.MParams cimport BoneLinks # noqa
from module.MMath cimport MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa

from mmd.PmxData import Vertex, Material, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MOptions import MOptionsDataSet # noqa
from utils import MBezierUtils # noqa
from utils.MLogger import MLogger # noqa

cdef c_calc_IK(PmxModel model, BoneLinks links, VmdMotion motion, int fno, MVector3D target_pos, BoneLinks ik_links, int max_count)

cdef tuple c_separate_local_qq(int fno, str bone_name, MQuaternion qq, MVector3D global_x_axis)

cdef tuple c_calc_global_pos(PmxModel model, BoneLinks links, VmdMotion motion, int fno, BoneLinks limit_links, bint return_matrix, bint is_local_x)

cpdef dict calc_global_pos_by_direction(MQuaternion direction_qq, dict target_pos_3ds_dic)

cdef list c_calc_relative_position(PmxModel model, BoneLinks links, VmdMotion motion, int fno, BoneLinks limit_links)

cdef list c_calc_relative_rotation(PmxModel model, BoneLinks links, VmdMotion motion, int fno, BoneLinks limit_links)

cpdef MQuaternion deform_rotation(PmxModel model, VmdMotion motion, VmdBoneFrame bf)

cdef MQuaternion c_calc_direction_qq(PmxModel model, BoneLinks links, VmdMotion motion, int fno, BoneLinks limit_links)



