# -*- coding: utf-8 -*-
#
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


def on_select_all(event, target_ctrl):
    keyInput = event.GetKeyCode()
    if keyInput == 1:  # 1 stands for 'ctrl+a'
        target_ctrl.SelectAll()
    event.Skip()
