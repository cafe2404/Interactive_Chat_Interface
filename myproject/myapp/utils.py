from django.utils import timezone
import jwt
from django.conf import settings
from datetime import timedelta

def create_access_token(user):
    payload = {
        'user_id': user.id,
        'email': user.email,
        'iat': timezone.now(),  # Thời gian tạo token
        'exp': timezone.now() + timedelta(hours=24),  # Access token hết hạn sau 24 giờ
    }
    access_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')
    return access_token


# from rest_framework_simplejwt.tokens import RefreshToken
#
# def create_access_token(user):
#     refresh = RefreshToken.for_user(user)
#     return str(refresh.access_token)

