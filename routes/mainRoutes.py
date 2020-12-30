import dotenv
import dbOperation
import json
import helper

from os                 import getenv
from app                import app
from flask              import request, jsonify
from middleWare         import allowCors, isValidKEY
from bson.json_util     import dumps
from userUtils          import *

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

    isExists:bool = dbOperation.userExists(userName.strip().lower(), app.DB)
    allowed:bool = isValidKEY(req['KEY'], req['userType'])

    if isExists:
        return allowCors(jsonify({"msg" : "User already exists", "status" : False}))

    if not allowed:
        return allowCors(jsonify({"msg" : "KEY do not match", "status" : False}))

    block = {
        "name" : f'{req["name"].strip()}',
        "username" : f'{req["username"].strip().lower()}',
        "password" : f'{req["password"].strip()}',
        "type" : f'{req["userType"].strip()}',
    }
    if app.DB.insert([block], getenv('USER_COLLECTION')) != None:
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
        return 'Get Hello'
    elif request.method == 'DELETE':
        return 'Delete Hello'
    else:
        return 'xxxxxx', 400


@app.route('/api/user/', methods = ['GET', 'POST', 'DELETE'])
def userOps():
    if request.method == 'GET':
        return 'Get Hello'
    elif request.method == 'POST':
        return 'Get Hello'
    elif request.method == 'DELETE':
        return 'Delete Hello'
    else:
        return 'xxxxxx', 400