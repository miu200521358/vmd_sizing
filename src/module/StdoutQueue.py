# -*- coding: utf-8 -*-
#

import sys
import multiprocessing


class StdoutQueue():
    
    queue = None

    # 初期化
    def __init__(self, *args, **kwargs):
        m = multiprocessing.Manager()
        self.queue = m.Queue(*args, **kwargs)

    def get(self, *args, **kwargs):
        try:
            return self.queue.get(*args, **kwargs)
        except Exception as e:
            raise e

    def put(self, obj):
        self.queue.put(obj)

    # printでの出力
    def write(self, msg):
        self.queue.put(msg)

    def flush(self):
        sys.__stdout__.flush()

