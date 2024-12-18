#
# Unpublished work.
# Copyright (c) 2011-2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner:
#
# DESCRIPTION: Dlog Class to establish logging in Dart

import logging

'''
Setup Logging
'''
dlog = logging.getLogger('Dart')
dlog.setLevel(logging.DEBUG)
dlog.propagate = False

dlogRunner = logging.getLogger('DartRunner')
dlogRunner.setLevel(logging.DEBUG)
dlogRunner.propagate = False