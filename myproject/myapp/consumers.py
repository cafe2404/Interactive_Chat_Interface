import json
from channels.generic.websocket import AsyncWebsocketConsumer
import jwt # Uncomment this line
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken
from myapp.models import ChatMessage
from django.utils.timezone import localtime

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "room_name"):
            await self.channel_layer.group_discard(self.room_name, self.channel_name)
        if hasattr(self, "user_group"):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)

    async def receive(self, text_data):
        if not text_data.strip():
            await self.send_json({"type": "error", "message": "Empty message"})
            return

        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send_json({"type": "error", "message": "Invalid JSON"})
            return

        msg_type = data.get("type")

        if msg_type == "auth":
            await self.authenticate(data.get("token"))
            return

        elif msg_type == "chat.message":
            await self.handle_chat_message(data)
            return

        else:
            await self.send_json({"type": "error", "message": "Unknown message type"})

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "chat.message",
            "message": event["message"],
            "sender": event["sender"],
            "sent_at": event.get("sent_at"),
            "files": event.get("files", [])
        }))

    async def send_json(self, data):
        await self.send(text_data=json.dumps(data))

    @database_sync_to_async
    def get_user_by_email(self, email):
        User = get_user_model()
        return User.objects.filter(email=email).first()

    @database_sync_to_async
    def get_user_by_id(self, user_id):
        User = get_user_model()
        return User.objects.filter(id=user_id).first()

    async def authenticate(self, token): # Uncomment this method
        try:
            # payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            payload = AccessToken(token)
            # email = payload.get("email")
            user_id = payload.get("user_id")
            self.user = await self.get_user_by_id(user_id)

            if self.user:
                await self.send_json({
                    "type": "auth.success",
                    "user_id": self.user.id,
                    "email": self.user.email
                })
                self.user_group = f"user_{self.user.id}"
                await self.channel_layer.group_add(self.user_group, self.channel_name)
            else:
                await self.send_json({"type": "auth.failed", "message": "User not found"})
                await self.close()

        except jwt.InvalidTokenError:
            await self.send_json({"type": "auth.failed", "message": "Invalid token"})
            await self.close()

    @database_sync_to_async
    def save_message(self, sender, receiver, message):
        return ChatMessage.objects.create(sender=sender, receiver=receiver, message=message)

    @database_sync_to_async
    def save_file_urls(self, chat_msg, file_urls):
        from myapp.models import ChatFile
        for url in file_urls:
            ChatFile.objects.create(message=chat_msg, file=url)

    async def handle_chat_message(self, data):
        if not hasattr(self, "user"):
            await self.send_json({"type": "error", "message": "You must authenticate first"})
            return

        receiver_id = data.get("receiver_id")
        message = data.get("message", "").strip()

        if not receiver_id or not message:
            await self.send_json({"type": "error", "message": "receiver_id and message are required"})
            return

        receiver = await self.get_user_by_id(receiver_id)
        if not receiver:
            await self.send_json({"type": "error", "message": "Receiver not found"})
            return

        msg = await self.save_message(self.user, receiver, message)

        files = data.get("files", [])
        if files:
            await self.save_file_urls(msg, files)

        # Gửi hồi âm lại chính sender
        await self.send_json({
            "type": "chat.sent",
            "to": receiver.id,
            "message": message,
            "sent_at": localtime(msg.sent_at).strftime("%Y-%m-%d %H:%M:%S"),
            "files": files
        })

        # Gửi cho receiver nếu họ online
        receiver_group = f"user_{receiver.id}"
        await self.channel_layer.group_send(
            receiver_group,
            {
                "type": "chat.message",
                "sender": self.user.id,
                "message": message,
                "sent_at": localtime(msg.sent_at).strftime("%Y-%m-%d %H:%M:%S"),
                "files": files
            }
        )



