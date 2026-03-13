from flask import Flask
from flask_restx import Api
from flask_bcrypt import Bcrypt
from app.api.v1 import namespaces as v1_namespaces

bcrypt = Bcrypt()


def create_app(config_class):
    """
    Application factory that creates and configures the Flask app.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    bcrypt.init_app(app)

    api = Api(
        app,
        version='1.0',
        title='HBnB API',
        description='HBnB Application API',
        doc='/api/v1/'
    )

    for ns in v1_namespaces:
        api.add_namespace(ns, path=f'/api/v1/{ns.name}')

    return app