from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
import logging
from urllib.parse import parse_qs
from jwt import decode as jwt_decode
from django.conf import settings

logger = logging.getLogger(__name__)

class JWTAuthMiddleware(BaseMiddleware):
    """
    Middleware для аутентификации пользователей по JWT токену.
    Токен должен передаваться в строке запроса как ?token=<jwt_token>
    """

    def get_user_model(self):
        """
        Ленивая загрузка User модели
        """
        from django.contrib.auth import get_user_model
        return get_user_model()

    def get_anonymous_user(self):
        """
        Ленивая загрузка AnonymousUser
        """
        from django.contrib.auth.models import AnonymousUser
        return AnonymousUser()

    @database_sync_to_async
    def get_user(self, token):
        from rest_framework_simplejwt.tokens import UntypedToken
        from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
        
        # Получаем User модель в начале метода
        User = self.get_user_model()
        
        try:
            # Декодируем JWT токен
            UntypedToken(token)
            decoded_data = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            
            # Получаем user_id из токена
            user_id = decoded_data.get('user_id')
            if not user_id:
                logger.warning("No user_id in token")
                return self.get_anonymous_user()
            
            try:
                return User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(f"User with id {user_id} does not exist")
                return self.get_anonymous_user()
            
        except (InvalidToken, TokenError) as e:
            logger.warning(f"Token validation failed: {str(e)}")
            return self.get_anonymous_user()
        except Exception as e:
            logger.error(f"Unexpected error in get_user: {str(e)}")
            return self.get_anonymous_user()

    async def __call__(self, scope, receive, send):
        query_string = scope.get("query_string", b"").decode("utf-8")
        params = parse_qs(query_string)
        token_list = params.get("token", [])

        if token_list:
            token = token_list[0]
            user = await self.get_user(token)
            scope["user"] = user
            if user.is_authenticated:
                logger.debug(f"Authenticated user: {user.email}")
            else:
                logger.warning("Authentication failed: Invalid JWT token")
        else:
            scope["user"] = self.get_anonymous_user()
            logger.warning("No JWT token provided")

        return await super().__call__(scope, receive, send)
