from rest_framework.routers import DefaultRouter
from .views import UserViewSet, UserGamesViewSet

urlpatterns = []

routers = DefaultRouter()
routers.register("", UserViewSet, basename="user")
routers.register("user-games", UserGamesViewSet, basename="user-games")

urlpatterns += routers.urls
