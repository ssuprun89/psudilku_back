from rest_framework.routers import DefaultRouter

from .views import WhoIamViewSet, WhoIamPlayersViewSet

urlpatterns = []

routers = DefaultRouter()
routers.register("", WhoIamViewSet, basename="whoiam")
routers.register("players", WhoIamPlayersViewSet, basename="whoiam-players")

urlpatterns += routers.urls
