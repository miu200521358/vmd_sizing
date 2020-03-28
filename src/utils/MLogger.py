# -*- coding: utf-8 -*-
#
import logging
import traceback
from datetime import datetime
import os


class MLogger():

    DECORATION_IN_BOX = "in_box"
    DECORATION_BOX = "box"
    DECORATION_LINE = "line"
    
    is_file = False
    outout_datetime = ""

    def __init__(self, module_name, level=logging.INFO):
        self.module_name = module_name
        self.default_level = level
        self.logger = logging.getLogger("VmdSizing").getChild(module_name)

    def test(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}

        kwargs["level"] = 1
        self.print_logger(msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["level"] = logging.DEBUG
        self.print_logger(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["level"] = logging.INFO
        self.print_logger(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["level"] = logging.WARNING
        self.print_logger(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["level"] = logging.ERROR
        self.print_logger(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["level"] = logging.CRITICAL
        self.print_logger(msg, *args, **kwargs)

    # 実際に出力する実態
    def print_logger(self, msg, *args, **kwargs):
        target_level = kwargs.pop("level", logging.INFO)
        if self.logger.isEnabledFor(target_level) and self.default_level <= target_level:

            if self.is_file:
                for f in self.logger.handlers:
                    # 既存のハンドラはすべて削除
                    self.logger.removeHandler(f)
                
                # ログディレクトリ作成
                os.makedirs("log", exist_ok=True)

                # ファイル出力ありの場合、ハンドラ紐付け
                handler = logging.FileHandler("log/VmdSizing_{0}.log".format(self.outout_datetime))
                self.logger.addHandler(handler)
                    
            if args and isinstance(args[0], Exception):
                log_msg = logging.LogRecord('name', target_level, "(unknown file)", 0, "{0}\n\n{1}".format(msg, traceback.format_exc()), None, exc_info=None, func=None).getMessage()
            else:
                log_msg = logging.LogRecord('name', target_level, "(unknown file)", 0, msg, args, exc_info=None, func=None).getMessage()

            extra_args = {}
            extra_args["module_name"] = self.module_name

            self.logger._log(target_level, log_msg, None, extra=extra_args)
    
            target_decoration = kwargs.pop("decoration", None)
            title = kwargs.pop("title", None)

            if not self.is_file:
                if target_decoration:
                    if target_decoration == MLogger.DECORATION_BOX:
                        print(self.create_box_message(log_msg, target_level, title))
                    elif target_decoration == MLogger.DECORATION_LINE:
                        print(self.create_line_message(log_msg, target_level, title))
                    elif target_decoration == MLogger.DECORATION_IN_BOX:
                        print(self.create_in_box_message(log_msg, target_level, title))
                    else:
                        print(self.create_simple_message(log_msg, target_level, title))
                else:
                    print(self.create_simple_message(log_msg, target_level, title))

    def create_box_message(self, msg, level, title=None):
        msg_block = []
        msg_block.append("■■■■■■■■■■■■■■■■■")

        if level == logging.CRITICAL:
            msg_block.append("■　**CRITICAL**　")

        if level == logging.ERROR:
            msg_block.append("■　**ERROR**　")

        if level == logging.WARNING:
            msg_block.append("■　**WARNING**　")

        if level <= logging.INFO and title:
            msg_block.append("■　**{0}**　".format(title))

        for msg_line in msg.split("\n"):
            msg_block.append("■　{0}".format(msg_line))

        msg_block.append("■■■■■■■■■■■■■■■■■")

        return "\n".join(msg_block)

    def create_line_message(self, msg, level, title=None):
        msg_block = []

        for msg_line in msg.split("\n"):
            msg_block.append("■■ {0} --------------------".format(msg_line))

        return "\n".join(msg_block)

    def create_in_box_message(self, msg, level, title=None):
        msg_block = []

        for msg_line in msg.split("\n"):
            msg_block.append("■　{0}".format(msg_line))

        return "\n".join(msg_block)

    def create_simple_message(self, msg, level, title=None):
        msg_block = []
        
        for msg_line in msg.split("\n"):
            # msg_block.append("[{0}] {1}".format(logging.getLevelName(level)[0], msg_line))
            msg_block.append(msg_line)
        
        return "\n".join(msg_block)

    @classmethod
    def initialize(cls, level=logging.INFO, is_file=False):
        # logging.basicConfig(level=level)
        logging.basicConfig(level=level, format="%(message)s [%(module_name)s]")
        cls.is_file = is_file
        cls.outout_datetime = "{0:%Y%m%d_%H%M%S}".format(datetime.now())
