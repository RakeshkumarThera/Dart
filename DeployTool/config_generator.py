import sys
import traceback

import json
import argparse

from database_handler import database_handler

class config_generator:

    def __init__(self):
        pass

    def get_vmname_ip(self, number, dhcp):
        handler = database_handler()
        vms = handler.get_vm_name_ip(number, dhcp)
        if len(vms) == 0:
            return []

        if not handler.delete_unavailable_vm_name_ip(vms):
            return []

        return vms


    def generate_docker_config(self, cluster_name, vms, cluster_type):
        config = {}
        config['cluster'] = {}
        config['cluster']['name'] = cluster_name
        config['cluster']['domain'] = "labs.teradata.com"
        config['cluster']['queenNodes'] = []
        config['cluster']['queenVMName'] = []
        config['cluster']['workerNodes'] = []
        config['cluster']['workerVMName'] = []
        config['cluster']['username'] = "root"
        config['cluster']['password'] = "aster4data"
        config['cluster']['clusterType'] = cluster_type
        config['cluster']['deployment'] = "docker"

        config['kubeCluster'] = {}
        config['kubeCluster']['domain'] = "labs.teradata.com"
        config['kubeCluster']['kubemaster'] = [vms[0]["vm_ip"]] 
        config['kubeCluster']['kubemasterVMName'] = [vms[0]["vm_name"]]

        config['kubeCluster']['kubenodes'] = []
        config['kubeCluster']['kubenodesVMName'] = []
        for i in range(1, len(vms)):
            config['kubeCluster']['kubenodes'].append(vms[i]["vm_ip"])
            config['kubeCluster']['kubenodesVMName'].append(vms[i]["vm_name"])

        config['kubeCluster']['username'] = "root"
        config['kubeCluster']['password'] = "aster4data"

        j = json.dumps(config, indent=4)

        return j


    def generate_pm_config(self, cluster_name, vms, cluster_type):
        config = {}
        config['cluster'] = {}
        config['cluster']['name'] = cluster_name
        config['cluster']['domain'] = "labs.teradata.com"
        config['cluster']['queenNodes'] = [vms[0]["vm_ip"]]
        config['cluster']['queenVMName'] = [vms[0]["vm_name"]]
        config['cluster']['workerNodes'] = [vms[1]["vm_ip"], vms[2]["vm_ip"]]
        config['cluster']['workerVMName'] = [vms[1]["vm_name"], vms[2]["vm_name"]]
        config['cluster']['username'] = "root"
        config['cluster']['password'] = "aster4data"
        config['cluster']['clusterType'] = cluster_type

        config['viewpoint'] = {}
        config['viewpoint']['viewpointNodes'] =  [vms[3]["vm_ip"]]
        config['viewpoint']['viewpointVMName'] = [vms[3]["vm_name"]]

        config['qgm'] = {}
        config['qgm']['qgmNodes'] = [vms[4]["vm_ip"]]
        config['qgm']['qgmVMName'] = [vms[4]["vm_name"]]

        config['tdCluster'] = {}
        config['tdCluster']['tdNodes'] = [vms[5]["vm_ip"], vms[6]["vm_ip"]]
        config['tdCluster']['tdVMName'] = [vms[5]["vm_name"], vms[5]["vm_name"]]

        j = json.dumps(config, indent=4)

        return j


    def generate_ad_config(self, cluster_name, vms, cluster_type):
        
        config = {}
        config['cluster'] = {}
        config['cluster']['name'] = cluster_name
        config['cluster']['domain'] = "labs.teradata.com"
        config['cluster']['queenNodes'] = [vms[0]["vm_ip"]]
        config['cluster']['queenVMName'] = [vms[0]["vm_name"]]
        config['cluster']['workerNodes'] = []
        config['cluster']['workerVMName'] = []
        for i in range(1, len(vms)):    
            config['cluster']['workerNodes'].append(vms[i]["vm_ip"])
            config['cluster']['workerVMName'].append(vms[i]["vm_name"])

        config['cluster']['nameNodes'] = []
        config['cluster']['nameVMName'] = []

        config['cluster']['username'] = "root"
        config['cluster']['password'] = "aster4data"
        config['cluster']['clusterType'] = cluster_type

        j = json.dumps(config, indent=4) 

        return j


    def main(self, cluster_type, cluster_name, number_of_node, dhcp):
        config = ""
        if cluster_type == "pm":
            vms = self.get_vmname_ip(7)
            if len(vms) == 0:
                return None
            config = self.generate_pm_config(cluster_name, vms, cluster_type)
        elif cluster_type == "docker":
            vms = self.get_vmname_ip(number_of_node, dhcp)
            if len(vms) == 0:
                return None
            config = self.generate_docker_config(cluster_name, vms, cluster_type)
        else:
            vms = self.get_vmname_ip(number_of_node, dhcp)
            if len(vms) == 0:
                return None
            config = self.generate_ad_config(cluster_namevms, vms, cluster_type)
       
        return config


if __name__ == "__main__":
    try:
        c = config_generator() 
        print c.main("docker", "test_cluster")
    except:
        print(sys.exc_info())
        print(traceback.format_exc())
        sys.exit(2)
