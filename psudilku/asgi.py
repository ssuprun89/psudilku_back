import os

from django.core.asgi import get_asgi_application


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "psudilku.settings")

django_asgi_app = get_asgi_application()


from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from ws.urls import websocket_urlpatterns
from psudilku.middleware.auth_ws_middleware import TokenAuthMiddleware


application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': TokenAuthMiddleware(URLRouter(websocket_urlpatterns))
})
