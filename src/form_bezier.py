# -*- coding: utf-8 -*-

import wx
import wx.xrc
import logging
import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VmdSizing").getChild(__name__)

def pt(p, q, t):
    assert 0 <= t <= 1
    return [a + (b - a) * float(t) for a,b in zip(p, q)]
def mid(p, q):
    return pt(p, q, .5)

class Bezier:
    def __init__(self, ctrls, dt=3*1e-3):
        self.ctrls = ctrls
        self.dt = dt
    def __iter__(self):
        ctrl = self.ctrls
        dt = self.dt
        
        t = 0
        while t <= 1:
            x,y = self.walkdown(ctrl, t)
            yield x,y
            t += dt
    def walkdown(self, ctrl, t):
        dt = self.dt
        if len(ctrl) == 1:
            return ctrl[0]
        else:
            ps = [pt(p, q, t) for p,q in zip(ctrl, ctrl[1:])]
            return self.walkdown(ps, t)

class Mapper(object):
    # coordinate mapper: bounds -> client
    def __init__(self, size, lowerleft, upperright):
        self.size = size 
        self.ll = lowerleft
        self.ur = upperright

    def toClient(self, x, y):
        w, h = self.size
        xs,ys = map(float, self.ll)
        xe,ye = map(float, self.ur)
        
        xx,yy = x - xs, y - ys
        xp,yp = (xe - xs) / w, (ye - ys) / h
        xn,yn = xx / xp, h - yy / yp
        #print x,y,'=>',xn,yn
        return int(xn), int(yn)

class BezierPoint():
 
    """マウスドラッグで移動できるオブジェクト用のクラス"""
 
    def __init__(self, x, y, target_ctrl_x, target_ctrl_y):
        """コンストラクタ"""
        self.size = 2
        self.pos = wx.Point(x, y)  # 表示位置を記録
        self.diff_pos = wx.Point(0, 0)
        self.target_ctrl_x = target_ctrl_x
        self.target_ctrl_y = target_ctrl_y
 
    def HitTest(self, pnt):
        """与えられた座標とアタリ判定して結果を返す"""
        rect = self.GetRect()  # 矩形領域を取得
        
        # 座標が矩形内に入ってるか調べる
        return rect.x - 5 <= pnt.x < (rect.x + rect.width + 5) and rect.y - 5 <= pnt.y < (rect.y + rect.height + 5)
 
    def GetRect(self):
        """矩形領域を返す"""
        return wx.Rect(self.pos.x, self.pos.y, self.size, self.size)
 
    def SavePosDiff(self, pnt):
        """
        マウス座標と自分の座標の相対値を記録。
        この情報がないと、画像をドラッグした時の表示位置がしっくりこない
        """
        self.diff_pos.x = self.pos.x - pnt.x
        self.diff_pos.y = self.pos.y - pnt.y
 
    def Draw(self, dc, select_enable):
        r = self.GetRect()  # 矩形領域を取得

        if select_enable:
            # 丸を描画
            dc.DrawCircle(r.x, r.y, self.size)
    
    def UpdatePos(self):
        self.target_ctrl_x.SetValue(self.pos.x)
        self.target_ctrl_y.SetValue(127 - self.pos.y)

class BezierPanel(wx.Panel):
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        panel = super(BezierPanel, self)
        panel.__init__(parent, id=id, pos=pos, size=size, style=style, name=name)
        self.objs = []
        self.drag_obj = None
        self.drag_start_pos = (0,0)
        self.iserror = False
    
    def addObj(self, obj):
        self.objs.append(obj)
