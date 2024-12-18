# [KubeKit Configurator](https://github.td.teradata.com/kubekit/kubekit-configurator)


This [KubeKit](https://teraworks.teradata.com/display/TDUDA/KubeKit+Home?src=contextnavpagetreemode)
component brings up Kubernetes on a given set of infrastructure.

- Uses [Ansible](http://ansible.com/) to configure the hosts
- Support for vSphere and Intelli\* platforms. AWS is **BETA**
- Only vanilla Kubernetes is supported.

## Security Note
- v1.2.0 of of Kubekit-Configurator has hardened the kubernetes installation to the [CIS 1.2.0](https://www.cisecurity.org/benchmark/kubernetes/) specification utilizing the security application [kube-bench](https://github.com/aquasecurity/kube-bench) from [Aqua Security](https://www.aquasec.com/).  Any deviations to the CIS recommendation have been documented in the [KNOWN_ISSUES](KNOWN_ISSUES.md) file.

## Requirements

- Pre-provisioned infrastructure (VMs or physical hosts)
    - For VMs, see [KubeKit Provisioner](https://github.td.teradata.com/kubekit/kubekit-provisioner)

- Inventory (see [example inventory](example-inventory.yaml))

        ansible --inventory-file=./inventory/inventory.local all -m ping

        ansible-playbook --inventory-file=./inventory/inventory.local kube-cluster.yml
- Software
    - ansible >= v2.4.0

### Requirements NOTE

before running ansible-playbook
- High Availability for the masters is disabled by default. To enable High Availability, in the inventory.yaml file set `disable_master_ha = "false"` and make sure to include the variable `kube_virtual_ip_api` with an unassigned and available IP in the cluster network. 
- `docker_registry_path` was moved from `/var` to `/var/lib/docker/registry` This is configurable to a new directory.

### How to Launch Your Local Cluster (Virtualbox with Vagrant)

1. Download the box from Artifactory under `dependencies-snapshot-sd/uda/kubekit/dependencies/tdc-sles-kube-vagrant/`
2. Make sure you don't have any pre-existing boxes: `vagrant box remove NAME`
3. Add the box to Vagrant via `vagrant box add /path/to/box --name NAME`
4. Execute the following instructions

```
cluster_type:'1:1' vagrant up
show_msg=t vagrant status
```

Now run the configurator against your vagrant cluster

```
ansible-playbook -i vagrant_inventory.yaml kube-cluster.yml
```

## Certificates

The configurator can optionally accept user-provided certificates for use by
Kuberentes components. To provide your own certificates, place the following
files in `<INVENTORY_DIR>/files/ssl`:

- ca.crt  (Signing/intermediate CA certificate)
- node.key (Node private key)
- node.crt (CA-signed node certificate)

If any of the certificates files are not provided, the configurator will
generate a self-signed certificate for use by the Kubernetes componentes.

## Configuring Time Servers for Timesyncd (NTP)

The configurator allows for user-provided time servers to be used.
To do so, add a variable in your inventory file with the name `time_servers` and populate it as a list with your time server(s).
Please make sure the time servers you use are reachable and not blocked by any firewalls or time drift issues may arise.

## Additional Users

The group `kube` grants permission to use the kubectl command on the local machine.
kubeconfig is specified via the exported variable KUBECONFIG in /etc/profile.local

## Known issues
  - If using AWS, t2.micro does not have enough processing power to handle Kubernetes and will
  typically fail during the "create DNS" phase.
  - `kubectl describe nodes` will show a warning if you have more than 3 search domains:
     - `Warning  CheckLimitsForResolvConf  2m (x8061 over 2d)  kubelet, 192.168.0.5  Resolv.conf file '/etc/resolv.conf' contains search line consisting of more than 3 domains!`

## Troubleshooting

PROBLEM: I get an error that says "Failed to connect to host via ssh" right
after flannel is restarted.

SOLUTION: This is a known issue ([UKS-195](https://jira.td.teradata.com/jira/browse/UKS-195))
that only occurs when running the configurator over VPN. The current workaround
is to run it from within the same network as the target platform and not over VPN.


## Hacking

These are additional steps you need to perform if you want to contribute code.

### If You Need to Build a New Box

1. Download the latest OVA maintained by the KubeOS team ( see download links on [Kubekit Teraworks Home](https://teraworks.teradata.com/display/TDUDA/KubeKit+Home) )
2. Import it to VirtualBox `VBoxManage import /path/to/ova --vsys 0 --eula accept`
3. Start the VM
4. Login as root/root
5. Run `curl https://raw.githubusercontent.com/mitchellh/vagrant/master/keys/vagrant.pub >> ~/.ssh/authorized_keys`
6. Run `shutdown now`
7. Get the VM's GUID via `VBoxManage list vms`
8. Create the box via `vagrant package --base VM_GUID --output /path/to/save/box`
9. Publish the box to Artifactory in `dependencies-snapshot-sd/uda/kubekit/dependencies/tdc-sles-kube-vagrant/`
10. Make sure to update the config.vm.box setting of the Vagrantfile
