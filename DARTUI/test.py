from flask import Flask, render_template, jsonify, request
from flask_restful import Resource, Api
from DatabaseConnection import *
import subprocess,psycopg2
import os, sys, time, json, datetime, traceback
from subprocess import check_output
from DartexeHistory import *
from DartexeLogger import DartexeLogger
from flask import send_from_directory

app = Flask(__name__)
api = Api(app)

HTTP_STATUS_OK = 200
HTTP_STATUS_INTERNAL_ERROR = 500
HTTP_STATUS_PAGE_NOT_FOUND = 404

#app.config['UPLOAD_FOLDER'] = '/root/DARTUI/logs/'

logger = None
DartexeLogger.setLogger("logs/dartexe_service.log", "debug", "DartexeService")
logger = DartexeLogger.getLogger("DartexeService")

#@app.route('/file/<filename>')
#def getLogContent(filename):
#    msg = ""
#    httpCode = None
#    content = ""
#    try:
#        with open(app.config['UPLOAD_FOLDER'] + filename, "r") as f:
#            while True:
#                line = f.readline()
#                if not line:
#                    break
#
#                content = content + line + "</br>"
#
#        msg = "Read Log Successfully"
#        httpCode = HTTP_STATUS_OK
#    except:
#        print sys.exc_info()
#        print traceback.format_exc(sys.exc_info()[2])
#        logger.error(sys.exc_info())
#        logger.error(traceback.format_exc(sys.exc_info()[2]))
#        msg = "Something wrong"
#        httpCode = HTTP_STATUS_INTERNAL_ERROR
#
#    return jsonify({"msg": msg, "content": content}), httpCode
#
#@app.route('/download/<filename>')
#def downloadLogFile(filename):
#    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/')
def dui():
    logger.info("#_____________________________Application Launched_____________________________#")
    logger.info("Home page Rendered")
    return render_template("test.html")

@app.route('/help')
def help():
    logger.info("Help Page Opened")
    return render_template("help.html")

@app.route('/history')
def history_page():
    logger.info("Hisoty Page Opened")
    return render_template("history.html")

@app.route('/UserId', methods=['POST', 'GET'])
def UserId():
    data = request.get_json()
    user = data['user']
    logger.info("User is : %s" %user)
    return jsonify(user)

@app.route('/history_command', methods=['POST', 'GET'])
def HistoryCommand():
    data = request.get_json()
    print (data)
    command = data['command']
    print (command)
    return jsonify(data)


@app.route('/cmd', methods=['POST', 'GET'])
def cmd():
    text = request.get_json()
    text= json.loads(request.get_data())
    logger.info("Command Generated is : %s" %text)
    path = '/root/Dart/'
    os.chdir( path )
    process = subprocess.Popen(text['command'], shell=True, stdout=subprocess.PIPE)
    processId = process.pid + 1;
    logger.info("process id is:%s" %processId)
    return jsonify({"processId": processId})
    
def execCmdLocal(cmd):
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True )        
    stdout, stderr = proc.communicate()
    status = proc.poll()
    if status != 0:
         print("Failed to execute command %s" % cmd)
    return status, stdout

@app.route('/runid', methods=['GET','POST'])
def runid():
    command = request.args.get('command')
    print ("command is %s"%command)
    user = request.args.get('user')
    processId = request.args.get('processid')
    processId = int(processId)
    print type(processId)
    logger.info("My Process id is : %s" %processId)
    time.sleep(20)
    cmdStr = 'cd /root/Dart/log; ls -rt DartRunner*.log | tail -5'
    ret = execCmdLocal(cmdStr)
    logNames = ret[1].split()
    print logNames
    logger.info("Listed Lognames are : %s" %logNames)
    for log in logNames:
        print ("Greping from logname: %s" %log)
        logger.info("Greping from logname: %s" %log)
        grep = "cd /root/Dart/log;ls -rt DartRunner*.log | tail -5;grep -i 'Process Id' *"+log
        logger.info("this is grep command that is to be executed: %s" %grep)
        print ("this is grep command that is to be executed:",grep)
        ret1 = execCmdLocal(grep)
        x = ret1[1][-6:]
        DartProcessId = x[:-1]
        DartProcessid = int(DartProcessId)
        if (DartProcessid == processId):
            print("Matched pid is : %s" %processId)
            logger.info("Matched pid is : %s" %processId)
            logger.info("Final Log for fetching RunId is : %s" %log)
            runId = ""
            print('The DartRunner Log generated is: %s'%log)
            with open('/root/Dart/log/' + log, "r") as fd:
                for line in fd:
                    if 'runId' in line:
                        runId = line.split()[-1]
                        runId = runId.strip()
                        print('Run Id: %s'%runId)
                        logger.info('Run Id: %s'%runId)
                    elif 'run' in line:
                        runId = line.split('=')[-1]
                        runId = runId.strip()
                        print('Run Id:%s'%runId)
                        logger.info('Run Id: %s'%runId)
                        break  
                     
        else:
            print("Process Ids Does not match")
            logger.info("Process Ids Does not match")
            print DartProcessid
            print processId
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")    
    post_history(user, runId, timestamp, command)
    return jsonify({"run_id": runId})

@app.route('/testset', methods=['GET','POST'])
def testset():
    path = request.args.get('path')
    print "path = ", path
    logger.info('Path to select the Testset is: %s'%path)
    #path='/root/Dart/testset/pipelining/main/REG/'
    tests = os.listdir(path)
    test_files={}
    testfiles_list=[]
    for file in tests:
        if not file.endswith('.est'):

            testfiles_list.append(file)
    test_files['test'] = testfiles_list
    return jsonify(test_files)

@app.route('/clusters', methods=['GET','POST'])
def clusters():
    path = request.args.get('path')
    print "path = ", path
    logger.info('Path to select the Clusters is: %s'%path)
    clusters = os.listdir(path)
    cluster_set={}
    cluster_sets=[]
    for file in clusters:
        if file.endswith('.cfg'):
           file = file[:-4]
        cluster_sets.append(file)
    cluster_set['cluster'] = cluster_sets
    return jsonify(cluster_set)

@app.route('/install', methods=['GET','POST'])
def InstallTests():
    path = "/root/Dart/testset/"
    print "path = ", path
    logger.info('Path to select the InstallTest is: %s'%path)
    install = os.listdir(path)
    install_test={}
    install_tests=[]
    for file in install:
        if file.endswith('.est'):
            install_tests.append(file)
    install_test['install'] = install_tests
    return jsonify(install_test)

@app.route('/data', methods=['GET','POST'])
def data():
    data=HealthCheck()
    return jsonify(data)

@app.route('/conn_history', methods=['GET','POST'])
def HistoryData():
    historyGetter = DartexeHistory()
    historyData = historyGetter.main(request)
    return jsonify(historyData)

@app.route('/delete_history', methods=['DELETE'])
def DeleteHistory():
    data = request.get_json()
    runIds = data['ids']
    print (runIds)
    logger.info('Runids that are selected to be deleted are: %s'%runIds)
    delete(runIds)
    return jsonify(runIds)

@app.route('/gitpull', methods=['GET'])
def GitPull():
    path = '/root/Dart/'
    os.chdir( path )
    process = subprocess.Popen("git pull", shell=True)
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M")
    post_gittime(timestamp)
    return jsonify(timestamp)

@app.route('/postgitpulltime', methods=['GET'])
def PostGitPull():
    timestamp = get_gittime()
    print timestamp
    return jsonify(timestamp)



if __name__ == '__main__': 
  app.run(host='0.0.0.0', port=8080)
