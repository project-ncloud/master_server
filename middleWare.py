from os                 import getenv
from functools          import wraps
from flask_jwt_extended import get_jwt_identity
from flask              import jsonify, request

def onlyAdminAllowed(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        if get_jwt_identity() != "admin": return allowCors(jsonify({"msg":"Bad user", "status": False}), 400)
        return func(*args, **kwargs)
    return decorator


def blockSpecialUsername(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        req = request.json
            
        if req.get('username').lower() in getenv('RESTRICT_KEYWORD'): return allowCors(jsonify({"msg":"Username not allowed", "status": False}), 400)
        return func(*args, **kwargs)
    return decorator


def onlyselfAllowed(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        req = request.form

        if req.get('username') == None:
            req = request.json

        identity = get_jwt_identity()
        if identity != req.get('username'): return allowCors(jsonify({"msg":"Username not allowed", "status": False}), 400)
        return func(*args, **kwargs)
    return decorator


def allowCors(response, status = 200):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, status

def isValidKEY(KEY, userType = 'STUDENT'):
    """if userType == 'STUDENT' and client == getenv('STUDENT_CLOUD_KEY'):
        return True
    elif userType == 'FACULTY' and client == getenv('FACULTY_CLOUD_KEY'):
        return True"""
    
    return True if KEY == getenv('STUDENT_CLOUD_KEY') else False


#To check if all the required data available or not
def isRequiredDataAvailable(data, keys):
    if data == None: return False
    length = len(keys)
    operationCounter = 0

    for item in data:
        for key in keys:
            if item.__str__() == key:
                if item != None:
                    operationCounter += 1
                
                break
        
    return True if operationCounter == length else False