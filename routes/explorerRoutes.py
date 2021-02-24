import dotenv
import dbOperation
import json
import helper
import requests

from datetime           import timedelta
from os                 import getenv
from app                import app, end, final
from flask              import request, jsonify
from middleWare         import *
from bson.json_util     import dumps
from userUtils          import *
from NcloudUtils        import *

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)


# Routes - 
#   Fetch DIR Data
#   Upload File
#   Downlaod File
#   Delete File
#   Create Folder
#   Fetch Only DIR


# This func will check if the user is eligible to use this route
def verifyUser(username:str):
    pass


def get_default_path(req, servers):
    block = {
        "path": None,
        "is_exists": False
    }
    for server in servers:
            if req.get('server_name') == server.get('name') and req.get('server_address') == server.get('address'):
                for host in server.get('hosts'):
                    if req.get('host_name') == host.get('name') and req.get('username') in host.get('validUsers'):
                        block['path'] = host.get('path')
                        block['is_exists'] = True
                        return block

    return block

    

# Using Query Params
@app.route('/dir/', methods=['GET'])
def getDIR():
    req = request.args

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_exists" : False,
        "is_host_exists" : False,
        "data": [],
        "status" : False
    }

    try:
        if isRequiredDataAvailable(req, ["host_name", "server_name", "server_address", "username", "path"]) == False:
            resBlock['msg'] = "No Query data found"
            raise end(Exception)


        servers = getServers(app.DB)

        block:dict = get_default_path(req, servers)
        path:str = block.get('path')

        if block.get('is_exists') == False:
            resBlock['msg'] = "User doesn't exists into the host"
            raise end(Exception)


        if req.get('path').find(path) == 0:
            resBlock['msg'] = "Valid Path"
            resBlock['status'] = True
            #<Pending>

            #</Pending>
            raise final(Exception)
        else:
            resBlock['msg'] = "Invalid Path"
            raise end(Exception)



    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))


@app.route('/explorer/access/', methods=["GET"])
@jwt_required
@onlyselfAllowedINGET
def get_access_for_permission():
    req = request.args

    # Response Block
    resBlock = {
        "msg" : None,
        "token" : None,
        "status" : False
    }

    tokenBLK = {
        "writable": False,
        "host_name": "",
        "server_address": ""
    }

    try:
        if isRequiredDataAvailable(req, ["server_name", "address", "host_name", "path"]) == False:
            resBlock['msg'] = "Missing data"
            raise end(Exception)

        servers = getServers(app.DB)

        targetHost = None

        for server in servers:
            if req.get("address") == server.get("address") and req.get("server_name") == server.get("name"):
                hosts = server.get('hosts')
                tokenBLK["server_address"] = server.get("address")

                for host in hosts:
                    if req.get("host_name") == host.get("name") and req.get("path") == host.get("path"):
                        targetHost = host
                        tokenBLK["host_name"] = host.get("name")
                        break

                break

        
        if targetHost == None:
            resBlock["msg"] = "Host not found"
            raise end(Exception)

        
            
        is_valid_user = True if get_jwt_identity() in targetHost.get("validUsers") else False
        is_shared_user = False

        if is_valid_user:
            tokenBLK["writable"] = targetHost.get("writable")

        if is_valid_user == False and targetHost.get("admin") != None:
            adminObj = targetHost.get("admin")
            tokenBLK["writable"] = adminObj.get("writable")
            is_shared_user = True if get_jwt_identity() in adminObj.get("sharedUsers") else False

        if is_valid_user or is_shared_user:
            resBlock["token"] = create_access_token(identity=get_jwt_claims(), user_claims=tokenBLK, expires_delta = timedelta(days = 300))
            resBlock["msg"] = "Access granted"
            resBlock["status"] = True
            raise final(Exception)
        else:
            resBlock["msg"] = "User not found"
            raise end(Exception)
                
    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))