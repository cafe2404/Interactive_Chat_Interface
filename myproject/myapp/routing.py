from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]


# ws://localhost:8000/ws/chat/1_2/
# {
#   "type": "auth",
#   "token": ""
# }

# {
#   "type": "chat.message",
#   "receiver_id": 2,
#   "message": "Hello"
# }

# {
#   "type": "chat.message",
#   "receiver_id": 2,
#   "message": "Do you hear me?",
#   "files": [
#     "http://localhost:8000/media/uploads/files/Kiến Thức - Long Khang.xlsx",
#     "http://localhost:8000/media/uploads/images/hình ảnh.jpg"
#   ]
# }

