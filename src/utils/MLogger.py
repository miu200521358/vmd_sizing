# -*- coding: utf-8 -*-
#
import logging
import traceback


class MLogger():

    DECORATION_BOX = "box"
    DECORATION_LINE = "line"
    DECORATION_SIMPLE = "simple"

    def __init__(self, module_name, level=0):
        self.module_name = module_name
        self.level = level
        self.logger = logging.getLogger("VmdSizing").getChild(module_name)
    
    def test(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}

        kwargs["logger"] = 0
        kwargs["level"] = logging.DEBUG
        kwargs["module_name"] = self.module_name
        self.print_logger(msg, *args, **kwargs)
    
    def debug(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["logger"] = self.logger.debug
        kwargs["level"] = logging.DEBUG
        kwargs["module_name"] = self.module_name
        self.print_logger(msg, *args, **kwargs)
    
    def info(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["logger"] = self.logger.info
        kwargs["level"] = logging.INFO
        kwargs["module_name"] = self.module_name
        self.print_logger(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["logger"] = self.logger.warning
        kwargs["level"] = logging.WARNING
        kwargs["module_name"] = self.module_name
        self.print_logger(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["logger"] = self.logger.error
        kwargs["level"] = logging.ERROR
        kwargs["module_name"] = self.module_name
        self.print_logger(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        if not kwargs:
            kwargs = {}
            
        kwargs["logger"] = self.logger.critical
        kwargs["level"] = logging.CRITICAL
        kwargs["module_name"] = self.module_name
        self.print_logger(msg, *args, **kwargs)

    # 実際に出力する実態
    def print_logger(self, msg, *args, **kwargs):
        target_logger = kwargs.pop("logger", None)
        if not target_logger:
            target_logger = self.logger.debug

        target_level = kwargs.pop("level", 0)
        if self.level <= target_level:
            extra_args = {}
            extra_args["module_name"] = self.module_name

            if args and isinstance(args, Exception):
                target_logger("{0}\n\n{1}".format(msg, traceback.format_exc()), *args, extra=extra_args)
            else:
                target_logger(msg, *args, extra=extra_args)
    
            target_decoration = kwargs.pop("decoration", None)
            title = kwargs.pop("title", None)

            if target_decoration:
                log_msg = logging.LogRecord('name', target_level, "(unknown file)", 0, msg, args, exc_info=None, func=None).getMessage()
                if target_decoration == MLogger.DECORATION_BOX:
                    print(self.create_box_message(log_msg, target_level, title))

                if target_decoration == MLogger.DECORATION_LINE:
                    print(self.create_line_message(log_msg, target_level, title))

                if target_decoration == MLogger.DECORATION_SIMPLE:
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

    def create_simple_message(self, msg, level, title=None):
        msg_block = []
        
        for msg_line in msg.split("\n"):
            # msg_block.append("[{0}] {1}".format(logging.getLevelName(level)[0], msg_line))
            msg_block.append(msg_line)
        
        return "\n".join(msg_block)

    @classmethod
    def initialize(cls, level=logging.INFO):
        # logging.basicConfig(level=level)
        logging.basicConfig(level=level, format="%(message)s [%(module_name)s]")

