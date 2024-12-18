# author: Saif ali Karedia

import netrc
import atexit
from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim, vmodl


def power_on(child):
    print "Power on VM %s" % child.name
    # child.PowerOn()


def power_off(child):
    print "Power off VM %s" % child.name
    # child.PowerOffVM_Task()


def power_node(vms):
    '''
    NETRC_REMOTE_MACHINE_NAME = 'vsphere'
    info = netrc.netrc()
    login, _, password = info.authenticators(NETRC_REMOTE_MACHINE_NAME)

    service_instance = None

    try:
        service_instance = SmartConnect(host="sd-api-vc02.labs.teradata.com", user=login,
                                        pwd=password)
        atexit.register(Disconnect, service_instance)
    except IOError as e:
        print e

    if not service_instance:
        raise SystemExit("Unable to connect to vcenter server. Exitting ...")

    content = service_instance.RetrieveContent()

    container = content.rootFolder  # starting point to look into
    viewType = [vim.VirtualMachine]  # object types to look for
    recursive = True  # whether we should look into it recursively
    containerView = content.viewManager.CreateContainerView(container, viewType, recursive)

    results = {}
    children = containerView.view
    vms_list = vms.keys()
    for child in children:
        if child.name in vms_list:
            print child.runtime.powerState
            if vms[child.name] == 'ON':
                print "Turning ON " + child.name
                power_on(child)
            if vms[child.name] == 'OFF':
                print "Turning OFF " + child.name
                power_off(child)'''

    for key in vms:
        if vms[key] == 'ON':
            print 'turning ON' + str(key)
            # print (child.name)
                    # power_on(child)
        if vms[key] == 'OFF':
            print 'turning OFF' + str(key)
            # print (child.name)
            # power_off(child)

    # power_node(['asters'],'ON')
