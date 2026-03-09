from gevent import monkey
monkey.patch_all()

from gevent.pywsgi import  WSGIServer
from services.config import configs
from main import create_app

app = create_app()

# if __name__ == '__main__':
#     http_server = WSGIServer(('0.0.0.0', 8809), app)
#     http_server.serve_forever()
