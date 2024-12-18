# Copyright (c) 2016, Teradata, Inc.  All rights reserved.
# Teradata Confidential
#
# Primary owner: Mark.Gilkey@Teradata.com
# Secondary owner: Akhila.Pabbaraju@Teradata.com

"""
PURPOSE:
   The extends the TestBase class to include functions (methods) that
   stop and start the Aster server, and that check its status via the
   "ncli system show" command.
   This class will be used as the base class for various tests that need to
   stop and restart the server, such as some Port Configuration Management
   tests.

USEFUL BACKGROUND INFO:
   1) This test frequently uses queenExecCommand() and possibly the
      workerExecCommand(), each of which returns a tuple that contains
      stdout, stderr, and an error code.  This test has a lot of local
      variables named "output" that are tuples like that.  ;-)
   2) Some of my comments might assume that you are already familiar with
      the Dart testing tool.

NOTES:
   1) In almost all cases, the phrase "the server" refers to Aster AX 7.0
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


import time


# For Dart-compatible logging
from lib.Dlog import dlog

# Dart-compatible library.
from lib.TestBase import TestBase

# Functions for processing a 3-tuple that contains STDOUT and STDERR strings,
# and a numeric error code.
from lib.OutErrTupleUtilities import *



# Set the environment properly when we ssh into the nodes so that we can
# run ncli commands, etc.
SOURCE_CMD = "source /home/beehive/config/asterenv.sh ; "

# We call the queenExecCmd() method a lot.  It returns a tuple with 3 elements,
# which as I recall are stdout, stderr, and an error code.
# The following variables are more human-readable than the raw index numbers.
STDOUT_COL = 0
STDERR_COL = 1
ERRCODE_COL = 2

# Give some commands a little extra time to complete, just in case.
# AX_DELAY_LENGTH is primarily for things like starting and activating the
# server.  (There is a separate delay for shutdown.)
# The units are seconds, e.g. 10 means 10 seconds.
AX_DELAY_LENGTH = 10

# After shutting down, ports are not necessarily released immediately, so we
# delay after shutting down and before doing anything else (in particular,
# before (re-)starting the server.  As you can see below, I've gotten different
# advice from different people about how long this delay should be.  ;-)
#AX_SHUTDOWN_DELAY_LENGTH = 10
#!!!AX_SHUTDOWN_DELAY_LENGTH = 190  # 180+ (see Daniel Yu's comment timestamped
                                  # 19/Aug/16 8:47 AM in JIRA BH-10079).
AX_SHUTDOWN_DELAY_LENGTH = 250     # Alfred Yeung says 2 * 120, and I added
                                   # a small FudgeFactor.

# I saw this test fail once when it SEEMED like the only problem was
# that a softstartup took about 390 seconds, so I've increased the
# timeout to 600, even though a typical startup is 45-60 seconds
# when there are only a few workers.
# I raised the timeout again (to 2400 seconds) after we started using YARN,
# because now that YARN is involved, startup takes MUCH longer.
ASTER_STARTUP_TIMEOUT = 2400



# ----------------------------------------------------------------------------
class TestBasePlusStartStop(TestBase):

    """
    PURPOSE:
       This runs a mildly stressful test on the Port Configuration Management
       feature by repeatedly:
          * Starting and stopping the server.
          * Making sure that it will run some SQL statements after each start.
          * Changing port numbers sometimes (while the server is down).
          * ... and more if I have time...  ;-)
   """

    def set_up_start_stop_commands(self):

        """
        PURPOSE:
            Initialize a bunch of strings that contain ncli commands, etc.
        RETURNS: 
            Nothing.
        """

        self.START_COMMAND_EXPECTED_OUT = []
        self.SHUTDOWN_COMMAND_EXPECTED_OUT = []
        self.ACTIVATE_COMMAND_EXPECTED_OUT = []
        self.ACTIVATE_COMMAND_EXPECTED_ERR = []

        # "Old" commands
        self.START_COMMAND = "ncli system softstartup"
        self.SHUTDOWN_COMMAND = "ncli system softshutdown"
        self.ACTIVATE_COMMAND = "ncli system activate"
        # Old expected output.
        self.START_COMMAND_EXPECTED_OUT.append("startup complete")
        self.SHUTDOWN_COMMAND_EXPECTED_OUT.append("shutdown complete")
        self.ACTIVATE_COMMAND_EXPECTED_OUT.append("Activation Complete")
        # "New" commands
        #self.START_COMMAND = "asteryarn --action=START_INSTANCE "
        #self.SHUTDOWN_COMMAND = "asteryarn --action=STOP_INSTANCE "
        #self.ACTIVATE_COMMAND = ""
        #if self.START_COMMAND.find("asteryarn") >= 0:
        #   self.START_COMMAND += " -instanceName=almostAnything"
        #   self.START_COMMAND += " --queenNode=" + self.byn0
        #   self.SHUTDOWN_COMMAND += " -instanceName=almostAnything"
        #   self.SHUTDOWN_COMMAND += " --queenNode=" + self.byn0
        # New expected output.
        # IMPORTANT: Because the "ncli system soft..." commands are "mapped"
        # to the new commands, newer builds of the product should get the
        # new outputs EVEN IF you use the old commands!
        self.START_COMMAND_EXPECTED_OUT.append("instance started successfully")
        # This isn't good enough, but I'm not getting back the entire
        # output; and in particular I'm not getting back a clear
        # "success" message.
        self.SHUTDOWN_COMMAND_EXPECTED_OUT.append("processed successfully")
        # For Activate, the New output is empty but you get a no-op error msg.
        self.ACTIVATE_COMMAND_EXPECTED_OUT.append("")
        self.ACTIVATE_COMMAND_EXPECTED_ERR.append(
            "activate command is no-op as it is handled through yarn")


    def get_byn0(self):
        """
        PURPOSE:
           If the queen has a byn0 (bynet) IP address, return it.
           Otherwise, return an empty string.
           The first 2 lines of "ifconfig" output are typically:
              byn0 ...
              inet addr:39.64.8.5 ...
           where of course 39.64.8.5 is replaced with the actual bynet address.
        """
        # If self.byn0 doesn't already exist, we'll get a NameError exception,
        # which means that we need to get the byn0 address and set
        # self.byn0 to that for future use.
        try:
            if self.byn0 != None:
                return self.byn0
        except NameError:
            pass   # Fall through and get the byn0 address

        # If self.byn0 was not defined, or was equal to None, then get it.

        byn0_address = ""

        # Get the first 2 lines of output from ifconfig (which will contain
        # the bynet0 IP address).
#        cmd = "/sbin/ifconfig"
        cmd = "ifconfig"
        output = self.queenExecCommand(cmd)
        stdout = output[STDOUT_COL]
        stdout_lines = stdout.split("\n")
        line1 = stdout_lines[0]
        line2 = stdout_lines[1]
        line1 = line1.strip()
        # If the first line starts with "byn0"...
        if line1[0:4] == "byn0":
            # ... then extract the IP address.
            line2 = line2.strip()
            line2 = line2.split(" ")
            address_column = line2[1]
            if address_column[0:5] == "addr:":
                subfields = address_column.split(":")
                byn0_address = subfields[1]
                self.byn0 = byn0_address

        return byn0_address


    def ncli_system_show(self, p_diagnostic_level=0):
        """
        PURPOSE:
           Run "ncli system show" and return the result.
        """
        cmd = SOURCE_CMD + "ncli system show"
        output = self.queenExecCommand(cmd, node=0, timeout=60)
        display_out_and_err(output, p_diagnostic_level=p_diagnostic_level)
        return output


    def get_cluster_state_from_output(self, output):
        """
        PURPOSE:
           This crudely parses the input string named "output" to see whether
           it contains something similar to:
              "| Cluster State | xyz |"
           and returns the "xyz" if it's present, or None if it's not present.
           The parsing is crude and could be spoofed by malicious inputs,
           but is likely to be reasonably accurate in real-world situations.
        NOTES:
           This is a fairly generic function that could be useful in other
           tests and probably should be moved to a library.
        """

        # Split the input into individual lines.
        s_array = output.split("\n")
        count = len(s_array)

        found = False
        i = 0
        # process each line until we find "Cluster State" or run out of lines.
        while i < count and found == False:
            # Get the next line
            line = s_array[i]
            line = line.strip()

            fields = line.split("|")
            if len(fields) == 4:
                name = fields[1]
                if name.strip() == "Cluster State":
                    state = fields[2]
                    return state.strip()

            i += 1

        return None


    def test_get_cluster_state_from_output(self):

        """
        PURPOSE:
           This tests the get_cluster_state_from_output() method.  It's just an
           internal self-test method; it doesn't test consul.
        """

        s = self.get_cluster_state_from_output("| Cluster State | unknown |")
        print "=====>", s
        assert s == "unknown"

        s = self.get_cluster_state_from_output(
            "   |   Cluster State  |  Up  | ")
        print "=====>", s
        assert s == "Up"

        # Missing the leading vertical bar ("|"), so should fail (return None).
        s = self.get_cluster_state_from_output("Cluster State  |  Up  | ")
        print "=====>", s
        assert s == None

        state_str = "+---------------------+---------+\n" + \
                    "| Value               | State   |\n" + \
                    "+---------------------+---------+\n" + \
                    "| Cluster State       | unknown |\n" + \
                    "| Incorporation State | --      |\n" + \
                    "| Backup Status       | --      |\n" + \
                    "+---------------------+---------+\n" + \
                    "3 rows\n"
        s = self.get_cluster_state_from_output(state_str)
        print "=====>", s
        assert s == "unknown"


    def cluster_state_is(self, expected_server_state):
        """
        PURPOSE:
            Check that the server has the expected status, as reported by
            "ncli system show".  For example, if we expect the server to be
            down (e.g. after we gave the command to shut it down), then
            "ncli system show" should report status "unknown".
        INPUTS:
            expected_server_state: the expected server state, e.g. "unknown"
                if the server is down.
        """
        # Check the status -- e.g. check that the server is down.
        output = self.ncli_system_show()
        output_message = output[STDOUT_COL]
        server_state = self.get_cluster_state_from_output(output_message)
        if server_state == expected_server_state:
            passed = True
        else:
            msg = "ERROR: expected_server_state = '" + expected_server_state
            msg += "', but actual state was '" + server_state + "'."
            dlog.error(msg)
            passed = False
        return passed


    # Deprecated -- keeping temporarily for backwards compatibility until
    # I can update calling code to use the new name of this function.
    def server_status_is(self, expected_server_state):
        return self.cluster_state_is(expected_server_state)


    def outputSaysClusterStateIsUp(self):

        """
        PURPOSE:
           Return True if the string contains something similar to:
              "| Cluster State | Up |"
           Otherwise, return False.
        """

        return self.server_status_is("Up")


    def outputSaysClusterStateIsUnknown(self):

        """
        PURPOSE:
           Return True if the string contains something similar to:
              "| Cluster State | unknown |"
           Otherwise, return False.
        """

        return self.server_status_is("unknown")


    def runNcliSoftCommandAndDisplayOutputAndError(self, ncli_cmd,
         p_diagnostic_level=0, p_expected_out_str="", p_expected_err_str="",
         ax_delay_length=AX_DELAY_LENGTH):

        """
        PURPOSE:
           Run an "ncli softXYZ" command, such as ncli softshutdown,
           and display the output.  This also displays the status before
           and after the command.
        INPUTS:
           ncli_cmd: the ncli command to run, e.g. "ncli system softshutdown".
           p_diagnostic_level: Set to 0 to reduce/eliminate diagnostic messages,
              or 1 to get more diagnostics.
           p_expected_out_str: The expected output (stdout).
              We test whether the actual output INCLUDES the expected output;
              we don't require an exact match.
           p_expected_err_str: The expected stderr.
              We test whether the actual error INCLUDES the expected error;
              we don't require an exact match.
        RETURNS:
           This returns the stdout from when we issued the ncli_cmd.
        """

        # Optional diagnostic: show system status before the command.
        self.ncli_system_show()

        # Run the requested ncli command.
        cmd = SOURCE_CMD + ncli_cmd
        output = self.queenExecCommand(cmd, node=0,
                 timeout=ASTER_STARTUP_TIMEOUT)
        out = output[STDOUT_COL]
        err = output[STDERR_COL]
        errcode = int(output[ERRCODE_COL])
        if p_diagnostic_level > 0 or errcode > 0:
            msg = "========DDDIAGNOSTIC: runNcliSoftCommand\n"
            msg += "- - cmd - -\n"
            msg += cmd + "\n"
            msg += "- - stdout - -\n"
            msg += out + "\n"
            msg += "- - stderr - -\n"
            msg += err + "\n"
            msg += "- - errcode - -\n"
            msg += str(errcode) + "\n"
            msg += "=======\n"
            if errcode > 0:
                dlog.error(msg)
            else:
                print msg    # DDDIAGNOSTIC on screen only if not an error.
        passed = output_contains_expected(output, p_expected_out_str,
                 p_expected_err_str)
        time.sleep(ax_delay_length)

        return output


    def shut_down_server(self):
        """
        PURPOSE: Shut down the AX server.
        RETURNS: True if we did not detect any error while shutting down.
        """

        # Shut down the server.
        dlog.info("----- shut_down_server() -----")
        passed = False

        cmd = self.SHUTDOWN_COMMAND
        output = self.runNcliSoftCommandAndDisplayOutputAndError(cmd,
                 p_diagnostic_level=0,
                 p_expected_out_str=self.SHUTDOWN_COMMAND_EXPECTED_OUT,
                 ax_delay_length=AX_SHUTDOWN_DELAY_LENGTH
                 )
        if output[ERRCODE_COL] == 0:
            passed = True
        else:
            msg = "ERROR: Shutdown command returned error "
            msg += str(output[ERR_CODE_COL])
            print msg
            dlog.error(msg)
            passed = False
        if passed:
            # Check the status -- i.e. check that the server is down.
            expected_server_state = "unknown" # This is what "ncli system show"
                                              # says when the server is down.
            passed = self.server_status_is(expected_server_state)

        dlog.info("--- shut_down_server() exiting passed = ---" + str(passed))
        return passed


    def start_server(self, expected_status = "Up"):
        """
        PURPOSE: Start the AX server.
        INPUTS:
            expected_status: In almost all cases, after activating the server,
                you expect the cluster state (as shown by the command
                "ncli system show") to be "Up".  In rare cases, such as
                negative tests (e.g. if you sabotaged the ports file), you
                might expect the status to be something else, or you might
                not even want to check.  In those rare cases, you can
                specify an alternative expected status, or you can specify
                None to say that you don't want to check the status.
        """
        dlog.info("----- start_server() -----")
        passed = False
        cmd = self.START_COMMAND
        output = self.runNcliSoftCommandAndDisplayOutputAndError(cmd,
                 p_diagnostic_level=0,
                 p_expected_out_str=self.START_COMMAND_EXPECTED_OUT,
                 ax_delay_length=AX_DELAY_LENGTH
                 )

# Argh! Although BH-9218 has been fixed (supposedly), there is now a
# separate JIRA (BH-9859) with the same symptom, so I might need to
# re-enable this code until BOTH bugs are fixed. --mgilkey 2016-08-05
# Supposedly, this bug BH-9218 has been fixed, so I am commenting out this code
# for now and will remove it if indeed the bug is fixed.
#        # ----- Try to detect and correct when nodes are passive.
#        # Due to a bug, nodes sometimes come up Passive rather than Active.
#        # (BH-9218)  This bug interferes with long-running testing, so I'm
#        # trying to detect it and then continue, rather than halt.
#        err_message = output[STDERR_COL]
#        while "Passive" in err_message:
#            print "====SEVERE WARNING: BH-9218: Passive nodes. Retrying start."
#            # Note that we saw 9218 again.
#            f = open("/home/mg186014/bh-9218.log", "a")
#            msg = time.strftime("%Y-%m-%d %H:%M:%S") + "   "
#            msg += str(self.byn0) + "\n"
#            f.write(msg)
#            f.close()
#            # Shut down and try again to restart.
#            self.shut_down_server()
#            output = self.runNcliSoftCommandAndDisplayOutputAndError(cmd,
#                 p_diagnostic_level=0,
#                 p_expected_out_str=self.START_COMMAND_EXPECTED_OUT,
#                 ax_delay_length = AX_DELAY_LENGTH
#                 )
#            err_message = output[STDERR_COL]
#        # -----

        # Check that the server is in the expected state (usually "Up").
        if expected_status != None:
            passed = self.cluster_state_is(expected_status)
            if not passed:
                print "------------------\n" + str(output) + "--------------\n"

        else:
            # No error detected. Let the caller check further if she wants,
            # e.g. if running negative tests.
            passed = True

        return passed


    def activate_server(self, expected_status = "Up"):
        """
        PURPOSE: Activate the server (after starting it).
        INPUTS:
            expected_status: In almost all cases, after activating the server,
                you expect the cluster state (as shown by the command
                "ncli system show") to be "Up".  In rare cases, such as
                negative tests (e.g. if you sabotaged the ports file), you
                might expect the status to be something else, or you might
                not even want to check.  In those rare cases, you can
                specify an alternative expected status, or you can specify
                None to say that you don't want to check the status.
        """
        # Activate the server.
        if self.ACTIVATE_COMMAND == "":
            return
        dlog.info("----- activate_server() -----")
        passed = False
        cmd = "ncli system activate"
        output = self.runNcliSoftCommandAndDisplayOutputAndError(cmd,
                 p_diagnostic_level=0,
                 p_expected_out_str=self.ACTIVATE_COMMAND_EXPECTED_OUT,
                 ax_delay_length=AX_DELAY_LENGTH)

        # Check that the server is in the expected state (usually "Up").
        if expected_status != None:
            passed = self.cluster_state_is(expected_status)
        else:
            # No error detected. Let the caller check further if she wants,
            # e.g. if running negative tests.
            passed = True

        return passed


    def sanity_test_myself(self):

        # Set to False if the test fails.
        passed = False

        # Queen's bynet IP address.
        self.byn0 = None
        self.byn0 = self.get_byn0()

        # Initialize strings with "ncli system soft*" commands.
        self.set_up_commands()

        # Stop the server.
        passed = self.shut_down_server()

        # Verify that the server is down.
        if passed:
            passed = self.cluster_state_is("unknown")
            passed = passed and self.server_status_is("unknown")
            passed = passed and self.outputSaysClusterStateIsUnknown()

        # Start the server.
        if passed:
            passed = self.start_server()
        if passed:
            passed = self.activate_server()

        # Verify that the server is up.
        if passed:
            passed = self.cluster_state_is("Up")
            passed = passed and self.server_status_is("Up")
            passed = passed and self.outputSaysClusterStateIsUp()

        return passed


    def run(self):

        """
        PURPOSE:
           Run the main portion of the test.
        """

        passed = self.sanity_test_myself()

        return passed

