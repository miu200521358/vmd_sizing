# -*- coding: utf-8 -*-
#
from collections import OrderedDict
cimport cython


cdef class BoneLinks:
    cdef dict __links

