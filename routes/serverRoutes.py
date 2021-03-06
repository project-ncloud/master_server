import dotenv
import dbOperation
import json
import helper
import requests
import psutil

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


@app.route('/servers/', methods = ['OPTIONS'])
def getServerData_dummy():
    return allowCors(jsonify({}))

@app.route('/servers/', methods = ['GET'])
#@jwt_required
#@onlyAdminAllowed
def getServerData():
    return allowCors(jsonify(getServers(app.DB)), 200)



@app.route('/user/servers/', methods = ['GET'])
@jwt_required
@onlyselfAllowedINGET
def getServerDataForUser():
    req = request.args

    # Response block
    resBlock = {
        "msg" : None,
        "data" : [],
        "shared" : [],
        "status" : False
    }

    try:
        if req == None or req.get('username') == None:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        resServer = []
        resShared = []
        
        servers = getServers(app.DB)

        for server in servers:
            hosts = server.get('hosts')
            for host in hosts:
                admin = host.get('admin')

                is_you_user_admin = True if admin.get('name') == req.get('username') else False

                hdd = {
                    "used": 0,
                    "total": 0
                }

                alive = isServerAlive(server)
                if alive :
                    try:
                        res = requests.get(f'http://{server.get("address")}/host/info/', json = {
                            "path": host.get('path')
                        })

                        if res.ok:
                            hdd = res.json()
                        else:
                            raise Exception
                    except Exception:
                        print("Error Occurred :: While getting disk usage")

                if req.get('username') in host.get('validUsers') or host.get('public') == True:
                    resServer.append({
                        "server_name" : server.get('name'),
                        "total": hdd.get("total"),
                        "used": hdd.get("used"),
                        "is_running" : alive,
                        "address" : server.get('address'),
                        "host_name" : host.get('name'),
                        "path" : host.get('path'),
                        "writable" : host.get('writable'),
                        "is_you_user_admin" : is_you_user_admin,
                        "admin" : admin if is_you_user_admin == True else False,
                        "validUsers" : host.get("validUsers") if is_you_user_admin == True else [],
                        "shared": {
                            "writable" : admin.get("writable"),
                            "shared" : admin.get("sharedUsers")
                        } if is_you_user_admin else {}
                    })

                

                if req.get('username') in admin.get('sharedUsers'):
                    resShared.append({
                        "server_name" : server.get('name'),
                        "total": hdd.get("total"),
                        "used": hdd.get("used"),
                        "is_running" : alive,
                        "address" : server.get('address'),
                        "host_name" : host.get('name'),
                        "path" : host.get('path'),
                        "admin_name" : admin.get('name'),
                        "writable" : admin.get('writable')
                    })

        resBlock['data'] = resServer
        resBlock['shared'] = resShared
        resBlock['msg'] = "Operation successful"
        resBlock['status'] = True
        raise final

    
    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))




@app.route('/server/', methods = ['POST'])
def createServer():
    req = request.json

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_name_exists" : False,
        "is_server_address_exists" : False,
        "is_server_running" : False,
        "status" : False
    }

    try:
        if isRequiredDataAvailable(req, ["name", "address", "auto_start"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

            
        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('name'):
                resBlock['msg'] = "Server already exists with this name"
                resBlock['is_server_name_exists'] = True
                raise end(Exception)

            if server.get('address') == req.get('address'):
                resBlock['msg'] = "Server already exists with this path"
                resBlock['is_server_address_exists'] = True
                raise end(Exception)


        try:
            res = requests.get(f'http://{req.get("address")}/init/')
            if not res.ok:
                raise Exception

        except Exception as e:
            resBlock['msg'] = "Server is not running or not exists"
            resBlock['is_server_running'] = False
            raise end(Exception)

        

        # Saving server data into database
        ret, val =  app.DB.insert([{
            "name" : req.get('name'),
            "address" : req.get('address'),
            "autoStart" : req.get('auto_start'),
            "hosts" : []
        }], getenv('SERVER_COLLECTION'))


        if ret == False:
            resBlock['msg'] = "Error ocurred while saving into database"
            raise end(Exception)


        resBlock['msg'] = "Operation successful"
        resBlock['status'] = True
        raise final(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))


@app.route('/server/', methods = ['PUT'])
def changeServerConfig():
    req = request.json

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_name_exists" : False,
        "is_server_address_exists" : False,
        "is_server_running" : False,
        "status" : False
    }

    try:
        if isRequiredDataAvailable(req, ["current_name", "current_address"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        if req.get('hosts') != None:
            req['hosts'] = None

            
        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('current_name') and server.get('address') == req.get('current_address'):
                resBlock['msg'] = "Server already exists with this name"
                resBlock['is_server_name_exists'] = True
                resBlock['is_server_address_exists'] = True

                if req.get('address') != None:
                    try:
                        res = requests.get(f'http://{req.get("address")}/init/')
                        if not res.ok:
                            raise Exception

                        resBlock['is_server_running'] = True

                    except Exception as e:
                        resBlock['msg'] = "Server is not running or not exists"
                        resBlock['is_server_running'] = False
                        raise end(Exception)

                updateBLK = {
                    "name" : server.get('name') if req.get('name') == None else req.get('name'),
                    "address" : server.get('address') if req.get('address') == None else req.get('address'),
                    "address" : server.get('address') if req.get('address') == None else req.get('address'),
                    "autoStart" : server.get('autoStart') if req.get('auto_start') == None else req.get('auto_start')
                }

                ret, msg = app.DB.update_doc({"name" : req.get('current_name')}, updateBLK, getenv('SERVER_COLLECTION'))

                if ret == False:
                    resBlock['msg'] = "Failed while saving server configs into database"
                    raise end(Exception)


                resBlock['msg'] = "Operation successful"
                resBlock['status'] = True
                raise final(Exception)

        resBlock['msg'] = "Server not found"
        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))



@app.route('/server/', methods = ['DELETE'])
def removeServer():
    req = request.json

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_exists" : True,
        "is_server_running" : False,
        "status" : False
    }

    try:
        if isRequiredDataAvailable(req, ["name", "address"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

            
        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('name') and server.get('address') == req.get('address'):
                
                try:
                    res = requests.get(f'http://{req.get("address")}/init/')
                    if not res.ok:
                        raise Exception

                    resBlock['is_server_running'] = True
                    res = requests.get(f'http://{req.get("address")}/reset/')

                    if not res.ok:
                        raise Exception


                except Exception as e:
                    resBlock['msg'] = "Server is not running or not exists"
                    resBlock['is_server_running'] = False
                    raise end(Exception)


                # Removing server data from database
                ret, dummy = app.DB.remove({
                    "name": req.get('name'),
                    "address": req.get('address'),
                }, getenv('SERVER_COLLECTION'))


                if ret == False:
                    resBlock['msg'] = "Error ocurred while removing from database"
                    raise end(Exception)


                resBlock['msg'] = "Operation successful"
                resBlock['status'] = True
                raise final(Exception)

        resBlock['msg'] = "Server not exists"
        resBlock['is_server_exists'] = False
        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))




@app.route('/server/control/<address>', methods = ['GET'])
def getServerInfo(address):
    addr:str = str(address)

    # Response block
    resBlock = {
        "msg" : None,
        "is_running": None,
        "status" : False
    }

    try:
        if addr == None or addr.strip() == '':
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        try:
            res = requests.get(f'http://{addr}/alive/')
            if not res.ok:
                raise Exception
        except Exception as e:
            resBlock['msg'] = "No response from the server"
            resBlock['is_running'] = False
            raise end(Exception)

        resJson = res.json()
        resBlock['msg'] = "Operation successful"
        resBlock['is_running'] = resJson.get('status')
        resBlock['status'] = True
        raise final(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))



@app.route('/server/control/', methods = ['POST'])
def serverControl():
    req = request.json

    # Response block
    resBlock = {
        "msg" : None,
        "is_running": None,
        "status" : False
    }

    try:
        if isRequiredDataAvailable(req,["address", "action"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        try:
            res = requests.post(f'http://{req.get("address")}/alive/', json = {
                "action" : req.get("action")
            })
            if not res.ok:
                raise Exception
        except Exception as e:
            resBlock['msg'] = "No response from the server"
            resBlock['is_running'] = False
            raise end(Exception)

        resJson = res.json()
        resBlock['msg'] = "Operation successful"
        resBlock['is_running'] = resJson.get('status')
        resBlock['status'] = True
        raise final(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))



@app.route('/ncloud/config/', methods = ['GET', 'POST'])
def nCloudConfig():
    data:dict = getNcloudConfig(app.DB)

    # Response block
    resBlock = {
        "msg" : None,
        "data" : None,
        "status" : False
    }

    try:
        if data == None:
            resBlock['msg'] = "Config not found"
            raise end(Exception)

        if request.method == 'GET':
            resBlock['data'] = data
            resBlock['msg'] = "Operation successful"
            resBlock['status'] = True
            raise final(Exception)

        else:
            req = request.json

            if req == None:
                resBlock['msg'] = "No JSON data found"
                raise end(Exception)

            block:dict = {}
            for item in data:
                # Pattern -     "autoStartSrvr": data.get('autoStartSrvr') if req.get('autoStartSrvr') == None else req.get('autoStartSrvr'),
                block.setdefault(item.__str__(), data.get(item.__str__()) if req.get(item.__str__()) == None else req.get(item.__str__()))

            ret, msg = app.DB.update_doc({"name" : "admin"}, block, getenv('ADMIN_COLLECTION'))

            if ret == False:
                resBlock['msg'] = "Failed while saving nCloud configs into database"
                raise end(Exception)

            resBlock['msg'] = "Operation successful"
            resBlock['status'] = True
            raise final(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))

