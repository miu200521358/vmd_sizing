# -*- coding: utf-8 -*-
#
import unittest

from mmd.PmxReader import PmxReader
from mmd.VmdReader import VmdReader
from mmd.PmxData import PmxModel, Vertex, Material, Bone, Morph, DisplaySlot, RigidBody, Joint # noqa
from mmd.VmdData import VmdMotion, VmdBoneFrame, VmdCameraFrame, VmdInfoIk, VmdLightFrame, VmdMorphFrame, VmdShadowFrame, VmdShowIkFrame # noqa
from module.MMath import MRect, MVector2D, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from module.MOptions import MOptions # noqa
from module.MParams import BoneLinks # noqa
from utils import MBezierUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class TestMServiceUtils(unittest.TestCase):

    def test_calc_global_pos_dic01(self):
        PmxReader()


if __name__ == "__main__":
    unittest.main(exit=False, verbosity=1, defaultTest="TestMServiceUtils.test_calc_global_pos_dic01")

