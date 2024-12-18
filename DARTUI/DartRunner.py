from flask import Flask, render_template, request
from flask_restful import Resource, Api
import subprocess,psycopg2,wtforms,sqlalchemy

app = Flask(__name__)
api = Api(app)


@app.route('/')
def dui():
    return render_template("DartRunner.html")

@app.route('/cmd', methods=['POST', 'GET'])
def cmd():
    text = request.get_data()
    print(text)
    subprocess.Popen(text, shell=True)
    return text

class Process(Resource):
    def get(self, name):
        return {'process': name}


api.add_resource(Process, '/submit/process/<string:name>')


if __name__ == '__main__':
    app.run()





















#@app.route("/cmd")
#def cmd():
   # # osname = os.uname()[3]
   # # print(osname)
   # # return dumps({'name': osname})
   # subprocess.Popen('nohup ls -l &', shell=True)
   # for i in range(10):
   #  print(random.randint(0, 100))
   # time.sleep(30)
   #print request.args
