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
    req = request.json


    if request.method == 'POST':
        
        #Approve the user
        msg, ret = approveReq(req.get('username'), app.DB)
        if ret == True:
            config:dict = getNcloudConfig(app.DB)

            if config.get('addall_inNewHosts') == True:
                servers = getServers(app.DB)
                operationStatus:int = 0
                for server in servers:
                    hosts = server.get('hosts')
                    for host in hosts:
                        '''
                        Pending Task
                        call a request to node server to add user and send the sucess respose
                        '''
                        try:
                            res = requests.post(f'http://{server.get("address")}/<Pending>')

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

        #Send the user data to node
    else:
        return 'Delete Hello'