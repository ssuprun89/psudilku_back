from django.urls import path
from .views import (
PingView,
    TokenView,
    TokenVerifyViewToken,
)

urlpatterns = [
    path("ping/", PingView.as_view(), name="token_obtain_pair"),
    path("token/", TokenView.as_view(), name="token_obtain_pair"),
    path("token/verify/", TokenVerifyViewToken.as_view(), name="token_verify"),
]
