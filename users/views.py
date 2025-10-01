from datetime import timedelta

from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin, UpdateModelMixin
from .serializers import UserSerializer, UserGamesSerializer

from users.models import User, UserGames
from utils.base_controller import GetObject404User, GetObject404


class UserViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, GetObject404User):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        return [AllowAny()] if self.action == "create" else [IsAuthenticated()]


class UserGamesViewSet(GenericViewSet, RetrieveModelMixin, UpdateModelMixin, GetObject404):
    queryset = UserGames.objects.all()
    serializer_class = UserGamesSerializer

    @action(detail=True, methods=["patch"], url_path="free-trial")
    def free_trial(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.free_trial is None:
            instance.free_trial = timezone.now() + timedelta(days=7)
            instance.save()
        return self.retrieve(request, *args, **kwargs)
