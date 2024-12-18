#
# Unpublished work.
# Copyright (c) 2011-2012 by Teradata Corporation. All rights reserved.
# TERADATA CORPORATION CONFIDENTIAL AND TRADE SECRET
#
# Copyright (c) 2005-2011 Aster Data Systems, Inc. All Rights Reserved.
# For more information, please see COPYRIGHT in the top-level directory.
#
# Primary Owner: alen.cheng@teradata.com
# Secondary Owner:
#
# DESCRIPTION: DartWebService use python Flask module to implement a web
#              service

import json
import os
import sys, traceback

import psycopg2
from flask import Flask, jsonify, request
from flask import render_template
from flask import send_from_directory

import DartException
from DartDBHandler import DartDBHandler
from DartWebLogger import DartWebLogger
from DartTestSummaryReporter import DartTestSummaryReporter
from DartTestResultsDetail import DartTestResultsDetail
from DartDataTransform import DartDataTransform
from DartDashboard import DartDashboard

app = Flask(__name__)
app.debug = True

app.config['UPLOAD_FOLDER'] = '/root/DartLogs/'


HTTP_STATUS_OK = 200
HTTP_STATUS_INTERNAL_ERROR = 500
HTTP_STATUS_PAGE_NOT_FOUND = 404


dartdbHostname = "127.0.0.1"
dartdbName = "dartdb"
dartdbUser = "dart"
dartdbPassword = "aster4data"

testlinkdbHostname = "127.0.0.1"
testlinkdbName = "testlinkdb"
testlinkdbUser = "testlink"
testlinkdbPassword = "aster4data"

logger = None
DartWebLogger.setLogger("./dart_web_service.log", "debug", "DartWebService")
logger = DartWebLogger.getLogger("DartWebService")


@app.route('/file/<filename>')
def getLogContent(filename):
    msg = ""
    httpCode = None
    content = ""
    try:
        with open(app.config['UPLOAD_FOLDER'] + filename, "r") as f:
            while True:
                line = f.readline()
                if not line:
                    break

                content = content + line + "</br>"

        msg = "Read Log Successfully"
        httpCode = HTTP_STATUS_OK
    except:
        print sys.exc_info()
        print traceback.format_exc(sys.exc_info()[2])
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR

    return jsonify({"msg": msg, "content": content}), httpCode
    

@app.route('/download/<filename>')
def downloadLogFile(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/admin', methods=['GET'])
def renderAdmin():
    return render_template('admin.html')


@app.route('/tagBottom', methods=['GET'])
def renderTagBottom():
    return render_template('dashboard.html')


@app.route('/tagNav', methods=['GET'])
def renderTagNav():
    return render_template('navMain.html')


@app.route('/tag', methods=['GET'])
def renderTag():
    return render_template('tag.html')


@app.route('/index', methods=['GET'])
def renderIndex():
    return render_template('index.html')


@app.route('/failTestNav', methods=['GET'])
def renderFailTestNav():
    return render_template('failTestNav.html')


@app.route('/failTestBottom', methods=['GET'])
def renderFailTestBottom():
    return render_template('failTestBottom.html')


@app.route('/failTestByOwner', methods=['GET'])
def renderFailTestByOwner():
    return render_template('failTestByOwner.html')


@app.route('/failTest', methods=['GET'])
def renderFailTest():
    return render_template('failTest.html')


@app.route('/failSummaryNav', methods=['GET'])
def renderFailSummaryNav():
    return render_template('failSummaryNav.html')


@app.route('/failSummaryBottom', methods=['GET'])
def renderFailSummaryBottom():
    return render_template('failSummaryBottom.html')


@app.route('/failSummaryReport', methods=['GET'])
def renderFailSummaryReport():
    return render_template('failSummaryReport.html')


@app.route('/deleteTestRun', methods=['GET'])
def renderDeleteRun():
    return render_template('deleteTestRun.html')


@app.route('/summaryDetail', methods=['GET'])
def renderSummaryDetail():
    return render_template('summaryDetail.html')


@app.route('/summaryReport', methods=['GET'])
def renderSummaryReport():
    return render_template('summaryReport.html')


@app.route('/groupByTestset', methods=['GET'])
def renderGroupByTestset():
    return render_template('groupByTestset.html')


@app.route('/testsetReport', methods=['GET'])
def renderTestsetReport():
    return render_template('testsetReport.html')


@app.route('/navTestset', methods=['GET'])
def renderNavTestset():
    return render_template('navTestset.html')


@app.route('/file/log', methods=['GET'])
def showLogFile():
    return render_template('log.html')


@app.route('/utility.js', methods=['GET'])
def renderUtility():
    return render_template('utility.js')


@app.route('/report/history', methods=['GET'])
def renderHistory():
    return render_template('history.html')


@app.route('/report/cluster', methods=['GET'])
def renderReportCluster():
    return render_template('cluster.html')


@app.route('/report/testByCluster', methods=['GET'])
def renderTestByCluster():
    return render_template('testByCluster.html')


@app.route('/', methods=['GET'])
def renderMain():
    return render_template('main.html')


@app.route('/navMain', methods=['GET'])
def renderNavMain():
    return render_template('navMain.html')


@app.route('/dashboard', methods=['GET'])
def renderDashboard():
    return render_template('dashboard.html')


@app.route('/report/test', methods=['GET'])
def renderReportTest():
    return render_template('test.html')


@app.route('/navBar', methods=['GET'])
def renderNavBar():
    return render_template('navBar.html')


@app.route('/testInfo', methods=['GET'])
def renderTestInfo():
    return render_template('testInfo.html')


@app.route('/report', methods=['GET'])
def renderReport():
    return render_template('report.html')

@app.route('/compareResult', methods=['GET'])
def renderCompareResult():
    return render_template('compareResult.html')

@app.route('/api/transform_data', methods=['GET'])
def transformData():
    msg =""
    httpCode = None
    res = {}

    try:
        runidArr = request.args.get('run_id')
        d = DartDataTransform(runidArr)
        res = d.main()
        msg = 'Get run_id successfully'
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR

    return jsonify({"msg" : msg,"results": res}), httpCode


@app.route('/api/dashboard', methods=['GET'])
def createDashboard():
    httpCode = ""
    data = {}
    try:
        handler = getDBHandler("dartdb")
        d = DartDashboard(handler)
        data = d.main(request)
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        httpCode = HTTP_STATUS_INTERNAL_ERROR

    return jsonify(data), httpCode

    
@app.route('/api/summary_report', methods=['GET'])
def testSummaryReport():
    msg = ""
    httpCode = None
    results = {}
    handler = None
    try:
        releaseName = request.args.get('release_name')
        handler = getDBHandler(request.args.get('dbname'))
        d = DartTestSummaryReporter(handler)
        results = d.getTestResultsSummary(releaseName)

        msg = "Get Summary Report Successfully"
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    finally:
        del handler

    return jsonify({"msg": msg, "results": results}), httpCode


@app.route('/api/summary_detail', methods=['GET'])
def testSummaryDetail():
    msg = ""
    httpCode = None
    results = {}
    handler = None
    try:
        releaseName = request.args.get('release_name')
        handler = getDBHandler(request.args.get('dbname'))
        d = DartTestResultsDetail(handler)
        results = d.getTestResultsDetail(releaseName)

        msg = "Get Summary Report Successfully"
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    finally:
        del handler

    return jsonify({"msg": msg, "results": results}), httpCode


@app.route('/api/insert_row', methods=['POST'])
def insertRow():
    postBody = json.loads(request.get_data())

    msg = ""
    httpCode = None
    handler = None
    rowid = ""
    try:
        handler = getDBHandler(postBody['dbname'])
        rowid = handler.insert(postBody['table'], postBody['column'])

        msg = "Insert Row Successfully"
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    finally:
        del handler

    return jsonify({"msg": msg, 'id': rowid}), httpCode


@app.route('/api/update_row', methods=['POST'])
def updateRow():
    postBody = json.loads(request.get_data())

    msg = ""
    httpCode = None
    handler = None
    try:
        handler = getDBHandler(postBody['dbname'])
        print postBody['updating_column']
        handler.update(postBody['table'], postBody['updating_column'], postBody['condition'])

        msg = "Update Row Successfully"
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    finally:
        del handler

    return jsonify({"msg": msg}), httpCode

@app.route('/api/delete_row', methods=['DELETE'])
def deleteRow():
    msg = ""
    httpCode = None
    handler = None
    try:
        dbName = request.args.get('dbname')
        table = request.args.get('table')
        parameter = request.args.get('condition')

        handler = getDBHandler(dbName)
        handler.delete(table, parameter)
        
        msg = "Delete Row Successfully"
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    finally:
        del handler

    return jsonify({"msg": msg}), httpCode
    


@app.route('/api/select_rows', methods=['GET'])
def selectRows():
    msg = ""
    httpCode = None
    results = {}
    handler = None
    try:
        dbName = request.args.get('dbname')
        table = request.args.get('table')
        condition = request.args.get('condition')
        columns = request.args.get('columns')
        command = request.args.get('command')

        handler = getDBHandler(dbName)
        results = handler.select(table, condition, columns, command)

        msg = "Select Data Successfully"
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg 
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        print sys.exc_info()
        print traceback.format_exc(sys.exc_info()[2])
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    finally:
        del handler

    return jsonify({"msg": msg, "results": results}), httpCode


@app.route('/api/select_sequence', methods=['GET'])
def selectSequence():
    msg = ""
    httpCode = None
    sequence = 0
    handler = None
    try:
        dbName = request.args.get('dbname')
        table = request.args.get('table')

        handler = getDBHandler(dbName)
        sequence = handler.selectSequence(table)

        msg = "Select Data Successfully"
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    finally:
        del handler

    return jsonify({"msg": msg, "sequence": str(sequence)}), httpCode


@app.route('/api/select_date', methods=['GET'])
def selectDate():
    msg = ""
    httpCode = None
    date = ""
    handler = None
    try:
        dbName = request.args.get('dbname')

        handler = getDBHandler(dbName)
        date = handler.selectDate()

        msg = "Select Data Successfully"
        httpCode = HTTP_STATUS_OK
    except DartException.DartParameterException, e:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = e.msg
        httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except psycopg2.Error:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Database operation error"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR
    finally:
        del handler

    return jsonify({"msg": msg, "date": str(date)}), httpCode


@app.route('/api/upload_log', methods=['PUT'])
def uploadLog():
    msg = ""
    httpCode = None
    try:
        fileInfo = request.files['file']

        if fileInfo:
            fileInfo.save(os.path.join(app.config['UPLOAD_FOLDER'], fileInfo.filename))

            msg = "Upload log Successfully"
            httpCode = HTTP_STATUS_OK
        else:
            msg = "Upload log Fail"
            httpCode = HTTP_STATUS_PAGE_NOT_FOUND
    except:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        msg = "Something wrong"
        httpCode = HTTP_STATUS_INTERNAL_ERROR

    return jsonify({"msg": msg}), httpCode


def getDBHandler(dbName):
    if dbName == 'dartdb':
        return DartDBHandler(dartdbHostname, dartdbName, dartdbUser, dartdbPassword)
    else:
        return DartDBHandler(testlinkdbHostname, testlinkdbName, testlinkdbUser, testlinkdbPassword)


if __name__ == '__main__':

    try:
        pid = os.fork()
        if pid > 0:
            sys.exit(0)
        else:
            app.run(host="0.0.0.0", port=8083, threaded=True)
    except OSError:
        logger.error(sys.exc_info())
        logger.error(traceback.format_exc(sys.exc_info()[2]))
        sys.exit(-1)
