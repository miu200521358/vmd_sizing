import wx
import threading
import time
import datetime
from functools import wraps

class SimpleThread(threading.Thread):
    """呼び出し可能オブジェクト（関数など）を実行するだけのスレッド"""
    def __init__(self, acallable):
        self.acallable = acallable
        self._result = None
        super(SimpleThread, self).__init__()
    
    def run(self):
        self._result = self.acallable()
    
    def result(self):
        return self._result

def task_takes_time(acallable):
    """
    関数デコレータ
    acallable本来の処理は別スレッドで実行しながら、
    ウィンドウを更新するwx.YieldIfNeededを呼び出し続けるようにする
    """
    @wraps(acallable)
    def f():
        t = SimpleThread(acallable)
        t.start()
        while t.is_alive():
            wx.YieldIfNeeded()
            time.sleep(0.01)
        return t.result()
    return f

class Frame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(380, 200))

        sizer_1 = wx.BoxSizer(wx.HORIZONTAL)
        self.csv_btn_ctrl = wx.Button(self, wx.ID_ANY, u"CSV変換実行", wx.DefaultPosition, wx.Size(200, 50), 0)
        self.csv_btn_ctrl.SetToolTip(u"VMDをCSVに変換します。")
        self.csv_btn_ctrl.Bind(wx.EVT_BUTTON, self.OnButton)
        sizer_1.Add(self.csv_btn_ctrl, 0, wx.ALL, 5)

        self.SetSizer(sizer_1)
        sizer_1.Fit(self)
        self.Layout()

        self.Centre()
        self.Show(True)

    def OnButton(self, event):
        @task_takes_time
        def doit():
            #何か時間がかかる処理をする
            print(datetime.datetime.now())
            time.sleep(1)
            return "spam"
        print(doit())
        print(datetime.datetime.now())


app = wx.App()
#デバッグするときはwx.PySimpleApp()を使う
#app = wx.PySimpleApp()
Frame(None, wx.ID_ANY, 'wxthr.py')
app.MainLoop()
