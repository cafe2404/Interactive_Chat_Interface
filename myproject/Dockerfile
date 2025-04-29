FROM python:3.10.9

ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

# Sao chép django.sh vào đúng vị trí trong container
COPY django.sh /app/django.sh

# Cấp quyền thực thi cho django.sh
RUN chmod +x /app/django.sh

EXPOSE 8000

# Đảm bảo đường dẫn đến django.sh chính xác
ENTRYPOINT ["/app/django.sh"]