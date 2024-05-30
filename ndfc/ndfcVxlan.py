#Jeff Comer
# click app to deploy and configure fabric for vxlan evpn in ndfc

import click
import requests
import json, yaml
import urllib3
import urllib.parse
import hvac
import os, warnings
import csv, pprint

#export VAULT_ADDR='ip address for vault'
#export VAULT_TOKEN='vault access token'

API_BASE_URL = "https://172.16.14.96"
API_AUTH_PATH = "/login"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

@click.command()
@click.option("--fabric_type", type=click.Choice(['Easy_Fabric', 'Easy_Fabric_Classic']), help='[default: Easy_Fabric]',show_default=True, required=False)
@click.option("--fabric", type=str, help='Name of the fabric to create or change', required=True)
@click.option("--seedfile", type=str, help='Path and name of seed file (nsoDevices2.csv for example)', required=True)
@click.option("--port_defs", type=str, help='Path and name of the port definitions(port-defs.csv for example)', required=True)
def buildNdfcFabric(fabric_type, fabric, seedfile, port_defs):
    #get credentials from vault and acquire bearer token from NDFC
    client = hvac.Client(verify=False)
    ndfcusername = client.secrets.kv.v2.read_secret_version(mount_point='cml', path="ndfc-admin").get("data").get("data").get("username")
    ndfcpassword = client.secrets.kv.v2.read_secret_version(mount_point='cml', path="ndfc-admin").get("data").get("data").get("password")
    nxosusername = client.secrets.kv.v2.read_secret_version(mount_point='cml', path="nxos-admin").get("data").get("data").get("username")
    nxospassword = client.secrets.kv.v2.read_secret_version(mount_point='cml', path="nxos-admin").get("data").get("data").get("password")
    authUrl = API_BASE_URL + API_AUTH_PATH
    authPayload = {'username':ndfcusername, 'password':ndfcpassword}
    response = requests.post(authUrl, headers=headers, json=authPayload, verify=False)
    token = response.json()["token"]
    tokenHdrValue = "AuthCookie=" + token
    headers["Cookie"] = tokenHdrValue

    #Create Fabric of Type fabric_type in NDFC
    fabCreateUrl = API_BASE_URL + f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/{fabric_type}'
    fabPayload = {
        "FABRIC_NAME": "cml-nxos-vxlan",
        "BGP_AS": "65100",
        "EXTRA_CONF_TOR": "vrf context management\n        ip route 0.0.0.0/0 172.16.14.254",
        "EXTRA_CONF_LEAF": "vrf context management\n        ip route 0.0.0.0/0 172.16.14.254",
        "EXTRA_CONF_SPINE": "vrf context management\n        ip route 0.0.0.0/0 172.16.14.254",
        "VRF_LITE_AUTOCONFIG": "Back2Back&ToExternal",
        "FABRIC_INTERFACE_TYPE": "p2p",
        "SUBNET_TARGET_MASK": "31",
        "RP_LB_ID": "251",
        "GRFIELD_DEBUG_FLAG": "Enable"
    }
    createFabResponse = requests.post(fabCreateUrl, headers=headers, json=fabPayload, verify=False)
    print("Fabric Create Status: ", createFabResponse)

    #Read data from seed file and discover switches
    with open(seedfile, 'r') as csv_file:
        csvread = csv.DictReader(csv_file)
        csvDict = list(csvread)

    switchList = []
    switchSerialList = []
    seedList = []

    for i in range(len(csvDict)):
        switchDict = {}
        if (csvDict[i]['deviceType'] == "nxos"):
            deviceIndex = csvDict[i]['deviceName'] + "(" + csvDict[i]['serialNumber'] + ")"
            switchDict = {'sysName':csvDict[i]['deviceName'], 'ipaddr':csvDict[i]['deviceIp'], 'deviceIndex':deviceIndex, 'platform':csvDict[i]['platform'], 'version':csvDict[i]['version']}
            switchList.append(switchDict)
            seedList.append(csvDict[i]['deviceIp'])
    seedString = ", ".join(str(x) for x in seedList)
    switchPayload = {"seedIP":seedString, "username":nxosusername, "password":nxospassword, "preserveConfig":False, "switches":switchList}
    addSwitchUrl = API_BASE_URL + f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/discover'
    addSwitchResponse = requests.post( addSwitchUrl, headers=headers, json=switchPayload, verify=False)
    print("Switch Add Status: " + addSwitchResponse.text)

    #routine to get switch serial numbers from ndfc (in CML, they are dynamically generated) and define switch roles
    switchInfoUrl = API_BASE_URL + f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/inventory/switchesByFabric'
    switchRoleUrl = API_BASE_URL + "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/switches/roles"
    switchRoleList = []
    switchInfoResponse = requests.get(switchInfoUrl, headers=headers, verify=False)
    switchInfoJson = switchInfoResponse.json()
    for i in range(len(csvDict)):
        if (csvDict[i]['deviceType'] == "nxos"):
            for k in range(len(switchInfoJson)):
                switchDict = {}
                switchSerialDict = {}
                if (csvDict[i]['deviceIp'] == switchInfoJson[k]['ipAddress']):
                    switchDict = {"serialNumber":switchInfoJson[k]['serialNumber'], "role":csvDict[i]['role']}
                    switchSerialDict = {'host':csvDict[i]['deviceName'], 'serialNumber':switchInfoJson[k]['serialNumber']}
                    switchRoleList.append(switchDict)
                    switchSerialList.append(switchSerialDict)
    switchRoleResponse = requests.post(switchRoleUrl, headers=headers, json=switchRoleList, verify=False)
    print("Switch Role Config Status: ", switchRoleResponse)

    #config host interfaces per port-defs
    switchIntUrl = API_BASE_URL + "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/globalInterface/pti?isMultiEdit=true"
    with open(port_defs, 'r') as ports_file:
        portread = csv.DictReader(ports_file)
        portsDict = list(portread)
    switchIntList = []
    
    for i in range(len(portsDict)):
        for k in range(len(switchSerialList)):
            accessIntDict = {}
            if (switchSerialList[k]['host'] == portsDict[i]['name'] and portsDict[i]['intfType'] == "access"):
                accessInterfaces = []
                accessIntPayload = {
                    "policy": "int_access_host",
                    "interfaces": [
                        {
                            "serialNumber": switchSerialList[k]['serialNumber'],
                            "fabricName": fabric,
                            "ifName": portsDict[i]['interface'],
                            "interfaceType": "INTERFACE_ETHERNET",
                            "nvPairs": {
                                "BPDUGUARD_ENABLED": "true",
                                "PORTTYPE_FAST_ENABLED": "true",
                                "MTU": "jumbo",
                                "SPEED": "Auto",
                                "ACCESS_VLAN": "",
                                "DESC": "",
                                "CDP_ENABLE": "true",
                                "ENABLE_ORPHAN_PORT": "false",
                                "PORT_DUPLEX_MODE": "auto",
                                "CONF": "",
                                "ADMIN_STATE": "true",
                                "ENABLE_NETFLOW": "false",
                                "NETFLOW_MONITOR": "",
                                "NETFLOW_SAMPLER": "",
                                "ENABLE_PFC": "false",
                                "ENABLE_QOS": "false",
                                "QOS_POLICY": "",
                                "QUEUING_POLICY": "",
                                "INTF_NAME": portsDict[i]['interface']
                            }
                        }
                    ]
                }
                print(accessIntPayload)
                switchIntPolResponse = requests.post(switchIntUrl, headers=headers, json=accessIntPayload, verify=False)
                print("Access port config status: ", switchIntPolResponse)
    
    #Create VPC Pair from lear switches
    #https://172.16.14.96/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair
    #{"peerOneId":"9X9F395JCVC","peerTwoId":"949JZ1IIXKW","useVirtualPeerlink":false}
    vpcCreateUrl = API_BASE_URL + "/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/vpcpair"
    vpcList = []
    for i in range(len(csvDict)):
        if (csvDict[i]['vpcId'] != "NA" and csvDict[i]['deviceType'] == "nxos" and csvDict[i]['deviceName'] not in vpcList):
            peer1Name = csvDict[i]['deviceName']
            vpcList.append(peer1Name)
            print(peer1Name)
            for k in range(len(switchInfoJson)):
                if (csvDict[i]['deviceIp'] == switchInfoJson[k]['ipAddress']):
                    peer1Id = switchInfoJson[k]['serialNumber']
                    print(peer1Id)
            for j in range(len(csvDict)):
                if (csvDict[j]['deviceName'] != peer1Name and csvDict[j]['vpcId'] == csvDict[i]['vpcId']):
                    peer2Name = csvDict[j]['deviceName']
                    for l in range(len(switchInfoJson)):
                        if (csvDict[j]['deviceIp'] == switchInfoJson[l]['ipAddress']):
                            peer2Id = switchInfoJson[l]['serialNumber']
            #vpcPayload = {"peerOneId":peer1Id,"peerTwoId":peer2Id,"useVirtualPeerlink":False}
            vpcPayload = {"peerOneId":"9X9F395JCVC","peerTwoId":"949JZ1IIXKW","useVirtualPeerlink":False}
            print(vpcPayload)
            vpcCreateResponse = requests.post(vpcCreateUrl, headers=headers, json=vpcPayload, verify=False)
            print("Create vpc status: ", vpcCreateResponse.text)
                    


    #Recalulate configs based on fabric parms and deploy underlay
    switchRecalcUrl = API_BASE_URL + f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-save'
    switchDeployUrl = API_BASE_URL + f'/appcenter/cisco/ndfc/api/v1/lan-fabric/rest/control/fabrics/{fabric}/config-deploy'
    switchRecalcResponse = requests.post( switchRecalcUrl, headers=headers, verify=False)
    print("Fabric Recalc Status: " + switchRecalcResponse.text)
    switchDeployResponse = requests.post( switchDeployUrl, headers=headers, verify=False)
    print("Switch Config Deploy Status: " + switchDeployResponse.text)

if __name__ == "__main__":
    buildNdfcFabric()