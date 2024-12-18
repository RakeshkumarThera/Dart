# author: Saif ali Karedia

from project import create_app

config_name = 'development' # specify the environment here
application = create_app(config_name)


if __name__ == "__main__":
    application.run(host='0.0.0.0', threaded=True)
