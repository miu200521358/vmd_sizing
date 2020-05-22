# -*- coding: utf-8 -*-
#
import wx
import wx.xrc
from abc import ABCMeta, abstractmethod
from threading import Thread, Event

from module.StdoutQueue import StdoutQueue
from utils import MFormUtils # noqa
from utils.MLogger import MLogger # noqa

logger = MLogger(__name__)


# https://wiki.wxpython.org/LongRunningTasks
# https://teratail.com/questions/158458
# http://nobunaga.hatenablog.jp/entry/2016/06/03/204450
class BaseWorkerThread(Thread, metaclass=ABCMeta):

    """Worker Thread Class."""
    def __init__(self, frame, result_event, console):
        """Init Worker Thread Class."""
        Thread.__init__(self)
        self.frame = frame
        self._want_abort = 0
        self.event_id = wx.NewId()
        self.stop_event = Event()
        self.result_event = result_event
        self.result = True
        # メイン終了時にもスレッド終了する
        self.daemon = True
        # ログ出力用スレッド
        self.queue = StdoutQueue()
        self.monitor = Thread(target=monitering, name="MonitorThread", args=(console, self.queue))
        self.monitor.daemon = True

    def stop(self):
        self.stop_event.set()

    def run(self):
        # モニタリング開始
        self.monitor.start()

        # スレッド実行
        self.thread_event()

        # モニター除去
        self.monitor._delete()

        # 後処理実行
        self.post_event()
    
    def post_event(self):
        self.stop_event.clear()
        self.stop_event.set()

        wx.PostEvent(self.frame, self.result_event(result=self.result))

    def abort(self):
        self._want_abort = 1
    
    @abstractmethod
    def thread_event(self):
        pass


# コンソールに文字列を出力する
def monitering(console, queue):
    while True:
        try:
            console.write(queue.get(timeout=3))
            console.flush()
        except Exception:
            pass

