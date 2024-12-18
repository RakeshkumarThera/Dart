#!/usr/bin/env python

# Copyright 2015 Michael Rice <michael@michaelrice.org>
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

'''
This script uses pyvmomi api to fetch a list of all vms in a container.
The container can be based on a folder, host system, datacenter, resource pool,
etc. In this script, you can create containers based on a folder or a host. The
options provided to the program determine how the container will be generated.
Please see help using -h for more information.

In order to be able to use this program, you need to have pyvmomi installed.

It also uses netrc to get login credentials for the vCenter server.
The netrc remote machine should be 'vsphere'. So the netrc file should contain
lines as follows with appropriate substitutions.

machine vsphere
        login <username>
        password <password>


The script takes 2 arguments from the user - the vCenter server to connect to
and the full name of the esx host from which you want the list of vms.
'''

import traceback
import sys
import atexit
import argparse
import requests
import random
import netrc

from pyVmomi import vim, vmodl
from pyVim.connect import SmartConnect, Disconnect

import tasks

requests.packages.urllib3.disable_warnings()

NETRC_REMOTE_MACHINE_NAME = 'vsphere'

PROG_DESC = '''
Get a list of vms in a container. The container may be a folder or an esx host.
\nTo get all vms in a folder -
./get_vms_in_container.py -s sd-api-vc02.labs.teradata.com -f hdp_red67\n\n
To get all vms on an esx-host -
./get_vms_in_container.py -s sd-api-vc02.labs.teradata.com -e \
sd-labs-esx279.labs.teradata.com'''

info = netrc.netrc()
USER, _, PASSWORD = info.authenticators(NETRC_REMOTE_MACHINE_NAME)


def get_obj(content, vimtype, name):
   """
   Return an object by name, if name is None the
   first found object is returned
   """
   obj = None
   container = content.viewManager.CreateContainerView(
      content.rootFolder, vimtype, True)
   for c in container.view:
      if name:
         if c.name == name:
            obj = c
            break
      else:
         obj = c
         break

   return obj


def get_container_view(content, c_type, c_name):
   'Return the appropriate container'

   container = get_obj(content, [c_type], c_name)

   if not container:
      raise SystemExit("Container '%s' not found. Exitting ..." % c_name)

   return content.viewManager.CreateContainerView(container,
                                                  [vim.VirtualMachine], True)


def create_host_folder(content, host_folder, folder_name):
    host_folder.CreateFolder(folder_name)


def shutdown(child, service_instance):
    print "Shutdown VM %s" %child.name
    child.ShutdownGuest()


def power_off(child, service_instance):
    print "Power off VM %s" %child.name
    child.PowerOffVM_Task()


def destroy(child, service_instance):
    print "Destroy VM %s" %child.name
    child.Destroy_Task()


def get_uuid(child, service_instance):
    print "get VM %s uuid" %child.name
    return child.config.uuid


def reboot(child, service_instance):
    print "Reboot VM %s" %child.name
    TASK = child.ResetVM_Task()
    tasks.wait_for_tasks(service_instance, [TASK])


def create_snapshot(child, service_instance):
    print "Create Snapshot %s" %child.name
    TASK = child.CreateSnapshot_Task(name="pre-aster-install", description="pre-aster-install", memory=True, quiesce=False)
    tasks.wait_for_tasks(service_instance, [TASK])


def delete_folder(server, folder):
    login = USER
    password = PASSWORD

    service_instance = None
    try:
        service_instance = SmartConnect(host=server, user=login, pwd=password)

        atexit.register(Disconnect, service_instance)
        content = service_instance.RetrieveContent()
        created_folder = get_obj(content, [vim.Folder], folder)
        if (created_folder):
            created_folder.Destroy_Task()
            print("Folder '%s' is deleted" % folder)
            return 0
    except:
        print("Folder '%s' is not deleted" % folder)
        return -1


def create_folder(server, paraent_folder, folder):
    login = USER
    password = PASSWORD

    service_instance = None
    try:
        service_instance = SmartConnect(host=server, user=login, pwd=password)

        atexit.register(Disconnect, service_instance)
        content = service_instance.RetrieveContent()
        parent_folder = get_obj(content, [vim.Folder], paraent_folder)
        create_host_folder(content, parent_folder, folder)
        print("Successfully created the host folder '%s'" % folder)
        return 0
    except:
        print("Failure created the host folder '%s'" % folder)
        print(sys.exc_info())
        print(traceback.format_exc())
        sys.exit(1)


def setup_network(server, uuid, ip, hostname, gateway):
    login = USER
    password = PASSWORD

    service_instance = None
    try:
        service_instance = SmartConnect(host=server, user=login, pwd=password)

        atexit.register(Disconnect, service_instance)
        content = service_instance.RetrieveContent()

        vm = content.searchIndex.FindByUuid(None, uuid, True)
        creds = vim.vm.guest.NamePasswordAuthentication(
            username="root", password="aster4data"
        )

        try:
            pm = content.guestOperationsManager.processManager

            ps = vim.vm.guest.ProcessManager.ProgramSpec(
                programPath="/usr/bin/python",
                #arguments="/root/setup_vm.py %s %s" %(hostname, ip)
                arguments="/root/setup_vm.py %s %s %s" %(hostname, ip, gateway)
            )
            res = pm.StartProgramInGuest(vm, creds, ps)

            if res > 0:
                print "Program executed, PID is %d" % res

        except IOError, e:
            print e
    except vmodl.MethodFault as error:
        print "Caught vmodl fault : " + error.msg
        return -1

    return 0


def set_cpu_num(vm, number):
    vm_spec = vim.vm.ConfigSpec()
    vm_spec.numCPUs = int(number)
    print "CPU core number set to %s" %vm_spec.numCPUs
    vm.Reconfigure(vm_spec)


def set_vm_spec(vm, size):
    vm_spec = vim.vm.ConfigSpec()
    vm_spec.memoryMB = int(size)
    print "Memory size set to %s" %vm_spec.memoryMB
    vm.Reconfigure(vm_spec)


def set_cpu_and_memrory(server, vms, cpu_cores, memory):
   login = USER
   password = PASSWORD

   service_instance = None

   try:
      service_instance = SmartConnect(host=server, user=login,
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
   for child in children:
       if child.name in vms:
            set_cpu_num(child, cpu_cores)
            set_vm_spec(child, memory)


def change_vlan(server, uuid, network_name):
    login = USER
    password = PASSWORD

    service_instance = None
    try:
        service_instance = SmartConnect(host=server, user=login, pwd=password)

        atexit.register(Disconnect, service_instance)
        content = service_instance.RetrieveContent()

        vm = content.searchIndex.FindByUuid(None, uuid, True)
        creds = vim.vm.guest.NamePasswordAuthentication(
            username="root", password="aster4data"
        )

        device_change = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nicspec = vim.vm.device.VirtualDeviceSpec()
                nicspec.operation = \
                    vim.vm.device.VirtualDeviceSpec.Operation.edit
                nicspec.device = device
                nicspec.device.wakeOnLanEnabled = True

                nicspec.device.backing = \
                        vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
                nicspec.device.backing.network = \
                        get_obj(content, [vim.Network], network_name)
                nicspec.device.backing.deviceName = network_name

                nicspec.device.connectable = \
                    vim.vm.device.VirtualDevice.ConnectInfo()
                nicspec.device.connectable.startConnected = True
                nicspec.device.connectable.allowGuestControl = True
                device_change.append(nicspec)
                break

        config_spec = vim.vm.ConfigSpec(deviceChange=device_change)
        task = vm.ReconfigVM_Task(config_spec)
        tasks.wait_for_tasks(service_instance, [task])
        print "Successfully changed network"

    except vmodl.MethodFault as error:
        print "Caught vmodl fault : " + error.msg
        return -1

    return 0


def get_esx_host(server, esx_list):
    login = USER
    password = PASSWORD

    service_instance = None

    try:
        service_instance = SmartConnect(host=server, user=login,
                                        pwd=password)
        atexit.register(Disconnect, service_instance)
    except IOError as e:
        print e

    if not service_instance:
       raise SystemExit("Unable to connect to vcenter server. Exitting ...")

    content = service_instance.RetrieveContent()

    host_index = random.randint(0, 14)
    esx_host = esx_list[host_index]
    host = get_obj(content, [vim.HostSystem], esx_host)
    total_mem = int(host.hardware.memorySize) / 1048576
    usage_mem = int(host.summary.quickStats.overallMemoryUsage)
    free_mem = (total_mem - usage_mem) / 1024

    counter = 2
    while free_mem < 56 and counter <= 15:
        host_index = (host_index + 1) % 15
        esx_host = esx_list[host_index]
        host = get_obj(content, [vim.HostSystem], esx_host)
        total_mem = int(host.hardware.memorySize) / 1048576
        usage_mem = int(host.summary.quickStats.overallMemoryUsage)
        free_mem = (total_mem - usage_mem) / 1024
        counter = counter + 1

    return esx_host
     

def main(server, esx_folder, vms, callback):
   """
   Let this thing fly
   """
   login = USER
   password = PASSWORD

   service_instance = None

   try:
      service_instance = SmartConnect(host=server, user=login,
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
   for child in children:
       if child.name in vms:
          ret = callback(child, service_instance)
          # keep result if get VM uuid
          results[child.name] = ret

   return results


if __name__ == "__main__":
   main()
