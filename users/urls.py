from rest_framework.routers import DefaultRouter
from .views import UserViewSet

urlpatterns = []

routers = DefaultRouter()
routers.register("", UserViewSet, basename="user")

urlpatterns += routers.urls
