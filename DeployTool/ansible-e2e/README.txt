===============================================================================
         Hortonworks Data Platform Installation and Uninstallation
===============================================================================
This folder contains following major ANSIBLE scripts to perform following
operations:
    1. Uninstall HDP and
    2. Install HDP
Let's take a look at the individual operations. Following are some of the
important points to be noted before using these scripts:
    1. Only supports HDP.
    2. Works only in commodity environment (RHEL platform)

Some important variables used in this document are:
    a. INSTALL_DIR=${TOP}/test/tools/HadoopInstallation/HDP




-------------------------------------------------------------------------------
                Pre-requisites to perform HDP Un/Installation 
-------------------------------------------------------------------------------
Before, proceeding further let's take a look at the pre-requisites to 
perform these operations.
I. Following must be installed one the system:
    1. Ansible any version greater than 1.9. To install ANSIBLE follow:
       http://docs.ansible.com/ansible/intro_installation.html
    2. Python version 2.6 or greater should be installed.
    3. CURL should be installed.

II. Create/Modify following files:
    1. Modify '${INSTALL_DIR}/hosts' file to add you cluster details as follows:
       . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
            $ cat ${INSTALL_DIR}/hosts
            [<hdp_cluster_name>]
            <Node1-fdqn> ansible_ssh_pass=<password> ansible_ssh_host=<ip>
            <Node2-fdqn> ansible_ssh_pass=<password> ansible_ssh_host=<ip>
            <Node3-fdqn> ansible_ssh_pass=<password> ansible_ssh_host=<ip>
            <Node4-fdqn> ansible_ssh_pass=<password> ansible_ssh_host=<ip>
       . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

       Please take a look at the existing '${INSTALL_DIR}/hosts' file for more details.
       *** NOTE: You can have multiple cluster information in '${INSTALL_DIR}/hosts' file.
            This will make your file look as follows:
       . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
            $ cat ${INSTALL_DIR}/hosts
            [<hdp_cluster1_name>]
            .
            .
            .

            [<hdp_cluster2_name>]
            .
            .
            .

            [<hdp_cluster3_name>]
            .
            .
            .
       . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

       *** NOTE: Having multiple cluster information does not mean script will 
                perform un/installation on all of them. User will have to kick
                off scripts for individual clusters one by one.

    2. Create a file named '<hdp_cluster_name>' under '${INSTALL_DIR}/group_vars' directory.
       This file will contain the details about the roles of each node.
       Roles can be:
         1. namenode
         2. edgenode
         3. datanode

       Example file format is as follows for cluster HRH023:
       . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .
             $ cat group_vars/HRH023 
             edgenode:   hrh023e1.labs.teradata.com
             namenode:   hrh023m1.labs.teradata.com

             datanodes:
                     node1: hrh023d1.labs.teradata.com
                     node2: hrh023d3.labs.teradata.com
                     node3: hrh023d2.labs.teradata.com
       . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . . .

       *** NOTE: IF YOU HAVE MULTIPLE CLUSTER INFO IN '${INSTALL_DIR}/hosts'
                FILE, THEN FOR EACH CLUSTER THERE SHOULD BE SEPARATE 
                <hdp_cluster_name> FILE UNDER '${INSTALL_DIR}/group_vars'
                DIRECTORY.




-------------------------------------------------------------------------------
           Automating Hadoop Uninstallation (HDP Uninstallation)
-------------------------------------------------------------------------------
* Script Name: Uninstall_HDP.yml 
        This script will perform full uninstallation of hadoop as well as 
ambari server. Once this is done, installation script can be used to perform 
fresh installation. (Please see next section, for HDP installation)
There are three modes of uninstallation:
1. Full - Uninstalls both Hadoop and Ambari. This is the DEFAULT mode.
2. Only Hadoop - Uninstalls only hadoop. Use only_hadoop_uninstall=True.
3. Only Ambari - Uninstalls only ambari. Use only_ambari_uninstall=True.
                 Please make sure hadoop is uninstalled before using this 
                 mode.

* Input parameters to the script:
    Required parameters:
      1. hdp_cluster: Accepts HDP cluster name to be given while performing 
                      uninstallation. Please make sure that You provide correct 
                      cluster name. This can be found by logging on to Ambari.
      2. ambari_server: Host FDQN/IP to be used as ambari server.
    Optional parameters:
      3. ambari_server_port: Ambari server port to be used to connect to Ambari.
                             Default is 8080. Please make sure that you provide
                             correct port. This is the port used to connect to
                             Ambari server.
      4. only_ambari_uninstall: To perform uninstallation of only ambari, this
                                option can be used.
                                Correct values accepted: True and False.
                                Default value is 'False'.
      5. only_hadoop_uninstall: To perform uninstallation of only hadoop, this
                                option can be used.
                                Correct values accepted: True and False.
                                Default value is 'False'.


* How to execute?
    Usage:
        ansible-playbook Uninstall_HDP.yml --extra-vars="hdp_cluster=<hadoop_cluster_name> ambari_server=<ambari_server> ambari_server_port=<port_num>"
    Example:
        1. Full Uninstallation -
            ansible-playbook Uninstall_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081"
        2. Uninstall only hadoop -
            ansible-playbook Uninstall_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081 only_hadoop_uninstall=True"
        3. Uninstall only ambari - 
            ansible-playbook Uninstall_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081 only_ambari_uninstall=True"



-------------------------------------------------------------------------------
             Automating Hadoop Installation (HDP Installation)
-------------------------------------------------------------------------------
* Script Name: Install_HDP.yml
        This script perform full installation of hadoop cluster as well as 
ambari. Hadoop cluster installation is performed using HDP blueprints.
To perform installation one must ensure that cluster does not have old HDP. If 
cluster has HDP already installed, please make sure to run 'Uninstall_HDP.yml'.
There are three modes of installation:
1. Full - Installs both Hadoop and Ambari. This is the DEFAULT mode.
2. Only Hadoop - Installs only hadoop. Use only_hadoop_install=True.
                 Please make sure ambari is installed before using this mode.
3. Only Ambari - Installs only ambari. Use only_ambari_install=True.

* Input parameters to the script:
    Required parameters:
        1. hdp_cluster: Accepts HDP cluster name to be given while installation.
        2. ambari_server: Host FDQN/IP to be used as ambari server.
    Optional parameters:
        3. ambari_server_port: Ambari server port to be used to connect to Ambari.
                               Default 8080.
        4. ambari_server_version: Ambari repo to be used for installation.
                                  Default is 2.2.2
        4. only_ambari_install: To perform uninstallation of only ambari, this
                                option can be used.
                                Correct values accepted: True and False.
                                Default value is 'False'.
        5. only_hadoop_install: To perform uninstallation of only hadoop, this
                                option can be used.
                                Correct values accepted: True and False.
                                Default value is 'False'.

* How to install particular version of HDP?
    Currently, by default these scripts will install 
        * HDP2.4 and 
        * ambari version as 2.2.2.
    But to install some other version on HDP, user needs to follow few things:
        1. Check on hortonworks which ambari version is suitable with which
           HDP version.
        2. Make sure to copy required ambari repo at 
           '${INSTALL_DIR}/roles/ambari_install/files/repo/', if it does not
           exists at the mentioned location. [Ambari repo till 2.2.2 are 
           available in the mentioned directory.]
        3. Update stack version in below blueprint to the HDP version you want
           to set:
             '${INSTALL_DIR}/roles/hadoop_install/files/blueprints/aoh_blueprint
    NOW you're good to go.

* How to execute?
STEP 1: Perform setup and install ambari.
    Usage:
        ansible-playbook Install_HDP.yml --extra-vars="hdp_cluster=<hadoop_cluster_name> ambari_server=<ambari_server> ambari_server_port=<port_num>"
    Example:
        1. With default ambari version -
        >> ansible-playbook Install_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081"
        2. With 2.2.0 ambari version -
        >> ansible-playbook Install_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081 ambari_server_version=2.2.0"
        3. Only ambari installation -
           ansible-playbook Install_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081 ambari_server_version=2.2.0 only_ambari_install=True"
        4. Only hadoop installation -
           ansible-playbook Install_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081 ambari_server_version=2.2.0 only_hadoop_install=True"

    This step generates following three files in /tmp which used for performing
     hadoop installation. 
        1. <hadoop_cluster_name>_ambari_blueprint
        2. <hadoop_cluster_name>_ambari_host_mapping
        3. <hadoop_cluster_name>_ambari_create_hadoop_cluster.sh

STEP 2: Impose blueprint i.e. install hadoop services using blueprint.
    Run following after STEP 1.
        1. cd /tmp
        2. ./<hadoop_cluster_name>_ambari_create_hadoop_cluster.sh

    Track the progress of installation from the output of script or ambari itself. 

***** Improvements planned for the script:
    - Get rid of manual steps like:
        - Provide a way to mention HDP version via command line.
        - Step 2. (Priority 1)
        - Update the tracking and completion of hadoop installation.
    - Provide a way to specify the services. (Create blueprints on the fly)
    - Add support for other features such as Kerberos, LZO, proxy setup etc. (Priority 1)
    - Add support any number of nodes in the cluster. (Shell script)



-------------------------------------------------------------------------------
            Example of HDP Un-installation and Installation
-------------------------------------------------------------------------------
Step 1: Required files are created as follows:
        A] hosts file:
            $ cat hosts 
            [HRH023]
            hrh023m1.labs.teradata.com ansible_ssh_pass=TCAMPass123 ansible_ssh_host=10.25.215.135
            hrh023d1.labs.teradata.com ansible_ssh_pass=TCAMPass123 ansible_ssh_host=10.25.215.113
            hrh023d2.labs.teradata.com ansible_ssh_pass=TCAMPass123 ansible_ssh_host=10.25.214.197
            hrh023d3.labs.teradata.com ansible_ssh_pass=TCAMPass123 ansible_ssh_host=10.25.215.141
            hrh023e1.labs.teradata.com ansible_ssh_pass=TCAMPass123 ansible_ssh_host=10.25.215.83

            [ambari-server]
            hrh023m1.labs.teradata.com ansible_ssh_pass=TCAMPass123

        B] File in group_vars:
            $ cat group_vars/HRH023 
            edgenode:   hrh023e1.labs.teradata.com
            namenode:   hrh023m1.labs.teradata.com

            datanodes:
                    node1: hrh023d1.labs.teradata.com
                    node2: hrh023d3.labs.teradata.com
                    node3: hrh023d2.labs.teradata.com

Step 2: Uninstall previous HDP cluster [HRH023], where ambari server resides on 'hrh023m1.labs.teradata.com' listening at port '8081'. 
        >> ansible-playbook Uninstall_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081"

Step 3: Installing HDP2.4 with ambari server residing on 'hrh023m1.labs.teradata.com' listening at port '8081' with cluster name as 'HRH023', with 2.2.0 ambari version.
        >> ansible-playbook Install_HDP.yml --extra-vars="hdp_cluster=HRH023 ambari_server=hrh023m1.labs.teradata.com ambari_server_port=8081 ambari_server_version=2.2.0"

Step 4: Execute script in /tmp
        >> cd /tmp
        >> ./<hadoop_cluster_name>_ambari_create_hadoop_cluster.sh




--------------
SUPPORT NOTES:
--------------
1. This script has been tested against following versions of HDP
        * HDP2.3
        * HDP2.4
2. Currently, this un/install script targets following hadoop services:
        * AMBARI_METRICS
        * FALCON
        * FLUME
        * HBASE
        * HDFS
        * HIVE
        * KERBEROS (Yet to be tested with installation)
        * MAHOUT
        * MAPREDUCE2
        * OOZIE
        * PIG
        * SLIDER
        * SPARK
        * SQOOP
        * TEZ
        * YARN
        * ZOOKEEPER
3. Cluster configuration being target here is:
        1 Master Node
        1 Edge Node
        3 data nodes
4. Linux distribution supported here are:
        * RHEL


---------------------
Troubleshooting Tips:
---------------------
1. ERROR Seen while running some curl commands in hadoop uninstallation: 
     "curl: (7) couldn't connect to host" 

   This error is majorly observed when curl tries to connect to an invalid URL.
   Please make sure the AMBARI URL shown in the error is correct and you
   have passed correct arguments to the ANSIBLE script.


