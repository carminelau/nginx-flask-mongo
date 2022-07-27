from flask import Flask
from flask_pymongo import PyMongo

application = Flask( __name__)
application.config["MONGO_URI"] = "mongodb://mongo:27017/SSDB"
application.config['MONGO_CONNECT'] = True

mongo = PyMongo(application)

db=mongo.db