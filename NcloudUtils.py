from db         import Mongo
from os         import getenv
from helper     import *

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