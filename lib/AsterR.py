# -*- coding: utf-8 -*-
#coding:utf-8
#
# Unpublished work.
# Copyright (c) 2017 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: Trupti.Purohit@teradata.com
# Secondary Owner: Nilesh.Dhamanekar@teradata.com
#
# DESCRIPTION: Class to setup and run TeradataAsterR tests

import re
import shutil
import os
import codecs
from collections import OrderedDict

from lib.TestBase import TestBase
from lib.Dlog import dlog

#ACT DB constants
USER_BEEHIVE = 'beehive'
USER_BEEHIVE_PASSWD = 'beehive'

class AsterR(TestBase):

    def __init__(self, cfgJson, testParams=None):
        TestBase.__init__(self, cfgJson, testParams)
        self.sourceCmd = "source /home/beehive/config/asterenv.sh; "

        if 'actLoc' in self.cfgJson['common']:
            self.ACT_PATH = self.cfgJson['common']['actLoc']

        if 'nClusterLoaderLoc' in self.cfgJson['common']:
            self.LOADER_PATH = self.cfgJson['common']['nClusterLoaderLoc']

        if "sqlmrFunctionsLoc" in self.cfgJson['common']:
            self.SQLMR_FUNCTIONS_PATH=self.cfgJson['common']['sqlmrFunctionsLoc']

        if "clients" in self.cfgJson:
            self.clientDict = cfgJson['clients']
            if "RPackageLocation" in self.clientDict:
                self.ASTER_R_PATH = self.clientDict['RPackageLocation']
            if "ODBCDSN" in self.clientDict:
                self.DSN = self.clientDict['ODBCDSN']
            if 'ToolchainPath' in self.clientDict:
                self.TOOLCHAIN_PATH = self.clientDict['ToolchainPath']
            if 'RclientLocation' in self.clientDict:
                self.R_CLIENT_LOC = self.clientDict['RclientLocation']
            if 'ClientPkgLocation' in self.clientDict:
                self.CLNT_PKG_LOCATION = self.clientDict['ClientPkgLocation']
            self.DRIVER_MANAGER = "unixODBC"
            if 'DriverManager' in self.clientDict:
                self.DRIVER_MANAGER = self.clientDict['DriverManager']
            if 'RVersion' in self.clientDict:
                self.R_VERSION = self.clientDict['RVersion']

        self.RODBC_SETUP_DIR = os.path.join("odbcSetup")
        self.ODBC_TEMPLATES_DIR=os.path.join("testsrc/clients/AsterR/ODBCTemplate")

    #function to install SQLMR functions or files into the database
    #functions will be installed from location specified in sqlmrFunctionsLoc in cluster config
    #under common section
    def installSqlMRFiles(self,functionNames):
        if self.SQLMR_FUNCTIONS_PATH:
            dlog.info("Install SQLMR functions from path %s" % self.SQLMR_FUNCTIONS_PATH)
        else:
            dlog.error("sqlmrFunctionsLoc is not set in cluster config file")
            return False

        for functioname in functionNames:
            function_path = os.path.join(self.SQLMR_FUNCTIONS_PATH ,functioname)
            if not self.installSqlMR(function_path, database='beehive'):
                dlog.info('ERROR: Failed to install the function %s' % os.path.basename(function_path))
                return False
            dlog.info('Function %s installed' % function_path)
        return True

    #execute R scripts and compare results
    def execRBatchAndCompareOutputUsingRDiff(self,
                                             testName,
                                             database="beehive",
                                             dsn=None,
                                             username="beehive",
                                             password="beehive",
                                             inputRScript=None,
                                             expectedOutputFile=None,
                                             replaceRegex = False
                                            ):

        DSNname = "AsterDSN"
        #For every cluster in cluster config, create a DSN entry in odbc.ini
        #the name of DSN is in format - AsterDSN followed by queen ID to make sure its unique.
        ODBCINIFile = "%s/odbc.ini" % self.RODBC_SETUP_DIR
        currentclusterIP = self.cluster.queenNodes[0]
        DSNname = "DSN" + currentclusterIP
        clientport = 2406

        #docker deployment uses different port than default port
        if "deployment" in self.cfgJson['cluster']:
            if self.cfgJson['cluster']['deployment'].lower() == 'docker':
                dlog.info("For docker deployment use port 30002")
                clientport = '30002'

        if DSNname in open(ODBCINIFile).read():
            dlog.info("DSN for the cluster %s is already created in %s " % (currentclusterIP,ODBCINIFile))
        else:
            if self.DRIVER_MANAGER.lower() == "datadirect":
		odbcDSN = "[" + DSNname + "]\n" + "Driver=%s/stage/home/beehive/clients-linux64/stage/clients-odbc-linux64//DataDirect/lib/libAsterDriver.so\n" %(os.getcwd() + "/" + self.RODBC_SETUP_DIR) + "SERVER=%s\nDATABASE=%s\nPORT=%s\nUID=%s\nPWD=%s\nNumericAndDecimalAsDouble=1\nByteaAsVarchar=1\n\n"\
                          % (currentclusterIP, "beehive", clientport, username, password)
            else:
		odbcDSN = "[" + DSNname + "]\n" + "Driver=\"Aster Driver\"\n" + "SERVER=%s\nDATABASE=%s\nPORT=%s\nUID=%s\nPWD=%s\nNumericAndDecimalAsDouble=1\nByteaAsVarchar=1\n\n"\
                          % (currentclusterIP, "beehive", clientport, username, password)
            f  = open(ODBCINIFile, 'a')
            f.write(odbcDSN)
            f.close()
            dlog.info("Added DSN %s to odbc.ini" % odbcDSN)
        dsn = DSNname

        # Copy and edit input R script to modify DSN
        try:
            inputfilename = inputRScript.split("/")[-1]
            newInputRScript = os.path.join(self.tempSpaceDir, inputfilename)
            fp1 = open(inputRScript, 'r')
            fp1 = codecs.open(inputRScript, "r", "utf-8")
            fp2 = codecs.open(newInputRScript, "w", "utf-8")
            
            for line in fp1:
                fp2.write(line.replace("<REPLACE_DSN>", DSNname))
            fp1.close()
            fp2.close()
        except IOError, err:
            dlog.error(str(err))
        dlog.info("Successfully created new input R script %s" % newInputRScript)

        # Replace DSN and if required other regex
        replacements = {'<REPLACE_DSN>': dsn
                        }


        ignorePatterns = {
                          'r_[a-z]*\d*_\d*_\d*_\d".r_[a-z]*\d*_t__aa_[a-z]*_*[a-z]*\d*[a-z]*_*\d*':'tempschemaname.temptablename',
                          'public".r_[a-z]*\d*_t__aa_[a-z]*\d*[a-z]*_*\d*':'tempschemaname.temptablename',
                          'r_[a-z]*\d*_\d*_\d*_\d".["]*r_[a-z]*\d*_t__aa_cox_survfit\d*[a-z]*_*\d*':'tempschemaname.temptablename',
                          'r_[a-z]*\d*_\d*_\d*_\d".r_[a-z]*\d*_t__sqlmr_stdout\d*':'tempschemaname.temptablename',
                          'r_[a-z]*\d*_\d*_\d*_\d".r_[a-z]*\d*_t__aa_glm\d*[a-z]*_*\d*':'tempschemaname.temptablename',

                          # random table/view name
                          'i\d{14,16}':'i<***>',
                          'o\d{15,16}':'o<***>',
                          'sw\d{15,16}':'sw<***>',
                          'si\d{15,16}':'si<***>',
                          'nbayes\d{15,16}':'nbayes<***>',
                          'a\d{15,16}':'a<***>',
                          'r\d{15,16}':'r<***>',
                          's\d{15,16}':'s<***>',
                          # database name
                          'database\(.*?\)':'DATABASE(***)',
                          # domain name
                          'domain\(.*?\)':'DOMAIN(***)',
                          # elapsed time
                          'Training time.*':'Training time ***',
                          # first size
                          'File size.*':'File size ***',
                          # temp table name
                          '_*tmp_\d{8,10}':'_tmp_<***>',
                          '_*tmp_glmp_m\d{14,16}':'__tmp_glmp_m<***>',
                          '_*tmp_glmp_m\d{14,16}':'__tmp_glmp_m<***>',
                          '_*tmp_glmp_i\d{14,16}':'__tmp_glmp_i<***>',
                          '_*tmp_glm_o\d{14,16}':'__tmp_glm_o<***>',
                          # column name
                          '_*tmp_knn_alias\d{14,16}_\d{1}':'__tmp_knn_alias<***>',
                          # temp table/view/output table name
                          '_*tmp_knn_train\d{14,16}':'__tmp_knn_train<***>',
                          '_*tmp_knn_test\d{14,16}':'__tmp_knn_test<***>',
                          '_*tmp_knn_out\d{14,16}':'__tmp_knn_out<***>',
                          # temp function name
                          'tempFUN\d{22}':'tempFUN<***>',
                          'tempFUN\d{21}':'tempFUN<***>',
                          'tempCombinerFUN\d*':'tempCombinerFUN<***>',
                          # rscript name



                          'ta_[\d|\w]{11,12}.rscript':'ta_<***>.rscript',
                          'r__\d{4,5}_\d{16}_\d{1}':'r__<***>',
                          'r__t__txtparse_out\d{16}':'r__t__txtparse_out<***>',
                          # driver name
                          'Driver=.*Aster.*Driver.*':'Driver=\"Aster Driver\"',

                          # temporary table name (taTransferInternal.R)
                          'ta_\d{8,15}':'ta_<***>',
                          # temporary table name (ta.reify)
                          'reify_\d{8,15}':'reify_<***>',
                          '_out\d{14,16}':'_out_<***>',
                          # temporary schema name
                          'r_beehive_t__ta_cox\S*':'r_beehive_t__ta_cox',
                          'r_.*_\d*_\d*_\d*_\d*_\d*_\d*_\d*_seq\d*':'r_<***>',
                          'line [0-9]*, column b:\(.*\)':'line x, column b:y',
                          '"?r_.*_:1\d*_\d*_\d*"?':'r_<***>',
                          'r_beehive_\d*_\d*_\d*':'r_beehive_tempschema',
                          'r_beehive_t__glm_stdout\d*':'r_beehive_t__glm_stdout',
                          'r_.*_t__glm_o\d*':'r_*_t__glm_o*',
                          'r_.*_t__glm_stdout\d*':'r_*_t__glm_stdout',
                          'r_t__ta_create\d*':'r_t__ta_create',
                          'ERROR: value out of range: .*flow':'ERROR: value out of range: overflow',
                          'sparsesvmtrainer3n\d*':'sparsesvmtrainer3n*',
                          '_train0n\d*':'_train0n<***>',

                          # R not installed warning
                          'Warning message:\s+':'',
                          '(Warning )?In .ta.connection.R.installed.checkServer\(conn = taConnection, silent = FALSE\) :\s+':'',
                          '  R might not be installed in Aster Database\s+':''
                         }

        expectedOutputFileName = expectedOutputFile.split("/")[-1]
        newExpectedROutputFile = os.path.join(self.tempSpaceDir,
                                                expectedOutputFileName) + \
                                                ".expected.out"
        if shutil.copyfile(expectedOutputFile, newExpectedROutputFile):
            dlog.error("Failed to copy %s file to %s" %(expectedOutputFile,
                                                        newExpectedROutputFile))
            return False

        try:
            # Search for patterns and replace expected result
            fp1 = codecs.open(expectedOutputFile, "r", "utf-8")
            fp2 = codecs.open(newExpectedROutputFile, "w", "utf-8")
            for line in fp1:
                # replace DSN
                for key,value in replacements.iteritems():
                    line = line.replace(key, value)

                # replace random and uncertain values in result file
                    for ignorePattern, replaceSymbol in ignorePatterns.iteritems():
                        p = re.compile(ignorePattern, re.I)
                        line = p.sub(replaceSymbol, line)

                fp2.write(line)
            fp1.close()
            fp2.close()
        except IOError, err:
            dlog.error(str(err))

        generatedROutputFile = os.path.join(self.tempSpaceDir,
                                                expectedOutputFileName) + \
                                            ".generated.out.tmp"



        if os.path.exists('./.RData'):
            dlog.info('Remove .RData in current directory')
            os.remove('./.RData')
        customLib = os.path.join(self.RODBC_SETUP_DIR, "customLib")
        rPath = "%s/%s/bin/R" % (self.RODBC_SETUP_DIR, self.R_VERSION)
        if self.DRIVER_MANAGER.lower() == "datadirect":
           dlog.info('configure command parameters for DataDirect driver manager')

           LD_LIBRARY_PATH = "%s/%s/stage/home/beehive/clients-linux64/stage/clients-odbc-linux64/DataDirect/lib" % (os.getcwd(),self.RODBC_SETUP_DIR)

           ODBCSYSINI = self.RODBC_SETUP_DIR
           ODBCINI = "%s/odbc.ini" % self.RODBC_SETUP_DIR

           R_CMD = "LD_LIBRARY_PATH=%s ODBCSYSINI=%s ODBCINI=%s "\
                       % (LD_LIBRARY_PATH, ODBCSYSINI, ODBCINI) \
                    + "R_LIBS_USER=%s %s CMD " % (customLib, rPath)

        else:
            dlog.info('configure command parameters for unixODBC driver manager 2.3.1')

            PATH = "%s/unixODBC-2.3.1/bin/" % self.TOOLCHAIN_PATH
            ODBCSYSINI = self.RODBC_SETUP_DIR
            LD_LIBRARY_PATH = "%s//stage/home/beehive/clients-linux64/stage/clients-odbc-linux64/unixODBC/lib:%s/unixODBC-2.3.1/lib"\
                                  % (self.RODBC_SETUP_DIR,
                                     self.TOOLCHAIN_PATH)

            R_CMD = "PATH=%s:$PATH ODBCSYSINI=%s LD_LIBRARY_PATH=%s "\
                       % (PATH, ODBCSYSINI, LD_LIBRARY_PATH) \
                    + "R_LIBS_USER=%s %s CMD " % (customLib, rPath)



        R_SCRIPT_CMD = R_CMD + " BATCH --no-save %s %s" % (newInputRScript,
                                                    generatedROutputFile)

        # Run R script
        dlog.info("Executing command %s" % R_SCRIPT_CMD)
        status,stdout,stderr = self.execCmdLocal(R_SCRIPT_CMD)

        if status != 0:
            dlog.error("Failed to run R command %s: " % R_SCRIPT_CMD)
            dlog.error(stdout + stderr)

        if not os.path.exists(newExpectedROutputFile):
            dlog.error("File doesn't exist: %s" % newExpectedROutputFile)
            return False

        if not os.path.exists(generatedROutputFile):
            dlog.error("File doesn't exist: %s" % generatedROutputFile)
            return False

        # Search for patterns and replace actual result
        newGeneratedROutputFile = os.path.join(self.tempSpaceDir,
                                                expectedOutputFileName) +\
                                                ".generated.out"
        shutil.copyfile(generatedROutputFile, newGeneratedROutputFile)
        try:
            fp1 = codecs.open(generatedROutputFile, "r", "utf-8")
            fp2 = codecs.open(newGeneratedROutputFile, "w", "utf-8")
            for line in fp1:
                # replace DSN info
                for key,value in replacements.iteritems():
                    line = line.replace(key, value)

                # replace random and uncertain values in result file
                for ignorePattern, replaceSymbol in ignorePatterns.iteritems():
                    p = re.compile(ignorePattern, re.I)
                    line = p.sub(replaceSymbol, line)

                fp2.write(line)
            fp1.close()
            fp2.close()
        except IOError, err:
            dlog.error(str(err))

        diffFile = os.path.join(self.tempSpaceDir, expectedOutputFileName) +\
                        ".diff"
        R_DIFF = R_CMD + " Rdiff "
        rDiffCmd = R_DIFF + " %s %s > %s" % (newExpectedROutputFile,
                                             newGeneratedROutputFile,
                                             diffFile)

        dlog.info("Executing command %s" % rDiffCmd)
        status,stdout,stderr,  = self.execCmdLocal(rDiffCmd)
        if status != 0:
            dlog.error("Failed to execute command %s" % rDiffCmd)
            dlog.error(stdout+stderr)
            return False

        if int(os.stat(diffFile).st_size) == 0:
            return True
        else:
            dlog.error("Diff command generated output of size > 0 bytes")
            with open(diffFile, 'r') as f:
               dlog.info(f.read())
            return False


    #this method generates input .R script for the given template and expression file
    def testExpressions(self, templatefile, expressionfile):

      inputfilesDir = os.path.join("log", self.testParams["NAME"],"rInputScript")
      if os.path.exists(inputfilesDir):
            shutil.rmtree(inputfilesDir)
      os.makedirs(inputfilesDir)

      inputExpressionFile = os.path.join("testsrc/clients/AsterR/expression_tests/expression_files/")  + expressionfile
      if not os.path.exists(inputExpressionFile):
            dlog.error("File doesn't exist: %s" % inputExpressionFile)
            return False

      create_vdf_line=[]
      dlog.info("Test expressions from file %s" % expressionfile)
      rInputFilename = expressionfile.replace("txt","")
      idx = expressionfile.find("/")
      if  idx > 0:
            rInputFilename = expressionfile[idx+1:]
            rInputFilename = rInputFilename.replace(".txt",".R")

      idx = templatefile.find(".tmpl")
      if  idx > 0:
            nameprefix = templatefile[0:idx]
      rInputFilename = nameprefix + "_"  + rInputFilename
      rInputFilepath = os.path.join(inputfilesDir,rInputFilename)
      f3 = open(rInputFilepath , "w")

      templatefilePath = os.path.join("testsrc/clients/AsterR/expression_tests/expression_files/templates/")  + templatefile
      f1 = open("%s" % templatefilePath, "r")
      for ln in f1.readlines():
          ln = ln.strip()
          #replace REPLACE_EXP with each expression from the file
          if not ln.startswith( '#' ) and ln.find("REPLACE_EXP")>=0 :
              f4 = open("%s" % (inputExpressionFile), "r")
              for expr in f4.readlines():
                  line = ln
                  expr = expr.strip()
                  if expr:
                      #ignore comments from the file of expressions
                       if expr.find( 'TableName:' ) > 0:
                           useTableName = re.sub(".*TableName:","",expr)
                           for vdf_stmt in create_vdf_line:
                                new_vdf = vdf_stmt.replace("REPLACE_TABLENAME",useTableName)
                                f3.write(new_vdf + "\n")
                       elif not expr.startswith( '#' ):
                          line = line.replace("REPLACE_EXP",expr)
                          f3.write(line + "\n")
                       else:
                          f3.write(expr + "\n")
              f4.close()
          #replace the REPLACE_TABLENAME string with table name on which expressions are run
          elif not ln.startswith( '#' ) and ln.find("REPLACE_TABLENAME")>=0:
               create_vdf_line.append(ln)
          else:
               f3.write(ln + "\n")

      f1.close()
      f3.close()
      return rInputFilepath

    def run(self):
        "Run R test"
        status = True
        user = self.testParams.get('USER', 'beehive')
        password = self.testParams.get('PASSWORD', 'beehive')
        database = self.testParams.get('database', 'beehive')

        # Create tempSpce directory for Copying and editing input/output files
        self.tempSpaceDir = os.path.join("log", self.testParams["NAME"])
        if os.path.exists(self.tempSpaceDir):
            shutil.rmtree(self.tempSpaceDir)
            if os.path.exists(self.tempSpaceDir):
                dlog.error("Failed to delete tempSpaceDir %s"\
                                % self.tempSpaceDir)
                return False
        os.makedirs(self.tempSpaceDir)
        if not os.path.exists(self.tempSpaceDir):
            dlog.error("Failed to create tempSpaceDir %s" % self.tempSpaceDir)
            return False
        dlog.info("Successfully recreated tempSpaceDir %s" % self.tempSpaceDir)

        #run one oe more setup .sql files
        if 'SETUPSQLFILE' in self.testParams:
            setupDict = self.testParams['SETUPSQLFILE']
            for setupSqlFile in setupDict:
                username = setupSqlFile.get('USERNAME', user)
                password = setupSqlFile.get('PASSWORD', password)
                database = setupSqlFile.get('DATABASE', database)
                actparams = setupSqlFile.get('ACTPARAMS', "")
                dlog.info("Invoking SETUPSQLFILE: {}".format(setupSqlFile))
                status2, stdout = self.excSqlFile(setupSqlFile['SETUPFILELOC'], username, password,
                                                database, actparams)
                if status2 != 0:
                    dlog.error("Failed to execute sql file {}".format(setupSqlFile))
                    dlog.error(stdout)
                    return False
                else:
                    dlog.info("Successfully executed SETUPSQLFILE: %s" \
                            % setupSqlFile)


        #load data into tables.
        #user can load data from same file into multiple tables. Especially for viper tests

        if 'LOADDATA' in self.testParams:
            loadDataDict = self.testParams['LOADDATA']
            dlog.info("Started loading data")
            for load in loadDataDict:
                username = load.get('USERNAME', 'beehive')
                password = load.get('PASSWORD', 'beehive')
                database = load.get('DATABASE', 'beehive')
                loadParams = load.get('LOADERPARAMS', None)
                loadtables = load['TABLENAME']
                for tablename in loadtables:
                    status2 =  self.loadDataFile(load['LOADFILELOC'], tablename,
                                  username, password, database, loadParams)
                    if not status2:
                        dlog.error("Failed to load data with these params: %s" %load)
                        return False

        #check if SQLMR function needs to be installed
        if 'INSTALLSQLMR' in self.testParams:
            if 'REMOVESQLMR' in self.testParams:
                functionlist = self.testParams['REMOVESQLMR']
            else:
                functionlist = self.testParams['INSTALLSQLMR']

            #remove old installation of function
            for functioname in functionlist:
                #check if its a file of type say - textParserFiles/text_parser_stop_words.txt
                #in that case consider only the file name
                idx = functioname.find("/")
                if  idx > 0:
                    functioname = functioname[idx+1:]
                if not self.removeSqlMR("public/" + functioname,user="db_superuser", password = "db_superuser"):
                    dlog.info('ERROR: Failed to remove the function %s' % functioname)
                    return False
                else:
                    dlog.info('Function %s removed public/' % functioname)

            status  = self.installSqlMRFiles(self.testParams['INSTALLSQLMR'])
            if not status:
                return False

        #if the TYPE is AstetR, execute the scripts using R console
        if self.testParams['TYPE']=="AsterR":
            if 'USER' in self.testParams:
                    username = self.testParams['USER']
            else:
                dlog.info('USER is not defined in the input file! Using the default beehive user')
                username = USER_BEEHIVE

                password = None
            if 'PASSWORD' in self.testParams:
                password = self.testParams['PASSWORD']
            else:
                dlog.info('PASSWORD is not defined in the input file! Using the default beehive password')
                password = USER_BEEHIVE_PASSWD

            if 'INPUTRSCRIPT' in self.testParams:
                inputRScript = self.testParams['INPUTRSCRIPT']

                if 'EXPECTEDOUTFILE' in self.testParams:
                    expectedOutFile = self.testParams['EXPECTEDOUTFILE']
                else:
                    dlog.error("Expected output file is not specified")
                    return False

                database = "beehive"
                dsn = "AsterDSN"
                replaceRegex = self.testParams.get("REPLACEREGEX", False)
                status =  self.execRBatchAndCompareOutputUsingRDiff(self.testParams["NAME"], database,
                                                         dsn, username,password,
                                                         inputRScript,
                                                         expectedOutFile,
                                                         replaceRegex)
                if not status:
                    dlog.error("Test failed")


            elif "EXPRESSIONFILE" in self.testParams:
                expressionfile = self.testParams['EXPRESSIONFILE']

                if "TEMPLATE" in self.testParams:
                    templatefile = self.testParams['TEMPLATE']
                else:
                    dlog.error("template file is not specified.")
                    return False

                if 'EXPECTEDOUTFILE' in self.testParams:
                    expectedOutFile = self.testParams['EXPECTEDOUTFILE']
                else:
                    dlog.error("Expected output file is not specified")
                    return False

                inputRScript = self.testExpressions(templatefile,expressionfile)

                database = "beehive"
                dsn = "AsterDSN"
                replaceRegex = self.testParams.get("REPLACEREGEX", False)

                status =  self.execRBatchAndCompareOutputUsingRDiff(self.testParams["NAME"], database,
                                                         dsn, username,password,
                                                         inputRScript,
                                                         expectedOutFile,
                                                         replaceRegex)
                if not status:
                    dlog.error("Test failed : " + inputRScript)

        #check if SQLMR function needs to be removed
        if 'REMOVESQLMR' in self.testParams:
            functionlist = self.testParams['REMOVESQLMR']
            for functioname in functionlist:
                if not self.removeSqlMR(functioname):
                    dlog.info('ERROR: Failed to remove the function %s' % functioname)
                    return False
                else:
                    dlog.info('Function %s removed' % functioname)


        #clean up the tables
        if 'CLEANUPSQLFILE' in self.testParams:
            setupDict = self.testParams['CLEANUPSQLFILE']

            for cleanupSqlFile in setupDict:
                username = cleanupSqlFile.get('USERNAME', user)
                password = cleanupSqlFile.get('PASSWORD', password)
                database = cleanupSqlFile.get('DATABASE', database)
                actparams = cleanupSqlFile.get('ACTPARAMS', "")
                dlog.info("Invoking CLEANUPSQLFILE: {}".format(cleanupSqlFile))
                status2, stdout = self.excSqlFile(cleanupSqlFile['CLEANUPFILELOC'], username, password,
                                                database, actparams)
                if status2 != 0:
                    dlog.error("Failed to execute sql file {}".format(cleanupSqlFile))
                    dlog.error(stdout)
                    return False
                else:
                    dlog.info(stdout)
        return status
