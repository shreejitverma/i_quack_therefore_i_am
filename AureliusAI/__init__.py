from flask import Flask
from flask_cors import CORS
import logging

#Set up logger
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# logging.basicConfig(filename='server.log', format='%(asctime)s:%(module)s:%(levelname)s:%(message)s')
app = Flask(__name__)
cors = CORS()

#Factory
def create_app():
    #Imports
    from . import simple_views, ai, models
    #Configurations
    
    #Blueprint registration
    from .ai import ai
    from .simple_views import simple_views
    app.register_blueprint(ai)
    app.register_blueprint(simple_views)
    
    cors.init_app(app)

    return app
