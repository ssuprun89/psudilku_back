from django.urls import path
from .views import (
    TokenView,
    TokenRefreshTokenView,
    TokenVerifyViewToken,
)

urlpatterns = [
    path("token/", TokenView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshTokenView.as_view(), name="token_refresh"),
    path("token/verify/", TokenVerifyViewToken.as_view(), name="token_verify"),
]
