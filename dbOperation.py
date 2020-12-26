from os import getenv
from db import Mongo


def userExists(userName:str ,client:Mongo):
    if client.isDocExists({'username' : f'{userName.strip()}'}, getenv('USER_COLLECTION')):
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

