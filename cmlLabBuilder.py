# Jeff Comer
# click app to deploy nxos vxlan evpn topology to cml

import click
import requests
import json, yaml
import urllib3
import urllib.parse
import hvac
import os, warnings
import csv

#export VAULT_ADDR='ip address for vault'
#export VAULT_TOKEN='vault access token'

API_BASE_URL = "https://172.16.14.40"
API_AUTH_PATH = "/api/v0/authenticate"
API_LAB_IMPORT = "/api/v0/import"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}
authDict = {}

@click.command()
@click.option("--cml_ip", type=str, help='CML IP Address', required=False)
@click.option("--topo", type=str, help='Path and name for topology yaml file', required=True)
def buildCmlTopo(cml_ip, topo):
    #get credentials from vault and acquire bearer token from CML
    client = hvac.Client(verify=False)
    username = client.secrets.kv.v2.read_secret_version(mount_point='cml', path="cml-admin").get("data").get("data").get("username")
    password = client.secrets.kv.v2.read_secret_version(mount_point='cml', path="cml-admin").get("data").get("data").get("password")
    authUrl = API_BASE_URL + API_AUTH_PATH
    cmlAuthPayload = {'username':username, 'password':password}
    response = requests.post(authUrl, headers=headers, json=cmlAuthPayload, verify=False)
    cmlToken = response.json()
    tokenHdrValue = "Bearer " + cmlToken
    headers['Authorization'] = tokenHdrValue

    #read topology yaml and create json payload for api post
    with open(topo, 'r') as topoIn:
        topoYaml = yaml.safe_load(topoIn)
        topJsonStr = json.dumps(topoYaml)
        #print(json.dumps(topoYaml))

    #post to cml and raise exception on error response
    labCreateUrl = API_BASE_URL + API_LAB_IMPORT
    topoCreate = requests.post(labCreateUrl, headers=headers, data=topJsonStr, verify=False)
    topoCreatJson = topoCreate.json()
    labId = str(topoCreate.json()['id'])
    print(labId)

    #start the created lab
    labStartUrl = API_BASE_URL + "/api/v0/labs/" + labId + "/start"
    labStartResponse = requests.put(url=labStartUrl, headers=headers, verify=False)

    #check node status for given lab and start any nodes that failed to start
    



if __name__ == "__main__":
    buildCmlTopo()