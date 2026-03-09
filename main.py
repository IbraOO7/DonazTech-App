from flask import Flask
from services.log_config import logger
from services.config import configs
from api import api
from api.routes import ns, routing
import os
from databases.config import init_db

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.register_blueprint(routing)
    api.init_app(app)
    app.config.from_mapping(
        SECRET_KEY=configs.SECRET_KEY,
    )
    init_db()
    api.add_namespace(ns)
    os.makedirs(app.instance_path, exist_ok=True)
    return app
