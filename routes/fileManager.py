import dotenv
import dbOperation
import json
import helper
import requests

from os                 import getenv, path
from app                import app, end, final
from flask              import request, jsonify, send_file, send_from_directory, safe_join, abort
from middleWare         import allowCors, isValidKEY, isRequiredDataAvailable
from bson.json_util     import dumps
from userUtils          import *
from NcloudUtils        import *
from pathlib            import Path


class Directories:
    @staticmethod
    def getOnlyDir(location = '/'):
        DIR = Path(location).iterdir()
        DIRS = []

        for item in DIR:
            if item.is_dir():
                DIRS.append(item.__str__())

        return {
            "path" : location,
            'dirs' : DIRS
        }

    
    @staticmethod
    def getDirData(location = '/'):
        DIR = Path(location).iterdir()
        data = []

        for item in DIR:
            fullPath = item.__str__()
            extension = ''
            mode, ino, dev, nlink, uid, gid, size, atime, mtime, ctime = item.stat()
            fSize = float(size / 1048576)
            size_in_str = str(round(fSize, 1)) + 'MB'
            if int(fSize) <= 0:
                size_in_str = str(round(fSize * 1024, 1)) + 'KB'
            elif int(fSize) >= 1024:
                size_in_str = str(round(fSize / 1024, 2)) + 'GB'


            if not item.is_dir() and fullPath.find('.') > 0:
                extension = fullPath[fullPath.rfind('.') : ]

            data.append({
                "name": fullPath[fullPath.rfind('\\') + 1:],
                "extension" : extension,
                "is_dir" : item.is_dir(),
                "stat" : mtime,
                "size" : size_in_str
            })

        return {
            "path" : location,
            'data' : data
        }

    

    @staticmethod
    def previousFolder(location:str):
        if location == '/':
            return None


        if location.rfind('/') == 0:
            return Directories.getData()

        return Directories.getData(location[0 : location.rfind('/')])


    
    @staticmethod
    def nextFolder(currentPath = '/', location = ''):
        if currentPath == '/':
            location = currentPath + location
        else:
            location = currentPath + '/' + location


        return Directories.getData(location)



@app.route('/file/upload')
def uploadFile():
    files = request.files

    files['image'].save(path.join('D:/save/', files['image'].filename))
    

    return allowCors(jsonify({"msg":"Success"}))


@app.route("/file/download/<image_name>")
def downloadFile(image_name):
    try:
        x = send_from_directory(Path('D:/save/'), filename=image_name, as_attachment=True)
        return x
    except Exception as e:
        print('Exception Ocurred :: ' + e)

    return allowCors(jsonify({"msg":"Success"}))



@app.route("/dir/", methods = ['POST'])
def getFolder():
    req = request.json
    path = req.get('path')

    if path:
        path = path.strip()

    if path == None or path == '':
        return allowCors(jsonify({"path":None, "data":[]}))

    if not Path(path).exists():
        return allowCors(jsonify({"path":None, "data":[]}))

    data = Directories.getDirData(req.get('path'))

    return allowCors(jsonify(data))
