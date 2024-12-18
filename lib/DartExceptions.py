#
# Unpublished work.
# Copyright (c) 2011-2012 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: naveen.williams@teradata.com
# Secondary Owner:
#
# DESCRIPTION: Dart Exception Definitions

class LogFileCreationError(Exception): pass
class ConfigFileValidationError(Exception): pass
class TestRunFileValidationError(Exception): pass
class UpdateCfgFileValidationError(Exception): pass
class RaisedKillSignalError(Exception): pass


if __name__ == "__main__":

    try:
        raise LogFileCreationError('LogFile1', 'LogFile2')

    except LogFileCreationError as e:
        print('The First Argument Passed is: %s' % e.args[0])
        raise
