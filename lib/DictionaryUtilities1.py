# Copyright (c) 2016, Teradata, Inc.  All rights reserved.
# Teradata Confidential
#
# Primary owner: Mark.Gilkey@Teradata.com
# Secondary owner: Akhila.Pabbaraju@Teradata.com
#

"""
PURPOSE:

    This contains a function to compare two dictionaries.
    Later, we might add other useful functions for operating on dictionaries.

DESIRABLE ENHANCEMENTS:
   1) More and better error-checking.
   2) I should be consistent about using camelCase vs. under_scores in names.
      I really should stick to one style (preferably the Aster coding
      standards style, which is camelCase according to
      https://confluence.asterdata.com/display/~gl186019/Aster+Python+Style+Guide?src=search#AsterPythonStyleGuide-Naming
      ).

"""


import types


# For Dart-compatible logging
from lib.Dlog import dlog



# ---------------------- Generic Utilities ---------------------------

def dictionaries_are_equal(dict1, dict2):
    """
    PURPOSE: return True if 2 dictionaries match, else return False.
        Returns False if 1 or both are not dictionaries.
        Returns False if 1 or both are None.

    """
    if dict1 == None or type(dict1) != types.DictType:
        msg = "ERROR: dictionaries_are_equal(): " + \
              "Supposed dictionary dict1 was not a dictionary"
        dlog.error(msg)
        return False
    if dict2 == None or type(dict2) != types.DictType:
        msg = "ERROR: dictionaries_are_equal(): " + \
              "Supposed dictionary dict2 was not a dictionary"
        dlog.error(msg)
        return False

    keys1 = dict1.keys()
    keys2 = dict2.keys()

    if len(keys1) != len(keys2):
        return False

    for key in keys1:
        if key not in keys2:
            return False
        if dict1[key] != dict2[key]:
            return False

    return True


