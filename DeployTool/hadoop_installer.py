import json
import time
import os
import string
import sys
import traceback
import requests
import shutil
import subprocess

import paramiko

class hadoop_installer:

    def __init__(self):
        self.ambari_version = {'2.5': '2.4.1', '2.3': '2.4.1', '2.1': '2.2.1'}
        self.blueprints_name = {'2.5': 'aoh25_blueprint', '2.4': 'aoh24_blueprint', \
                                '2.3': 'aoh_vm_blueprint'}


    def parse_config_file(self, cfg_file):
        with open(cfg_file, "r") as f:
            cfg_str = f.read()
            cfg = json.loads(cfg_str)

        return cfg['cluster']


    def check_config(self, cfg):
        if 'queenNodes' not in cfg:
            print "Miss queenNodes information"
            return None

        if 'workerNodes' not in cfg:
            print "Miss workerNodes information"
            return None

        if 'nameNodes' not in cfg:
            print "Miss nameNodes information"
            return None

        if 'distroType' not in cfg:
            print "Miss distroType"
            return None

        if 'version' not in cfg:
            print "Miss version"
            return None

        if cfg['distroType'] == "hdp":
            if cfg['version'] != "2.5" and cfg['version'] != "2.3" and cfg['version'] != "2.4":
                print "This veriosn is not supported"
                return None
            cfg['ambari_version'] = self.ambari_version[cfg['version']]
            cfg['blueprint'] = self.blueprints_name[cfg['version']]
            ansible_home_list = os.path.abspath(__file__).split("/")[:-1]
            ansible_home = "/".join(ansible_home_list) + "/ansible-e2e"
            cfg['ansible-e2e_home'] = ansible_home
        elif cfg['distroType'] == "cdh":
            if cfg['version'] != "5.5.1" and cfg['version'] != "5.5.2" \
                and cfg['version'] != "5.8.0" and cfg['version'] != "5.9.0":
                print "This veriosn is not supported"
                return None

        return cfg


    def exec_command(self, cmd, ssh):
        stdin, stdout, stderr = ssh.exec_command(cmd)
        status = stdout.channel.recv_exit_status()
        print "status = ", status

        print "".join(stdout.readlines())
        print "".join(stderr.readlines())
        if status == 0:
            print "".join(stdout.readlines())
            return True
        else:
            print "".join(stderr.readlines())
            return False


    def run_shell_command(self, cmd, err, job="", ssh_handler=None):
        env = os.environ.copy()
        env["PATH"] = "/usr/sbin:/sbin:" + env["PATH"]
        print "cmd = ", cmd
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        out, err = p.communicate()
        status = p.poll()
        output = out + err

        print status
        print output

        if job == "install_hdp" and "Ambari Server is already running." in output:
            #stop ambari-server
            self.exec_command("/etc/init.d/ambari-server stop", ssh_handler)
            print "Stop ambari-server......."
            time.sleep(10)
            return True

        if status != 0 and job == "install_hdp":
            print "Retry running ansible again"
            return True

        if status != 0 and job == "send_key" and err != "":
            return True

        if status != 0 and err != "":
            print err
            return True

        return False


    def exec_command_install_cdh(self, hadoop, password, master_ip, ips, vm_list):
        location = "/".join(os.path.abspath(__file__).split("/")[:-1])
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(master_ip, username='root', password=password)

        if not self.exec_command("echo -e \"\n\n\n\" | ssh-keygen -f /root/.ssh/id_dsa -t dsa -N ''", ssh):
            if not self.exec_command("echo -e \"y\\n\" | ssh-keygen -f /root/.ssh/id_dsa -t dsa -N ''", ssh):
                print "Generate ssh key fail"
                return False

        if not self.exec_command(
                "cat /root/.ssh/id_dsa.pub >> /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys", ssh):
            print "Make authorized_keys fail"
            return False

        if self.run_shell_command("sshpass -p %s scp -o StrictHostKeyChecking=no -r root@%s:/root/.ssh/ %s/" % (
        password, master_ip, location), "Download key fail"):
            return False

        for i in range(len(ips) - 1):
            if self.run_shell_command("sshpass -p %s scp -o StrictHostKeyChecking=no -pr %s/.ssh root@%s:" % (
            password, location, ips[i]), "Transfer key to %s fail" % ips[i]):
                return False


        for i in range(len(ips) - 1):
            if not self.exec_command("ssh -o StrictHostKeyChecking=no root@%s date" % ips[i], ssh):
                print "Test ssh passwordless on %s fail" % ips[i]
                return False

        shutil.rmtree("%s/.ssh" % location)

        if not self.exec_command("chmod 755 /root/tdhadoop.conf", ssh):
            print "chmod 755 /root/tdhadoop.conf error"
            return False

        if not self.exec_command("mkdir -p /opt/teradata/hadoop-builder/", ssh):
            return False

        if not self.exec_command("cp -a /root/tdhadoop.conf /opt/teradata/hadoop-builder/", ssh):
            return False

        cmd = "PACKAGE_DIRECTORY='/var/opt/teradata/packages/hadoop'; rm -f /data/htdocs/{*.tar.gz,*.rpm}; rm -f ${PACKAGE_DIRECTORY}/{*.tar.gz,*.rpm}"
        if not self.exec_command(cmd, ssh):
            return False

        os.makedirs("./cdh_package")
        cmd = "cd ./cdh_package; wget -r -nH -nd -np -R index.html* http://tully1.labs.teradata.com/repo/Factory_Releases/CDH-%s/" % \
              hadoop['version']
        if self.run_shell_command(cmd, "Download cdh package fail"):
            return False

        cmd = "sshpass -p %s scp -o StrictHostKeyChecking=no ./cdh_package/* root@%s:/var/opt/teradata/packages/hadoop/" % (
        password, master_ip)
        if self.run_shell_command(cmd, "Transfer cdh package fail"):
            return False

        shutil.rmtree("./cdh_package/")

        cmd = "cd /var/opt/teradata/packages/hadoop; tar xvf teradata-hadoop-builder*.tar.gz"
        if not self.exec_command(cmd, ssh):
            return False

        cmd = "zypper --non-interactive in /var/opt/teradata/packages/hadoop/teradata-hadoop-builder*.rpm"
        if not self.exec_command(cmd, ssh):
            return False

        # Use modified script because TPE team script doesn't support our e2e vCenter
        if hadoop['version'] == "5.9.0":
            cmd = "cp /root/BuildHadoop_CDH.sh /opt/teradata/hadoop-builder/"
            if not self.exec_command(cmd, ssh):
                return False

            cmd = "cp /root/hbUtils.sh /opt/teradata/hadoop-builder/scripts/utils/"
            if not self.exec_command(cmd, ssh):
                return False

        cmd = "cd /opt/teradata/hadoop-builder; sh BuildHadoop_CDH.sh 2>&1 | tee /var/opt/teradata/buildhadoop-`date +\"%m_%d_%Y:%H:%M:%S\"`.log"
        if not self.exec_command(cmd, ssh):
            return False

        if not self.exec_command("hcli factory config_postinstall", ssh):
            return False

        ssh.close()

        return True


    def create_tdhadoop_conf(self, vm_list, cluster_name):
        siteid = "".join(ch for ch in cluster_name if ch not in set(string.punctuation))
        siteid = siteid.upper()

        content = "CLUSTERNAME='%s'\n" % siteid
        content = content + "MASTER1=%s.labs.teradata.com\n" % vm_list[-1]
        for i in range(1, len(vm_list) - 1):
            content = content + "DATANODE%s=%s.labs.teradata.com\n" % (i, vm_list[i])

        content = content + "EDGENODE1=%s.labs.teradata.com" % vm_list[0]

        try:
            with open("./tdhadoop_%s.conf" % cluster_name, "w") as f:
                f.write(content)

            os.chmod("./tdhadoop_%s.conf" % cluster_name, 0755)

            return True
        except:
            print str(sys.exc_info())
            print traceback.format_exc()
            return False


    def transfer_conf_install_cdh(self, cluster_name, password, master_ip):
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            ssh.connect(master_ip, username='root', password=password)
            sftp = ssh.open_sftp()
            sftp.put('tdhadoop_%s.conf' % cluster_name, '/root/tdhadoop.conf')
            ssh.close()

            return True
        except:
            print str(sys.exc_info())
            print traceback.format_exc()
            return False


    def create_ansible_hosts(self, vm_list, ips, hadoop, cluster_name, vm_number, password):
        ansible_home = hadoop['ansible-e2e_home']
        if os.path.exists(ansible_home + "/hosts"):
            os.rename(ansible_home + "/hosts", ansible_home + "/hosts_bak")

        with open(ansible_home + "/hosts", "w") as f:
            f.write("[%s]\n" % cluster_name)
            f.write("%s.labs.teradata.com ansible_ssh_pass=%s ansible_ssh_host=%s\n" % (vm_list[0], password, ips[0]))
            for i in range(1, vm_number):
                f.write("%s.labs.teradata.com ansible_ssh_pass=%s ansible_ssh_host=%s\n" % (vm_list[i], password, ips[i]))

            f.write("\n")


    def change_vcore_number(self, ip, cluster_name):
        url = "http://%s:7180/api/v11/clusters/%s/services/YARN/roleConfigGroups/YARN-NODEMANAGER-BASE/config" % (
        ip, cluster_name)
        data = json.dumps({"items": [{"name": "yarn_nodemanager_resource_cpu_vcores", "value": "8"}]})
        auth = ('admin', 'admin')
        headers = {'Content-Type': 'application/json'}
        response = requests.put(url, data=data, auth=auth, headers=headers)

        return response.status_code


    def change_container_memory(self, ip, cluster_name):
        url = "http://%s:7180/api/v11/clusters/%s/services/YARN/roleConfigGroups/YARN-NODEMANAGER-BASE/config" % (
            ip, cluster_name)
        data = json.dumps({"items": [{"name": "yarn_nodemanager_resource_memory_mb", "value": "16384"}]})
        auth = ('admin', 'admin')
        headers = {'Content-Type': 'application/json'}
        response = requests.put(url, data=data, auth=auth, headers=headers)

        return response.status_code


    def restart_service(self, ip, cluster_name):
        url = "http://%s:7180/api/v11/clusters/%s/commands/restart" % (ip, cluster_name)
        data = json.dumps({"restartOnlyStaleServices": True, "redeployClientConfiguration": True})
        auth = ('admin', 'admin')
        headers = {'Content-Type': 'application/json'}
        response = requests.post(url, data=data, auth=auth, headers=headers)

        return response.status_code


    def create_ansible_group_file(self, ansible_home, hadoop, vm_list, cluster_name):
        if os.path.exists(ansible_home + "/group_vars/" + cluster_name):
            os.remove(ansible_home + "/group_vars/" + cluster_name)

        if not os.path.exists(ansible_home + "/group_vars/" + cluster_name):
            with open(ansible_home + "/group_vars/" + cluster_name, "w") as f:
                if hadoop['version'] == "2.1":
                    f.write("namenode:   %s.labs.teradata.com\n" % vm_list[0])
                else:
                    f.write("edgenode:   %s.labs.teradata.com\n" % vm_list[0])
                    f.write("namenode:   %s.labs.teradata.com\n" % vm_list[-1])
                f.write("\n")
                f.write("datanodes:\n")
                for i in range(1, len(vm_list) - 1):
                    f.write("        %s.labs.teradata.com\n" % vm_list[i])


    def create_host_mapping(self, vm_list, hadoop, cluster_name):
        host_mapping = {}
        host_mapping['blueprint'] = 'default-blueprint'
        host_mapping['default_password'] = 'simple'

        host_groups = []
        for i in range(len(vm_list)):
            node = {}
            if i == 0:
                if hadoop['version'] != "2.1":
                    node['name'] = "edgenode"
                    node['hosts'] = [{"fqdn": vm_list[i] + ".labs.teradata.com"}]
                else:
                    node['name'] = "namenode"
                    node['hosts'] = [{"fqdn": vm_list[i] + ".labs.teradata.com"}]
            elif i == len(vm_list) - 1 and hadoop['version'] != "2.1":
                node['name'] = "namenode"
                node['hosts'] = [{"fqdn": vm_list[i] + ".labs.teradata.com"}]
            else:
                node['name'] = "datanode" + str(i)
                node['hosts'] = [{"fqdn": vm_list[i] + ".labs.teradata.com"}]

            host_groups.append(node)

        host_mapping['host_groups'] = host_groups

        with open("/tmp/%s_ambari_host_mapping" % cluster_name, "w") as f:
            f.write(json.dumps(host_mapping, indent=4, sort_keys=True))


    def hdp_check_installation_progress(self, master_ip, cluster_name):
        cluster_name = cluster_name.replace("-", "_")
        print cluster_name
        auth = ('admin', 'admin')
        headers = {'X-Requested-By': 'ambari'}
        url = "http://%s:8080/api/v1/clusters/%s/requests/1" %(master_ip, cluster_name)
        response = requests.get(url, auth=auth, headers=headers)
        res = json.loads(response.text)
        progress = int(res['Requests']['progress_percent'])
        print "progress = ", progress

        return  progress


    def hdp_get_config(self, master_ip, cluster_name):
        cluster_name = cluster_name.replace("-", "_")
        auth = ('admin', 'admin')
        headers = {'X-Requested-By': 'ambari'}
        url = "http://%s:8080/api/v1/clusters/%s?fields=Clusters/desired_configs" %(master_ip, cluster_name)
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code != 200:
            print "Get cluster config fail"
            return (None, False)
        else:
            res = json.loads(response.text)
            configs = res['Clusters']['desired_configs']
            yarn_site = configs['yarn-site']

            return ({"name": "yarn-site", "tag": yarn_site['tag']}, True)


    def hdp_get_properties(self, master_ip, cluster_name, config):
        cluster_name = cluster_name.replace("-", "_")
        auth = ('admin', 'admin')
        headers = {'X-Requested-By': 'ambari'}
        url = "http://%s:8080/api/v1/clusters/%s/configurations?type=yarn-site&tag=%s" %(master_ip, cluster_name, config['tag'])
        response = requests.get(url, auth=auth, headers=headers)
        if response.status_code != 200:
            print "Get cluster config fail"
            return None
        else:
            res = json.loads(response.text)
            properties = res['items'][0]['properties']

            return properties


    def hdp_change_container_memory(self, master_ip, cluster_name, properties, os_version):
        cluster_name = cluster_name.replace("-", "_")
        auth = ('admin', 'admin')
        headers = {'X-Requested-By': 'ambari'}
        if os_version == "RHEL7.3":
            properties["yarn.nodemanager.resource.memory-mb"] = "32000"
        else:
            properties["yarn.nodemanager.resource.memory-mb"] = "16000"
        tag = "version" + str(int(time.time()))
        data = json.dumps([{"Clusters":{"desired_config":[{"type":"yarn-site", "tag": tag, "properties": properties}]}}])
        url = "http://%s:8080/api/v1/clusters/%s" %(master_ip, cluster_name)
        response = requests.put(url, auth=auth, headers=headers, data=data)

        if response.status_code != 200:
            print "Change Yarn container memory failure"
            return False

        return True


    def install_hdp(self, vm_list, hadoop, cluster_name, password, ips):
        ansible_home = hadoop['ansible-e2e_home']

        # generate ansible config fiel for this cluster
        self.create_ansible_group_file(ansible_home, hadoop, vm_list, cluster_name)

        cmd = "chmod 600 %s/files/ssh/id_rsa.pub %s/files/ssh/id_rsa" % (ansible_home, ansible_home)
        ret = self.run_shell_command(cmd, "Change id_rsa.pub mode fail")
        if ret:
            return

        # for vm in vm_list:
        for ip in ips:
            # transfer ssh key
            # cmd = "sshpass -p %s ssh-copy-id -i %s/files/ssh/id_rsa.pub root@%s" %(password, ansible_home, vm)
            cmd = "sshpass -p %s ssh-copy-id -i %s/files/ssh/id_rsa.pub root@%s" % (password, ansible_home, ip)
            is_rerun = self.run_shell_command(cmd, "Transfer ssh key fail on IP %s" % ip, "send_key")

            # if transfer key fail, sleep 60 seconds then sent it again
            if is_rerun:
                print "sleep 60 seconds then retry sending key"
                time.sleep(60)
                cmd = "sshpass -p %s ssh-copy-id -i %s/files/ssh/id_rsa.pub root@%s" % (password, ansible_home, ip)
                ret = self.run_shell_command(cmd, "Transfer ssh key fail on VM %s" % ip)
                if ret:
                    return False

        # ping cluster
        cmd = "cd %s; ansible -u root -m ping %s" % (ansible_home, cluster_name)
        ret = self.run_shell_command(cmd, "Run ansible ping fail")
        if ret:
            return False

        # install HDP using ansible
        print "Run ansible to install HDP"

        shutil.copy("%s/Install_HDP.yml" %ansible_home, "%s/Install_HDP_%s.yml" %(ansible_home, cluster_name))
        yml_file = "Install_HDP_%s.yml" %cluster_name
        retry_file = "Install_HDP_%s.retry" %cluster_name
        cmd = "cd %s; /usr/bin/ansible-playbook %s --extra-vars=\"hdp_cluster=%s \
              ambari_server=%s.labs.teradata.com \
              ambari_server_port=8080 ambari_version=%s blueprint=%s\"" % (
        ansible_home, yml_file, cluster_name, vm_list[-1], hadoop['ambari_version'], hadoop['blueprint'])

        # Create Paramiko ssh handler to stop ambari-server if the error is Ambari-server is running
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ips[-1], username='root', password=password)

        ret = self.run_shell_command(cmd, "Run ansible fail", "install_hdp", ssh)

        # if install fail, install again
        install_count = 1
        while ret and install_count <= 3 :
            cmd = "cd %s; /usr/bin/ansible-playbook %s --extra-vars=\"hdp_cluster=%s \
              ambari_server=%s.labs.teradata.com \
              ambari_server_port=8080 ambari_version=%s blueprint=%s\" --limit @%s/%s" \
                  % (ansible_home, yml_file, cluster_name, vm_list[-1], \
                     hadoop['ambari_version'], hadoop['blueprint'], ansible_home, retry_file)
            print "cmd = ", cmd
            ret = self.run_shell_command(cmd, "Run ansible retry fail", "install_hdp", ssh)
            if install_count == 3:
                return False

            install_count = install_count + 1

        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ips[-1], username='root', password=password)
        self.exec_command("/etc/init.d/ambari-server start", ssh)
        ssh.close()

        # remove tracking progress in creating hadoop cluster script
        cmd = "head -n-2 /tmp/%s_ambari_create_hadoop_cluster.sh > /tmp/%s_ambari_create_hadoop_cluster_auto.sh; \
               chmod 777 /tmp/%s_ambari_create_hadoop_cluster_auto.sh" % (cluster_name, cluster_name, cluster_name)
        ret = self.run_shell_command(cmd, "Run head command fail")
        if ret:
            return False

        self.create_host_mapping(vm_list, hadoop, cluster_name)

        # run creating hadoop cluster script
        cmd = "cd /tmp; /tmp/%s_ambari_create_hadoop_cluster_auto.sh" % cluster_name
        ret = self.run_shell_command(cmd, "Run creating hadoop script fail")
        if ret:
            return False

        os.remove("/tmp/%s_ambari_create_hadoop_cluster_auto.sh" % cluster_name)
        os.remove("%s/%s" %(ansible_home, yml_file))
        if os.path.isfile("%s/%s" % (ansible_home, retry_file)):
            os.remove("%s/%s" % (ansible_home, retry_file))

        while True:
            if self.hdp_check_installation_progress(ips[-1], cluster_name) == 100:
                break

            time.sleep(300)

        configs = self.hdp_get_config(ips[-1], cluster_name)
        if not configs[1]:
            return False

        properties = self.hdp_get_properties(ips[-1], cluster_name, configs[0])
        if properties is None:
            return False

        if not self.hdp_change_container_memory(ips[-1], cluster_name, properties, hadoop['os']):
            return False

        return True


    def create_hosts_file(self, vm_list, ips, password, cluster_name):
        hosts_content = "hosts_content_%s" %cluster_name
        with open(hosts_content, "w") as f:
            f.write("\n")
            for i in range(len(vm_list)):
                f.write("%s %s.labs.teradata.com %s\n" %(ips[i], vm_list[i], vm_list[i]))

        time.sleep(60)

        for i in range(len(ips)):
            if self.run_shell_command("sshpass -p %s scp -o StrictHostKeyChecking=no %s root@%s:/root/" \
                                  %(password, hosts_content, ips[i]), "Create /etc/hosts fail"):
                return False

            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ips[i], username='root', password=password)

            self.exec_command("cat %s >> /etc/hosts" %hosts_content, ssh_client)

            ssh_client.close()

        os.remove(hosts_content)

        return True


    def install_cdh(self, vm_list, hadoop, cluster_name, password, master_ip, ips):
        # Create tdhadoop.conf
        if not self.create_tdhadoop_conf(vm_list, cluster_name):
            print "Create tdhadoop.conf fail %s" % cluster_name
            return False

        # Transfer tdhadoop.conf to master
        # time.sleep(60)
        if not self.transfer_conf_install_cdh(cluster_name, password, master_ip):
            print "Transfer tdhadoop.conf fail %s" % cluster_name
            return False

        # Create /etc/hosts
        if not self.create_hosts_file(vm_list, ips, password, cluster_name):
            print "Create /etc/hosts fail %s" %cluster_name
            return False

        # Execute installing command on master
        if not self.exec_command_install_cdh(hadoop, password, master_ip, ips, vm_list):
            print "Install cdh fail %s" % cluster_name
            return False

        os.remove("./tdhadoop_%s.conf" % cluster_name)
        time.sleep(300)

        siteid = "".join(ch for ch in cluster_name if ch not in set(string.punctuation))
        siteid = siteid.upper()
        # Change CDH vcore number to 8
        ret = self.change_vcore_number(master_ip, siteid)
        print "Change CDH vcore number status code is %s at %s" % (ret, cluster_name)
        if ret != 200:
            print "Change CDH vcore number fail at %s" % cluster_name
            return False

        time.sleep(120)

        # Change CDH container memory
        ret = self.change_container_memory(master_ip, siteid)
        print "Change CDH container memory status code is %s at %s" % (ret, cluster_name)
        if ret != 200:
            print "Change container memory fail at %s" % cluster_name
            return False

        # After change vcore number and container memory, we should restart service
        ret = self.restart_service(master_ip, siteid)
        print "Restart CDH service status code is %s at %s" % (ret, cluster_name)
        if ret != 200:
            print "Restart CDH service fail at %s" % cluster_name
            return False

        time.sleep(720)
        return True


    def install_cdh_by_cluster(self, vm_list, cfg, cluster_name, password, ips):
        print "Installing cdh on %s" % cluster_name
        return self.install_cdh(vm_list, cfg, cluster_name, password, ips[-1], ips)


    def install_hdp_by_cluster(self, vm_list, cfg, cluster_name, password, ips):
        print "Installing HDP on %s" % cluster_name
        return self.install_hdp(vm_list, cfg, cluster_name, password, ips)


    def main(self, cfg_file, os_version):
        # get config file
        cfg = self.parse_config_file(cfg_file)
        if cfg is None:
            return False

        cfg['os'] = os_version
        cfg = self.check_config(cfg)
        if cfg is None:
            return False

        ips = []
        vm_list = []

        queen_ip = cfg['queenNodes'][0]
        queen_vm_name = cfg['queenVMName'][0]
        ips.append(queen_ip)
        vm_list.append(queen_vm_name)

        for worker in cfg['workerNodes']:
            ips.append(worker)

        for worker_name in cfg['workerVMName']:
            vm_list.append(worker_name)

        namenode_ip = cfg['nameNodes'][0]
        namenode_vm_name = cfg['nameVMName'][0]
        ips.append(namenode_ip)
        vm_list.append(namenode_vm_name)

        cluster_name =  cfg['name']

        ret = False
        if 'distroType' in cfg and cfg['distroType'] == "hdp":
            # Generate host file
            self.create_ansible_hosts(vm_list, ips, cfg, cluster_name, len(vm_list), cfg['password'])
            # Install HDP
            ret = self.install_hdp_by_cluster(vm_list, cfg, cluster_name, cfg['password'], ips)
        else:
            ret = self.install_cdh_by_cluster(vm_list, cfg, cluster_name, cfg['password'], ips)

        time.sleep(600)

        return ret
