# Copyright (c) 2016, Teradata, Inc.  All rights reserved.
# Teradata Confidential
#
# Primary owner: Mark.Gilkey@Teradata.com
# Secondary owner: Akhila.Pabbaraju@Teradata.com
#
# Knowledgeable developers include:
#    Alfred Yeung
#    Feni Chawla

"""
PURPOSE:

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

"""


# For Dart-compatible logging
from lib.Dlog import dlog



# --------- Utility Functions for port-related ncli Commands -----------------

def extract_port_number(line):
    """
    PURPOSE:
       Given a string that contains a key-value pair and looks similar
       to the following:
           | PORT_MONITORING | 40011 |
       return the port number (the value 40011 in this case).
    INPUTS:
       line: The string that contains a line of output from a command like
          "ncli consulinfo showkeyswithprefix..."
          "ncli consulinfo getvalue..."
      """
    line = line.split("|")
    # Get the column that has the port number.
    try:
        port_number = line[2]
        port_number = port_number.strip()
    except IndexError:
        msg = "ERROR: extract_port_number(): line = " + str(line)
        dlog.error(msg)
        return None
    return port_number


def extractActivePortNumberFromNetconfig(line):
    """
    PURPOSE:
       Given a string that contains a key-value pair and looks similar
       to the following:
           | PORT_MONITORING | 40011 | 40011 |
       where the first number is the "Configured" port number and the
       second number is the "Active" port number,
       return the active port number (the value 40011 in this case).
    INPUTS:
       line: The string that contains a line of output from a command like
          "ncli netconfig showport ..."
      """
    line = line.split("|")
    # Get the column that has the port number.
    try:
        port_number = line[3]
        port_number = port_number.strip()
    except IndexError:
        msg = "ERROR: extractActivePortNumberFromNetconfig(): line = "
        msg += str(line)
        dlog.error(msg)
        return None
    return port_number




# ----------------------------------------------------------------------------

class PortInfoClass(object):

    """
    PURPOSE:
        This contains info related to ports, particularly the names of the
        files that contain port info and the default and alternate port
        numbers.
    BACKGROUND INFO:
    The list of port file names was originally a simple array/list, and it
    could still be a simple list, but I made it a class it's easier to document
    in one place, rather than have to document it every place that I use it.

    The basic idea is that this class contains one variable,
    which is a list of port file names.
    The first element in the list is the name of the required port file name,
    i.e. the file that the server uses when it starts, and which therefore
    must exist when the server starts.
    For flat-file based AX, this is
        /home/beehive/config/ports
    For consul-based AX, this is
        /home/beehive/config/serviceports.json
    Elements 2 through N-1 of the list are the names of alternate port files,
    which typically have names that are variations of the required file name.
    For example, the names might be
        /home/beehive/config/ports.alternate1
        /home/beehive/config/ports.alternate2
        etc.
    The last element is "the empty slot", i.e. if we haven't done any
    rotations yet, there should be no file with that name.  The empty slot
    allows us to do the rotation.  Just as you need a temporary variable
    in order to exchange/rotate values among variables:
       temp = x
       x = y
       y = temp
    so also you need an empty slot when you are rotating files.
    Technically, the "empty slot" can be ANY slot other than the first
    slot, which holds the required file name.  But for simplicity, we'll
    assume that at the start of the program, the empty slot is the last
    file name, e.g.
        /home/beehive/config/ports.alternateN
    For more information about the "empty slot", see Rotate.py.

    We could have made this class more sophisticated, such as making
    the "required file name" a separate variable rather than the first
    (zeroeth) element of the list, but all of the code in this test
    assumes that the required file name is the zeroeth element, so when
    I introduced this class I tried to make this class similar to
    (compatible with) the existing code.

    Similarly, we could add lots of OOP-style methods to this class, but
    that would require changing all the existing code, which simply expects
    a list.
    """

    # It would be better to read this info from the ports file if we knew
    # where there was a "clean" copy to read from.  However, since we might
    # be running after a previous test aborted and left behind an incorrect
    # ports file, I've hard-coded these values for now.
    # I probably should have made this a 2-dimensional dictionary so that
    # the keys and values are paired.
    DEFAULT_PORT_NAMES_AND_NUMBERS = (
                     "PORT_ICE_SERVER",
                     "PORT_ICE_SERVER_DATA",
                     "PORT_LOG_SERVER",
                     "PORT_MONITORING",
                     "PORT_STATSSERVER",
                     "PORT_WORKERBASEPORT",
                     "PORT_WORKERDAEMON",
                     "2115",
                     "2117",
                     "2008",
                     "2195",
                     "1953",
                     "9010",
                     "1985"
                     )
    ALTERNATE_PORT_NAMES_AND_NUMBERS = (
                     "PORT_ICE_SERVER",
                     "PORT_ICE_SERVER_DATA",
                     "PORT_LOG_SERVER",
                     "PORT_MONITORING",
                     "PORT_STATSSERVER",
                     "PORT_WORKERBASEPORT",
                     "PORT_WORKERDAEMON",
                     "40008",
                     "40009",
                     "40010",
                     "40011",
                     "40017",
                     "43000",
                     "40018"
                     )


    PORT_OUT_OF_RANGE_ERR_MSG = \
      "Error: Specified port number is not in available port number range." + \
      " Please specify port number between 1024 to 65535."

    def __init__(self, p_serviceports_file_list=None):

        if p_serviceports_file_list != None:
            self.serviceports_file_list = p_serviceports_file_list
        else:   # Use defaults
            # Consul / serviceports.json file names
            #serviceports_file_list = [
            #    # Required file name
            #    "/home/beehive/consul/serviceports.json",
            #    # Alternate port file(s)
            #    "/home/beehive/consul/serviceports.json.alternate1",
            #    # Empty slot
            #    "/home/beehive/consul/serviceports.json.alternate2"
            #    ]

            # Flat file names
            # Note that when we use "flat file" rather than consul, the
            # "actual" or "required" file is the name of the "inactive" file
            # (the one that the user may change), not the name of the "active"
            # file (the one that AX reads reads from while running).
            self.serviceports_file_list = [
                # Required file name
                "/home/beehive/config/ports",
                # Alternate port file(s)
                    "/home/beehive/config/ports.alternate1",
                # Empty slot
                "/home/beehive/config/ports.alternate2"
                ]


    def get_service_ports_file_list(self):
        """
        PURPOSE: Returns the list of names of files that contain port info.
        """
        return self.serviceports_file_list

