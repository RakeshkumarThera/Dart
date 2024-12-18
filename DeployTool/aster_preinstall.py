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
# DESCRIPTION: This tool is uesd to execute pre-setting before install
#              Aster. 
#              THe script run steps 1 - 6 follow the following page
#              https://teraworks.teradata.com/pages/viewpage.action?spaceKey=~rp186015&title=FF-R2+Yarn-Based+Installer+Instructions+for+Install+and+Bring-Up

import os
import sys
import shutil
import subprocess
import json
import time

import paramiko


class aster_preinstall:

    def __init__(self):
        pass


    def run_shell_command(self, cmd):
        env = os.environ.copy()
        env["PATH"] = "/usr/sbin:/sbin:" + env["PATH"]
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        out, err = p.communicate()
        status = p.poll()
        output = out + err

        print "status = ", status
        print output
        if status != 0 and err != "":
            return False

        return True


    def exec_command(self, cmd, ssh):
        stdin, stdout, stderr = ssh.exec_command(cmd)
        status = stdout.channel.recv_exit_status()
        print "status = ", status

        if status == 0:
            print "".join(stdout.readlines())
            return True
        elif status == 1 and "already exists" in "".join(stdout.readlines()):
            return True
        elif status == 9 and "already exists" in "".join(stderr.readlines()):
            return True
        else:
            print "".join(stderr.readlines())
            return False


    def create_cluster_config(self, queen_ip, ips, worker_number, is_install_hadoop):
        with open(".cluster_config", "w") as f:
            f.write("PRIMARY_IP=%s\n" %queen_ip)
            f.write("HDFS_NAMENODE=%s\n" %ips[-1])
            f.write("DB_CHECKSUMS=off\n")
            if is_install_hadoop:
                f.write("DB_STORAGE=hdfs\n")
            else:
                f.write("DB_STORAGE=localStorage\n")
            f.write("NUM_WORKERS=%s\n" %worker_number)
            f.write("NUM_PARTITIONS=%s\n" %(worker_number * 2))
    
            f.flush()

        time.sleep(180)


    def check_ssh_connect_on_all_node(self, ips, password):
        for i in range(len(ips)):
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ips[i], username='root', password=password)

            for j in range(len(ips)):
                self.exec_command("ssh -o StrictHostKeyChecking=no root@%s date" %ips[j], ssh_client)
                self.exec_command("su - beehive -c \"ssh -o StrictHostKeyChecking=no %s date\"" % ips[j], ssh_client)

            ssh_client.close()


    def main(self, queen_ip, ips, password, is_install_hadoop):
        location = "/".join(os.path.abspath(__file__).split("/")[:-1])
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect(queen_ip, username='root', password=password)
        if not self.exec_command("groupadd beehive", ssh):
            print "groupadd beehive fail"
            return False

        if not self.exec_command("useradd -m -g beehive -d /home/beehive beehive", ssh):
            print "useradd beehive fail"
            return False

        if not self.exec_command("echo -e \"\n\n\n\" | ssh-keygen -f /root/.ssh/id_dsa -t dsa -N ''", ssh):
            print "Generate ssh key fail"
            return False

        if not self.exec_command("cat /root/.ssh/id_dsa.pub >> /root/.ssh/authorized_keys; chmod 600 /root/.ssh/authorized_keys", ssh):
            print "Make authorized_keys fail"
            return False
        
        if not self.run_shell_command("sshpass -p %s scp -o StrictHostKeyChecking=no -r root@%s:/root/.ssh/ %s/" %(password, queen_ip, location)):
            print "Download key fail"
            return False
    
        for i in range(1, len(ips)):
            if not self.run_shell_command("sshpass -p aster4data scp -o StrictHostKeyChecking=no -pr %s/.ssh root@%s:" %(location, ips[i])):
                print "Transfer key to %s fail" %ips[i]
                return False

        if not self.exec_command("cp -r /root/.ssh /home/beehive/", ssh) or \
                not self.exec_command("chown -R beehive:beehive /home/beehive/.ssh", ssh):
            print "Generate beehive key fail"
            return False

        for i in range(1, len(ips)):
            if not self.exec_command("ssh -o StrictHostKeyChecking=no root@%s date" %ips[i], ssh):
                print "Test ssh passwordless on %s fail" %ips[i]
                return False
    
        shutil.rmtree("%s/.ssh" %location)

        for i in range(1, len(ips)):
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ips[i], username='root', password=password)

            self.exec_command("groupadd beehive", ssh_client)
            self.exec_command("useradd -m -g beehive -d /home/beehive beehive", ssh_client)
            self.exec_command("cp -r /root/.ssh /home/beehive/", ssh_client)
            self.exec_command("chown -R beehive:beehive /home/beehive/.ssh", ssh_client)

            ssh_client.close()

        for i in range(1, len(ips)):
            if not self.exec_command("ssh -o StrictHostKeyChecking=no beehive@%s date" %ips[i], ssh):
                print "Test ssh beehive passwordless on %s fail" %ips[i]
                return False

        for i in range(1, len(ips)):
            if not self.exec_command("su - beehive -c \"ssh -o StrictHostKeyChecking=no %s date\"" %ips[i], ssh):
                print "Test ssh beehive passwordless on %s fail" %ips[i]
                return False

        if not self.exec_command("chmod ugo+rx /sbin/ifconfig", ssh):
            print "Change mode of /sbin/ifconfig fail"
            return False

        for i in range(1, len(ips)):
            ssh_client = paramiko.SSHClient()
            ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh_client.connect(ips[i], username='root', password=password)

            self.exec_command("chmod ugo+rx /sbin/ifconfig", ssh_client)

            ssh_client.close()

        # Create .cluster_config
        self.create_cluster_config(queen_ip, ips, len(ips) - 2, is_install_hadoop)

        # SCP .cluster_config to Queen:/home/beehive/
        if not self.run_shell_command("sshpass -p %s scp -o StrictHostKeyChecking=no .cluster_config root@%s:/home/beehive/" %(password, queen_ip)):
            print "SCP .cluster_config to Queen fail"
            return False

        # Change /home/beehive/.cluster_config owner to beehive
        if not self.exec_command("chown beehive:beehive /home/beehive/.cluster_config", ssh):
            print "Change /home/beehive/.cluster_config owner to beehive fail"
            return False

        self.check_ssh_connect_on_all_node(ips, password)

        # Create /aster in HDFS
        if is_install_hadoop:
            run_command_count = 1
            while run_command_count <= 6:
                ret = self.exec_command("su - hdfs -c \"hdfs dfs -mkdir /aster\"", ssh)
                if ret:
                    break
        
                # Create /aster fail. Sleep 5 minutes then try again
                if run_command_count == 6:
                    print "Create /aster  fail"
                    return False

                run_command_count = run_command_count + 1
                print "Create /aster  fail. Wait for 10 minutes then try again."
                time.sleep(600)

            if not self.exec_command("su - hdfs -c \"hdfs dfs -chown -R beehive:beehive /aster\"", ssh):
                print "Change /aster owner to beehive fail"
                return False

        time.sleep(300)
        os.remove(".cluster_config")

        return True
    

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Please provide config file"
        sys.exit(1)
    else:
        cfg = ""
        with open(sys.argv[1], "r") as f:
            cfg = f.read()

        cfg_dict = json.loads(cfg)
        ips = cfg_dict['ips']
        password = cfg_dict['password']
        queen_ip = cfg_dict['queen_ip']
        a = aster_preinstall()
        a.main(queen_ip, ips, password, False)
