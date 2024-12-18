#! /bin/bash
#add following command to crontab
#*/10 * * * * /bin/bash /home/beehive/DartWebService/monitor.sh

ret=$(ps auxw | grep DartWebService.py | grep -v grep)

if [[ -z "$ret" ]]; then
    /usr/bin/python /root/DartWebService/DartWebService.py
fi
