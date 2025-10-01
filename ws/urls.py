from django.urls import path
from .views import PhaseWebsocketConsumer, WhoIamWebsocketConsumer

websocket_urlpatterns = [
    path("ws/zone-rush/<str:room_name>/", PhaseWebsocketConsumer.as_asgi(), name="ws_path"),
    path("ws/who-iam/<str:room_name>/", WhoIamWebsocketConsumer.as_asgi(), name="ws_path"),
]
