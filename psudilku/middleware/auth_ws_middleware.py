from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.conf import settings
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qsl

from users.models import User


@database_sync_to_async
def get_user(user_id):
    return User.objects.filter(id=user_id).first()


class TokenAuthMiddleware(BaseMiddleware):
    def __init__(self, inner):
        super().__init__(inner)

    def parse_header(self, query_string):
        params = query_string.decode()
        parse_dict = dict(parse_qsl(params))
        return parse_dict.get("token", "")

    async def __call__(self, scope, receive, send):
        token = self.parse_header(scope["query_string"])
        try:
            valid_data = AccessToken(token)
            user = await get_user(valid_data.payload["user_id"])
            if not user:
                return Response(data={"auth": "Your token is not valid"}, status=400)
            scope["user"] = user
        except Exception as e:
            print(e)
            return Response(data={"auth": "You need provide auth headers"}, status=401)
        return await super().__call__(scope, receive, send)
