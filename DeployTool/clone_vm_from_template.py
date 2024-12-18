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
This script uses pyvmomi api to clone a new vm from an existing template.

In order to be able to use this program, you need to have pyvmomi installed.

It also uses netrc to get login credentials for the vCenter server.
The netrc remote machine should be 'vsphere'. So the netrc file should contain
lines as follows with appropriate substitutions.

machine vsphere
        login <username>
        password <password>


The script takes the following arguments from the user -
the vCenter server to connect to
and the full name of the esx host from which you want the list of vms.
'''

import random
import argparse
import atexit
import netrc

from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect


NETRC_REMOTE_MACHINE_NAME = 'vsphere'

#info = netrc.netrc()
#USER, _, PASSWORD = info.authenticators(NETRC_REMOTE_MACHINE_NAME)
USER = "td\\da230151"
PASSWORD = "CALLORuter92@$"


def wait_for_task(task):
    """ wait for a vCenter task to finish """

    task_done = False
    while not task_done:
        if task.info.state == 'success':
            return task.info.result

        if task.info.state == 'error':
            print "there was an error"
            task_done = True

    return None


def get_obj(content, vimtype, name):
   """
   Return an object by name, if name is None the
   first found object is returned
   """
   obj = None
   container = content.viewManager.CreateContainerView(
      content.rootFolder, vimtype, True)
   for c in container.view:
      if c.name == name:
         obj = c
         break

   if not obj:
      raise SystemExit("Unable to find obj %s. Exitting ..." % name)

   return obj


def clone_vm(content, template, cluster_name, folder, vm_name, datastore, esx_host):
   """
   Clone a VM from a template.
   """
   reclone_count = 1
   result = None
   while result is None and reclone_count <= 5:

      cluster = get_obj(content, [vim.ClusterComputeResource], cluster_name)

      resource_pool = cluster.resourcePool

      datastore = get_obj(content, [vim.Datastore], datastore)

      relospec = vim.vm.RelocateSpec()
      relospec.datastore = datastore
      relospec.pool = resource_pool
      host = get_obj(content, [vim.HostSystem], esx_host)
      relospec.host = host

      clonespec = vim.vm.CloneSpec()
      clonespec.location = relospec
      clonespec.powerOn = True

      destfolder = get_obj(content, [vim.Folder], folder)

      print "cloning VM {}...".format(vm_name)

      task = template.Clone(folder=destfolder, name=vm_name, spec=clonespec)
      result = wait_for_task(task)
      reclone_count = reclone_count + 1
      n = random.randint(1, 28)
      if n <= 9:
         n = '0' + str(n)
      else:
         n = str(n)

      datastore = "sd_aster_02-vol" + n


def main(server, template_name, vm_name, cluster_name, folder, datastore, esx_host):
   """
   Let this thing fly
   """
   login = USER
   password = PASSWORD

   service_instance = None

   try:

      service_instance = SmartConnect(host=server, user=login, pwd=password)

      atexit.register(Disconnect, service_instance)

   except IOError as e:
      print e

   if not service_instance:
      raise SystemExit("Unable to connect to vcenter server. Exitting ...")

   content = service_instance.RetrieveContent()

   template = get_obj(content, [vim.VirtualMachine], template_name)
   clone_vm(content, template, cluster_name, folder, vm_name, datastore, esx_host)


if __name__ == "__main__":
   main("sd-api-vc02.labs.teradata.com", "tdc-sles-kube-v1-12.02.17.08", "test_vm", "sd_aster_03", "aster_eng_dart", "esx324_datastore", "sd-labs-esx324.td.teradata.com")
