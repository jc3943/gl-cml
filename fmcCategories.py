# TEST OBJECT POSTING
import json
import difflib
import sys
import requests
import pprint
import copy
import warnings
import time
import os
#from collections import MutableMapping

warnings.filterwarnings('ignore') # Turn off Warnings

def debug_echo(on,vnam,param):
# Debug Print Function
    if on:
        ftd ="TRACE=====>> "
        btd =" <<=====TRACE"
        print("")
        print (ftd + vnam +" = "+ str(param) + btd)
        print("")
#END ECHO CODE
def rest_get (url):
    debug_echo(True,"Invoked rest_get URL = ", url)
#    global json_resp
#    json_resp.clear()
    try:
        r = requests.get(url, headers=headers, verify=False)
        status_code = r.status_code
        print(status_code)
        resp = r.text
#        print(resp)  
        if (status_code == 200):
            print("GET successful. Response data --> ")
            json_resp = json.loads(resp)
#            print(json.dumps(json_resp,sort_keys=True,indent=4, separators=(',', ': ')))
        else:
            r.raise_for_status()
            print("Error occurred in GET --> "+resp)
    except requests.exceptions.HTTPError as err:
        print ("Error in connection --> "+str(err))
    finally:
        if r : r.close()
    return(json_resp)
    debug_echo(ON,"Exited rest_get",np)
#END GET CODE
def rest_del (url):
    debug_echo(ON,"Invoked REST_DEL URL = ", url)
    try:
        r = requests.delete(url, headers=headers, verify=False)
        status_code = r.status_code
        resp = r.text
        print (resp)
        print (status_code)
        if (status_code == 200):
            print("DELETE successful. Response data --> ")
            json_resp = json.loads(resp)
#            print(json.dumps(json_resp,sort_keys=True,indent=4, separators=(',', ': ')))
        else:
            r.raise_for_status()
            print("Error occurred in DELETE --> "+resp)
    except requests.exceptions.HTTPError as err:
        print ("Error in connection --> "+str(err))
    finally:
        if r : r.close()
    return(json_resp)
    debug_echo(ON,"Exited rest_del",np)
#END DELETE CODE
def rest_post(url,payload):
    debug_echo(ON,"Invoked rest_post URL",url)
    debug_echo(ON,"Passed post payload",type(payload))
    try:
        print("Trying to post")
        data = json.dumps(payload)
        print("DATA = ",data,type(data))
        r = requests.post(url, data=json.dumps(payload), headers=headers, verify=False)
        print("Reply=",r)
        status_code = r.status_code
        resp = r.text
        if (status_code == 201 or status_code == 202):
            print("Post was successful..."+url)
            jr = json.loads(resp)
        else:
            r.raise_for_status()
            print("Status code:-->"+str(status_code))
            print("Error occurred in POST --> "+str(resp))
    except requests.exceptions.HTTPError as err:
        print ("Error in connection --> "+str(err))
        print (resp)
        pass
    finally:
        if r : r.close()
    return(jr)
#END POST CODE
def rest_put(url,payload):
    debug_echo(ON,"Invoked rest_put URL",url)
    debug_echo(ON,"Passed payload",payload)
    try:
        print("I'm trying to put here!!!")
        print("URL is",url)
        print("TYPE OF PAYLOAD IS:", type(payload))
        print("PAYLOAD is",payload)
        r = requests.put(url, data=payload, headers=headers, verify=False)
        r = requests.put(url, data=json.dumps(payload), headers=headers, verify=False)
        status_code = r.status_code
        resp = r.text
        if (status_code == 200):
            print("Put was successful...")
            jr = json.loads(resp)
            print(json.dumps(jr,sort_keys=True,indent=4, separators=(',', ': ')))
        else:
            r.raise_for_status()
            print("Status code:-->"+str(status_code))
            print("Error occurred in PUT --> "+resp)
    except requests.exceptions.HTTPError as err:
        print ("Error in connection --> "+str(err))
        print (resp)
    finally:
        if r : r.close()
    return(jr)
    debug_echo(OFF,"Exited rest_put",np)
#END PUT CODE

def GFS(sourceofTruth): # GET FILE SIZE (the number of lines in the file)
     with open(sourceofTruth,'r') as SOT:   # SOT is the Source of Truth
        prfrows=SOT.readlines()
     fsiz=len(prfrows)
     print(fsiz)
     return(fsiz)
#END GET FILE SIZE

def read_prf(sourceofTruth):    #List Read Policy Rule File (prf)
    debug_echo(ON,"Invoked read_prf. Source of truth is ",sourceofTruth)
    prfrow=[]
    with open(sourceofTruth,'r') as SOT:   # SOT is the Source of Truth
        prfow=SOT.readlines()
#    print("----->>> ", type(prfrow),prfrow)
    print("----->>> ", type(prfrow))
    return (prfrow)
#END READ POLICY RULE FILE AND STORE IN A LIST
def delete_keys_from_dict(dictionary, keys):
        keys_set = set(keys)

        modified_dict = {}
        for key, value in dictionary.items():
                if key not in keys_set:
                        if isinstance(value, MutableMapping):
                                modified_dict[key] = delete_keys_from_dict(value, keys_set)
                                continue
                        elif isinstance(value, list):
                                for i in range(len(value)):
                                        if isinstance(value[i], MutableMapping):
                                                value[i] = delete_keys_from_dict(value[i], keys_set)

                        modified_dict[key] = "" if key in value_to_be_emptied else copy.deepcopy(value)

        return modified_dict
#END READ POLICY RULE FILE AND STORE IN A LIST
def pretty_print(data):
        res = json.dumps(data, indent=indent_size, sort_keys=True)
        print(res)

np = ""                           # No Paramenter
blank= " "                        # Blank Space
comma=","
dot="."
ON = True
OFF = False
server = "https://172.16.14.89" # Set the server IP (FMC)
new_resp = {} # A post response dictionary used to extract key values 
# Set the username and password credentials to generate an authentication token

username = "admin"
password = "DEVP@ssw0rd"

print (" ")
print (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
print ("===>>>  catg.py has started  <<<===")
print ("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
print (" ")
os.system('date')
print ("-- ARCHIVE FMC IN JSON --")
oc = 0 # Object count =  number of objects in the sot file
gc = 0 # Group count
obdic = {} # Dictionary which is a list of objects. The source of truth is an object that contains a list of objects.
oob =  {} # One Object
oids = [] # Object ID List = list of uuids
nmiddic = {"name" : " ", "id" : " "} # Name ID dictionary (for group creation)
nmiddiclst = [] # Name ID dictionary List (for group creation)
gplol =[] #group payload object(id) list
keys_to_be_deleted=["metadata","links","paging"]
value_to_be_emptied=["id"]

debug_echo(ON,"= BEGIN GENERATING AUTHENTICATION TOKEN",np)
r = None
headers = {'Content-Type': 'application/json'}
api_auth_path = "/api/fmc_platform/v1/auth/generatetoken"
auth_url = server + api_auth_path
try:
    r = requests.post(auth_url, headers=headers, auth=requests.auth.HTTPBasicAuth(username,password), verify=False)
    auth_headers = r.headers
    auth_token = auth_headers.get('X-auth-access-token', default=None)
    if auth_token == None:
        print("auth_token not found. Exiting...")
        sys.exit()
except Exception as err:
    print ("Error in generating auth token --> "+str(err))
    sys.exit()
headers['X-auth-access-token']=auth_token
debug_echo(ON,"AUTHENTICATION TOKEN IS: ", auth_token)
#**************************************
#End Generate the authentication token*
#**************************************
print(" --Authentication Token Generated.")
os.system('date')

#SET POLICY URI

pol_path = "/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/policy/accesspolicies"
purl=server + pol_path # Policy Container URL

#CREATE TEST CATEGORIES

categories = ["TestCategory1",
            "TestCategory2",
            "TestCategory3"]
print("Number of Categories: ",len(categories))


#CREATE THE TEST POLICY PAYLOAD

appl={
  "type": "AccessPolicy",
  "name": "cattst_fw_policy",
  "defaultAction": {
    "action": "BLOCK"
  }
}
#POST THE TEST POLICY AND GET THE OBJECT UUID IN ORDER TO BUILD THE CATEGORY URI
try:
    app=rest_post(purl,appl)
    print("policy "+appl["name"]+" container object posted")
except:
    print("policy post exception... trying to continue")
    pass
print (app["id"])
prid= app["id"]
print ("PRID= ",prid)

#CREATE THE TEST CATEGORY PAYLOAD 
catpay={  "type": "Category",
          "name": ""
       }
print(catpay)

#SET THE CATEGORY URI
tcurl = " https://172.16.14.89/api/fmc_config/v1/domain/e276abec-e0f2-11e3-8169-6d9ed49b625f/policy/accesspolicies/"+prid+"/categories?section=Mandatory"
print(tcurl)


#BEGIN THE CATEGORY POSTING LOOP
for category in range(0,len(categories)):
    print(category)
    catpay["name"]=categories[category]
    print(catpay)
    try:
        catline=rest_post(tcurl,catpay)
        print("category "+catpay["name"]+" container object posted")
    except:
        print("policy post exception... trying to continue")
        pass

print (" ")
print (">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
print ("===>>>  catg.py has ended  <<<===")
print ("<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")