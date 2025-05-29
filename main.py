# python manage.py runserver → chỉ hỗ trợ HTTP, KHÔNG hỗ trợ WebSocket. Xem trang 159 =====================

# django-admin startproject myproject
# cd myproject
# python manage.py runserver

# cd myproject
# docker compose up -d db
# docker compose build myapp
# docker compose up myapp

# cd myproject
# docker compose down -v
# docker compose up -d
# docker compose build myapp
# docker compose up myapp

# $env:PG_HOST = "localhost"
# python manage.py makemigrations
# python manage.py migrate
# docker compose build myapp
# docker compose up myapp

# =================================================================
# python manage.py shell
# from django.contrib.auth import get_user_model
# User = get_user_model()
# User.objects.filter(email="cmpisalesinside@gmail.com").first()
# User.objects.create_user(username="tony lee", email="cmpisalesinside@gmail.com", password="123456")

# python manage.py makemigrations
# python manage.py migrate
# python manage.py createsuperuser
# python manage.py runserver

# ================================================================
# cd myproject
# docker compose down -v
# docker compose up -d
# docker compose build myapp
# docker compose up myapp

# docker compose exec myapp python manage.py makemigrations
# docker compose exec myapp python manage.py migrate
# docker compose build myapp
# docker compose up myapp