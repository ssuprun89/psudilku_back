from django.urls import path, include

urlpatterns = [
    path("user/", include("users.urls"), name="user"),
    path("auth/", include("auths.urls"), name="auths"),
    path("zone-rush/", include("phase10.urls"), name="phase"),
    path("who-iam/", include("whoiam.urls"), name="whoiam"),
]
