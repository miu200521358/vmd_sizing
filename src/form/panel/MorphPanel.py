# -*- coding: utf-8 -*-
#

import wx
from form.panel.BasePanel import BasePanel
from utils import MFormUtils


class MorphPanel(BasePanel):
    
    def __init__(self, frame, parent, tab_idx):
        super().__init__(frame, parent, tab_idx)

        self.fit()
