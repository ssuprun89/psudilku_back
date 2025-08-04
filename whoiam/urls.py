from rest_framework.routers import DefaultRouter

from .views import WhoIamViewSet

urlpatterns = []

routers = DefaultRouter()
routers.register("", WhoIamViewSet, basename="whoiam")

urlpatterns += routers.urls
