from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView

from users.models import User


class TokenView(TokenObtainPairView):
    queryset = User.objects.filter()
    permission_classes = (AllowAny,)


class TokenRefreshTokenView(TokenRefreshView):
    queryset = User.objects.filter()
    permission_classes = (AllowAny,)


class TokenVerifyViewToken(TokenVerifyView):
    queryset = User.objects.filter()
    permission_classes = (AllowAny,)
