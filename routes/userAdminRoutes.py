import dotenv
import dbOperation
import json
import helper
import requests

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

# Routes
#   Add User Admin              [DONE]
#   Change User Admin           [Pending]
#   Delete User Admin           [DONE]
#   
#   Add sub Share               [Pending]
#   Delete sub share            [Pending]
#   Add user into sub share     [DONE]
#   Delete user from sub share  [DONE]


@app.route('/userAdmin/add/', methods=['POST'])
@jwt_required
@VIPAllowed
def addUserAdmin():
    req = request.json

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_exists" : False,
        "is_host_exists" : False,
        "is_usename_exists_in_valid_user" : False,
        "status" : False
    }


    try:
        if isRequiredDataAvailable(req, ["host_name", "server_name", "server_address", "username"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        # Some other checks regarding username and KEY
        isExists, pending, isManager = dbOperation.userExists(req.get('username').strip().lower(), app.DB)

        if not (isExists and not isManager):
            resBlock['msg'] = "Username doesn't exists"
            raise end(Exception)

        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('server_name') and server.get('address') == req.get('server_address'):
                resBlock['is_server_exists'] = True
                hosts = server.get('hosts')

                for host in hosts:
                    if host.get('name') == req.get('host_name'):
                        resBlock['is_host_exists'] = True

                        if req.get('username') in host.get('validUsers'):
                            resBlock['is_usename_exists_in_valid_user'] = True
                        else:
                            resBlock['msg'] = "Username is not exists in host's valid users."
                            raise end(Exception)


                        admin = host['admin']
                        admin['name'] = req.get('username')

                        ret, msg = app.DB.update_doc({"address" : server.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                        if ret:
                            resBlock['msg'] = "Operation successful"
                            resBlock['status'] = True
                            raise final(Exception)
                        else:
                            resBlock['msg'] = "Failed to add admin while saving into the database"
                            raise end(Exception)

        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))



@app.route('/userAdmin/remove/', methods=['POST'])
@jwt_required
@VIPAllowed
def removeUserAdmin():
    req = request.json

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_exists" : False,
        "is_host_exists" : False,
        "status" : False
    }


    try:
        if isRequiredDataAvailable(req, ["host_name", "server_name", "server_address", "username"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('server_name') and server.get('address') == req.get('server_address'):
                resBlock['is_server_exists'] = True
                hosts = server.get('hosts')

                for host in hosts:
                    if host.get('name') == req.get('host_name'):
                        resBlock['is_host_exists'] = True

                        admin = host['admin']
                        admin['name'] = ''

                        ret, msg = app.DB.update_doc({"address" : server.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                        if ret:
                            resBlock['msg'] = "Operation successful"
                            resBlock['status'] = True
                            raise final(Exception)
                        else:
                            resBlock['msg'] = "Failed to remove admin while saving into the database"
                            raise end(Exception)

        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))




@app.route('/userAdmin/sharedUser/', methods=['POST', 'DELETE'])
@jwt_required
def addSharedUser():
    req = request.json

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_exists" : False,
        "is_host_exists" : False,
        "status" : False
    }


    try:
        if isRequiredDataAvailable(req, ["host_name", "server_name", "server_address", "username"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        # Some other checks regarding username and KEY
        isExists, pending, isManager = dbOperation.userExists(get_jwt_identity().strip().lower(), app.DB)

        manager = isManager

        if not (isExists or isManager):
            resBlock['msg'] = "Request is sent from unauthorized user"
            raise end(Exception)


        # Some other checks regarding username and KEY
        isExists, pending, isManager = dbOperation.userExists(req.get('username').strip().lower(), app.DB)

        if not (isExists or not isManager):
            resBlock['msg'] = "Username doesn't exists"
            raise end(Exception)

        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('server_name') and server.get('address') == req.get('server_address'):
                resBlock['is_server_exists'] = True
                hosts = server.get('hosts')

                for host in hosts:
                    if host.get('name') == req.get('host_name'):
                        resBlock['is_host_exists'] = True

                        admin = host['admin']

                        if admin['name'] != get_jwt_identity() and manager != True:
                            resBlock['msg'] = "Request is sent from unauthorized user"
                            raise end(Exception)


                        if request.method == 'POST':
                            if req.get('username') not in admin.get('sharedUsers'):
                                admin['sharedUsers'].append(req.get('username'))
                        else:
                            if req.get('username') in admin.get('sharedUsers'):
                                admin['sharedUsers'].remove(req.get('username'))

                        ret, msg = app.DB.update_doc({"address" : server.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                        if ret:
                            resBlock['msg'] = "Operation successful"
                            resBlock['status'] = True
                            raise final(Exception)
                        else:
                            resBlock['msg'] = "Failed to add admin while saving into the database"
                            raise end(Exception)

        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))




@app.route('/userAdmin/writable/', methods=['POST'])
@jwt_required
def changePermission():
    req = request.json

    # Response Block
    resBlock = {
        "msg" : None,
        "is_server_exists" : False,
        "is_host_exists" : False,
        "status" : False
    }


    try:
        if isRequiredDataAvailable(req, ["host_name", "server_name", "server_address", "writable"]) == False:
            resBlock['msg'] = "No JSON data found"
            raise end(Exception)

        # Some other checks regarding username and KEY
        isExists, pending, isManager = dbOperation.userExists(get_jwt_identity().strip().lower(), app.DB)

        manager = isManager

        if not (isExists or isManager):
            resBlock['msg'] = "Request is sent from unauthorized user"
            raise end(Exception)

        servers = getServers(app.DB)

        for server in servers:
            if server.get('name') == req.get('server_name') and server.get('address') == req.get('server_address'):
                resBlock['is_server_exists'] = True
                hosts = server.get('hosts')

                for host in hosts:
                    if host.get('name') == req.get('host_name'):
                        resBlock['is_host_exists'] = True

                        admin = host['admin']

                        if admin['name'] != get_jwt_identity() and manager != True:
                            resBlock['msg'] = "Request is sent from unauthorized user"
                            raise end(Exception)

                        admin['writable'] = True if req.get('writable') == True else False

                        ret, msg = app.DB.update_doc({"address" : server.get('address')}, {"hosts" : hosts}, getenv('SERVER_COLLECTION'))
                        if ret:
                            resBlock['msg'] = "Operation successful"
                            resBlock['status'] = True
                            raise final(Exception)
                        else:
                            resBlock['msg'] = "Failed to update config while saving into the database"
                            raise end(Exception)

        raise end(Exception)

    except end:
        return allowCors(jsonify(resBlock), 400)
    except final:
        return allowCors(jsonify(resBlock))