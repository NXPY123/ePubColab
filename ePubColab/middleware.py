from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware.base import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


@database_sync_to_async
def get_user(token):
    try:
        return Token.objects.get(key=token).user
    except Token.DoesNotExist:
        raise AuthenticationFailed("Invalid token")


class TokenAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        query_string = parse_qs(scope["query_string"].decode())
        token = query_string.get("token", [None])[0]
        if token:
            scope["user"] = await get_user(token)
        else:
            scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)
