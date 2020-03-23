# -*- coding: utf-8 -*-
#

import wx


class BasePanel(wx.Panel):

    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        self.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DLIGHT))

        self.frame = frame
        self.parent = parent
        self.tab_idx = tab_idx
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.is_fix_tab = False
    
    def fit(self):
        self.SetSizer(self.sizer)
        self.Layout()
        self.sizer.Fit(self.parent)

    def get_tab_idx(self):
        return self.tab_idx
    
    def disable(self):
        pass

    def fix_tab(self):
        self.is_fix_tab = True

    def release_tab(self):
        self.is_fix_tab = False

        