from flask import Blueprint
from . import views
import logging

#Set up logger
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)
# logging.basicConfig(filename='server.log', format='%(asctime)s:%(module)s:%(levelname)s:%(message)s')

#Blueprint
simple_views = Blueprint('simple_views', __name__)

#Routes
@simple_views.route('/Marcus_Aurelius')
def Marcus_Aurelius_page():
    return views.stoicism()

@simple_views.route('/appinfo')
def app_info():
    return views.ai()
