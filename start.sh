#!/bin/bash

# Activating virtual environment
. venv/*/activate

# Starting the server 
waitress-serve --call --port=5000 'app:create_app'


# Exiting
deactivate