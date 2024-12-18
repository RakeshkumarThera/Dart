
# Known Issues

## CIS Benchmark report
### Deviations:

#### KUBELET MASTER
Master Node Reported Failures  

[FAIL] 1.1.13 Ensure that the admission control policy is set to SecurityContextDeny (Scored)  
  * causes pods to fail  

[FAIL] 1.3.3 Ensure that the --use-service-account-credentials argument is set (Scored)  
  * causes isses with pod security protocol and pods will fail.  

[FAIL] 1.5.7 Ensure that the --wal-dir argument is set as appropriate (Scored)  
  * etcd wal-dir defaults to etcd data dir. wal-dir is used for performance tuning. We use only 1 disk in the instance.  

[FAIL] 1.5.8 Ensure that the --max-wals argument is set to 0 (Scored)  
  * etcd defaults to 5 WAL files, 0 = unlimited. We set 20   
    
The following are kube-bench configuration issues, and not actual kubernetes failures:  
  * [FAIL] 1.4.1 Ensure that the API server pod specification file permissions are set to 644 or more restrictive (Scored)
  * [FAIL] 1.4.2 Ensure that the API server pod specification file ownership is set to root:root (Scored)  
  * [FAIL] 1.4.3 Ensure that the controller manager pod specification file permissions are set to 644 or more restrictive (Scored)   
  * [FAIL] 1.4.4 Ensure that the controller manager pod specification file ownership is set to root:root (Scored)  
  * [FAIL] 1.4.5 Ensure that the scheduler pod specification file permissions are set to 644 or more restrictive (Scored) 
  * [FAIL] 1.4.6 Ensure that the scheduler pod specification file ownership is set to root:root (Scored)  
  * [FAIL] 1.4.7 Ensure that the etcd pod specification file permissions are set to 644 or more restrictive (Scored)  
  * [FAIL] 1.4.8 Ensure that the etcd pod specification file ownership is set to root:root (Scored)  
  * [FAIL] 1.4.11 Ensure that the etcd data directory permissions are set to 700 or more restrictive (Scored)  
  * [FAIL] 1.4.12 Ensure that the etcd data directory ownership is set to etcd:etcd (Scored)  
  * [FAIL] 1.4.13 Ensure that the admin.conf file permissions are set to 644 or more restrictive (Scored)  
  * [FAIL] 1.4.14 Ensure that the admin.conf file ownership is set to root:root (Scored)  
  * [FAIL] 1.4.15 Ensure that the scheduler.conf file permissions are set to 644 or more restrictive (Scored)  
  * [FAIL] 1.4.16 Ensure that the scheduler.conf file ownership is set to root:root (Scored)  
  * [FAIL] 1.4.17 Ensure that the controller-manager.conf file permissions are set to 644 or more restrictive (Scored)  
  * [FAIL] 1.4.18 Ensure that the controller-manager.conf file ownership is set to root:root (Scored)  
  * [FAIL] 1.5.1 Ensure that the --cert-file and --key-file arguments are set as appropriate (Scored) 
  * [FAIL] 1.5.2 Ensure that the --client-cert-auth argument is set to true (Scored)  
  * [FAIL] 1.5.4 Ensure that the --peer-cert-file and --peer-key-file arguments are set as appropriate (Scored)  
  * [FAIL] 1.5.5 Ensure that the --peer-client-cert-auth argument is set to true (Scored)  
  * [FAIL] 1.5.9 Ensure that a unique Certificate Authority is used for etcd (Not Scored)   

#### KUBELET NODE
Worker Node Reported failures

[FAIL] 2.1.1 Ensure that the --allow-privileged argument is set to false (Scored)   
   * causes containers to fail  
   
[FAIL] 2.1.7 Ensure that the --protect-kernel-defaults argument is set to true (Scored)  
  * Teradata heavily modified kernel defaults. This fails
    
[FAIL] 2.1.10 Ensure that the --hostname-override argument is not set (Scored)  
  * causes virtual machine lookup/HA issues
  
The following are kube-bench configuration issues, and not actual kubernetes failures:  
  * [FAIL] 2.2.1 Ensure that the kubelet.conf file permissions are set to 644 or more restrictive (Scored)  
  * [FAIL] 2.2.2 Ensure that the kubelet.conf file ownership is set to root:root (Scored)  
  * [FAIL] 2.2.3 Ensure that the kubelet service file permissions are set to 644 or more restrictive (Scored)  
  * [FAIL] 2.2.4 Ensure that the kubelet service file permissions are set to 644 or more restrictive (Scored)  
  * [FAIL] 2.2.5 Ensure that the proxy kubeconfig file permissions are set to 644 or more restrictive (Scored)  
  * [FAIL] 2.2.6 Ensure that the proxy kubeconfig file ownership is set to root:root (Scored)  
```yaml
--allow-privileged : addition of this feature causes canal to break
--protect-kernel-defaults : TD modifies the kernel heavily and this fails
--hostname-override : vSphere HA will possibly have kube-proxy issues if this option is not set
```

### Sonobuoy reports failures
The [Sonobuoy Scanner|https://scanner.heptio.com/] from [Heptio|http://heptio.com/] was used to validate our Kubernetes v1.10.2 installation.  The CIS hardening preformed on the k8s installation caused some Sonobuoy tests to fail.

### DNS record IP changes can bring down the Kubernetes cluster for some time.
The Kubelet, on start, will resolve the IP address from the DNS record and bind to it.
If the IP of the DNS record were to change, the Kubelet will still try to contact the IP it binded to.
Eventually the master nodes will see that the Kubelet of the node is unresponsive so it thinks that the node is down and starts evicting all non-critical pods on it.
The Kubelet will eventually timeout trying to connect to the IP it binded to earlier and try to establish a new connection by resolving the DNS record again.
The Kubernetes cluster can be down for about 10 minutes or so when this happens.

Pods, regardless of this issue, should be designed in such a way as to account for node failure.

Make sure any any DNS records in your kubeconfig, which the Kubelet will pull the server connection details from, resolve to a static IP.

If you are pointing your DNS record to an AWS Load Balancer, please use the Network Load Balancer, which will attach an Elastic IP.

Relevant links:
* https://github.com/kubernetes-incubator/kube-aws/issues/598
* https://kubernetes.io/docs/tasks/administer-cluster/guaranteed-scheduling-critical-addon-pods/
* http://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html

### External Internet access required **MUST NOT ENABLE use_internal_repos**
Internet access is required for release 1.0.0 .  We have a dependency for kibana, calico-cni, flannel, and calico-node which requires internet connection.  Configurator will fail on aws using a non-internet security group as nodes cannot access internet sources.  You must load the correct image manually in this case.

### CVE-2017-7529 - NGINX security issue
The current NGINX version in nginx-ingress-controller-0.9.0-beta.13 is 1.3.5 and is vulnerable to the integer attack.  This issue was patched in NGINX v1.13.2. You will need to upgrade nginx-ingress-controller to at least 0.9.0-beta.16, which upgrades nginx to 1.13.6 to close this security issue.
Relevant links:
* http://mailman.nginx.org/pipermail/nginx-announce/2017/000200.html
* https://github.com/kubernetes/ingress-nginx/blob/nginx-0.9.0/Changelog.md#09-beta16
