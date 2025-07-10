from django.urls import path
from .views import PhaseWebsocketConsumer

websocket_urlpatterns = [
    path("ws/phase/<str:room_name>/", PhaseWebsocketConsumer.as_asgi(), name="ws_path"),
]