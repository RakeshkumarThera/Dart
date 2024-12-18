import os
import subprocess

class kube_installer:

    def __init__(self):
        pass


    def create_inventory_file(self, kubemaster, kubenodes, kubemaster_vm_name, kubenodes_vm_name, file_path, password, ansible_path):
        fw = open(file_path, "w")
        with open(ansible_path + "/inventory.yaml", "r") as fr:
            while True:
                line = fr.readline()
                if not line:
                    break
                fw.write(line)

        fw.write("    ansible_user: root\n")
        fw.write("    ansible_ssh_pass: %s\n" %password)

        fw.write("  # EDIT REQUIRED HOSTS #######################################################\n")
        fw.write("  children:\n   kube_cluster:\n     children:\n        kube_master:\n          hosts:\n")
        fw.write("            " + kubemaster_vm_name[0] + ".labs.teradata.com:\n")
        fw.write("              ansible_host: " + kubemaster[0] + "\n\n")
        fw.write("        kube_worker:\n          hosts:\n")
        for i in range(len(kubenodes)):
            fw.write("            " + kubenodes_vm_name[i] + ".labs.teradata.com:\n")
            fw.write("              ansible_host: " + kubenodes[i] + "\n")

        fw.close()


    def run_command(self, cmd):
        p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        status = p.poll()
        output = out + err

        print "status = ", status
        print output
        if status == 0:
            return True
        else:
            return False


    def ping_machine(self, file_path):
        cmd = "/usr/bin/ansible --inventory-file=%s -e 'host_key_checking=False' -u root all -m ping" %file_path
        return self.run_command(cmd)


    def run_ansible(self, file_path, yml_path):
        
        cmd = "/usr/bin/ansible-playbook --inventory-file=%s -u root %s" %(file_path, yml_path)
        return self.run_command(cmd)


    def main(self, kubemaster, kubenodes, kubemaster_vm_name, kubenodes_vm_name, cluster_name, password):
        ansible_path_list = os.path.abspath(__file__).split("/")[:-1]
        ansible_path = "/".join(ansible_path_list) + "/kubekit"
        file_path = ansible_path + "/inventory_" + cluster_name + ".yaml"
 
        self.create_inventory_file(kubemaster, kubenodes, kubemaster_vm_name, kubenodes_vm_name, file_path, password, ansible_path)        

        if not self.ping_machine(file_path):
            print "Ping machine file on %s" %cluster_name
            #os.remove(file_path)
            return False

        if not self.run_ansible(file_path, ansible_path + "/kube-cluster.yml"):
            print "Deploy Kubernate on %s fail" %cluster_name
            #os.remove(file_path)
            return False
        
        os.remove(file_path)
        
        return True


if __name__ == "__main__":
    installer = kube_installer()
    installer.main(["10.25.80.158"], ["10.25.80.159", "10.25.80.160"], ["asterdart0158"], ["asterdart0159","asterdart0160"], "test", "aster4data")
