from db         import Mongo
from os         import getenv
from helper     import *
from requests   import get

def getNcloudConfig(DB:Mongo):
    data:dict = DB.get_doc({}, getenv('ADMIN_COLLECTION'))
    if data == None:
        return None

    return {
        "addall_inNewHosts": data.get('addall_inNewHosts'),
        "autoStartSrvr": data.get('autoStartSrvr'),
        "allowRegistration": data.get('allowRegistration'),
        "pendingNewUser": data.get('pendingNewUser')
    }


def getServers(DB:Mongo):
    block:dict = DB.get_docs({}, getenv('SERVER_COLLECTION'))
    NN = Nas(block)
    return NN.getBlock()


def allAlive(DB:Mongo):
    servers:dict = getServers(DB)
    counter = 0
    for server in servers:
        try:
            res = get(f'http://{server.get("address")}/init/')

            if res.ok == False:
                raise Exception

        except Exception as e:
            print(f'Error ocurred :: {server.get("address")} is not alive\t\t[{server.get("name")}]')
            return False
    
    return True

def isServerAlive(server:dict):
    try:
        res = get(f'http://{server.get("address")}/init/')

        if res.ok == False:
            raise Exception

    except Exception as e:
        print(f'Error ocurred :: {server.get("address")} is not alive\t\t[{server.get("name")}]')
        return False

    return True