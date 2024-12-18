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


import atexit
import argparse
import requests

from pyVmomi import vim
from pyVmomi import vmodl
from pyVim.connect import SmartConnect, Disconnect

requests.packages.urllib3.disable_warnings()

NETRC_REMOTE_MACHINE_NAME = 'vsphere'

PROG_DESC = '''
VM Operation including power on, power off and revert snapshot\n
./operate_vm.py --vms="astere2e151,astere2e152" --action=power_on\n
./operate_vm.py --vms="astere2e151,astere2e152" --action=revert_snapshot --snapshot=no_aster_install\n
'''
#info = netrc.netrc()
#USER, _, PASSWORD = info.authenticators(NETRC_REMOTE_MACHINE_NAME)
USER = "td\\da230151"
PASSWORD = "CALLORuter92@$"

def wait_for_tasks(service_instance, tasks):
    """Given the service instance si and tasks, it returns after all the
   tasks are complete
   """
    property_collector = service_instance.content.propertyCollector
    task_list = [str(task) for task in tasks]
    # Create filter
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                 for task in tasks]
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                               pathSet=[],
                                                               all=True)
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = [property_spec]
    pcfilter = property_collector.CreateFilter(filter_spec, True)
    try:
        version, state = None, None
        # Loop looking for updates till the state moves to a completed state.
        while len(task_list):
            update = property_collector.WaitForUpdates(version)
            for filter_set in update.filterSet:
                for obj_set in filter_set.objectSet:
                    task = obj_set.obj
                    for change in obj_set.changeSet:
                        if change.name == 'info':
                            state = change.val.state
                        elif change.name == 'info.state':
                            state = change.val
                        else:
                            continue

                        if not str(task) in task_list:
                            continue

                        if state == vim.TaskInfo.State.success:
                            # Remove task from taskList
                            task_list.remove(str(task))
                        elif state == vim.TaskInfo.State.error:
                            raise task.info.error
            # Move to next version
            version = update.version
    finally:
        if pcfilter:
            pcfilter.Destroy()



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


def revert_snapshot(snapshots, snapname):
    snap_obj = []
    for snapshot in snapshots:
        if snapshot.name == snapname:
            snap_obj.append(snapshot)
        else:
            snap_obj = snap_obj + get_snapshots_by_name_recursively(
                                    snapshot.childSnapshotList, snapname)

    if len(snap_obj) == 1:
        snap_obj = snap_obj[0].snapshot
        snap_obj.RevertToSnapshot_Task()


def change_vlan(vm, content, network_name, service_instance):
    try:
        device_change = []
        for device in vm.config.hardware.device:
            if isinstance(device, vim.vm.device.VirtualEthernetCard):
                nicspec = vim.vm.device.VirtualDeviceSpec()
                nicspec.operation = \
                    vim.vm.device.VirtualDeviceSpec.Operation.edit
                nicspec.device = device
                nicspec.device.wakeOnLanEnabled = True

                #if not args.is_VDS:
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
        wait_for_tasks(service_instance, [task])
        print "Successfully changed network"

    except vmodl.MethodFault as error:
        print "Caught vmodl fault : " + error.msg
        return -1

    return 0



def main():
   """
   Let this thing fly
   """

   parser = argparse.ArgumentParser(description=PROG_DESC,
      formatter_class=argparse.RawDescriptionHelpFormatter)

   #parser.add_argument('--prefix', '-p', required=True,
   #                    help='clustr name prefix')

   #parser.add_argument('--start', required=True,
   #                    help='clustr name start index')

   #parser.add_argument('--end', required=True,
   #                    help='clustr name end index')
   parser.add_argument('--vms', required=True,
                       help='a list of VM name. EX: astere2e151,astere2e152,astere2e153')
    
   parser.add_argument('--snapshot', required=False,
                       help='provide a snapshot name if want to revert to snapshot')

   parser.add_argument('--size', required=False,
                       help='size in MB if action is increase_mem')

   parser.add_argument('--netname', required=False,
                       help='network vlan name')

   parser.add_argument('--number', required=False,
                       help='number of cpu core if action is change_cpu_number')

   parser.add_argument('--action', required=True,
                       help='power_on or revert_snapshot or power_off or reboot or increase_mem or list_vm')

   args = parser.parse_args()

   login = USER
   password = PASSWORD

   service_instance = None

   try:

      service_instance = SmartConnect(host="sd-api-vc02.labs.teradata.com", user=login,
                                      pwd=password)

      #atexit.register(Disconnect, service_instance)

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

   #vms = create_vm_list(args.prefix, args.start, args.end)
   vms = args.vms.split(',')
   children = containerView.view
   for child in children:
       if child.name in vms:
           print child.name
           if args.action == "revert_snapshot":
               revert_snapshot(child.snapshot.rootSnapshotList, args.snapshot)
           elif args.action == "power_on":
               child.PowerOn()
           elif args.action == "power_off":
               child.PowerOffVM_Task()
           elif args.action == "reboot":
               child.RebootGuest()
           elif args.action == "destroy":
               child.Destroy_Task()
           elif args.action == "increase_mem":
               vm_spec = vim.vm.ConfigSpec()
               set_vm_spec(child, vm_spec, args.size)
           elif args.action == "change_vlan":
               change_vlan(child, content, args.netname, service_instance)
           elif args.action == "change_cpu_num":
               vm_spec = vim.vm.ConfigSpec()
               set_cpu_num(child, vm_spec, args.number)
            


def set_vm_spec(vm, vm_spec, size):
    vm_spec.memoryMB = int(size)
    print "Memory size set to %s" %vm_spec.memoryMB
    vm.Reconfigure(vm_spec)


def set_cpu_num(vm, vm_spec, number):
    vm_spec.numCPUs = int(number)
    print "CPU core number set to %s" %vm_spec.numCPUs
    vm.Reconfigure(vm_spec)


def create_vm_list(prefix, start, end):
    vm_list = []
    for i in range(int(start), int(end) + 1):
        vm_list.append(prefix + (str(i)))

    return vm_list


if __name__ == "__main__":
    main()
