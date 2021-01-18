import dotenv
import dbOperation
import json
import helper
import requests

from os                 import getenv
from app                import app, end, final
from flask              import request, jsonify
from middleWare         import allowCors, isValidKEY, isRequiredDataAvailable
from bson.json_util     import dumps
from userUtils          import *
from NcloudUtils        import *


@app.route('/server/host/users/', methods = ['POST', 'DELETE'])
def addUsersIntoHost():
    # Assigning only json data
    req:dict = request.json

    # Response block
    resBlock = {
        "msg" : None,
        "error": [],
        "status": False
    }

    try:
        # Checking if the client sent json data with the request.
        if req == None or req.get('address') == None or req.get('address') == None or req.get('users') == None:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)


        # Fetching all Pi Server_data from the database
        servers = getServers(app.DB)

        # Decision variable to ensure that all the operations are executing successfully
        # 0 = No Error | 0 < = Error
        operationStatus = 0
        operationLimit = 0
        host_found = False
        server_found = False

        reqServer = None
        reqHost = None

        # Looping through the server data to add the username into each server's host
        for server in servers:
            if server.get('address') == req.get('address'):
                reqServer = server
                break

        # Checking if the server is exists or not
        if reqServer == None:
            resBlock['msg'] = "Server not found"
            raise end(Exception)


        # Checking if the server is alive or not
        if isServerAlive(server) == False:
            resBlock['msg'] = "Server is currently down"
            raise end(Exception)


        # Getting hosts
        hosts = reqServer.get('hosts')

        for host in hosts:
            if host.get('name') == req.get('hostname'):
                reqHost = host
                break

        # Checking if the server is exists or not
        if reqHost == None:
            resBlock['msg'] = "Host not found"
            raise final(Exception)
        


        validUsers = reqHost.get('validUsers')

        for user in req.get('users'):
            try:
                operationLimit += 1
                # Sending request to the Pi Server to add or remove the username to all of it's hosts
                if request.method == 'POST':
                    if user.lower() in validUsers:
                        resBlock['error'].append({
                            "username" : user.lower(),
                            "exists" : True
                        })
                        continue


                    userData:dict = app.DB.get_doc({"username": user.lower()}, getenv('USER_COLLECTION'))

                    if userData == None:
                        resBlock['error'].append({
                            "username" : user.lower(),
                            "exists" : False,
                            "inDB" : False
                        })
                        continue

                    res = requests.post(f'http://{server.get("address")}/user/', json = {
                        "username" : user,
                        "password" : userData.get("password"),
                        "hostname" : req.get('hostname')
                    })

                    if res.ok:
                        validUsers.append(user.lower())
                        operationStatus += 1
                    else:
                        raise Exception

                else:
                    if user.lower() not in validUsers:
                        resBlock['error'].append({
                            "username" : user.lower(),
                            "exists" : False
                        })
                        continue

                    res = requests.delete(f'http://{server.get("address")}/user/', json = {
                        "username" : user,
                        "hostname" : req.get('hostname')
                    })

                    if res.ok:
                        validUsers.remove(user.lower())
                        operationStatus += 1
                    else:
                        raise Exception

            except Exception as e:
                print(f'Exception :: {e}')
                resBlock['error'].append({
                    "username" : user.lower(),
                    "exists" : True,
                    "op_status" : False
                })

        reqHost.setdefault('validUsers', validUsers)
        ret, msg = app.DB.update_doc({"address" : reqServer.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                
        print(f'Operation state - {operationStatus}, \t Limit - {operationLimit}')
        if operationStatus == operationLimit:
            pass
        elif operationStatus > 0 and operationStatus < operationLimit:
            resBlock['msg'] = "Some targets are not completed"
            resBlock['status'] = True
            raise final(Exception)
        else:
            resBlock['msg'] = "Failed while adding users to the server" if request.method == 'POST' else "Failed while removing users from the server"
            raise end(Exception) 

        resBlock['msg'] = "Operation successful"
        resBlock['status'] = True
        raise final(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))
        

@app.route('/server/host/', methods = ['POST'])
def createHost():
    req = request.json

    # Response block
    resBlock = {
        "msg" : None,
        "is_server_exists" : None,
        "is_host_name_exists" : None,
        "is_host_path_exists" : None,
        "status" : False
    }

    try:
        if isRequiredDataAvailable(request.json, ["name", "path", "writable", "public", "server_name"]) == False:
            resBlock['msg'] = "Bad request"
            raise end(Exception)

        
        # Fetching all Pi Server_data from the database
        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('server_name'):

                resBlock['is_server_exists'] = True

                if isServerAlive(server) == False:
                    resBlock['msg'] = "Server needs to be online while creating host"
                    raise end(Exception)

                # Checking if any host with same name or same path exists
                hosts = server.get('hosts')
                for host in hosts:
                    if host.get('name') == req.get('name'):
                        resBlock['msg'] = "Same host name already exists into this server"
                        resBlock['is_host_name_exists'] = False
                        raise end(Exception)

                    if host.get('path') == req.get('path'):
                        resBlock['msg'] = "Same host path already exists into this server"
                        resBlock['is_host_path_exists'] = False
                        raise end(Exception)


                try:
                    hostBLK = {
                        "name" : req.get('name'),
                        "path" : req.get('path'),
                        "writable" : req.get('writable'),
                        "public" : req.get('public'),
                        "validUsers": []
                    }
                    res = requests.post(f'http://{server.get("address")}/host/', json = hostBLK)

                    if not res.ok:
                        raise Exception

                except Exception as e:
                    resBlock['msg'] = "Failed while creating host"
                    raise end(Exception)
                
                hosts.append(hostBLK)
                ret, msg = app.DB.update_doc({"address" : server.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                resBlock['msg'] = "Operation successful"
                resBlock['status'] = True
                raise final(Exception)

        resBlock['msg'] = "Server not found"
        resBlock['is_server_exists'] = False
        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))


@app.route('/server/host/', methods = ['DELETE'])
def removeHost():
    req = request.json

    # Response block
    resBlock = {
        "msg" : None,
        "is_server_exists" : None,
        "is_host_exists" : None,
        "status" : False
    }

    try:
        if isRequiredDataAvailable(request.json, ["name", "path", "server_name"]) == False:
            resBlock['msg'] = "Bad request"
            raise end(Exception)

        
        # Fetching all Pi Server_data from the database
        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('server_name'):

                resBlock['is_server_exists'] = True

                if isServerAlive(server) == False:
                    resBlock['msg'] = "Server needs to be online while creating host"
                    raise end(Exception)

                # Checking if any host with same name or same path exists
                hosts = server.get('hosts')
                for host in hosts:
                    if host.get('name') == req.get('name') and host.get('path') == req.get('path'):
                        
                        resBlock['is_host_exists'] = True
                        
                        try:
                            res = requests.delete(f'http://{server.get("address")}/host/', json = {
                                "name": req.get('name'),
                                "path": req.get('path')
                            })

                            if not res.ok:
                                raise Exception

                        except Exception as e:
                            resBlock['msg'] = "Failed while removing host"
                            raise end(Exception)

                        hosts.remove(host)
                        ret, msg = app.DB.update_doc({"address" : server.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                        resBlock['msg'] = "Operation successful"
                        resBlock['status'] = True
                        raise final(Exception)


                resBlock['msg'] = "Host not found"
                resBlock['is_host_exists'] = False
                raise end(Exception)

        resBlock['msg'] = "Server not found"
        resBlock['is_server_exists'] = False
        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))


@app.route('/server/host/config/', methods = ['POST'])
def changeConfigHost():
    req = request.json

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_exists" : False,
        "is_host_exists" : False,
        "status" : False
    }

    try:
        if isRequiredDataAvailable(req, ["current_host_name", "server_name"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        if req.get('validUsers') != None:
            req['validUsers'] = None


        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('server_name'):
                resBlock['is_server_exists'] = True

                hosts = server.get('hosts')

                for host in hosts:
                    if host.get('name') == req.get('current_host_name'):
                        resBlock['is_host_exists'] = True

                        try:
                            res = requests.post(f'http://{server.get("address")}/host/config/', json = {
                                "name" : req.get('name'),
                                "path" : req.get('path'),
                                "writable" : req.get('writable'),
                                "public" : req.get('public'),
                                "currentHostName" : req.get('current_host_name')
                            })

                            if not res.ok:
                                raise Exception

                        except Exception as e:
                            resBlock['msg'] = "Failed while changing config in host"
                            raise end(Exception)

                        for item in host:
                            # Pattern -     "autoStartSrvr": data.get('autoStartSrvr') if req.get('autoStartSrvr') == None else req.get('autoStartSrvr'),
                            host.__setitem__(item.__str__(), host.get(item.__str__()) if req.get(item.__str__()) == None else req.get(item.__str__()))

                        ret, msg = app.DB.update_doc({"address" : server.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                        resBlock['msg'] = "Operation successful"
                        resBlock['status'] = True
                        raise final(Exception)
                
                resBlock['msg'] = "Host not found"
                raise end(Exception)
        
        resBlock['msg'] = "Server not found"
        raise end(Exception)
  
    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))


# Dont need this method because we can do all with above method
'''@app.route('/server/host/user/', methods = ['POST', 'DELETE'])
def hostUserOps():
    # Assigning only json data
    req:dict = request.json

    # Checking if the client sent json data with the request.
    if req == None or req.get('address') != None or req.get('address') != None or req.get('user') != None:
        return allowCors(jsonify({"msg" : "No JSON Data found"}),400)
 
    # Fetching all Pi Server_data from the database
    servers = getServers(app.DB)

    # Decision variable to ensure that all the operations are executing successfully
    # 0 = No Error | 0 < = Error
    operationStatus = 0
    host_found = False
    server_found = False

    # Looping through the server data to add the username into each server's host
    for server in servers:
        if server.get('address') == req.get('address'):
            hosts = server.get('hosts')
            server_found = True
            # Checking if the server is alive or not
            if isServerAlive(server) == False:
                return allowCors(jsonify({"msg": "Server found but it's not turned on"}),401)
            
            for host in hosts:
                if host.get('name') == req.get('name'):
                    host_found = True
                    validUsers = host.get('validUsers')
                    user = req.get('user')
                    
                    try:
                        if (request.method == 'POST' and user.lower() in validUsers) or (request.method == 'DELETE' and user.lower() not in validUsers):
                            print('User found')
                            raise Exception

                        # Sending request to the Pi Server to add or remove the username to all of it's hosts
                        if request.method == 'POST':
                            res = requests.post(f'http://{server.get("address")}/Pending', json = {
                                "username" : user
                            })
                        else:
                            res = requests.post(f'http://{server.get("address")}/Pending', json = {
                                "username" : user
                            })

                        if res.ok:
                            if request.method == 'POST':
                                validUsers.append(user.lower())
                                print(f'{user} added into {host.get("name")}')
                            else:
                                validUsers.remove(user.lower())
                                print(f'{user} removed from {host.get("name")}')
                        else:
                            raise Exception
                    except Exception as e:
                        operationStatus = 1
                        print(f'{user} user operation failed while processing\t\t [{host.get("name")}]')

                    host.setdefault('validUsers', validUsers)
                    ret, msg = app.DB.update_doc({"address" : server.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))

    if not server_found:
        return allowCors(jsonify({"msg": "Server not found"}),404)

    if not host_found:
        return allowCors(jsonify({"msg": "Server found but it's not turned on"}),401)
            
    if operationStatus != 0:
        return allowCors(jsonify({"msg": "Some targets are failed"}),400)

    return allowCors(jsonify({"msg": "Success"}))
    '''