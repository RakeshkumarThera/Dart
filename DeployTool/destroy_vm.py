import sys
import traceback

import argparse
import atexit
import requests
import netrc

from pyVmomi import vim
from pyVmomi import vmodl
from pyVim.connect import SmartConnect, Disconnect
from database_handler import database_handler

NETRC_REMOTE_MACHINE_NAME = 'vsphere'

#info = netrc.netrc()
#USER, _, PASSWORD = info.authenticators(NETRC_REMOTE_MACHINE_NAME)
USER = "td\\da230151"
PASSWORD = "CALLORuter92@$"

class destroy_vm:

    def __init__(self, vms, ips):
        if vms is None or ips is None:
            sys.exit(2)
        else:
            self.vms = vms.split(",")
            self.ips = ips.split(",")


    def main(self):
        login = USER
        password = PASSWORD
        service_instance = None

        try:
            service_instance = SmartConnect(host="sd-api-vc02.labs.teradata.com", user=login, pwd=password)
        except IOError as e:
            print e

        if not service_instance:
            raise SystemExit("Unable to connect to vcenter server. Exitting ...")

        atexit.register(Disconnect, service_instance)
        content = service_instance.RetrieveContent()

        container = content.rootFolder  # starting point to look into
        viewType = [vim.VirtualMachine]  # object types to look for
        recursive = True  # whether we should look into it recursively
        containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

        children = containerView.view
        for child in children:
            if child.name in self.vms:
                print child.name
                child.PowerOffVM_Task()
                child.Destroy_Task()

        d = database_handler()
        for i in range(len(self.vms)):
            d.insert_vm_name_ip(self.vms[i], self.ips[i])    


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser(description='destroy_vm -- destroy VM and take back the VM name and IP')
        parser.add_argument('--vms',required=False, default=None, help='VMs name which you want to destroy')
        parser.add_argument('--ips',required=False, default=None, help='VMs IP which you want to destroy')

        args = parser.parse_args()
        destroyer = destroy_vm(args.vms, args.ips)
        destroyer.main()

    except Exception:
        print sys.exc_info()
        print traceback.format_exc()
        sys.exit(2)
