from configs import db

errors = db.errors_services
status = db.status_services
data_tool = db.data_tool
routes = db.routes

errors.create_index('timestamp', expireAfterSeconds=864000)
status.create_index('timestamp', expireAfterSeconds=864000)
