# Intelli* Kubekit Documentation

*NOTE* This documentation assumes you have a working stacki setup. See https://teraworks.teradata.com/display/TDUDA/Installation+Guide

### Stacki Provision Flags

The first step to setting up kubekit for Intellistar is marking the host for provisioning under the stacki interface. 

First we access the stacki host:
``` 
ssh root@<stacki_master_host>`
```

Then we need to aqcuire the first interface of the target host
```
stack list host //to get the list of hosts
stack list host interface <target host> //To see all interfaces connected to each host
```
For example, if we are trying to get the first interface of `morty3`:

```
[root@sd-tles-stack01 ~]# stack list host interface morty3
HOST   INTERFACE DEFAULT NETWORK  MAC               IP           NAME   MODULE VLAN OPTIONS CHANNEL
morty3 eth0      ------- sm3g_pri 24:6e:96:36:04:c4 39.87.48.14  ------ ------ ---- -------
morty3 eth1      ------- sm3g_sec 24:6e:96:36:04:c5 39.103.48.14 ------ ------ ---- -------
morty3 eth2      True    public   24:6e:96:36:04:c0 10.25.17.95  morty3 ------ ---- -------
```
The IP we are looking for in this case is `39.87.48.14`. With this IP, we can mark the respective host to be provisioned/wiped upon the next reboot. 

```
stack remove host partition "IP"
stack set host attr "IP" attr=nukedisks value=true
stack set host attr "IP" attr=nukecontroller value=true
stack set host boot "IP" action=install
```

If you'd like a convienent helper script for this, use the following.

```
#!/bin/bash
set -x
stack remove host partition "$*"
stack set host attr "$*" attr=nukedisks value=true
stack set host attr "$*" attr=nukecontroller value=true
stack set host boot "$*" action=install
```

### Running the Configurator

Once the host has come back up, copy in your ssh-key to the root user.

`ssh-copy-id root@<targethost>` 

Create a copy of the example inventory file with your hosts and desired configurations.


``` 

Now you're ready to go! Execute the playbook against your cluster and you'll have a kubernetes cluster once the configuration is complete.

`ansible-playbook -i your_inventory kube-cluster.yml`
