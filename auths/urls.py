from django.urls import path
from .views import (
    TokenView,
    TokenVerifyViewToken,
)

urlpatterns = [
    path("token/", TokenView.as_view(), name="token_obtain_pair"),
    path("token/verify/", TokenVerifyViewToken.as_view(), name="token_verify"),
]
