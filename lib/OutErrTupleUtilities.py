# Copyright (c) 2016, Teradata, Inc.  All rights reserved.
# Teradata Confidential
#
# Primary owner: Mark.Gilkey@Teradata.com
# Secondary owner: Akhila.Pabbaraju@Teradata.com
#

"""
PURPOSE:

This contains functions for operating on:
* strings,
* a 3-tuple returned by queenExecCmd(), which contains a numeric error
  code, a stdout string, and a stderr string.


USEFUL BACKGROUND INFO:
   1) This test frequently uses queenExecCommand() and workerExecCommand(),
      each of which returns a tuple that contains stdout, stderr, and an
      error code.  This test has a lot of local variables named "output"
      that are tuples like that.  ;-)
   2) My comments assume that you are already familiar with the Dart
      testing tool.
   3) This test, like the AX 7.0 product, was originally written to use
      "consul" and was later modified to use "flat files" to get port numbers.
      You might find some out-of-date references to consul in the comments
      (and perhaps even the code, although I think I fixed or commented out
      all of those).  It will be easier for you to understand this test
      if you understand the flat files (currently
          /var/tmp/.aster-ports (active)
          /home/beehive/config/ports (user-editable; copied to the "active"
              file when the server starts)

NOTES:
   1) I've started adding "TEST CASES COVERED" sections to some
      function/method headers.  These are not complete, but might be
      helpful sometimes.  In all cases, the test case names referenced
      are in the test plan.
   2) In almost all cases, the phrase "the server" refers to Aster AX 7.0
      (not the hardware, Hadoop, etc.).  The name "the server" might be
      less appropriate for AX than it was for AD, but I'm still in the
      habit of calling it "the server".

DESIRABLE ENHANCEMENTS:
   1) More and better error-checking.
   2) I should be consistent about using camelCase vs. under_scores in names.
      I really should stick to one style (preferably the Aster coding
      standards style, which is camelCase according to
      https://confluence.asterdata.com/display/~gl186019/Aster+Python+Style+Guide?src=search#AsterPythonStyleGuide-Naming
      ).
   N) The test plan might contain additional ideas for features that I'd
      like to add eventually.

"""


import types


# For Dart-compatible logging
from lib.Dlog import dlog


from PortMapperExceptions import SoftUpOrDownException


# We call the queenExecCmd() method a lot.  It returns a tuple with 3 elements,
# which are stdout, stderr, and an error code.
# The following variables are more human-readable than the raw index numbers
# into the tuple.
STDOUT_COL = 0
STDERR_COL = 1
ERRCODE_COL = 2



# ---------------------- String and Error Utilities --------------------------

def string_contains_expected(actual_string, expected_string,
    caller_name="runNcliSoftCommandAndDisplayOutputAndError()"):

    """
    PURPOSE:
        Return True if the actual string contains the expected string
        somewhere within it.
        Otherwise, return False or throw an exception.
    INPUTS:
        actual_string: the string in which we want to search.
        expected_string: the sub-string that we hope to find in the
            actual_string.
        caller_name: A string containing the name of the function that
            called this function, so we can have a better error message.
            It's legal to set this to an empty string.
    """

    # Check that the input parameter was actually a string.
    if type(actual_string) != types.StringType:
        msg = "ERROR: "
        if caller_name != None:
            msg += caller_name + ": "
        msg += "string_contains_expected(): actual_string is not a string."
        dlog.error(msg)
        return False

    # If we found the expected string inside the actual string...
    if actual_string.lower().find(expected_string.lower()) >= 0:
        return True
    else:
        return False


def some_substrings_in_string(p_actual_string, p_expected_substrings,
        p_caller_name = None, p_custom_exception = None):

    """
    PURPOSE:
        Return True if at least one of the strings in the list 
        p_expected_substrings is equal to, or a substring of, p_actual_string.
    INPUTS:
        p_actual_string: A string, typically stdout or stderr from a command.
        p_expected_substrings: a list of strings that we hope to find at 
            least one of.  For example, this could be a list of acceptable
            error messages.  If all strings are empty strings, we'll treat that
            as automatic pass.
        p_caller_name: The name of the method calling this (useful in 
            diagnostic messages).
        p_custom_exception: optional: pass an exception if you'd like that 
            specific exception thrown if we don't find one of the expected
            strings.
    RETURNS:
        Returns True if one or more of the strings in p_expected_substrings is
        in p_actual_string. Otherwise, we return false or raise
        p_custom_exception, depending upon whether p_custom_exception is None.
    """

    passed = False
    i = 0
    count = len(p_expected_substrings)

    # Keep looking for expected strings until we find one or run out.
    while not passed and i < count:
        passed = string_contains_expected(p_actual_string, 
                 p_expected_substrings[i], p_caller_name)
        i += 1
    if not passed:
        msg = "ERROR: "
        if p_caller_name != None:
            msg += p_caller_name + ": "
        # For example, "expected 'Error' in 'Error: broken connection'".
        msg += "expected '" + str(p_expected_substring) + \
               "' in '" + p_actual_string + "'."
        dlog.error(msg)
        if p_custom_exception != None:
            raise p_custom_exception

    return passed


def output_contains_expected(output, p_expected_out, p_expected_err,
    caller_name="runNcliSoftCommandAndDisplayOutputAndError()",
    custom_exception=SoftUpOrDownException):

    """
    PURPOSE:
        Check that the actual output contains at least one of the
        acceptable/expected outputs.
    INPUTS:
        output: The usual 3-part tuple with stdout, stderr, and error code.
        p_expected_out: the sub-string that we hope to find in stdout.
            This can be either a single string or a list of strings.
            If it's a list of strings, we're happy if at least one is in
            the actual output.
            Each string can be empty.  We'll treat that as automatic pass.
        p_expected_err: the sub-string that we hope to find in stderr.
            This can be either a single string or a list of strings.
            If it's a list of strings, we're happy if at least one is in
            the actual output.
            Each string can be empty.  We'll treat that as automatic pass.
        caller_name: A string containing the name of the function that
            called this function, so we can have a better error message.
            It's legal to set this to an empty string.
        custom_exception: If the user would like to throw an exception
            rather than merely return False if the expected string is not
            found, then the user can pass the exception she'd like thrown.
    """
    passed = False

    # We expect either a string or a list of strings.  If it's a single
    # string, then make it a list so that subsequent code can deal with 
    # the same data type (list) every time.
    if type(p_expected_out) == types.StringType:
        p_expected_out = [p_expected_out]
    if type(p_expected_err) == types.StringType:
        p_expected_err = [p_expected_err]

    # Check that the actual output contains at least one of the acceptable
    # output strings.
    out = output[STDOUT_COL]
    passed = some_substrings_in_string(p_actual_string = out, 
             p_expected_substrings = p_expected_out,
             p_caller_name = caller_name,
             p_custom_exception = custom_exception)

    if passed:
        err = output[STDERR_COL]
        passed = some_substrings_in_string(p_actual_string = err, 
                 p_expected_substrings = p_expected_err,
                 p_caller_name = caller_name,
                 p_custom_exception = custom_exception)

    return passed


def test_output_contains_expected():

    """
    PURPOSE: Do a quick sanity test of the method named
        output_contains_expected()
    """

    assert output_contains_expected(
        ("STDOUT: Four score and seven years ago", "STDERR: our fathers", 0),
        p_expected_out="score",
        p_expected_err="years",
        caller_name="test_output_contains_expected()",
        custom_exception=None
        )

    assert output_contains_expected(
        ("STDOUT: Four score and seven years ago", "STDERR: our fathers", 0),
        p_expected_out=["nomatch", "score", "notme"],
        p_expected_err=["zzz", "years", "y"],
        caller_name="test_output_contains_expected()",
        custom_exception=None
        )

    assert not output_contains_expected(
        ("STDOUT: Four score and seven years ago", "STDERR: our fathers", 0),
        p_expected_out="nomatch",
        p_expected_err="zzz",
        caller_name="test_output_contains_expected()",
        custom_exception=None
        )

    assert not output_contains_expected(
        ("STDOUT: Four score and seven years ago", "STDERR: our fathers", 0),
        p_expected_out=["nomatch", "notme"],
        p_expected_err=["zzz", "y"],
        caller_name="test_output_contains_expected()",
        custom_exception=None
        )


def display_out_and_err(out_and_err, p_diagnostic_level=1):
        """
        INPUTS:
           out_and_err: A tuple containing the output and error information,
               typically the return value from calling queenExecCommand().
           p_diagnostic_level: Influences the amount of diagnostic output shown.
               0 (or less) means don't show any.
        """

        if p_diagnostic_level <= 0:
            return

        dlog.info("===============")
        # If it looks like it might be a tuple with output and error info...
        length_out_and_err = len(out_and_err)
        if length_out_and_err >= 2 and length_out_and_err <= 3:
            dlog.info("-------------- out -----------")
            out = out_and_err[STDOUT_COL]
            dlog.info(out)
            err = out_and_err[1]
            if err != None and len(err) > 0:
                dlog.info("-------------- err -----------")
                dlog.info(err)
            if length_out_and_err == 3:
                errcode = out_and_err[ERRCODE_COL]
                if errcode != 0:
                    dlog.info("-------------- errcode -----------")
                    dlog.info(str(errcode))
        elif len(out_and_err) == 0:
            msg = "SEVERE WARNING: display_out_and_err(): Expected tuple " + \
                  "with 2 values, but got nothing."
            dlog.warning(msg)
        else:
            # I'm not sure what it is, so print it and try to figure it out.
            dlog.warning("SEVERE WARNING: display_out_and_err(): unexpected:")
            dlog.warning(out_and_err)
        dlog.info("===============")



