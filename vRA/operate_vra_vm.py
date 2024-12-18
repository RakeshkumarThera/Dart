import sys
import requests
import json

import argparse

BASE_URL = "https://cloud.labs.teradata.com"

def getMachineId(token, vm):
    headers = {"Accept": "application/json", "Authorization": token}
    ret = requests.get("%s/catalog-service/api/consumer/resources?%%24filter=name+eq+'%s'" %(BASE_URL, vm), headers=headers)

    if ret.status_code != 200:
        print "Get VM %s ID failed" %vm
        sys.exit(1)
    else:
        r = json.loads(ret.text)
        vmId = r["content"][0]["id"]
        subtenantRef = r["content"][0]["organization"]["subtenantRef"]
        subtenantLabel = r["content"][0]["organization"]["subtenantLabel"]
        componentId = r["content"][0]["providerBinding"]["bindingId"]

        return vmId, subtenantRef, subtenantLabel, componentId


def getActionId(token, operation, machineId):
    headers = {"Accept": "application/json", "Authorization": token}
    ret = requests.get("%s/catalog-service/api/consumer/resources/%s/actions" %(BASE_URL, machineId), headers=headers)

    print ret.status_code
    print "ret.text = ", ret.text


def getCreatingSnapshotTemplate(token, machineId, actionId):
    headers = {"Accept": "application/json", "Authorization": token}
    templateUrl = "%s/catalog-service/api/consumer/resources/%s/actions/%s/requests/template" %(BASE_URL, machineId, actionId)
    ret = requests.get(templateUrl, headers=headers)

    if ret.status_code != 200:
        print "Get VM %s template failed" %machineId
        sys.exit(1)
    else:
        print ret.text
        r = json.loads(ret.text)


def getSnapshotReference(token, vmId, vm, actionId, componentId):
    with open("snapshot_reference_template.json", "r") as f:
        j = f.read()
        template = json.loads(j)

    entries = []
    entries.append({"key": "provider-MachineName", "value":{"type": "string", "value": vm}})
    entries.append({"key": "provider-operationId", "value":{"type": "string", "value": "Infrastructure.Virtual.Action.RevertSnapshot"}})
    entries.append({"key": "provider-machineId", "value":{"type": "string", "value": componentId}})
    entries.append({"key": "provider-SnapshotReference"})

    template["dependencyValues"]["entries"] = entries
    headers = {"Accept": "application/json", "Authorization": token, "Content-Type": "application/json"}
    url = "%s/catalog-service/api/consumer/resources/%s/actions/%s/forms/request/provider-SnapshotReference/values" %(BASE_URL, vmId, actionId)
    ret = requests.post(url, data=json.dumps(template), headers=headers)

    if ret.status_code != 200:
        print "Get VM %s snapshot reference failed" %vm
    else:
        r = json.loads(ret.text)
        underlyingValue = r["values"][0]["underlyingValue"]
        snapId = underlyingValue["id"]
        snapName = underlyingValue["label"]
        snapComponentId = underlyingValue["componentId"]

        return snapId, snapName, snapComponentId


def revertSnapshot(token, vms, snapshot):
    template = None
    with open("snapshot_revert_request_template.json", "r") as f:
        j = f.read()
        template = json.loads(j)

    actionId = "8084fff0-71f0-4e67-b80e-be3cd75dc4c1"
    vmInfos = []
    for vm in vms:
        vmId, subtenantRef, subtenantLabel, componentId = getMachineId(token, vm)
        vmInfos.append((vmId, subtenantRef, subtenantLabel, vm, componentId))

    for vmInfo in vmInfos:
        snapId, snapName, snapComponentId = getSnapshotReference(token, vmInfo[0], vmInfo[3], actionId, vmInfo[4])
        template["resourceActionRef"]["id"] = actionId
        template["resourceRef"]["id"] = vmInfo[0]
        template["organization"]["subtenantRef"] = vmInfo[1]
        template["organization"]["subtenantLabel"] = vmInfo[2]

        entries = []
        entries.append({"key": "provider-MachineName", "value": {"type": "string", "value": vmInfo[3]}})
        entries.append({"key": "provider-operationId", "value": {"type":"string", "value": "Infrastructure.Virtual.Action.RevertSnapshot"}})
        entries.append({"key": "provider-machineId", "value": {"type": "string", "value": vmInfo[0]}})
        entries.append({"key": "provider-SnapshotReference", "value": {"type": "entityRef", "componentId": snapComponentId, 
                        "classId": "Infrastructure.Compute.Machine.Snapshot", "id": snapId, "label": snapName}})

        template["requestData"]["entries"] = entries
        print json.dumps(template)
        headers = {"Accept": "application/json", "Authorization": token, "Content-Type": "application/json"}
        url = "%s/catalog-service/api/consumer/requests" %BASE_URL
        ret = requests.post(url, data=json.dumps(template), headers=headers)

        if ret.status_code != 200 and ret.status_code != 201:
            print "Revert snapshot for VM %s failed" %vmInfo[3]
        else:
            print vmInfo[3]


def createSnapshot(token, vms, snapshot):
    template = None
    with open("snapshot_request_template.json", "r") as f:
        j = f.read()
        template = json.loads(j)

    actionId = "ef3c32a4-1d96-4e0e-b2f5-9c605b7cdacb"
    vmInfos = []
    for vm in vms:
        vmId, subtenantRef, subtenantLabel, componentId = getMachineId(token, vm)
        vmInfos.append((vmId, subtenantRef, subtenantLabel, vm, componentId))
    
    for vmInfo in vmInfos:
        template["resourceActionRef"]["id"] = actionId
        template["resourceRef"]["id"] = vmInfo[0]
        template["organization"]["subtenantRef"] = vmInfo[1]
        template["organization"]["subtenantLabel"] = vmInfo[2]

        entries = []
        entries.append({"key": "description", "value": {"type": "string", "value": "REST API Request"}})
        entries.append({"key": "reasons"})
        entries.append({"key": "provider-name", "value": {"type": "string", "value": snapshot}})
        entries.append({"key": "provider-description", "value": {"type": "string", "value": snapshot}})
        entries.append({"key": "provider-memory", "value": {"type": "boolean", "value": True}})

        template["requestData"]["entries"] = entries
        headers = {"Accept": "application/json", "Authorization": token, "Content-Type": "application/json"}
        url = "%s/catalog-service/api/consumer/requests" %BASE_URL
        ret = requests.post(url, data=json.dumps(template), headers=headers)

        if ret.status_code != 200 and ret.status_code != 201:
            print "Create snapshot for VM %s failed" %vmInfo[3]
        else:
            print vmInfo[3]


def powerOn(token, vms):
    actionId = "479a7ac1-5e74-4815-b3e4-d3bd811641f8"

    vmInfos = []
    for vm in vms:
        vmId, subtenantRef, subtenantLabel, componentId = getMachineId(token, vm)
        vmInfos.append((vmId, subtenantRef, subtenantLabel, vm, componentId))

    for vmInfo in vmInfos:
        template = {"type": "com.vmware.vcac.catalog.domain.request.CatalogResourceRequest",
                    "resourceId": vmInfo[0],
                    "actionId":"479a7ac1-5e74-4815-b3e4-d3bd811641f8",
                    "description": None, "data": {"description": None,"reasons": None}}
        headers = {"Authorization": token, "Content-Type": "application/json"}
        url = "%s/catalog-service/api/consumer/resources/%s/actions/%s/requests" %(BASE_URL, vmInfo[0], actionId)
        ret = requests.post(url, data=json.dumps(template), headers=headers)
        if ret.status_code != 200 and ret.status_code != 201:
            print "Power on VM %s failed" %vmInfo[3]
        else:
            print vmInfo[3]


def powerOff(token, vms):
    actionId = "0435c9a3-aa9c-4e98-822d-aa3785b8ab93"

    vmInfos = []
    for vm in vms:
        vmId, subtenantRef, subtenantLabel, componentId = getMachineId(token, vm)
        vmInfos.append((vmId, subtenantRef, subtenantLabel, vm, componentId))

    for vmInfo in vmInfos:
        template = {"type": "com.vmware.vcac.catalog.domain.request.CatalogResourceRequest",
                    "resourceId": vmInfo[0],
                    "actionId":"0435c9a3-aa9c-4e98-822d-aa3785b8ab93",
                    "description": None, "data": {"description": None,"reasons": None}}
        headers = {"Authorization": token, "Content-Type": "application/json"}
        url = "%s/catalog-service/api/consumer/resources/%s/actions/%s/requests" %(BASE_URL, vmInfo[0], actionId)
        ret = requests.post(url, data=json.dumps(template), headers=headers)
        if ret.status_code != 200 and ret.status_code != 201:
            print "Power off VM %s failed" %vmInfo[3]
        else:
            print vmInfo[3]


def getUserToken(user, password):
    data = {"username": "%s@td.teradata.com" %user, "password": password, "tenant":"vsphere.local"}
    headers = {"Content-Type": "application/json"}
    ret = requests.post("%s/identity/api/tokens" %BASE_URL, data=json.dumps(data), headers=headers)

    if ret.status_code != 200:
        print "Get user token failed"
        sys.exit(1)
    else:
        r = json.loads(ret.text)
        token = r["id"]

        return "Bearer %s" %token


def main(args):
    if not args.user or not args.password:
        print "Miss user QuickLook ID and password"
        sys.exit(1)

    token = getUserToken(args.user, args.password)
    
    vms = args.vms.split(",")
    if args.action == "create_snapshot":
        createSnapshot(token, vms, args.snapshot)
    elif args.action == "revert_snapshot":
        revertSnapshot(token, vms, args.snapshot)
    elif args.action == "power_on":
        powerOn(token, vms)
    elif args.action == "power_off":
        powerOff(token, vms)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create or revert snapshot on vRA")
    parser.add_argument('--user', required=True, help='your QuickLook ID')
    parser.add_argument('--password', required=True, help='your password')
    parser.add_argument('--vms', required=True, help='a list of VM name. EX: astere2e151,astere2e152,astere2e153')
    parser.add_argument('--snapshot', required=False, help='provide a snapshot name if want to revert to snapshot')
    parser.add_argument('--action', required=True, help='power_on or revert_snapshot or power_off or reboot or increase_mem or list_vm')

    args = parser.parse_args()
    main(args)
