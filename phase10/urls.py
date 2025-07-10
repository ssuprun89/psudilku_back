from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    PhaseViewSet,
)

urlpatterns = []

routers = DefaultRouter()
routers.register("", PhaseViewSet, basename="phase")

urlpatterns += routers.urls
