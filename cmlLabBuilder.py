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

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning)

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json"
}

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
    print(cmlToken)
    #read topology yaml and create json payload for api post
    with open(topo, 'r') as topoIn:
        topoYaml = yaml.safe_load(topoIn)
        print(json.dumps(topoYaml))

    #post to cml and raise exception on error response


if __name__ == "__main__":
    buildCmlTopo()