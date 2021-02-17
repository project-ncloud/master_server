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

# end and final classes are exception class but they meant to
# be used as goto statement for cleaner code
class end(Exception):
    pass

class final(Exception):
    pass


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = getenv('SECRET_KEY')
jwt = JWTManager(app)

# Setup Database
app.DB = Mongo(getenv('DB_URI_STRING'),getenv('DB_NAME'))


# Importing other routes
import routes.mainRoutes
import routes.hostRoutes
import routes.serverRoutes
import routes.userAdminRoutes
import routes.explorerRoutes



# Example of protected Route
@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200



# Where server starts
if __name__ == '__main__':
    # Load environment variables
    dotenv.load_dotenv(dotenv_path='./.env')

    # setup server vars
    DEBUG = True if getenv('TYPE') == 'dev' else False

    # Run server
    app.run(debug = DEBUG, host = '0.0.0.0', port = getenv('PORT'), load_dotenv = True)