#!/usr/bin/python
#
# Unpublished work.
# Copyright (c) 2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: divya.sivanandan@teradata.com
# Secondary Owner:
#
# Description: Logging help


import logging
import os
from os.path import dirname, abspath
from time import localtime, strftime

# Logger

CURRENT_TIME_STRING = strftime('%Y%m%d_%H%M%S', localtime())

class LogClass(object):

    @staticmethod
    def get_logger():
        # Set up Logging
        formatstr = '%(asctime)s:[%(levelname)s]:%(filename)s:%(lineno)s:pid%(process)s:%(threadName)s: %(message)s'
        formatter = logging.Formatter(formatstr, '%Y%m%d:%H:%M:%S')

        logdir = os.path.join(abspath(dirname(dirname(__file__))), "log")
        if not os.path.exists(logdir):
            os.mkdir(logdir)

        # Setup info log file
        logfile = '%s/testlink_%s.log' % (logdir, CURRENT_TIME_STRING)
        log_file_handler = logging.FileHandler(logfile, 'w')
        log_file_handler.setFormatter(formatter)

        slog = logging.getLogger('Scheduler')
        slog.addHandler(log_file_handler)
        slog.setLevel(logging.DEBUG)
        slog.propagate = False
        return slog, logfile


logger, logfile  = LogClass.get_logger()
