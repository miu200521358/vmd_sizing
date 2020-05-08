# -*- coding: utf-8 -*-
#
import wx

from form.panel.BasePanel import BasePanel
from form.parts.FloatSliderCtrl import FloatSliderCtrl
from module.MMath import MRect, MVector3D, MVector4D, MQuaternion, MMatrix4x4 # noqa
from utils import MFormUtils, MBezierUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__, level=1)


class BezierPanel(BasePanel):

    def __init__(self, frame: wx.Frame, parent: wx.Notebook, tab_idx: int):
        super().__init__(frame, parent, tab_idx)

        # 補間曲線の分割フレーム
        self.slice_start = 0
        self.slice_end = 10
        self.slice_middle = 5

        self.description_txt = wx.StaticText(self, wx.ID_ANY, "オリジナル補間曲線に指定された補間曲線を、指定された箇所で分割した場合の補間曲線を表示します。\n" \
                                             + "補間曲線は、数値で指定する他、MMDと同じくマウスで操作できます。\n補間曲線を正常に2分割できない場合、パネルに×が出ます。", \
                                             wx.DefaultPosition, wx.DefaultSize, 0)
        self.sizer.Add(self.description_txt, 0, wx.ALL, 5)

        self.static_line01 = wx.StaticLine(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        self.sizer.Add(self.static_line01, 0, wx.EXPAND | wx.ALL, 5)

        # 基本補間曲線
        self.base_sizer = wx.BoxSizer(wx.VERTICAL)

        self.base_bezier_title = wx.StaticText(self, wx.ID_ANY, u"オリジナル補間曲線", wx.DefaultPosition, wx.DefaultSize, 0)
        self.base_bezier_title.SetToolTip(u"元々の分割したいキーフレの補間曲線を指定します。")
        self.base_sizer.Add(self.base_bezier_title, 0, wx.ALL, 5)

        self.base_bezier = BezierBlock(self.frame, self, self.base_sizer)
        self.sizer.Add(self.base_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # 補間フレームの番号 ---------------
        self.value_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.number_title_txt = wx.StaticText(self, wx.ID_ANY, u"キー分割フレーム：　", wx.DefaultPosition, wx.DefaultSize, 0)
        self.number_title_txt.SetToolTip(u"キーをどの位置で分割するか指定して下さい。")
        self.value_sizer.Add(self.number_title_txt, 0, wx.ALL, 5)

        self.number_value_txt = wx.StaticText(self, wx.ID_ANY, u"（" + str(self.slice_middle) + "）", wx.DefaultPosition, wx.DefaultSize, 0)
        self.number_value_txt.SetToolTip(u"現在指定されているフレームの分割番号です。")
        self.value_sizer.Add(self.number_value_txt, 0, wx.ALL, 5)

        self.sizer.Add(self.value_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # 補間フレーム ----------------
        self.frame_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 補間の開始
        self.frame_start_ctrl = wx.SpinCtrl(self, id=wx.ID_ANY, size=wx.Size(80, -1), value=str(self.slice_start), min=0, max=999999999, initial=1)
        self.frame_start_ctrl.Bind(wx.EVT_SPINCTRL, self.OnReCalcBezier)
        self.frame_sizer.Add(self.frame_start_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        # 補間を区切るフレーム
        self.slice_slider_ctrl = FloatSliderCtrl(self, wx.ID_ANY, self.slice_middle, self.slice_start, self.slice_end, 1, self.number_value_txt, \
                                                 wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL, scrollevt=self.OnRePaintBezier)
        self.frame_sizer.Add(self.slice_slider_ctrl, 1, wx.ALL | wx.EXPAND, 5)

        # 補間の終了
        self.frame_end_ctrl = wx.SpinCtrl(self, id=wx.ID_ANY, size=wx.Size(80, -1), value=str(self.slice_end), min=0, max=999999999, initial=1)
        self.frame_end_ctrl.Bind(wx.EVT_SPINCTRL, self.OnReCalcBezier)
        self.frame_sizer.Add(self.frame_end_ctrl, 0, wx.EXPAND | wx.ALL, 5)

        self.sizer.Add(self.frame_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # 分割フレーム -------------
        self.split_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 開始補間曲線
        self.split_before_sizer = wx.BoxSizer(wx.VERTICAL)

        self.before_bezier_title = wx.StaticText(self, wx.ID_ANY, u"分割キー補間曲線", wx.DefaultPosition, wx.DefaultSize, 0)
        self.before_bezier_title.SetToolTip(u"分割したキーフレの補間曲線を表示します。")
        self.split_before_sizer.Add(self.before_bezier_title, 0, wx.ALL, 5)

        self.before_bezier = BezierBlock(self.frame, self, self.split_before_sizer)
        self.split_sizer.Add(self.split_before_sizer, 0, wx.EXPAND | wx.ALL, 5)

        # 終端補間曲線
        self.split_after_sizer = wx.BoxSizer(wx.VERTICAL)

        self.after_bezier_title = wx.StaticText(self, wx.ID_ANY, u"終端キー補間曲線", wx.DefaultPosition, wx.DefaultSize, 0)
        self.after_bezier_title.SetToolTip(u"終わりのキーフレの補間曲線を表示します。")
        self.split_after_sizer.Add(self.after_bezier_title, 0, wx.ALL, 5)

        self.after_bezier = BezierBlock(self.frame, self, self.split_after_sizer)
        self.split_sizer.Add(self.split_after_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.sizer.Add(self.split_sizer, 0, wx.EXPAND | wx.ALL, 5)

        self.fit()

    # ベジェ曲線の再計算 -----------------
    def OnReCalcBezier(self, event):
        self.slice_slider_ctrl.SetMin(float(self.frame_start_ctrl.GetValue()))
        self.slice_slider_ctrl.SetMax(float(self.frame_end_ctrl.GetValue()))

    def OnRePaintBezier(self, event):
        self.splitBezier()  # ベジェ分割
        self.frame.Refresh(False)

    def splitBezier(self):
        # ベジェ曲線の分割
        t, x, y, bresult, aresult, before_bz, after_bz = \
            MBezierUtils.split_bezier_mmd(self.base_bezier.start_x.GetValue(), self.base_bezier.start_y.GetValue(), \
                                          self.base_bezier.end_x.GetValue(), self.base_bezier.end_y.GetValue(), \
                                          self.frame_start_ctrl.GetValue(), int(self.slice_slider_ctrl.GetValue()), self.frame_end_ctrl.GetValue())

        if bresult:
            # 前半のキー
            self.before_bezier.panel.iserror = False
            self.before_bezier.start_x.SetValue(int(before_bz[1].x()))
            self.before_bezier.start_y.SetValue(int(before_bz[1].y()))
            self.before_bezier.end_x.SetValue(int(before_bz[2].x()))
            self.before_bezier.end_y.SetValue(int(before_bz[2].y()))
        else:
            self.before_bezier.panel.iserror = True

        if aresult:
            # 後半のキー
            self.after_bezier.panel.iserror = False
            self.after_bezier.start_x.SetValue(int(after_bz[1].x()))
            self.after_bezier.start_y.SetValue(int(after_bz[1].y()))
            self.after_bezier.end_x.SetValue(int(after_bz[2].x()))
            self.after_bezier.end_y.SetValue(int(after_bz[2].y()))
        else:
            self.after_bezier.panel.iserror = True


class BezierBlock():
    def __init__(self, frame, parent, parent_sizer):
        super().__init__()

        self.frame = frame
        self.parent = parent
        self.parent_sizer = parent_sizer

        self.panel_sizer = wx.BoxSizer(wx.HORIZONTAL)

        # 補間曲線パネル
        self.panel = BezierViewPanel(self.parent, size=(130, 130))
        self.panel_sizer.Add(self.panel, 0, wx.ALL, 0)

        # 補間曲線値
        self.value_sizer = wx.FlexGridSizer(0, 2, 5, 0)

        # 開始X
        self.start_x_title = wx.StaticText(self.parent, wx.ID_ANY, u"開始X: ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.value_sizer.Add(self.start_x_title, 0, wx.ALL, 5)
        self.start_x = wx.SpinCtrl(self.parent, id=wx.ID_ANY, size=wx.Size(60, -1), value="20", min=0, max=127, initial=20)
        self.start_x.Bind(wx.EVT_SPINCTRL, self.parent.OnRePaintBezier)
        self.value_sizer.Add(self.start_x, 0, wx.ALL, 0)
        # 開始Y
        self.start_y_title = wx.StaticText(self.parent, wx.ID_ANY, u"開始Y: ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.value_sizer.Add(self.start_y_title, 0, wx.ALL, 5)
        self.start_y = wx.SpinCtrl(self.parent, id=wx.ID_ANY, size=wx.Size(60, -1), value="20", min=0, max=127, initial=20)
        self.start_y.Bind(wx.EVT_SPINCTRL, self.parent.OnRePaintBezier)
        self.value_sizer.Add(self.start_y, 0, wx.ALL, 0)
        # 終了X
        self.end_x_title = wx.StaticText(self.parent, wx.ID_ANY, u"終了X: ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.value_sizer.Add(self.end_x_title, 0, wx.ALL, 5)
        self.end_x = wx.SpinCtrl(self.parent, id=wx.ID_ANY, size=wx.Size(60, -1), value="107", min=0, max=127, initial=107)
        self.end_x.Bind(wx.EVT_SPINCTRL, self.parent.OnRePaintBezier)
        self.value_sizer.Add(self.end_x, 0, wx.ALL, 0)
        # 終了Y
        self.end_y_title = wx.StaticText(self.parent, wx.ID_ANY, u"終了Y: ", wx.DefaultPosition, wx.DefaultSize, 0)
        self.value_sizer.Add(self.end_y_title, 0, wx.ALL, 5)
        self.end_y = wx.SpinCtrl(self.parent, id=wx.ID_ANY, size=wx.Size(60, -1), value="107", min=0, max=127, initial=107)
        self.end_y.Bind(wx.EVT_SPINCTRL, self.parent.OnRePaintBezier)
        self.value_sizer.Add(self.end_y, 0, wx.ALL, 0)

        self.panel_sizer.Add(self.value_sizer, 0, wx.ALL, 0)
        self.parent_sizer.Add(self.panel_sizer, 0, wx.ALL, 5)

        # ベジェ曲線描画
        self.panel.Bind(wx.EVT_PAINT, self.OnPaint)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnPaintBezierMouseLeftDown)
        self.panel.Bind(wx.EVT_LEFT_UP, self.OnPaintBezierMouseLeftUp)
        self.panel.Bind(wx.EVT_MOTION, self.OnPaintBezierMouseMotion)
    
    # ベジェ曲線の描画 -------------------------
    def OnPaint(self, event: wx.Event):
        dc = wx.PaintDC(self.panel)
        dc = wx.BufferedDC(dc)  # 画面に表示されないところで描画を行うためのデバイスコンテキストを作成
        m = Mapper(self.panel.GetSize(), (0, 0), (127, 127))
        target_ctrl = [(0, 0), (self.start_x.GetValue(), self.start_y.GetValue()), (self.end_x.GetValue(), self.end_y.GetValue()), (127, 127)]

        self.clearbezier(dc)
        # self.drawgrid(target_ctrl, m, dc)
        self.drawguide(target_ctrl[0], target_ctrl[1], self.start_x, self.start_y, m, dc)
        self.drawguide(target_ctrl[2], target_ctrl[3], self.end_x, self.end_y, m, dc)
        self.drawbezier(target_ctrl, m, dc)
        self.drawbeziererror(m, dc)

    def clearbezier(self, dc):
        self.setColor(dc, 'white')
        dc.DrawRectangle(*(0, 0) + tuple(self.panel.GetSize()))

    def drawbezier(self, target_ctrl, m, dc):
        # draw bezier curve
        self.setColor(dc, 'blue')
        # dc.DrawPointList([m.toClient(x, y) for x, y in Bezier(target_ctrl)])
        lst = list(BezierLine(target_ctrl))
        dc.DrawLineList([m.toClient(*p) + m.toClient(*q) for p, q in zip(lst, lst[1:])])

    def drawguide(self, target_ctrl_start, target_ctrl_end, target_ctrl_x, target_ctrl_y, m, dc):
        #
        self.setColor(dc, 'black')
        line = m.toClient(*target_ctrl_start) + m.toClient(*target_ctrl_end)
        dc.DrawLine(*line)

        # draw control points
        self.setColor(dc, 'red')
        pnt = BezierPoint(*m.toClient(target_ctrl_x.GetValue(), target_ctrl_y.GetValue()) + (target_ctrl_x, target_ctrl_y))
        self.panel.addObj(pnt)
        pnt.Draw(dc, True)

    def drawgrid(self, target_ctrl, m, dc):
        xs, ys = m.ll
        xe, ye = m.ur
        
        self.setColor(dc, 'black')
        dc.DrawLine(*m.toClient(xs, 0) + m.toClient(xe, 0))
        dc.DrawLine(*m.toClient(0, ys) + m.toClient(0, ye))
        
        dc.SetFont(self.panel.GetFont())
        dc.DrawText('%+d' % xs, *m.toClient(xs, 0))
        dc.DrawText('%+d' % ye, *m.toClient(0, ye))

    def drawbeziererror(self, m, dc):
        if self.panel.iserror:
            xs, ys = m.ll
            xe, ye = m.ur

            self.setColor(dc, 'red', 5)
            dc.DrawLine(*m.toClient(0, 0) + m.toClient(xe, ye))
            dc.DrawLine(*m.toClient(0, ye) + m.toClient(xe, 0))

    def setColor(self, dc, color, w=1):
        dc.SetPen(wx.Pen(color, w))
        dc.SetBrush(wx.Brush(color))

    def OnPaintBezierMouseLeftDown(self, event):
        """マウスの左ボタンが押された時の処理"""
        pos = event.GetPosition()  # マウス座標を取得
        obj = self.findBezierPoint(pos)  # マウス座標と重なってるオブジェクトを取得
        if obj is not None:
            self.panel.drag_obj = obj  # ドラッグ移動するオブジェクトを記憶
            self.panel.drag_start_pos = pos  # ドラッグ開始時のマウス座標を記録
            self.panel.drag_obj.SavePosDiff(pos)

    def OnPaintBezierMouseLeftUp(self, event):
        """マウスの左ボタンが離された時の処理"""
        if self.panel.drag_obj is not None:
            pos = event.GetPosition()
            self.panel.drag_obj.pos.x = pos.x + self.panel.drag_obj.diff_pos.x
            self.panel.drag_obj.pos.y = pos.y + self.panel.drag_obj.diff_pos.y
            self.panel.drag_obj.UpdatePos()
            self.parent.splitBezier()  # ベジェ分割

        self.panel.drag_obj = None
        self.frame.Refresh(False)

    def OnPaintBezierMouseMotion(self, event):
        """マウスカーソルが動いた時の処理"""
        if self.panel.drag_obj is None:
            # ドラッグしてるオブジェクトが無いなら処理しない
            return

        # ドラッグしてるオブジェクトの座標値をマウス座標で更新
        pos = event.GetPosition()
        self.panel.drag_obj.pos.x = pos.x + self.panel.drag_obj.diff_pos.x
        self.panel.drag_obj.pos.y = pos.y + self.panel.drag_obj.diff_pos.y
        self.panel.drag_obj.UpdatePos()
        self.parent.splitBezier()          # ベジェ分割
        self.frame.Refresh(False)   # 描画更新

    def findBezierPoint(self, pnt):
        """マウス座標と重なってるオブジェクトを返す"""
        result = None
        for obj in self.panel.objs:
            if obj.HitTest(pnt):
                result = obj
        return result


def pt(p, q, t):
    assert 0 <= t <= 1
    return [a + (b - a) * float(t) for a, b in zip(p, q)]


def mid(p, q):
    return pt(p, q, .5)


class BezierLine:
    def __init__(self, ctrls, dt=3 * 1e-3):
        self.ctrls = ctrls
        self.dt = dt

    def __iter__(self):
        ctrl = self.ctrls
        dt = self.dt
        
        t = 0
        while t <= 1:
            x, y = self.walkdown(ctrl, t)
            yield x, y
            t += dt

    def walkdown(self, ctrl, t):
        dt = self.dt # noqa
        if len(ctrl) == 1:
            return ctrl[0]
        else:
            ps = [pt(p, q, t) for p, q in zip(ctrl, ctrl[1:])]
            return self.walkdown(ps, t)


class Mapper(object):
    # coordinate mapper: bounds -> client
    def __init__(self, size, lowerleft, upperright):
        self.size = size
        self.ll = lowerleft
        self.ur = upperright

    def toClient(self, x, y):
        w, h = self.size
        xs, ys = map(float, self.ll)
        xe, ye = map(float, self.ur)
        
        xx, yy = x - xs, y - ys
        xp, yp = (xe - xs) / w, (ye - ys) / h
        xn, yn = xx / xp, h - yy / yp
        # print x,y,'=>',xn,yn
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


class BezierViewPanel(wx.Panel):
    
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.TAB_TRAVERSAL, name=wx.PanelNameStr):
        panel = super(BezierViewPanel, self)
        panel.__init__(parent, id=id, pos=pos, size=size, style=style, name=name)
        self.objs = []
        self.drag_obj = None
        self.drag_start_pos = (0, 0)
        self.iserror = False
    
    def addObj(self, obj):
        self.objs.append(obj)

