#!/usr/bin/python
#
# Unpublished work.
# Copyright (c) 2016 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: adam.hsu@teradata.com
# Secondary Owner:
#
# Description: ssh to queen and then create an act shell or terminal

from lib.Dlog import dlog

class ActShellOnQueen(object):
    def __init__(self, testInstance, user, password, database, actParams):
        self.testInstance = testInstance
        self.user = user
        self.password = password
        self.database = database
        self.actParams = actParams
        self.queenInteract = None
        self.prompt = '(]| )#'
        self.actPrompt = '{DATABASE}=>'.format(DATABASE=database)

    def openShellOK(self):
        # Open a Queen interactive session
        self.queenInteract = self.testInstance.openQueenContainerInteract(timeout=60, display=False)

        # Flush the output to start with a clean plate
        self.queenInteract.flush()
        commandStr = ''
        self.queenInteract.send(commandStr)
        index, out = self.queenInteract.expect(self.prompt, timeout=30)
        dlog.info(out)

        commandStr = '/home/beehive/clients/act -U %s -w %s -d %s %s' % \
                     (self.user, self.password, self.database, self.actParams)
        self.queenInteract.send(commandStr)
        index, out = self.queenInteract.expect(self.actPrompt, timeout=30)
        dlog.info(out)
        if not index == 0:
            dlog.info('Unable to connect to act!')
            return False
        else:
            return True

    def getCommandResults(self, commandStr):
        self.queenInteract.send(commandStr)
        index, out = self.queenInteract.expect(self.actPrompt, timeout=30)
        dlog.info(out)
        return out

    def partiallyCompareCommandResultsWithExpected(self, commandStr, expectedList):
        self.queenInteract.send(commandStr)
        index, out = self.queenInteract.expect(self.actPrompt, timeout=30)

        # Convert the actual output to a str list and then compare it with the expected str list.
        # Each item in the list is stripped. For example:
        #
        ## show enable_setrole_in_transaction;
        ## enable_setrole_in_transaction
        ##-------------------------------
        ## off
        ##(1 row)
        #
        # =>
        #
        ##['show enable_setrole_in_transaction;', 'enable_setrole_in_transaction', '-------------------------------', 'off', '(1 row)']

        actualList = []
        for x in out.split('\n'):
            if x == '':
                continue  # Ignore ''
            actualList.append(x.strip())

        # This step is to check order also. For example:
        #
        # actualList = 'show enable_setrole_in_transaction;', 'enable_setrole_in_transaction', '-------------------------------', 'off', '(1 row)']
        #         expectedList = ['off', '-------------------------------']
        # =>
        # simplifiedActualList = ['-------------------------------', 'off']
        #
        # Then we know the order is wrong by comparing expectedList and simplifiedActualList
        simplifiedActualList = []
        for x in actualList:
            if x in expectedList:
                simplifiedActualList.append(x)

        dlog.info('ORIGINAL ACTUAL OUTPUT => \n{ACTUAL}'.format(ACTUAL=out))
        dlog.info('ACTUAL OUTPUT LIST => {CONVERTED}'.format(CONVERTED=simplifiedActualList))
        dlog.info('EXPECTED OUTPUT LIST => {EXPECTED}'.format(EXPECTED=expectedList))

        if expectedList == simplifiedActualList:
            dlog.info('All expected items exist in ACTUAL OUTPUT LIST and the order in ACTUAL OUTPUT LIST is as expected')
            return True
        else:
            dlog.info('ERROR: At least one expected item does not exist in ACTUAL OUTPUT LIST or the order in ACTUAL OUTPUT LIST is not as expected')
            return False

    def openShellOKforQueendbContainer(self):
        # Open a Queen interactive session

        self.queenInteract = self.testInstance.openQueenContainerInteract(timeout=60, display=False)
        # Flush the output to start with a clean plate
        self.queenInteract.flush()
        commandStr = ''
        self.queenInteract.send(commandStr)
        index, out = self.queenInteract.expect(self.prompt, timeout=30)
        dlog.info(out)

        commandStr = '/home/beehive/clients/act -U %s -w %s -d %s %s' % \
                            (self.user, self.password, self.database, self.actParams)
        self.queenInteract.send(commandStr)
        index, out = self.queenInteract.expect(self.actPrompt, timeout=30)
        dlog.info(out)

        if not index == 0:
            dlog.info('Unable to connect to act!')
            return False
        else:
            return True