# -*- coding: utf-8 -*-
#

import time
import os
import copy
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


class MoveService():
    @classmethod
    def execute(cls, options, org_motion_frames):
        cls.options = options

        logger.test("MoveService")


