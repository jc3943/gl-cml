#Jeff Comer
# click app to configure vxlan evpn overlay in ndfc

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