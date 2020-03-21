# -*- coding: utf-8 -*-
#
import wx
import wx.xrc
from abc import ABCMeta, abstractmethod
from threading import Thread, Event
from utils import MFormUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


# https://wiki.wxpython.org/LongRunningTasks
# https://teratail.com/questions/158458
# http://nobunaga.hatenablog.jp/entry/2016/06/03/204450
class BaseWorkerThread(Thread, metaclass=ABCMeta):

    """Worker Thread Class."""
    def __init__(self, form, result_event):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.form = form
        self._want_abort = 0
        self.event_id = wx.NewId()
        self.stop_event = Event()
        self.result_event = result_event
        self.result = True
        # メイン終了時にもスレッド終了する
        self.daemon = True

    def stop(self):
        self.stop_event.set()

    def run(self):
        # スレッド実行
        self.thread_event()

        # 後処理実行
        self.post_event()
    
    def post_event(self):
        wx.PostEvent(self.form, self.result_event(result=self.result))

    def abort(self):
        self._want_abort = 1
    
    @abstractmethod
    def thread_event(self):
        pass


