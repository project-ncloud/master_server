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

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)


@app.route('/api/init/', methods = ['GET'])
def init():
    response = jsonify(message="Simple server is running")
    return allowCors(response)



@app.route('/register/', methods = ['POST'])
def register():
    req = request.form
    userName:str = req['username']

    # Checking if registration allowed or not
    res = requests.get(f'http://{getenv("OWN_URL")}/server/config/')
    serverConfig:dict = res.json()
    if serverConfig.get('allowRegistration') != True:
        return allowCors(jsonify({"msg" : "Registration not allowed", "status" : False}), 400)

    # Deciding if the registered user data need to save pending section or main database
    collection:str = getenv('USER_COLLECTION') if serverConfig.get('pendingNewUser') != True else getenv('PENDING_USER_COLLECTION')

    # Some other checks regarding username and KEY
    isExists:bool = dbOperation.userExists(userName.strip().lower(), app.DB)
    allowed:bool = isValidKEY(req['KEY'], req['userType'])

    if isExists:
        return allowCors(jsonify({"msg" : "User already exists", "status" : False}))

    if not allowed:
        return allowCors(jsonify({"msg" : "KEY do not match", "status" : False}), 400)


    # Creating user block to insert into the database
    block = {
        "name" : f'{req["name"].strip()}',
        "username" : f'{req["username"].strip().lower()}',
        "password" : f'{req["password"].strip()}',
        "type" : f'{req["userType"].strip()}',
    }
    if app.DB.insert([block], collection) != None:
        return allowCors(jsonify({"msg" : "Added User", "status" : True}))
    
    return allowCors(jsonify({"msg" : "Failed to add user", "status" : False}))



@app.route('/login/', methods = ['POST'])
def login():
    req = request.form
    username:str = req['username']

    isExists:bool = dbOperation.userExists(username.strip().lower(), app.DB)
    
    if isExists:
        block = app.DB.get_doc({
            "username" : username
        }, getenv('USER_COLLECTION'))

        if block.get('password') == req['password'].strip():
            accessToken = create_access_token(identity = block.get('username'))
            response:response_class = jsonify({"msg" : "Login Sucessful", "status" : True, "access_token" : accessToken })
            response.headers.add('Authorization', 'Bearer ' + accessToken)
            return allowCors(response)
        else:
            return allowCors(jsonify({"msg" : "Password Does not match", "status" : False}), 401)

    return allowCors(jsonify({"msg" : "Username does not exists", "status" : False}), 401)


@app.route('/admin/', methods = ['post'])
def adminLogin():
    req = request.form

    block:dict = app.DB.get_doc({"name" : 'admin'}, getenv('ADMIN_COLLECTION'))

    if req['password'] != '' and req['password'] == block.get('key'):
        return allowCors(jsonify({"msg" : "Logged in", "status" : True}), 200)
    else:
        return allowCors(jsonify({"msg" : "Password doesnt match", "status" : False}), 401)



@app.route('/api/users/', methods = ['GET', 'DELETE'])
def usersOps():
    if request.method == 'GET':
        block:dict = app.DB.get_docs({}, getenv('USER_COLLECTION'))
        tmp = []
        for item in block:
            item.pop('password')
            item.pop('_id')
            tmp.append(item)
        
        return allowCors(jsonify(tmp))
    else:
        ret, dummy = app.DB.remove_all({}, getenv('USER_COLLECTION'))
        if ret == True:
            return allowCors(jsonify({"msg" : "Succefully Deleted"}))
        else:
            return allowCors(jsonify({"msg" : "Error ocurred while deleting users"}), 400)



@app.route('/api/user/', methods = ['POST', 'DELETE'])
def userOps():
    # Assigning only json data
    req = request.json

    # Checking if the client sent json data with the request.
    if req == None:
        return allowCors(jsonify({"msg" : "No JSON Data found"}),400)

    # POST - Approve Users from the pending section
    # Rules - If <addall_inNewHosts> True then server will going to add the user into all the PiServer
    if request.method == 'POST':
        
        #Approve the user
        msg, ret = approveReq(req.get('username'), app.DB)
        if ret == True:

            # Fetching Ncloud configs from the database
            config:dict = getNcloudConfig(app.DB)

            if config.get('addall_inNewHosts') == True:

                # Fetching all Pi Server_data from the database
                servers = getServers(app.DB)

                # Decision variable to ensure that all the operations are executing successfully
                # 0 = No Error | 0 < = Error
                operationStatus = 0

                # Looping through the server data to add the username into each server's host
                for server in servers:
                    hosts = server.get('hosts')
                    for host in hosts:
                        try:
                            # Sending request to the Pi Server to add the username to all of it's hosts
                            res = requests.post(f'http://{server.get("address")}/Pending', json = {
                                "username" : req.get("username")
                            })

                            if res.ok:
                                print(f'{req.get("username")} added into {host.get("name")}')
                            else:
                                raise Exception
                        except Exception as e:
                            operationStatus += 1
                            print(f'{req.get("username")} failed while adding into {host.get("name")}')
                        

                if operationStatus != 0:
                    return allowCors(jsonify({"msg": "Some targets are failed"}),400)

            return allowCors(jsonify({"msg": "Success"}))
              
        else:
            print("Error ocurred :: ", msg)
            return allowCors(jsonify({"msg" : "Failed while aproving"}),401)

    # Delete User
    else:

        # User is only available in pending section.
        # So we dont need to handle the main user collection while removing user
        if req.get("type").lower() == "pending":
            msg, ret = rejectReq(req.get('username'), app.DB)
            if ret == True:
                return allowCors(jsonify({"msg": "Successfully removed"}))
            else:
                return allowCors(jsonify({"msg": "Error ocurred while removing the user"}),400)
        
        # Deleting username from main line
        elif req.get("type").lower() == "normal":

            # Check if all the servers are running or not.
            # Its very important to make sure that every server is running. 
            # Otherwise it will create conflict with the database
            if allAlive(app.DB) == False:
                return allowCors(jsonify({"msg": "All the servers have to be running while deleting user from main line"}),401)


            # Fetching all Pi Server_data from the database
            servers = getServers(app.DB)

            # Decision variable to ensure that all the operations are executing successfully
            # 0 = No Error | 0 < = Error
            operationStatus = 0

            # Looping through the server data to add the username into each server's host
            for server in servers:
                hosts = server.get('hosts')

                for host in hosts:
                    validUsers = host.get('validUsers')
                    isExists = req.get('username').lower() in validUsers

                    if isExists == True:
                        try:
                            res = requests.get(f'http://{server.get("address")}/Pending/', json = {
                                "username" : req.get('username'),
                            })

                            if res.ok:
                                validUsers.remove(req.get("username"))
                                print(f'{req.get("username")} removed from {host.get("name")}')
                            else:
                                raise Exception
                        except Exception as e:
                            operationStatus += 1
                            print(f'{req.get("username")} failed while removing from {host.get("name")}')
                host.setdefault('validUsers', validUsers)
                app.DB.update_doc({"name" : server.get('name')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                

            # If some targets are failed, we will not remove the username from main line database,
            # Because there are maybe some Pi Servers turned off and if we remove username in that situation, it will create unstable situation
            if operationStatus != 0 :
                return allowCors(jsonify({"msg": "Some targets are failed"}),400)
            
            # Removing Username from main line database
            # Because we know that all the servers are on and all removed the username from their servers
            ret, dummy = app.DB.remove({"username" : req.get('username')}, getenv('USER_COLLECTION'))

            if ret:
                return allowCors(jsonify({"msg": "Operation successful"}))
            else:
                return allowCors(jsonify({"msg": "Error ocurred while removing user from db"}))
                
        else:
            return allowCors(jsonify({"msg": "Bad request"}),400)


