#
# Unpublished work.
# Copyright (c) 2017 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner:divya.sivanandan@teradta.com
# Secondary Owner:
#
__all__ = ["SyncpointManager"]


import os
import time
from Dlog import dlog
from SshConnect import SshConnect

# File name prefix for all syncpoint files
SYNCPOINT_FILE_PREFIX = "/tmp/syncpoint."


class SyncpointManager(object):
    """
       Manages a named syncpoint at the indicated node.  Exposes several methods for
       (un)setting the syncpoint, determining whether the syncpoint is set,
       determining what processes are waiting at the syncpoint, and resuming
       specific waiting processes.
       """

    def __init__(self, syncpointName, hostName, isSet=None, username=None, password=None):
        """
        @param syncpointName The (string) name of the syncpoint.

        @param hostName The hostname or IP adress of the node where the syncpoint
        will exist (if set).

        @param isSet If True, then the syncpoint will be set; if False, then the
        syncpoint will be unset; if None, then the syncpoint will be left as-is.
        """
        self.__name = syncpointName
        self.__hostName = hostName
        if username is None:
            dlog.error("Username is mandatory")
            raise
        if password is None:
            dlog.error("Password is mandatory")
            raise

        self.sshconnect = SshConnect(self.__hostName, username, password)

        # Enables Python syncpoints on hostName.
        stdout, stderr, status = self.run_cmd("touch /tmp/PY_SYNCPOINTS_ACTIVE")

        if isSet is not None:
            self.setIs(isSet)

    def run_cmd(self, cmd, timeout=300):
        """ Runs the cmd on self.__hostname remotely and returns result"""
        dlog.info("Running on %s : %s " % (self.__hostName, cmd))
        self.sshconnect.connect()
        stdout, stderr, status = self.sshconnect.execCommand(cmd, timeout=timeout)
        dlog.info(stdout + stderr)
        dlog.info(status)
        return stdout, stderr, status

    @staticmethod
    def clearAllSyncpoints(hostName, username, password):
        """Remove all syncpoints on specified host"""
        sshconnect = SshConnect(hostName, username, password)
        sshconnect.connect()
        stdout, stderr, status = sshconnect.execCommand("rm -f %s*" % SYNCPOINT_FILE_PREFIX,timeout=400)
        dlog.info(stdout + stderr)
        if status != 0:
            dlog.error("Removing the syncpoint file failed")
            raise
        else:
            dlog.info("Cleared all syncpoints")

    def syncpointName(self):
        """Return syncpoint name"""
        return self.__name

    def hostName(self):
        """Return hostname of node where syncpoint will exist (if set)"""
        return self.__hostName

    def isSet(self):
        """Return True if syncpoint set, else False"""
        cmd = "test -e %s" % self.__syncpointSetFile()
        stdout, stderr, status = self.run_cmd(cmd)
        if status in [0, 1]:
            return True
        return False

    def fileList(self, pattern):
        """Return a list of files with matching pattern"""
        file_list_cmd = "ls %s" % pattern
        stdout, stderr, status = self.run_cmd(file_list_cmd)
        stdout = stdout.rstrip("\n")  # Strip trailing newline
        if status == 0:
            pathnames = stdout.split("\n")
        else:
            if "No such file or directory" in stdout + stderr:
                pathnames = []  # No files matching filePattern
            else:
                dlog.error("No file exist with the pattern provided.")
                raise
        return pathnames

    def waitingProcesses(self):
        """Return list of PIDs of procesess waiting at the syncpoint"""
        pids = []
        fileNames = self.fileList(self.__syncpointProcessFileWildcard())
        dlog.info(fileNames)
        for fileName in fileNames:
            pid = int(os.path.basename(fileName).split("-")[1])
            pids.append(pid)
        return pids

    def waitingTags(self):
        """Return set of tag values for processes waiting at the syncpoint"""
        tags = []
        fileNames = self.fileList(self.__syncpointProcessFileWildcard())
        for fileName in fileNames:
            tag = os.path.basename(fileName).split("-")[2]
            tags.append(tag)
        return tags

    def setIs(self, value):
        """
        If value is True, set the syncpoint.  If value is False, clear the
        syncpoint and resume any processes waiting at the syncpoint.
        """
        if value:
            cmd = "touch %s" % self.__syncpointSetFile()
            stdout, stderr, status = self.run_cmd(cmd)
            if status != 0:
                dlog.error("Setting the syncpoint failed")
                raise
        else:
            self.setIsFalseButWaitingProcessesUnaffected()
            self.allWaitingProcessesAreResumed()

    def setIsFalseButWaitingProcessesUnaffected(self):
        """
        Clear the syncpoint without resuming any waiting processes.  Each waiting
        process has its own process-specific file that it waits on.
        """
        cmd = "rm -f %s" % self.__syncpointSetFile()
        stdout, stderr, status = self.run_cmd(cmd)
        if status != 0:
            dlog.error("Clearing the syncpoint failed")
            raise

    def allWaitingProcessesAreResumed(self):
        """Resume all processes (if any) waiting at the syncpoint"""
        cmd = "rm -f %s" % self.__syncpointProcessFileWildcard()
        stdout, stderr, status = self.run_cmd(cmd)
        if status != 0:
            dlog.error("Resuming process waiting at the syncpoint failed")
            raise

    def waitingProcessIsResumed(self, pid):
        """Resume specific process waiting at the syncpoint"""
        if pid not in self.waitingProcesses():
            msg = "PID %d not list of waiting processes" % pid
            raise Exception(msg)
        cmd = "rm -f %s" % self.__syncpointProcessFile(pid)
        stdout, stderr, status = self.run_cmd(cmd)
        if status != 0:
            dlog.error("Resuming process waiting at the syncpoint failed")
            raise

    def waitingTagIsResumed(self, tag):
        """Resume all processes w/ matching tag waiting at the syncpoint."""
        cmd = "rm -f %s" % self.__syncpointTagFile(tag)
        stdout, stderr, status = self.run_cmd(cmd)
        if status != 0:
            dlog.error("Resuming process with matching tag at the syncpoint failed")
            raise

    def waitingProcessIsInjectedOthersResumed(self, pid):
        """
        Inject syncpoint file for the process with the given pid.  Resume all
        other processes (if any) waiting at the syncpoint.
        """
        fileNames = self.fileList(self.__syncpointProcessFile(pid))
        if len(fileNames) == 0:
            msg = "No syncpoint process files for PID %d" % pid
            dlog.error(msg)
            raise
        self.__injectFilesResumeOthers(fileNames)

    def waitingTagIsInjectedOthersResumed(self, tag):
        """
        Inject syncpoint file for all processes w/ the matching tag.  Resume all
        other processes (if any) waiting at the syncpoint.
        """
        fileNames = self.fileList(self.__syncpointTagFileWildcard(tag))
        self.__injectFilesResumeOthers(fileNames)

        # ----------------------------------------------------------------------------

    def __injectFilesResumeOthers(self, injectFileNames):
        """
        Write a "1" into each of the files in the list injectFileNames.  Resume
        all other processes (if any) waiting at the syncpoint.  Note that in the
        current implementation, the processes corresponding to injectFileNames are
        also resumed (see Syncpoints.py in the primitives directory), the key
        difference being that a waiting process will get a return value indicating
        that the syncpoint it was waiting on was injected.  That process can then
        take some action (e.g., raise an exception to test error handling code).
        """
        wildcard = self.__syncpointProcessFileWildcard()
        allFiles = set(self.fileList(wildcard))
        resumeFiles = allFiles - set(injectFileNames)
        if not set(injectFileNames).issubset(allFiles):
            dlog.error("%s not subset of %s" % (injectFileNames, allFiles))
            raise

        # Signal the specified files.  The syncpoint treats any byte written as a
        # signalled injection (see Syncpoints.py in the primitives directory).
        for fileName in injectFileNames:
            stdout, stderr, status = self.run_cmd("echo 1 > %s" % fileName)
            if status != 0:
                dlog.error("signalling failed")
                raise

            # Wait for the injection to be received.  NOTE: this should be removed
            # in the future since it's timing dependent.
            time.sleep(3)

        # Resume all other files.
        for fileName in resumeFiles:
            stdout, stderr, status = self.run_cmd("rm -f %s" % fileName)
            if status != 0:
                dlog.error("Resuming failed")
                raise

    def __syncpointSetFile(self):
        return SYNCPOINT_FILE_PREFIX + self.__name

    def __syncpointProcessFile(self, pid):
        return SYNCPOINT_FILE_PREFIX + "%s-%d-*" % (self.__name, pid)

    def __syncpointTagFile(self, tag):
        return SYNCPOINT_FILE_PREFIX + "%s-*-%s" % (self.__name, tag)

    def __syncpointProcessFileWildcard(self):
        return SYNCPOINT_FILE_PREFIX + "%s-*" % self.__name

    def __syncpointTagFileWildcard(self, tag):
        return SYNCPOINT_FILE_PREFIX + "%s-*-%s" % (self.__name, tag)

