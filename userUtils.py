from os import getenv
import dotenv
from bson.objectid import ObjectId
import dbOperation
from db import Mongo

def approveReq(userName:str ,client:Mongo):
    user:dict = client.get_doc({"username": userName}, getenv('PENDING_USER_COLLECTION'))
    
    if user == None:
        return "Username doesn't exists", False
    else:
        x = user.copy()
        p_id = x.pop('_id')
        if client.isDocExists({"username": x.get('username')}, getenv('USER_COLLECTION')):
            return "User is already exists in main list", False
        u_id = client.insert([x], getenv('USER_COLLECTION'))
        if u_id == None:
            return "Error Occured", False
        else:
            client.remove_ById(p_id, getenv('PENDING_USER_COLLECTION'))
            return "User added to main list", True

def rejectReq(userName:str ,client:Mongo):
    user:dict = client.get_doc({"username": userName}, getenv('PENDING_USER_COLLECTION'))
    
    if user == None:
        return "Username doesn't exists", False
    else:
        ret , msg = client.remove({"username" : userName}, getenv('PENDING_USER_COLLECTION'))
        if ret == True:
            return "User removed from the pending list", True
        else:
            return "Error ocurred while removing user from the pending list", False



def getAllUsers(client:Mongo):
    return client.get_docs({}, getenv('USER_COLLECTION'))




def test():
    x:dict = {
        "name" : "Sourav Gain",
        "_id" : "bkcd3821092094",
        "var" : False
    }
    x.pop('_id')

    print(x)

'''dotenv.load_dotenv(dotenv_path='./.env')
DB = Mongo(getenv('DB_URI_STRING'), getenv('DB_NAME'))
#msg, ret = rejectReq('indsrkr', DB)
ret, msg = DB.update_doc({"username": "souravgain"}, {"username": "souravgain605"}, getenv('USER_COLLECTION'))
print(f'{msg.__str__()}')'''