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

API_BASE_URL = "https://172.20.104.96"
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
def buildNdfcFabric(fabric_type, fabric, seedfile):
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
        "VRF_LITE_AUTOCONFIG": "Back2Back&ToExternal",
        "FABRIC_INTERFACE_TYPE": "p2p",
        "SUBNET_TARGET_MASK": "31",
        "RP_LB_ID": "251",
        "GRFIELD_DEBUG_FLAG": "Enable"
    }
    createFabResponse = requests.post(fabCreateUrl, headers=headers, json=fabPayload, verify=False)

    #Read data from seed file and discover switches
    with open(seedfile, 'r') as csv_file:
        csvread = csv.DictReader(csv_file)
        csvDict = list(csvread)

    switchList = []
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
                if (csvDict[i]['deviceIp'] == switchInfoJson[k]['ipAddress']):
                    switchDict = {"serialNumber":switchInfoJson[k]['serialNumber'], "role":csvDict[i]['role']}
                    switchRoleList.append(switchDict)
    print(switchRoleList)
    switchRoleResponse = requests.post(switchRoleUrl, headers=headers, json=switchRoleList, verify=False)

if __name__ == "__main__":
    buildNdfcFabric()