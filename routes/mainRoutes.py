import dotenv
import dbOperation
import json
import helper
import requests

from datetime           import timedelta
from os                 import getenv
from app                import app
from app                import end, final
from flask              import request, jsonify
from middleWare         import *
from bson.json_util     import dumps
from userUtils          import *
from NcloudUtils        import *

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, get_jwt_claims

)


@app.route('/init/', methods = ['GET'])
def init():
    return allowCors(jsonify({"msg": "Server is running"}))



@app.route('/register/', methods = ['POST'])
#@blockSpecialUsername
def register():
    req = request.json
    userName:str = req['username']

    # chain condition
    ret = False

    # response block
    resBlock = {
        "msg" : None,                       # str
        "exists" : None,                    # bool
        "pending" : None,                   # bool
        "manager" : None,                   # bool
        "registration_allowed" : None,      # bool
        "is_valid_key" : None,              # bool
        "status" : False                    # bool
    }

    try:
        # Fetching server config data
        res = requests.get(f'http://{getenv("OWN_URL")}/ncloud/config/')
        serverConfig:dict = res.json().get('data')

        # Checking if registration allowed or not

        if serverConfig.get('allowRegistration') != True:
            resBlock['msg'] = "Registration not allowed"
            resBlock['registration_allowed'] = serverConfig.get('allowRegistration')
            raise end(Exception)

        # Deciding if the registered user data need to save pending section or main database
        collection:str = getenv('USER_COLLECTION') if serverConfig.get('pendingNewUser') != True else getenv('PENDING_USER_COLLECTION')

        # Some other checks regarding username and KEY
        isExists, pending, isManager = dbOperation.userExists(userName.strip().lower(), app.DB)
        allowed:bool = isValidKEY(req['KEY'])

        if isExists:
            resBlock['msg'] = "User already exists"
            resBlock['pending'] = pending
            resBlock['exists'] = True
            resBlock['manager'] = isManager
            raise end(Exception)
        

        if not allowed:
            resBlock['msg'] = "Incorrect key"
            resBlock['is_valid_key'] = False
            raise end(Exception)


        # Creating user block to insert into the database
        block = {
            "name" : f'{req["name"].strip()}',
            "username" : f'{req["username"].strip().lower()}',
            "password" : f'{req["password"].strip()}',
        }

        if app.DB.insert([block], collection) != None:
            resBlock['msg'] = "User added"
            resBlock['status'] = True
            raise end(Exception)
        
        resBlock['msg'] = "Failed to add user"
        raise end(Exception)
        
        
    except end:
        return allowCors(jsonify(resBlock))








@app.route('/login/', methods = ['POST'])
def login():
    req = request.json
    username:str = req['username']

    # response block
    resBlock = {
        "msg" : None,                       # str
        "exists" : None,                    # bool
        "pending" : None,                   # bool
        "manager" : None,                   # bool
        "access_token": None,               # str
        "user": None,                       # dict
        "status" : False                    # bool
    }

    try:
        isExists, pending, isManager = dbOperation.userExists(username.strip().lower(), app.DB)

        resBlock['exists'] = isExists
        resBlock['pending'] = pending
        resBlock['manager'] = isManager

        user = None

        if not isExists:
            resBlock['msg'] = f'{req["username"]} not exists'
            raise end(Exception)
        
        elif isExists and pending:
            resBlock['msg'] = f'{req["username"]} is in pending list'
            #Get user
            user = app.DB.get_doc({"username" : username.strip().lower()}, getenv('PENDING_USER_COLLECTION'))
            raise end(Exception)
        
        else:
            user = app.DB.get_doc({"username" : username.strip().lower()}, getenv('USER_COLLECTION' if not isManager else 'MANAGER_COLLECTION'))

            resBlock['user'] = {
                "name" : user.get('name'),
                "username" : username.strip().lower(),
                "manager" : isManager
            }

            # Assuming that password is incorrect
            resBlock['msg'] = "Password Incorrect"

            block = app.DB.get_doc({
                "username" : username.strip().lower()
            }, getenv('USER_COLLECTION' if not isManager else 'MANAGER_COLLECTION'))

            if block.get('password') == req['password'].strip():
                accessToken = create_access_token(identity = block.get('username').lower(), user_claims={
                    'is_manager' : resBlock.get('manager'), 
                    "name" : user.get('name'),
                    "username" : user.get('username')}, expires_delta = timedelta(days = 300))
                resBlock['msg'] = "Login Sucessful"
                resBlock['status'] = True
                resBlock['access_token'] = accessToken

            raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock))


@app.route('/user/')
@jwt_required
def sendSelf():
    data = get_jwt_claims()

    return allowCors(jsonify({
        "name" : data.get("name"),
        "username" : data.get("username"),
        "manager" : data.get("is_manager"),
        "admin" : data.get("is_admin")
    }))


@app.route('/admin/', methods = ['POST'])
def adminLogin():
    req:dict = request.json

    # response block
    resBlock = {
        "msg": None,            # str
        "access_token": None,   # str
        "status": False         # bool
    }

    block:dict = app.DB.get_doc({"name" : 'admin'}, getenv('ADMIN_COLLECTION'))

    # Assuming that password is incorrect
    resBlock['msg'] = "Password Incorrect"

    if req.get('password') != '' and req.get('password') != None and req.get('password') == block.get('key'):
        accessToken = create_access_token(identity = 'admin', user_claims={'is_admin' : True})
        
        resBlock['msg'] = "Login Successful"
        resBlock['access_token'] = accessToken
        resBlock['status'] = True

    return allowCors(jsonify(resBlock))



@app.route('/manager/', methods = ['POST'])
@jwt_required
@onlyAdminAllowed
def addManager():
    req = request.json
    userName:str = req['username']

    # chain condition
    ret = False

    # response block
    resBlock = {
        "msg" : None,                       # str
        "exists" : None,                    # bool
        "pending" : None,                   # bool
        "manager" : None,                   # bool
        "status" : False                    # bool
    }

    try:
        isExists, pending, isManager = dbOperation.userExists(userName.strip().lower(), app.DB)

        if isExists:
            resBlock['msg'] = "User already exists"
            resBlock['pending'] = pending
            resBlock['manager'] = isManager
            resBlock['exists'] = True
            raise end(Exception)


        # Creating user block to insert into the database
        block = {
            "name" : f'{req["name"].strip()}',
            "username" : f'{req["username"].strip().lower()}',
            "password" : f'{req["password"].strip()}',
        }

        if app.DB.insert([block], getenv('MANAGER_COLLECTION')) != None:
            resBlock['msg'] = "User added"
            resBlock['status'] = True
            raise final(Exception)
        
        resBlock['msg'] = "Failed to add user"
        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)

    except final:
        return allowCors(jsonify(resBlock))


@app.route('/manager/', methods = ['DELETE'])
@jwt_required
@onlyAdminAllowed
def removeManager():
    req = request.json
    userName:str = req['username']


    # response block
    resBlock = {
        "msg" : None,                       # str
        "exists" : True,                    # bool
        "pending" : None,                   # bool
        "manager" : None,                   # bool
        "status" : False                    # bool
    }

    try:
        isExists, pending, isManager = dbOperation.userExists(userName.strip().lower(), app.DB)

        if not isManager:
            resBlock['msg'] = "User is not manager"
            resBlock['pending'] = pending
            resBlock['manager'] = isManager
            resBlock['exists'] = False
            raise end(Exception)


        block = {
            "username" : f'{req["username"].strip().lower()}',
        }

        if app.DB.remove(block, getenv('MANAGER_COLLECTION')) != None:
            resBlock['msg'] = "Manager removed"
            resBlock['status'] = True
            raise final(Exception)
        
        resBlock['msg'] = "Failed to remove manager"
        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)

    except final:
        return allowCors(jsonify(resBlock))


@app.route('/api/users/', methods = ['GET'])
def usersOps():
    req = request.args

    user_type = "pending"
    if req.get('type') != 'pending':
        user_type = "normal"


    resBlock = {
        "msg" : None,
        "users": [],         # user info blocks
        "status": False      # bool
    }

    try:
        block:dict = app.DB.get_docs({}, getenv('PENDING_USER_COLLECTION' if user_type == "pending" else 'USER_COLLECTION'))

        if block == None:
            resBlock['msg'] = "No users found"
            raise end(Exception)
        
        for item in block:
            item.pop('password')
            item.pop('_id')
            resBlock['users'].append(item)

        resBlock['status'] = True
        resBlock['msg'] = "All users fetched successfully"
        raise end(Exception)
        
    except end:
        return allowCors(jsonify(resBlock))



"""
ret, dummy = app.DB.remove_all({}, getenv('USER_COLLECTION'))
            if ret == True:
                return allowCors(jsonify({"msg" : "Succefully Deleted"}))
            else:
                return allowCors(jsonify({"msg" : "Error ocurred while deleting users"}), 400)
"""



@app.route('/api/user/', methods = ['POST', 'DELETE'])
@jwt_required
@onlyAdminAllowed
def userOps():
    # Assigning only json data
    req = request.json

    '''
    What We expecting
    {
        "username" : "xxxxx"
    }
    '''

    # response block
    resBlock = {
        "msg" : None,
        "error":[],
        "status" : False
    }

    try:
        # Checking if the client sent json data with the request.
        if req == None or req.get('username').strip() == '' or req.get('username') == None:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)




        # POST - Approve Users from the pending section
        # Rules - If <addall_inNewHosts> True then server will going to add the user into all the PiServer
        if request.method == 'POST':
            
            #Approve the user
            msg, ret = approveReq(req.get('username'), app.DB)

            if ret != True:
                resBlock['msg'] = msg
                raise end(Exception)

            userData:dict = app.DB.get_doc({"username": req.get('username')}, getenv('USER_COLLECTION'))


            # Fetching Ncloud configs from the database
            config:dict = getNcloudConfig(app.DB)

            if config.get('addall_inNewHosts') == True:

                # Fetching all Pi Server_data from the database
                servers = getServers(app.DB)

                # Decision variable to ensure that all the operations are executing successfully
                # 0 = No Error | 0 < = Error
                operationStatus = 0

                operationLimit = len(servers)

                # Looping through the server data to add the username into each server's host
                for server in servers:
                    hosts = server['hosts']
                    try:
                        # Sending request to the Pi Server to add the username to all of it's hosts
                        res = requests.post(f'http://{server.get("address")}/users/', json = {
                            "username" : req.get("username"),
                            "password" : userData.get("password")
                        })

                        if not res.ok:
                            raise Exception

                        for host in hosts:
                            host['validUsers'].append(req.get("username"))

                        operationStatus += 1

                    except Exception as e:
                        print(e.__str__())
                        # Error block created for giving some information about server oparation error
                        errorBLK = {
                            "server_name" : server.get("name"),
                            "server_address" : server.get("address")
                        }
                        resBlock['error'].append(errorBLK)

                    app.DB.update_doc({"name" : server.get('name')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))

                
                        
                if operationStatus == operationLimit:
                    pass
                elif operationStatus == 0:
                    resBlock['msg'] = "Failed while adding into all servers"
                    raise end(Exception)
                elif operationStatus > 0 and operationStatus < operationLimit:
                    resBlock['msg'] = "Some operations failed while adding into some servers"
                    raise final(Exception)


            resBlock['msg'] = "Operation Successful"
            resBlock['status'] = True
            raise final(Exception)


        # Delete User
        else:

            # User is only available in pending section.
            # So we dont need to handle the main user collection while removing user
            if req.get("type").lower() == "pending":
                msg, ret = rejectReq(req.get('username'), app.DB)

                resBlock['msg'] = msg
                resBlock['status'] = ret

                if ret != True:
                    raise end(Exception)
                else:
                    raise final(Exception)

            
            # Deleting username from main line
            elif req.get("type").lower() == "normal":

                # Check if all the servers are running or not.
                # Its very important to make sure that every server is running. 
                # Otherwise it will create conflict with the database
                if allAlive(app.DB) == False and getenv('TYPE') == "production":
                    resBlock['msg'] = "All the servers have to be running while deleting user from main line"
                    raise end(Exception)


                userData:dict = app.DB.get_doc({"username": req.get('username')}, getenv('USER_COLLECTION'))

                if userData == None:
                    resBlock['msg'] = "User doesn't exists"
                    raise end(Exception)


                # Fetching all Pi Server_data from the database
                servers = getServers(app.DB)

                # Decision variable to ensure that all the operations are executing successfully
                # 0 = No Error | 0 < = Error
                operationStatus = 0

                operationLimit = 0

                # Looping through the server data to add the username into each server's host
                for server in servers:
                    hosts = server.get('hosts')

                    for host in hosts:
                        validUsers = host.get('validUsers')
                        isExists = req.get('username').lower() in validUsers

                        if isExists == True:
                            try:
                                operationLimit += 1
                                res = requests.delete(f'http://{server.get("address")}/user/', json = {
                                    "username" : req.get('username'),
                                    "password" : userData.get("password"),
                                    "hostname" : host.get("name")
                                })

                                if res.ok or getenv('TYPE') == "dev":
                                    operationStatus += 1
                                    validUsers.remove(req.get("username"))
                                    print(f'{req.get("username")} removed from {host.get("name")}')
                                else:
                                    raise Exception
                            except Exception as e:
                                errorBLK = {
                                    "server_name" : server.get("name"),
                                    "server_address" : server.get("address"),
                                    "host_name" : host.get("name")
                                }
                                resBlock['error'].append(errorBLK)

                    host.setdefault('validUsers', validUsers)
                    app.DB.update_doc({"name" : server.get('name')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                    


                # Removing Username from main line database
                # Because we know that all the servers are on and all removed the username from their servers
                if operationStatus == operationLimit:
                    ret, dummy = app.DB.remove({"username" : req.get('username')}, getenv('USER_COLLECTION'))

                    if not ret:
                        resBlock['msg'] = "Error ocurred while removing user from db"
                        raise end(Exception)

                elif operationStatus > 0 and operationStatus < operationLimit:
                    resBlock['msg'] = "Aborted remove operation from user list because some of the operation failed"
                    raise final(Exception)

                elif operationStatus == 0:
                    resBlock['msg'] = "Failed while removing from all servers"
                    raise end(Exception)

                resBlock['msg'] = "Operation Successful"
                resBlock['status'] = True
                raise final(Exception)
                 
            else:
                resBlock['msg'] = "Bad request"
                raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))

# Delete all the pending user from pending section
@app.route('/api/users/', methods = ['DELETE'])
@jwt_required
@onlyAdminAllowed
def pendingUserOps():
    # response block
    resBlock = {
        "msg" : None,
        "error":[],
        "status" : False
    }

    try:
        ret, dummy = app.DB.remove_all({}, getenv('PENDING_USER_COLLECTION'))

        if not ret:
            resBlock['msg'] = "Failed while removing all pending users from pending section"
            raise end(Exception)
        
        resBlock['msg'] = "Operation successful"
        resBlock['status'] = True
        raise final(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))



# Change the user password
@app.route('/api/user/password/', methods = ['POST'])
@jwt_required
@onlyselfAllowed
def changePassword():
    # Pending Task
    return allowCors(jsonify({}))