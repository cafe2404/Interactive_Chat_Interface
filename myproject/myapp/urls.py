from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("register", views.register, name="register"), # views.py
    path("login", views.loginUser),  # views.py

    path("", views.getUsers, name="getUsers"), # views.py
    path("create", views.addUser), # views.py
    path("read", views.getUser, name="getUser"), # views.py
    path("update", views.updateUser), # views.py
    path("delete", views.deleteUser), # views.py
    path("participant", views.get_participants, name="get_participants"),  # views.py

    path('restore', views.restore_user, name='restore_user'),
    path('obliterate', views.obliterate_user, name='obliterate_user'),
    path("recycleBin", views.getDeletedUsers, name="getDeletedUsers"), # views.py
    path("exclude", views.exclude_participants, name="exclude_participants"), # views.py

    path("refresh-token", views.refresh_token, name="refresh_token"), # views.py

    path('logout', views.logout_user, name='logout'), # views.py
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


