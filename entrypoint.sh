#!/bin/bash

# Load the environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | xargs)
fi

if [ -f setup_db.py ]; then
    echo "Running database setup script"
    python setup_db.py
else
    echo "setup_db.py not found, skipping database setup"
fi

# Start the Python application
exec python app.py