#!/usr/bin/python
#
# Unpublished work.
# Copyright (c) 2017 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Primary Owner: rohit.khurd@teradata.com
# Secondary Owner: 
#
# Description: Utility to be used by all to format their JSON test/config files,
#              while maintaining a standard for the same
#
# Note: This utility does not handle json tst files with comments.
#

import json
import os
import time
import sys, traceback
import shutil
from collections import OrderedDict
from optparse import OptionParser

USAGE='''TestFileFormatter.py -f inputFile [ -i | -t outputFile [ -d outputDir ] ]

      Usage Examples:
      * To overwrite input file's contents with formatted content
        $ TestFileFormatter.py -f sample.tst -i
      * To create a new file with formatted content
        Output directory would be '/tmp' since it is not specified
        Output filename will be the same as the input file name
        $ TestFileFormatter.py -f sample.tst
      * To create a new file with formatted content specifying a name
        Output directory would be '/tmp' since it is not specified
        $ TestFileFormatter.py -f sample.tst -t formatted.tst
      * Same as above but with a output directory to write the file to
        $ TestFileFormatter.py -f sample.tst -t formatted.tst -d "/root"
      * To see the help message
        $ TestFileFormatter.py -h
      Note: -i is used to replace the original input file's content with the formatted output
      '''


class TestFileFormatter(object):

   def __init__(self, inFile, outFile):
      '''
      Initialize the TestFileFormatter with in and out files
      '''
      self.infile_ = inFile
      self.outfile_ = None
      if inFile != outFile:
         self.outfile_ = outFile


   def formatFile(self):
      '''
      Create the (possibly temporary) file with formatted content
      '''
      tmpFile = self.outfile_
      if self.outfile_ is None:
         tmpFile = os.path.join('/tmp',
                                 'tff' + str(time.time()))

      # read input file
      ip = open(self.infile_)
      try:
         data = json.load(ip, object_pairs_hook=OrderedDict)
      except ValueError as e:
         sys.stderr.write('ERROR: Input File has invalid JSON: %s\n' % e)
         sys.stderr.write("Please remove C-Style comments or comments starting with a '#' , if there are any, before using this script.\n")
         sys.exit(2)
      finally:
         ip.close()

      # write to output file
      op = open(tmpFile, 'w')
      op.write("# This file has been formatted by %s\n" % os.path.basename(__file__))
      op.close()
      op = open(tmpFile, 'a')
      json.dump(data, op, indent=3, separators=(',', ': '), sort_keys=False)
      op.close()

      print 'Formatted content generated'
      if self.outfile_ is None:
         print 'Output File: %s' % self.infile_
         self.replaceFile(tmpFile)
      else:
         print 'Output File: %s' % self.outfile_
      print 'Formatted content successfully written to file'


   # called only for in-place format
   def replaceFile(self, tmpFile):
      shutil.move(tmpFile, self.infile_)


if __name__ == "__main__":

   def printUsage():
      print(USAGE)

   try:
      parser = OptionParser(usage = USAGE)
      parser.add_option('-f',
                        '--inputFile',
                        dest="inputFile",
                        default=None,
                        help='Test file to format, Example - sample.tst')
      parser.add_option('-t',
                        '--outputFile',
                        dest="outputFile",
                        default=None,
                        help='Name of file to write formatted output to')
      parser.add_option('-i',
                        '--inPlace',
                        dest="inPlace",
                        default=False,
                        action='store_true',
                        help='Overwrite input file with formatted output')
      parser.add_option('-d',
                        '--outputDir',
                        dest="outputDir",
                        default='/tmp',
                        help='Directory to write output file to')

      (options, args) = parser.parse_args(sys.argv[1:])

      if options.inputFile is None or \
         not os.path.isfile(options.inputFile):
         sys.stderr.write('ERROR: Input file not accessible or not provided (-f/--inputFile)\n')
         sys.exit(1)

      print 'Input File: %s' % options.inputFile

      if options.inPlace:
         tff = TestFileFormatter(options.inputFile, None)
      else:
         tmpOutFile = os.path.basename(options.inputFile)
         if options.outputFile is not None:
            tmpOutFile = options.outputFile

         if not os.path.isdir(options.outputDir):
            sys.stderr.write('ERROR: Output directory does not exist: %s\n' % options.outputDir)
            sys.exit(1)

         outputFile = os.path.join(options.outputDir, tmpOutFile)
         tff = TestFileFormatter(options.inputFile, outputFile)

      tff.formatFile()
   except Exception as e:
      print sys.exc_info()
      print traceback.format_exc(sys.exc_info()[2])
      print('ERROR: ' + str(e))
      printUsage()
      sys.exit(2)

