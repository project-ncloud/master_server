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


@app.route('/server/host/users/', methods = ['POST', 'DELETE'])
def hostUserOps():
    if request.method == 'POST':
        return 'Get Hello'
    elif request.method == 'DELETE':
        return 'Delete Hello'
    else:
        return allowCors(jsonify({"msg": "Bad Request"}), 400)


@app.route('/server/host/user/', methods = ['POST', 'DELETE'])
def hostUsersOps():
    if request.method == 'POST':
        return 'Get Hello'
    elif request.method == 'DELETE':
        return 'Delete Hello'
    else:
        return allowCors(jsonify({"msg": "Bad Request"}), 400)