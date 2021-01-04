import dotenv
import dbOperation
import json
import helper
import requests

from os                 import getenv
from app                import app
from flask              import request, jsonify
from middleWare         import allowCors, isValidKEY
from bson.json_util     import dumps
from userUtils          import *
from NcloudUtils        import *


@app.route('/server/host/users/', methods = ['POST', 'DELETE'])
def hostUsersOps():
    # Assigning only json data
    req:dict = request.json

    # Checking if the client sent json data with the request.
    if req == None or req.get('address') != None or req.get('address') != None or req.get('users') != None:
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
                    for user in req.get('users'):
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
                            operationStatus += 1
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
        




@app.route('/server/host/user/', methods = ['POST', 'DELETE'])
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