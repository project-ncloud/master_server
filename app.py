import dotenv
import os
from flask import Flask
from flask import jsonify
from flask import request
from bson.json_util import dumps
import json
from middleWare import allowCors
from middleWare import isValidKEY
from db import Mongo
import dbOperation
import helper

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')
jwt = JWTManager(app)

DB = Mongo(os.getenv('DB_URI_STRING'),os.getenv('DB_NAME'))


@app.route('/api/init/', methods = ['GET'])
def init():
    response = jsonify(message="Simple server is running")
    return allowCors(response)



@app.route('/register/', methods = ['POST'])
def register():
    req = request.form
    userName:str = req['username']

    isExists:bool = dbOperation.userExists(userName.strip().lower(), DB)
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
    if DB.insert([block], os.getenv('USER_COLLECTION')) != None:
        return allowCors(jsonify({"msg" : "Added User", "status" : True}))
    
    return allowCors(jsonify({"msg" : "Failed to add user", "status" : False}))



@app.route('/login/', methods = ['POST'])
def login():
    req = request.form
    username:str = req['username']

    isExists:bool = dbOperation.userExists(username.strip().lower(), DB)
    
    if isExists:
        block = DB.get_doc({
            "username" : username
        }, os.getenv('USER_COLLECTION'))

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

    block:dict = DB.get_doc({"name" : 'admin'}, os.getenv('ADMIN_COLLECTION'))

    if req['password'] != '' and req['password'] == block.get('key'):
        return allowCors(jsonify({"msg" : "Logged in", "status" : True}), 200)
    else:
        return allowCors(jsonify({"msg" : "Password doesnt match", "status" : False}), 401)
    



@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200



@app.route('/api/servers', methods = ['GET', 'POST'])
def servers():
    block:dict = DB.get_docs({}, os.getenv('SERVER_COLLECTION'))

    NN = helper.Nas(block)
    #print(NN.getBlock())

    return allowCors(jsonify(NN.getBlock()), 200)



if __name__ == '__main__':
    dotenv.load_dotenv(dotenv_path='./.env')
    app.run(debug=True)