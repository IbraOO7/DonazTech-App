from gevent import monkey
monkey.patch_all()

from gevent.pywsgi import  WSGIServer
from services.config import configs
from main import create_app

app = create_app()

