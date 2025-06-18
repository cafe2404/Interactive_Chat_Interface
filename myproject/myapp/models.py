from django.db import models
from django.utils.timezone import now

class ActiveUserManager(models.Manager):
    def get_queryset(self):
        # return super().get_queryset().filter(deleted_at__isnull=True)

        return super().get_queryset().filter(
            models.Q(deleted_at__isnull=True) |
            (models.Q(restored_at__isnull=False) & models.Q(deleted_at__isnull=True))
            # Chỉ lấy user khôi phục chưa bị xóa lại
        )

class DeletedUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=False)

# Create your models here.
class User(models.Model):
    your_name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    your_phone = models.CharField(max_length=255)
    company_name = models.CharField(max_length=255)
    company_tax = models.CharField(max_length=255)
    role = models.CharField(max_length=255, default="user")
    gender = models.CharField(max_length=255, default="Other")
    userImage = models.ImageField(upload_to="", blank=True, null=True)

    refresh_token = models.CharField(max_length=255, blank=True, null=True)
    refresh_expired = models.DateTimeField(blank=True, null=True)

    access_token_issued = models.DateTimeField(blank=True, null=True)
    access_token_expires = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(default=now)
    # updated_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(blank=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    restored_at = models.DateTimeField(blank=True, null=True)

    objects = models.Manager()  # Manager mặc định (lấy tất cả)
    active_users = ActiveUserManager()  # Chỉ lấy user chưa bị xóa mềm

    inactive_users = DeletedUserManager() # Chỉ lấy user đã bị xóa mềm

    def soft_delete(self):
        """Xóa mềm user, đồng thời reset restored_at để đảm bảo lọc đúng"""
        self.deleted_at = now() # Chỉ cập nhật deleted_at
        self.restored_at = None  # Reset lại restored_at để không nằm trong active_users nữa
        self.save(update_fields=['deleted_at', 'restored_at']) # Chỉ lưu trường deleted_at, không động đến updated_at

    def restore(self):
        """Khôi phục user từ thùng rác"""
        self.deleted_at = None
        self.restored_at = now()
        self.save(update_fields=['deleted_at', 'restored_at'])

    def hard_delete(self):
        """Xóa vĩnh viễn"""
        self.delete()

    class Meta:
        ordering = ["-created_at"]

class ChatMessage(models.Model):
    sender = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey('User', on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField(blank=True)  # Cho phép rỗng nếu chỉ gửi file
    file = models.FileField(upload_to="chat_files/", blank=True, null=True)
    sent_at = models.DateTimeField(default=now)

    class Meta:
        ordering = ['sent_at']

class ChatFile(models.Model):
    message = models.ForeignKey(ChatMessage, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='chat_files/')

