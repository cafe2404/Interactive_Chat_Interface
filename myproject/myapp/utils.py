from rest_framework_simplejwt.tokens import RefreshToken

def create_access_token(user):
    refresh = RefreshToken.for_user(user)
    refresh['email'] = user.email
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh)
    }


