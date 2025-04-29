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
        db_table = "myapp_user"
        ordering = ["-created_at"]




# from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
# from django.db import models
#
# class UserManager(BaseUserManager):
#     def create_user(self, email, name, password=None):
#         if not email:
#             raise ValueError("Users must have an email address")
#         user = self.model(email=self.normalize_email(email), name=name)
#         user.set_password(password)  # Hash password
#         user.save(using=self._db)
#         return user
#
#     def create_superuser(self, email, name, password):
#         user = self.create_user(email, name, password)
#         user.is_admin = True
#         user.save(using=self._db)
#         return user
#
# class User(AbstractBaseUser):
#     email = models.EmailField(unique=True)
#     name = models.CharField(max_length=255)
#     password = models.CharField(max_length=255)  # Mật khẩu được hash tự động
#     is_active = models.BooleanField(default=True)
#     is_admin = models.BooleanField(default=False)
#
#     objects = UserManager()
#
#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['name']
#
#     def __str__(self):
#         return self.email