import dotenv
import json
import dbOperation
import helper

from os                 import getenv
from flask              import Flask, jsonify, request
from bson.json_util     import dumps
from middleWare         import *
from db                 import *
from userUtils          import *

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity
)


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = getenv('SECRET_KEY')
jwt = JWTManager(app)

app.DB = Mongo(getenv('DB_URI_STRING'),getenv('DB_NAME'))

import routes.mainRoutes
import routes.hostRoutes
import routes.serverRoutes




@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200




if __name__ == '__main__':
    dotenv.load_dotenv(dotenv_path='./.env')
    app.run(debug=True)