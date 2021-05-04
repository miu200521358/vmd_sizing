# -*- coding: utf-8 -*-
#

from module.MMath cimport MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa


cdef class Deform:
    cdef public int index0


cdef class Vertex:
    cdef public int index
    cdef public MVector3D position
    cdef public MVector3D normal
    cdef public list uv
    cdef public list extended_uvs
    cdef public Deform deform
    cdef public float edge_factor


cdef class Ik:
    cdef public int target_index
    cdef public int loop
    cdef public float limit_radian
    cdef public list link


cdef class Bone:
    cdef public str name
    cdef public str english_name
    cdef public MVector3D position
    cdef public int parent_index
    cdef public int layer
    cdef public int flag
    cdef public MVector3D tail_position
    cdef public int tail_index
    cdef public int effect_index
    cdef public float effect_factor
    cdef public MVector3D fixed_axis
    cdef public MVector3D local_x_vector
    cdef public MVector3D local_z_vector
    cdef public int external_key
    cdef public Ik ik
    cdef public int index
    cdef public bint display

    cdef public float len_1d
    cdef public MVector3D len_3d
    cdef public MVector3D local_offset
    cdef public MVector3D global_ik_offset
    
    cdef public MVector3D ik_limit_min
    cdef public MVector3D ik_limit_max
    cdef public float dot_limit
    cdef public float dot_near_limit
    cdef public float dot_far_limit
    cdef public float dot_single_limit
    cdef public float degree_limit

    cdef public int BONEFLAG_TAILPOS_IS_BONE
    cdef public int BONEFLAG_CAN_ROTATE
    cdef public int BONEFLAG_CAN_TRANSLATE
    cdef public int BONEFLAG_IS_VISIBLE
    cdef public int BONEFLAG_CAN_MANIPULATE
    cdef public int BONEFLAG_IS_IK
    cdef public int BONEFLAG_IS_EXTERNAL_ROTATION
    cdef public int BONEFLAG_IS_EXTERNAL_TRANSLATION
    cdef public int BONEFLAG_HAS_FIXED_AXIS
    cdef public int BONEFLAG_HAS_LOCAL_COORDINATE
    cdef public int BONEFLAG_IS_AFTER_PHYSICS_DEFORM
    cdef public int BONEFLAG_IS_EXTERNAL_PARENT_DEFORM


cdef class RigidBody:
    cdef public str name
    cdef public str english_name
    cdef public int bone_index
    cdef public int collision_group
    cdef public int no_collision_group
    cdef public int shape_type
    cdef public MVector3D shape_size
    cdef public MVector3D shape_position
    cdef public MVector3D shape_rotation
    cdef public object param
    cdef public int mode
    cdef public int index
    cdef public str bone_name
    cdef public bint is_arm_upper
    cdef public bint is_small
    cdef public int SHAPE_SPHERE
    cdef public int SHAPE_BOX
    cdef public int SHAPE_CAPSULE


cdef class RigidBodyParam:
    cdef public float mass
    cdef public float linear_damping
    cdef public float angular_damping
    cdef public float restitution
    cdef public float friction


cdef class OBB:
    cdef public int fno
    cdef public MVector3D shape_size
    cdef public MVector3D shape_position
    cdef public MVector3D shape_rotation
    cdef public MQuaternion shape_rotation_qq
    cdef public MVector3D bone_pos
    cdef public int h_sign
    cdef public int v_sign
    cdef public bint is_aliginment
    cdef public bint is_arm_upper
    cdef public bint is_small
    cdef public bint is_arm_left
    cdef public MMatrix4x4 matrix
    cdef public MMatrix4x4 rotated_matrix
    cdef public MVector3D origin
    cdef public dict origin_xyz
    cdef public dict shape_size_xyz

    cpdef tuple get_collistion(self, MVector3D point, MVector3D root_global_pos, float max_length, float base_size)

cdef class PmxModel:
    cdef public str path
    cdef public str name
    cdef public str english_name
    cdef public str comment
    cdef public str english_comment
    cdef public dict vertices
    cdef public list indices
    cdef public list textures
    cdef public dict materials
    cdef public dict material_indexes
    cdef public dict bones
    cdef public dict bone_indexes
    cdef public dict morphs
    cdef public dict morph_indexes
    cdef public dict display_slots
    cdef public dict rigidbodies
    cdef public dict rigidbody_indexes
    cdef public dict joints
    cdef public str digest
    cdef public bint can_upper_sizing
    cdef public bint can_arm_sizing
    cdef public Vertex head_top_vertex
    cdef public Vertex left_sole_vertex
    cdef public Vertex right_sole_vertex
    cdef public Vertex left_toe_vertex
    cdef public Vertex right_toe_vertex
    cdef public Vertex left_ik_sole_vertex
    cdef public Vertex right_ik_sole_vertex
    cdef public Vertex finger_tail_vertex
    cdef public dict wrist_entity_vertex
    cdef public dict elbow_entity_vertex
    cdef public dict elbow_middle_entity_vertex
