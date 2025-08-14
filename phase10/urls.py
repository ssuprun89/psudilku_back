from rest_framework.routers import DefaultRouter

from .views import (
    PhaseViewSet,
    PhaseCustomLevelViewSet,
)

urlpatterns = []

routers = DefaultRouter()
routers.register("level-config", PhaseCustomLevelViewSet, basename="phase-custom-level")
routers.register("", PhaseViewSet, basename="phase")

urlpatterns += routers.urls
