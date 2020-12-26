from os import getenv

def allowCors(response, status = 200):
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response, status

def isValidKEY(client, userType = 'STUDENT'):
    if userType == 'STUDENT' and client == getenv('STUDENT_CLOUD_KEY'):
        return True
    elif userType == 'FACULTY' and client == getenv('FACULTY_CLOUD_KEY'):
        return True
    
    return False
