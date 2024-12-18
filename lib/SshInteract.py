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
# DESCRIPTION: SshInteract Class to establish an SSH interactive session to the host

import sys
import re
import time

class SshInteract:

    def __init__(self, client, timeout=60, newline='\r', buffer_size=1024,
                 display=False):
 
        self.channel = client.invoke_shell()
        self.newline = newline
        self.buffer_size = buffer_size
        self.display = display
        self.timeout = timeout
        self.current_output = ''
        self.current_output_clean = ''
        self.current_send_string = ''
        self.last_match = ''
        self.unsed_output = ''

    def __del__(self):
        self.close()

    def close(self):
        """Attempts to close the channel for clean completion."""
        try:
            self.channel.close()
        except:
            pass

    def flush(self):
        count = 0
        while ( count < 100 ):
            if self.channel.recv_ready():
                # Read some of the output
                buffer = self.channel.recv(self.buffer_size)
                if len(buffer) == 0:
                    break
            count += 1
        self.unsed_output = ''
        
    def expect(self, re_strings='', timeout=None):
    

        # Set the channel timeout
        timeout = timeout if timeout else self.timeout
        self.channel.settimeout(timeout)

        # Create an empty output buffer
        self.current_output = ''

        readoutput = self.unsed_output

        if len(re_strings) != 0 and isinstance(re_strings, str):
            re_strings = [re_strings]

        foundIndex = -1
        found = False
        timer = 0
        while ( timer <= timeout ) and not found:
            if self.channel.recv_ready():
                # Read some of the output
                buffer = self.channel.recv(self.buffer_size)
                if len(buffer) == 0:
                    break
                buffer = buffer.replace('\r', '')
                if self.display:
                    sys.stdout.write(buffer)
                    sys.stdout.flush()
                readoutput += buffer
                
                for re_index, re_string in enumerate(re_strings):
                    match = re.search(re_string, readoutput)
                    if match:
                        foundIndex = re_index
                        found = True
                        self.current_output = readoutput[:match.end()]
                        self.unsed_output = readoutput[match.end():]
                        self.last_match = match.group(0)
                        break
            time.sleep(0.5)
            timer = timer + 0.5
        if found:
            return foundIndex, self.current_output
        else:
            print('Timeout occurred waiting for the expected String!')
            return -1, ''

    def send(self, send_string):
        """Saves and sends the send string provided"""
        self.current_send_string = send_string
        self.channel.send(send_string + self.newline)
