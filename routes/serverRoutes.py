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




@app.route('/servers/', methods = ['GET'])
def getServerData():
    if request.method == 'GET':
        block:dict = app.DB.get_docs({}, getenv('SERVER_COLLECTION'))
        NN = helper.Nas(block)
        return allowCors(jsonify(NN.getBlock()), 200)
    else:
        return allowCors(jsonify({"msg": "Bad Request"}), 400)




@app.route('/server/', methods = ['POST', 'DELETE'])
def serverOps():
    json_data = request.json
    

    if request.method == 'POST':
        data:dict = app.DB.get_doc({}, getenv('ADMIN_COLLECTION'))
        #usernames = []
        #if data.get('addall_inNewHosts') == True:
        #    users = getAllUsers(DB)
        #    if users != None:
        #        for item in users:
        #            usernames.append(item.get('username'))
        hosts = []

        #checking if same server exists or not
        isExists = app.DB.get_doc({"address": json_data.get('address')}, getenv('SERVER_COLLECTION'))

        if isExists == None:
            ret, val =  app.DB.insert([{
                            "name" : json_data.get('name'),
                            "address" : json_data.get('address'),
                            "autoStart" : json_data.get('autoStart'),
                            "hosts" : hosts
                        }], getenv('SERVER_COLLECTION'))
            if ret == True:
                return allowCors(jsonify({"msg" : "Successfully Added"}), 200)
            else:
                return allowCors(jsonify({"msg" : "Error Occurred while adding server"}), 503)
        else:
            return allowCors(jsonify({"msg" : "Server already exists"}), 404)
            
    else:
        ret,dummy = app.DB.remove({
                        "name": json_data.get('name'),
                        "address": json_data.get('address'),
                    }, getenv('SERVER_COLLECTION'))
        if ret == True:
            return allowCors(jsonify({"msg" : "Server successfully removed"}), 200)
        else:
            return allowCors(jsonify({"msg" : "Error occurred while removing server"}), 503)



@app.route('/server/config/', methods = ['GET', 'POST'])
def serverConfig():
    data:dict = app.DB.get_doc({}, getenv('ADMIN_COLLECTION'))
    if request.method == 'GET':
        if data == None:
            return allowCors(jsonify({"msg": "Config not found"}), 400)
        
        return allowCors(jsonify({
            "addall_inNewHosts": data.get('addall_inNewHosts'),
            "autoStartSrvr": data.get('autoStartSrvr'),
            "allowRegistration": data.get('allowRegistration')
        }))

    else:
        req = request.json
        block = {
            "addall_inNewHosts": data.get('addall_inNewHosts') if req.get('addall_inNewHosts') == None else req.get('addall_inNewHosts'),
            "autoStartSrvr": data.get('autoStartSrvr') if req.get('autoStartSrvr') == None else req.get('autoStartSrvr'),
            "allowRegistration": data.get('allowRegistration') if req.get('allowRegistration') == None else req.get('allowRegistration')
        }
        ret, msg = app.DB.update_doc({"name" : "admin"}, block, getenv('ADMIN_COLLECTION'))
        if ret == True:
            return allowCors(jsonify({"msg": "Configs updated successfully"}), 200)
        else:
            return allowCors(jsonify({"msg": "Error ocurred while updating configs"}), 401)


@app.route('/server/control/', methods = ['GET', 'POST'])
def serverControl():
    req = request.json
    if request.method == 'GET':
        try:
            res = requests.get(f'http://{req.get("address")}/alive/')
            if res.status_code == 200:
                resJson = res.json()
                return allowCors(jsonify({"alive" : resJson.get('status')}))
            else:
                raise Exception
        except Exception as e:
            print("An exception ocurred ::", e)
            return allowCors(jsonify({"msg" : "Server probably Switched OFF","alive" : None}))
    else:
        return 'Get Hello'
    