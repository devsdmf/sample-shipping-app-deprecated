# -*- coding: utf-8 -*-
import logging
import sys

""" Logger Wrapper """
class Logger(object):

    _logger = None

    def __init__(self, name = None, level = None):
        name = 'default' if name is None else name

        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.INFO if level is None else level)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)

        self._logger.addHandler(handler)

    def debug(self, message):
        self._logger.debug(message)

    def info(self, message):
        self._logger.info(message)

    def warn(self, message):
        self._logger.warning(message)

    def error(self, message):
        self._logger.error(message)

    def critic(self, message):
        self._logger.critical(message)

