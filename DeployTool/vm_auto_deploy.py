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
# DESCRIPTION: This tool is uesd to deploy VM on vCenter and install HDP 
#              or CDH cluster
# 
# Dependency:
#     pip install pyvmomi
#     apt-get install sshpass
#     apt-get install ansible
#     
# Download ansible playbook
#     svn export https://athena.asterdata.com/svn/Engineering/infrastructure/trunk/ansible-e2e/
#
# Set .netrc
#     reference document http://www.mavetju.org/unix/netrc.php

import os
import sys
import json
import time
import traceback
import random
import socket

import argparse

import get_vms_in_container
import clone_vm_from_template
from aster_preinstall import aster_preinstall
from hadoop_installer import hadoop_installer
from database_handler import database_handler
from kube_installer import kube_installer
from config_generator import config_generator

ip_block_list = []
ESX_LIST = ["sd-labs-esx273.labs.teradata.com", "sd-labs-esx274.labs.teradata.com", "sd-labs-esx275.labs.teradata.com",
            "sd-labs-esx276.labs.teradata.com", "sd-labs-esx277.labs.teradata.com", "sd-labs-esx278.labs.teradata.com",
            "sd-labs-esx279.labs.teradata.com", "sd-labs-esx286.labs.teradata.com", "sd-labs-esx287.labs.teradata.com",
            "sd-labs-esx288.labs.teradata.com", "sd-labs-esx289.labs.teradata.com", "sd-labs-esx290.labs.teradata.com",
            "sd-labs-esx291.labs.teradata.com", "sd-labs-esx292.labs.teradata.com", "sd-labs-esx293.labs.teradata.com"]

class vm_auto_deploy:

    def __init__(self, config_file, source_type, os_version, aster_preinstall, esx, datastore, cluster, deploy_kube, cluster_type, cluster_name, number_of_node, noLoadSIMS, dhcp, change_config):
        self.change_config = change_config
        self.dhcp = dhcp
        self.noLoadSIMS = noLoadSIMS
        self.number_of_node = int(number_of_node)
        self.config_file = config_file
        if not self.config_file:
            if cluster_type is None or cluster_name is None or self.number_of_node == 0:
                print "Generating config needs cluster type, cluster name and number of node"
                sys.exit(1)

            self.cluster_type = cluster_type
            self.cluster_name = cluster_name

        self.source_type = source_type
        self.os_version = os_version
        self.aster_preinstall = aster_preinstall
        self.deploy_kube = deploy_kube
        self.deploy_ad = None

        self.server = "sd-api-vc02.labs.teradata.com"
        self.vm_cluster = ""
        if cluster is None:
            self.vm_cluster = "sd_aster_02"
        else:
            self.vm_cluster = cluster
        self.folder = "aster_eng_dart"
        self.vm_template = self.get_vm_template()

        n = random.randint(1, 28)
        if n <= 9:
            n = '0' + str(n)
        else:
            n = str(n)

        self.datastore = ""
        if datastore is None: 
            self.datastore = "sd_aster_02-vol" + n
        else:
            self.datastore = datastore

        self.esx_host = ""
        if esx is not None:
            self.esx_host = esx
        else:
            self.esx_host = get_vms_in_container.get_esx_host(self.server, ESX_LIST)


    def get_vm_template(self):
        vm_template = {}

        if self.os_version == "SLES11SP3":
            vm_template['edge'] = "template-hadoop-master-sles11"
            vm_template['worker'] = "template-hadoop-data-sles11"
            vm_template['master'] = "template-hadoop-master-sles11"
        elif self.os_version == "RHEL6.7":
            vm_template['edge'] = "redhat_6.7-x86_64_network"
            vm_template['worker'] = "redhat_6.7-x86_64_network"
            vm_template['master'] = "redhat_6.7-x86_64_network"
        elif self.os_version == "RHEL6.8":
            vm_template['edge'] = "redhat_6.8_x86_64_new"
            vm_template['worker'] = "redhat_6.8_x86_64_new"
            vm_template['master'] = "redhat_6.8_x86_64_new"
        elif self.os_version == "RHEL7.3":
            vm_template['edge'] = "redhat_7.3_x86_64"
            vm_template['worker'] = "redhat_7.3_x86_64"
            vm_template['master'] = "redhat_7.3_x86_64"
        elif self.os_version == "SLES12SP2":
            if self.dhcp:
                vm_template['edge'] = "tdc-sles-vmware-kube-12.02.17.12.11-dhcp"
                vm_template['worker'] = "tdc-sles-vmware-kube-12.02.17.12.11-dhcp"
                vm_template['master'] = "tdc-sles-vmware-kube-12.02.17.12.11-dhcp"
            else:
                #vm_template['edge'] = "tdc-sles-vmware-kube-12.02.18.02.00-200G"
                #vm_template['worker'] = "tdc-sles-vmware-kube-12.02.18.02.00-200G"
                #vm_template['master'] = "tdc-sles-vmware-kube-12.02.18.02.00-200G"
                vm_template['edge'] = "tdc-vmware-kube-os-sles12-sp2-01.01-18.06.08"
                vm_template['worker'] = "tdc-vmware-kube-os-sles12-sp2-01.01-18.06.08"
                vm_template['master'] = "tdc-vmware-kube-os-sles12-sp2-01.01-18.06.08"
        elif self.os_version == "promethium":
            vm_template['edge'] = "t_sles11x64sp3_TDC_ASTER_Q"
            vm_template['worker'] = "t_sles11x64sp3_TDC_ASTER_W"
            vm_template['viewpoint'] = "Teradata_Viewpoint_16.10.00.00_SLES11_SP3_on_VMware_20170908025418"
            vm_template['qgm'] = "t_sles11x64sp3_TDC_QGM_2.4new"
            vm_template['td'] = "Teradata_Database_16.20q.00.10_SLES11_SP3_on_VMware_20170912142914"

        return vm_template


    def generate_vm_list(self, vm_name):
        vm_list = []
        prefix = vm_name['prefix']
        start = vm_name['start']
        end = vm_name['end']

        for i in range(start, end + 1):
            vm_list.append(prefix + str(i))

        return vm_list


    def generate_cluster_list(self, cluster_name):
        cluster_list = []
        prefix = cluster_name['prefix']
        start = cluster_name['start']
        end = cluster_name['end']

        for i in range(start, end + 1):
            if i < 10:
                cluster_list.append(prefix + "0" + str(i))
            else:
                cluster_list.append(prefix + str(i))

        return cluster_list


    def check_config(self, cfg_dict):
        if 'queenNodes' not in cfg_dict:
            return False

        if 'queenVMName' not in cfg_dict:
            return False

        if 'workerNodes' not in cfg_dict:
            return False

        if 'workerVMName' not in cfg_dict:
            return False

        if 'nameNodes' not in cfg_dict:
            return False

        if 'nameVMName' not in cfg_dict:
            return False

        if 'name' not in cfg_dict:
            return False

        if 'password' not in cfg_dict:
            return False

        return True


    def parse_config_file(self, config_file):
        with open(config_file, "r") as f:
            cfg_str = f.read()
            cfg = json.loads(cfg_str)

        return cfg


    def generate_ip(self, cfg_dict, total_clusters):
        start_ip = cfg_dict['start_ip']
        segments = start_ip.split(".")
        ips = []

        ips.append(start_ip)
        last_seg = int(segments[3])
        third_seg = int(segments[2])
        i = 1
        while i < total_clusters:
            last_seg = last_seg + 1
            if last_seg > 255:
                third_seg = int(segments[2]) + 1
                last_seg = 1
            ip = "%s.%s.%s.%s" %(segments[0], segments[1], third_seg, last_seg)

            if ip in ip_block_list:
                continue

            ips.append(ip)
            i = i + 1
    
        return ips



    def run_aster_preinstall(self, queen_ip, ips, password, is_install_hadoop):
        preinstaller = aster_preinstall()
        return preinstaller.main(queen_ip, ips, password, is_install_hadoop)


    def get_gateway(self, ip):
        nums = ip.split(".")
        gateway = ""
        vlan = ""
        if nums[2] == "216" or nums[2] == "217":
            gateway = "10.25.217.254"
            vlan = "dvpg_vm_216"
        elif nums[2] == "218" or nums[2] == "219":
            gateway = "10.25.219.254"
            vlan = "dvpg_vm_218"
        elif nums[2] == "80" or nums[2] == "81" or nums[2] == "82" or nums[2] == "83":
            gateway = "10.25.83.254"
            vlan = "pg_vm_280"

        return gateway, vlan


    def get_machine_ip(self, machines):
        ips = []

        for machine in machines:
            ips.append(socket.gethostbyname("%s.labs.teradata.com" %machine))

        return ips


    def main(self):
        cfg_all = None
        if self.config_file:
            cfg_all = self.parse_config_file(self.config_file)
        else:
            generator = config_generator()
            cfg_str = generator.main(self.cluster_type, self.cluster_name, self.number_of_node, self.dhcp)
            cfg_all = json.loads(cfg_str)

        if cfg_all is None:
            print "Config parsing error"
            sys.exit(1)

        print "cfg_all = ", cfg_all

        cfg = None
        if self.deploy_ad:
            cfg = cfg_all['cluster']
        else:
            name = cfg_all['cluster']['name']
            deployment = cfg_all['cluster']['deployment']
            cfg = cfg_all['kubeCluster']
            cfg['name'] = name
            cfg['deployment'] = deployment

        #if not self.check_config(cfg):
        #    raise
        
        viewpoint = None
        qgm = None
        td_clusters = None
        if self.os_version == "promethium":
            viewpoint = cfg_all['viewpoint']
            if 'viewpointNodes' not in viewpoint or 'viewpointVMName' not in viewpoint:
                raise

            qgm = cfg_all['qgm']
            if 'qgmNodes' not in qgm or 'qgmVMName' not in qgm:
                raise

            td_clusters = cfg_all['tdCluster']
            if 'tdNodes' not in td_clusters or 'tdVMName' not in td_clusters:
                raise

        ips = []
        vm_list = []
        aster_ips = []
        node_type = []

        if self.deploy_ad:
            if len(cfg['queenNodes']) != 0:
                queen_ip = cfg['queenNodes'][0].encode("ascii")
                queen_vm_name = cfg['queenVMName'][0].encode("ascii")
                ips.append(queen_ip)
                aster_ips.append(queen_ip)
                vm_list.append(queen_vm_name)
                node_type.append("queen")

            for worker in cfg['workerNodes']:
                ips.append(worker)
                aster_ips.append(worker)
                node_type.append("worker")

            for worker_name in cfg['workerVMName']:
                vm_list.append(worker_name.encode("ascii"))

            if "nameNodes" in cfg and len(cfg['nameNodes']) != 0:
                namenode_ip = cfg['nameNodes'][0].encode("ascii")
                namenode_vm_name = cfg['nameVMName'][0].encode("ascii")
                ips.append(namenode_ip)
                aster_ips.append(namenode_ip)
                vm_list.append(namenode_vm_name)
                node_type.append("master")

        else:
            if len(cfg['kubemaster']) != 0:
                queen_ip = cfg['kubemaster'][0].encode("ascii")
                queen_vm_name = cfg['kubemasterVMName'][0].encode("ascii")
                ips.append(queen_ip)
                vm_list.append(queen_vm_name)
                node_type.append("kube-master")

            for worker in cfg['kubenodes']:
                ips.append(worker)
                aster_ips.append(worker)
                node_type.append("kube-node")

            for worker_name in cfg['kubenodesVMName']:
                vm_list.append(worker_name.encode("ascii"))

        if self.os_version == "promethium":
            ips.append(viewpoint['viewpointNodes'][0])
            vm_list.append(viewpoint['viewpointVMName'][0])
            node_type.append("viewpoint")

            ips.append(qgm['qgmNodes'][0])
            vm_list.append(qgm['qgmVMName'][0])
            node_type.append("qgm")

            for td in td_clusters['tdNodes']:
                ips.append(td)
                node_type.append("mpp")

            for td in td_clusters['tdVMName']:
                vm_list.append(td)

        cluster_name = cfg['name']
        cluster_type = "AOH"
        if "deployment" in cfg:
            cluster_type = cfg["deployment"]

        if self.source_type is not None and self.source_type == "ESX":
            #power off VM
            get_vms_in_container.main(self.server, self.folder, vm_list, get_vms_in_container.power_off)
            time.sleep(60)

            #destroy VM
            get_vms_in_container.main(self.server, self.folder, vm_list, get_vms_in_container.destroy)
            time.sleep(60)

            #delete folder
            get_vms_in_container.delete_folder(self.server, cluster_name)
            time.sleep(10)

            #create folder
            get_vms_in_container.create_folder(self.server, self.folder, cluster_name)

            #clone VM
            if self.deploy_ad:
                #deploy Aster
                if len(cfg['queenVMName']) != 0:
                    print "it is edge node. vm name = %s, template = %s" % (cfg['queenVMName'][0], self.vm_template['edge'])
                    clone_vm_from_template.main(self.server, self.vm_template['edge'], \
                                                cfg['queenVMName'][0], self.vm_cluster, \
                                                cluster_name, self.datastore, self.esx_host)

                for worker in cfg['workerVMName']:
                    print "it is worker node. vm name = %s, template = %s" % (worker, self.vm_template['worker'])
                    clone_vm_from_template.main(self.server, self.vm_template['worker'], \
                                                worker, self.vm_cluster, \
                                                cluster_name, self.datastore, self.esx_host)

                if "nameVMName" in cfg and len(cfg['nameVMName']) != 0:
                    print "it is master node. vm name = %s, template = %s" % (cfg['nameVMName'][0], \
                                                                              self.vm_template['master'])
                    clone_vm_from_template.main(self.server, self.vm_template['master'], \
                                                cfg['nameVMName'][0], self.vm_cluster, \
                                                cluster_name, self.datastore, self.esx_host)
            else:
                #deploy Kubernate
                print "self.vm_template = ", self.vm_template
                if len(cfg['kubemasterVMName']) != 0:
                    print "it is edge node. vm name = %s, template = %s" % (cfg['kubemasterVMName'][0], self.vm_template['edge'])
                    clone_vm_from_template.main(self.server, self.vm_template['edge'], \
                                                cfg['kubemasterVMName'][0], self.vm_cluster, \
                                                cluster_name, self.datastore, self.esx_host)

                for worker in cfg['kubenodesVMName']:
                    print "it is worker node. vm name = %s, template = %s" % (worker, self.vm_template['worker'])
                    clone_vm_from_template.main(self.server, self.vm_template['worker'], \
                                                worker, self.vm_cluster, \
                                                cluster_name, self.datastore, self.esx_host)

            if self.os_version == "promethium":
                #deploy Viewpoint
                if len(viewpoint['viewpointVMName']) != 0:
                    print "it is viewpoint node. vm name = %s, template = %s" % (viewpoint['viewpointVMName'][0], \
                                                                                 self.vm_template['viewpoint'])
                    clone_vm_from_template.main(self.server, self.vm_template['viewpoint'], \
                                                viewpoint['viewpointVMName'][0], self.vm_cluster, \
                                                cluster_name, self.datastore, self.esx_host)

                #deploy QGM
                if len(qgm['qgmVMName']) != 0:
                    print "it is qgm node. vm name = %s, template = %s" % (qgm['qgmVMName'][0], self.vm_template['qgm'])
                    clone_vm_from_template.main(self.server, self.vm_template['qgm'], \
                                                qgm['qgmVMName'][0], self.vm_cluster, \
                                                cluster_name, self.datastore, self.esx_host)
                #deploy TD
                if len(td_clusters['tdVMName']) != 0:
                    for td in td_clusters['tdVMName']:
                        print "it is td node. vm name = %s, template = %s" % (td, self.vm_template['td'])
                        clone_vm_from_template.main(self.server, self.vm_template['td'], \
                                                    td, self.vm_cluster, \
                                                    cluster_name, self.datastore, self.esx_host)

            # get VM uuid
            uuids = get_vms_in_container.main(self.server, self.folder, vm_list, get_vms_in_container.get_uuid)
            gateway = ""
            vlan = ""
            if not self.dhcp:
                gateway, vlan = self.get_gateway(ips[0])


            for i in range(len(vm_list)):
                if self.dhcp:
                    gateway = ""
                    get_vms_in_container.setup_network(self.server, uuids[vm_list[i]], ips[i], vm_list[i], gateway)
                else:
                    get_vms_in_container.setup_network(self.server, uuids[vm_list[i]], ips[i], vm_list[i], gateway)
                    get_vms_in_container.change_vlan(self.server, uuids[vm_list[i]], vlan)
                time.sleep(5)

            print "Setup IP and hostname"
            time.sleep(60 * 5)

            # reboot
            get_vms_in_container.main(self.server, self.folder, vm_list, get_vms_in_container.reboot)
            time.sleep(300)

        is_install_hadoop = False
        if 'distroType' in cfg:
            installer = hadoop_installer()
            if not installer.main(self.config_file, self.os_version):
                print "install Hadoop fail %s" %cluster_name
                sys.exit(1)

            is_install_hadoop = True

        #if not is_install_hadoop:
        #    time.sleep(300)

        if self.dhcp:
            cfg['kubemaster'] = self.get_machine_ip(cfg['kubemasterVMName'])
            cfg['kubenodes'] = self.get_machine_ip(cfg['kubenodesVMName'])
        
        if self.deploy_kube:
            installer = kube_installer()
            if not installer.main(cfg['kubemaster'], cfg['kubenodes'], cfg['kubemasterVMName'], cfg['kubenodesVMName'], cluster_name, cfg['password']):
                print "install Kubernate fail %s" %cluster_name
                sys.exit(1)
        
        if self.aster_preinstall:
            if not self.run_aster_preinstall(aster_ips[0], aster_ips, cfg['password'], is_install_hadoop):
                print "Aster preinstall run fail on Cluster %s" % cluster_name

        # shutdown all VM for creating snapshot
        get_vms_in_container.main(self.server, self.folder, vm_list, get_vms_in_container.shutdown)
        time.sleep(300)

        # if change configure is true, change cpu and memory
        if self.change_config:
            get_vms_in_container.set_cpu_and_memrory(self.server, cfg['kubemasterVMName'], 10, 48000)
            get_vms_in_container.set_cpu_and_memrory(self.server, cfg['kubenodesVMName'], 6, 40000)
        
        # create snapshot
        if self.source_type is not None and self.source_type == "ESX":
            get_vms_in_container.main(self.server, self.folder, vm_list, get_vms_in_container.create_snapshot)
            time.sleep(10)
        
        if not self.noLoadSIMS:
            handler = database_handler()
            # Select the cluster from DB. If it is not in DB then insert
            if len(handler.select_cluster(cluster_name)) == 0:
                ret = handler.insert_cluster({"cluster_name": cluster_name, "no_of_nodes": len(vm_list), "cluster_type": cluster_type})
                if not ret[1]:
                    print "Insert cluster infomation fail"
                    raise

                cluster_id = ret[0]
                for i in range(len(vm_list)):
                    node = {}
                    node["node_type"] = node_type[i]
                    node["node_ip"] = ips[i] 
                    node["hostname"] = "%s.labs.teradata.com" %vm_list[i]
                    handler.insert_node(cluster_id, node) 
        
        if not self.config_file:
            j = json.dumps(cfg_all, indent=4)
            with open(self.cluster_name + ".cfg", "w") as f:
                f.write(j)      
       

if __name__ == "__main__":

    try:
        parser = argparse.ArgumentParser(description='vm_auto_deploy - Deploy VM, Hadoop automatically')
        parser.add_argument('-c', '--config',required=False, default=None, help='Cluster config file')
        parser.add_argument('--sourceType', required=True, default=None, help='VRA or ESX')
        parser.add_argument('--esx', required=False, default=None, help='ESX host name')
        parser.add_argument('--datastore', required=False, default=None, help='vCenter datastore name')
        parser.add_argument('--cluster', required=False, default=None, help='vCenter cluster name')
        parser.add_argument('--osVersion', required=False, default=None, help='SLES11SP3 or RHEL6.7')
        parser.add_argument('--clusterType', required=False, default=None, help='AD or docker')
        parser.add_argument('--clusterName', required=False, default=None, help='SLES11SP3 or RHEL6.7 or SLES12SP2')
        parser.add_argument('--numberOfNode', required=False, default=0, help='if config file in not provide, please privide number of node')
        parser.add_argument('--noLoadSIMS', required=False, default=False, action='store_true', help='do not insert the cluster info to SIMS DB')
        parser.add_argument('--changeConfig', required=False, default=False, action='store_true', help='change cpu and memory to TDAP requirement')
        parser.add_argument('--dhcp', required=False, default=False, action='store_true', help='deploy VM with DHCP network')
        parser.add_argument('--deployKube', required=False, default=False, action='store_true',
                            help='Deploy Kubernate by Ansible')
        parser.add_argument('--asterPreinstall', required=False, default=False, action='store_true',
                            help='Do Aster pre-installation')

        args = parser.parse_args()
        deployer = vm_auto_deploy(args.config, args.sourceType, args.osVersion, args.asterPreinstall, args.esx, \
                                  args.datastore, args.cluster, args.deployKube, args.clusterType, args.clusterName, \
                                  args.numberOfNode, args.noLoadSIMS, args.dhcp, args.changeConfig)
        deployer.main()

    except Exception:
        print sys.exc_info()
        print traceback.format_exc()
        sys.exit(2)
