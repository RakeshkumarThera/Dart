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
# DESCRIPTION: DartParameterException Class inherit Python Exception for
#              Providing a customized exception type for Dart web service

class DartParameterException(Exception):

    def __init__(self, msg):
        self.msg = msg
