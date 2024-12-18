#
# Unpublished work.
# Copyright (c) 2011-2012 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: alen.cheng@teradata.com
# Secondary Owner:
#
# DESCRIPTION: DartWebLogger Class wrap the python logging for Dart Web
#              Service

import logging
import logging.handlers
import time


class DartWebLogger:

    level = {
        "CRITICAL": logging.CRITICAL, "critical": logging.CRITICAL,
        "ERROR": logging.ERROR, "error": logging.ERROR,
        "WARNING": logging.WARNING, "warning": logging.WARNING,
        "INFO":logging.INFO, "info":logging.INFO,
        "DEBUG": logging.DEBUG, "debug": logging.DEBUG,
        "NOTSET": logging.NOTSET, "notest": logging.NOTSET,
    }

    @classmethod
    def getLogger(cls, moduleName):
        logger = logging.getLogger(moduleName)

        return logger


    @classmethod
    def setLogger(cls, logFileName, logLevel, moduleName):
        logger = logging.getLogger(moduleName)
        formatter = logging.Formatter('%(asctime)s : %(message)s')
        logger.setLevel(cls.level[logLevel])

        rotatingFileHandler = logging.handlers.RotatingFileHandler(logFileName, maxBytes= 10 * 1024 * 1024, backupCount=5)
        rotatingFileHandler.setFormatter(formatter)
        logger.addHandler(rotatingFileHandler)
