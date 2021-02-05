from os import getenv
from db import Mongo


def userExists(userName:str, client:Mongo):
    # Checking if that user is existed in User Section
    if client.isDocExists({'username' : f'{userName.strip()}'}, getenv('USER_COLLECTION')):
        return True, False, False
    
    # Checking if that user is existed in Pending Section
    if client.isDocExists({'username' : f'{userName.strip()}'}, getenv('PENDING_USER_COLLECTION')):
        return True, True, False
   
    # Checking if that user is existed in Manager Section
    if is_manager(userName, client):
        return True, False, True
        
    return False, None, None



def is_manager(userName:str, client:Mongo):
    if client.isDocExists({'username' : f'{userName.strip()}'}, getenv('MANAGER_COLLECTION')):
        return True
    else:
        return False


def isPassCorrect(userName:str, password:str, client:Mongo):
    block = client.get_doc({
        "username" : userName
    }, getenv('USER_COLLECTION'))

    if block == None:
        return False

    if block.get('password') == password:
        return True
    else:
        return False

