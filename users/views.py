from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import CreateModelMixin, RetrieveModelMixin
from .serializers import UserSerializer

from users.models import User
from utils.base_controller import GetObject404User


class UserViewSet(GenericViewSet, CreateModelMixin, RetrieveModelMixin, GetObject404User):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        return [AllowAny()] if self.action == 'create' else [IsAuthenticated()]

