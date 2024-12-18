# Copyright (c) 2016, Teradata, Inc.  All rights reserved.
# Teradata Confidential
#
# Primary owner: Mark.Gilkey@Teradata.com
# Secondary owner: Akhila.Pabbaraju@Teradata.com
#

"""
PURPOSE:
    This contains definitions for one or more exceptions whose names
    give at least some clue about what failed.
"""


# ----------------------------------------------------------------------------
class SoftUpOrDownException(Exception):
    """
    PURPOSE:
        This exception is to provide a more specific exception type when
        reporting SOFTstartup and SOFTshutdown failures.  Currently, the
        exception has no real "content", other than the uniqueness of its
        name.  Feel free to improve that someday.
    """
    pass


