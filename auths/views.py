from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenVerifyView, TokenObtainPairView

from users.models import User
from users.serializers import UserSerializer


class PingView(APIView):
    permission_classes = (AllowAny,)
    def get(self, request, *args, **kwargs):
        return Response({"status": "ok"}, status=200)


class TokenView(TokenObtainPairView):
    queryset = User.objects.filter()
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        apple_id = request.data.get("apple_id")
        username = request.data.get("username")

        if not apple_id or not username:
            return Response({"detail": "apple_id and username required"}, status=400)

        user, created = User.objects.update_or_create(apple_id=apple_id, defaults={"username": username, "password": "<PASSWORD>"})

        refresh = RefreshToken.for_user(user)
        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user_data": UserSerializer(user).data
        }, status=200)


class TokenVerifyViewToken(TokenVerifyView):
    queryset = User.objects.filter()
    permission_classes = (AllowAny,)

# проверить сборку ордера от большего к меньшему
