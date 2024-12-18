# Copyright (c) 2016, Teradata, Inc.  All rights reserved.
# Teradata Confidential
#
# Primary owner: Mark.Gilkey@Teradata.com
# Secondary owner: Akhila.Pabbaraju@Teradata.com
#
# Knowledgeable developers include:
#    Alfred Yeung

"""
PURPOSE:
    This "library" contains code to extract info from the output of "netstat"
    commands.  These functions help us compare 2 sets of netstat outputs and
    return True if the netstat outputs are "substantially equivalent".
    I am not entirely sure what substantial equivalency is, but it includes:
       * The same number of each "type" of process, where processes are
         likely to include:
         * python
         * ProcMgmtMaster
         * Txman

    Here is simplified sample netstat output from "netstat -tnap | grep <port>":

        tcp  0  0  127.0.0.1:1985    127.0.0.1:59685   ESTABLISHED 8634/python
        tcp  0  0  39.64.8.5:38784   39.64.8.4:1985    ESTABLISHED 8947/Txman
        tcp  0  0  39.64.8.5:40168   39.64.8.3:1985    TIME_WAIT   -
        ...

    In the command, the value of <port> should be the value of
    PORT_WORKERDAEMON, which I can get by running a command like:
        ncli netconfig showport PORT_WORKERDAEMON

    I think I can ignore the actual port numbers, because those will vary
    depending upon whether I'm using the default port numbers or the
    alternate port numbers.

    I think I can ignore the "TIME_WAIT" lines, although I'm not sure.

    (This function(s) doesn't need to worry about executing the netstat command
    and retrieving the output; I'll use a separate function for that.  This
    library only "analyzes" the output once the output has been retrieved.)


DESIRABLE ENHANCEMENTS:
   1) More and better error-checking.
   2) I should be consistent about using camelCase vs. under_scores in names.
      I really should stick to one style (preferably the Aster coding
      standards style, which is camelCase according to
      https://confluence.asterdata.com/display/~gl186019/Aster+Python+Style+Guide?src=search#AsterPythonStyleGuide-Naming
      ).
"""




# ---------------------- Utility Functions for Netstat -----------------------

# This is the "base" of the netstat command that we will use in order to
# see which processes are using the port specified by PORT_WORKERDAEMON.
# We'll append the actual current PORT_WORKERDAEMON value to (a copy of) this
# command before we run this command.
NETSTAT_COMMAND_BASE = "netstat -tnap | grep -v WAIT | grep "


def extract_process_from_line(line):
    """
    PURPOSE:
        Given a line that looks like:
            tcp  0  0  39.64.8.5:38784  39.64.8.4:1985  ESTABLISHED 8947/Txman
        extract just the process name.  This seems easy because I think we can
        just extract everything after the last (only?) slash ("/") character.
    """

    fields = line.split("/")
    process = fields[-1]
    process = process.strip()
    return process


def count_processes_in_netstat(lines):
    """
    PURPOSE:
        Given a list of lines containing the output of "netstat" commands,
        return a dictionary with each unique process name and the number of
        times we found that process name.
        E.g. if there are 2 instances of Txman and 1 instance of
        ProcMgmtMaster, then we'll return a dictionary similar to:
            {
               "Txman":2,
               "ProcMgmtMaster":1
            }
        Since a typical linux system has dozens or hundreds of processes
        running, this could return a much larger dictionary, but typically
        the input to this function has already been filtered to include
        only processes that use a specified port number, so the dictionary
        is normally quite small.
    """
    counts = {}
    for line in lines:
        if line != None and line != "":
            process_name = extract_process_from_line(line)
            if process_name not in counts:
                counts[process_name] = 1
            else:
                counts[process_name] += 1
    return counts


