from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.models import User
from .models import User, ChatMessage, ChatFile
from .serializers import UserSerializer
from django.contrib.auth.hashers import check_password
from rest_framework import status
from django.contrib.auth.hashers import make_password
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
import os
from django.conf import settings
from rest_framework.pagination import PageNumberPagination
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, localtime
import datetime
from datetime import timedelta
import math
# import uuid
from .utils import create_access_token
# import jwt
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken, TokenError

# Register
@api_view(['POST'])
def register(request):
    try:
        company_name = request.data.get("company_name", "") # models.py
        your_name = request.data.get("your_name", "") # models.py
        your_phone = request.data.get("your_phone", "") # models.py
        company_tax = request.data.get("company_tax", "") # models.py
        email = request.data.get("email", "") # models.py
        password = request.data.get("password", "") # models.py
        gender = request.data.get("gender", "") # models.py

        # Kiểm tra email đã tồn tại chưa
        if User.objects.filter(email=email).exists():
            return Response({
                "DT": "",
                "EC": 1,
                "EM": "Email already registered"
            }, status=400)

        # Tạo user mới
        user = User.objects.create(
            company_name=company_name,
            your_name=your_name,
            gender=gender,
            your_phone=your_phone,
            company_tax=company_tax,
            email=email,
            password=make_password(password),
        )

        return Response({
            "DT": {
                "name": user.your_name,
                "gender": user.gender,
                "email": user.email,
                "phone": user.your_phone,
                "company's name": user.company_name,
                "company tax": user.company_tax,
                "created_at": localtime(user.created_at).strftime("%Y-%m-%d %H:%M:%S")
            },
            "EC": 0,
            "EM": "A new user created success"
        }, status=201)

    except Exception as e:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": f"Error: {str(e)}"
        }, status=500)

# Add loginUser.
@api_view(['POST'])
def loginUser(request):
    email_or_phone = request.data.get("email")
    password = request.data.get("password")

    try:
        # user = User.objects.get(email=email)
        user = User.objects.get(
            Q(email=email_or_phone) | Q(your_phone=email_or_phone)
        )
    except User.DoesNotExist:
        user = None

    if user is None or not check_password(password, user.password):
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "Invalid email or password"
        }, status=status.HTTP_400_BAD_REQUEST)  # hoặc 401 cũng được

    # Nếu đăng nhập thành công
    # access_token = create_access_token(user)
    # refresh_token = str(uuid.uuid4())

    tokens = create_access_token(user)
    access_token = tokens['access']
    refresh_token = tokens['refresh']
    refresh_expired = now() + timedelta(days=30)

    user.refresh_token = refresh_token
    user.refresh_expired = refresh_expired
    user.save()

    return Response({
        "DT": {
            "id": user.id,
            "name": user.your_name,
            "gender": user.gender,
            "email": user.email,
            "phone": user.your_phone,
            "company's name": user.company_name,
            "company tax": user.company_tax,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "refresh_expired": localtime(user.refresh_expired).strftime("%Y-%m-%d %H:%M:%S")
        },
        "EC": 0,
        "EM": "Login successful"
    }, status=status.HTTP_200_OK)

# logout User.
@csrf_exempt
@api_view(['POST'])
def logout_user(request):
    # email = request.data.get("email")
    refresh_token = request.data.get("refresh_token")

    if not refresh_token:
        return Response({"EC": 1, "EM": "Refresh token is required"}, status=400)

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()  # 👈 Đưa vào blacklist

        return Response({"EC": 0, "EM": "User logged out successfully"}, status=200)

    except TokenError:
        return Response({"EC": 1, "EM": "Invalid or expired refresh token"}, status=400)

# refresh_token
@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.data.get("refresh_token")
    email = request.data.get("email")

    if not refresh_token or not email:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "Refresh token and email are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email, refresh_token=refresh_token)
        if user.refresh_expired < now():
            return Response({
                "DT": "",
                "EC": 1,
                "EM": "Refresh token has expired"
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Tạo access token mới
        # new_access_token = create_access_token(user)

        tokens = create_access_token(user)
        new_access_token = tokens['access']
        refresh_token = tokens['refresh']

        # Trong hàm refresh_token, sau khi tạo new_access_token
        # decoded_payload = jwt.decode(new_access_token, settings.SECRET_KEY, algorithms=['HS256'])
        decoded_payload = AccessToken(new_access_token)
        user_id_from_token = decoded_payload.get('user_id')
        email_from_token = decoded_payload.get('email')
        iat_from_token = decoded_payload.get("iat")
        exp_from_token = decoded_payload.get("exp")

        # Chuyển đổi timestamp thành datetime để lưu vào User
        user.access_token_issued = datetime.datetime.fromtimestamp(iat_from_token)
        user.access_token_expires = datetime.datetime.fromtimestamp(exp_from_token)
        user.save()

        return Response({
            "DT": {
                "user_id": user_id_from_token,
                "email": email_from_token,
                "access_token": new_access_token,
                "refresh_token": refresh_token,  # Trả lại refresh token cũ
                "access_token_issued_at": datetime.datetime.fromtimestamp(iat_from_token).strftime("%Y-%m-%d %H:%M:%S"),
                "access_token_expires_at": datetime.datetime.fromtimestamp(exp_from_token).strftime("%Y-%m-%d %H:%M:%S"),
                "refresh_expired": localtime(user.refresh_expired).strftime("%Y-%m-%d %H:%M:%S")
            },
            "EC": 0,
            "EM": "Token refreshed successfully"
        }, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "Invalid refresh token or email"
        }, status=status.HTTP_401_UNAUTHORIZED)

# Get all Users
@api_view(['GET'])
def getUsers(request):
    # users = User.objects.all()
    users = User.active_users.all().order_by("id")  # Sắp xếp theo thứ tự từ nhỏ đến lớn

    data = [
        {
            "id": user.id,
            "your_name": user.your_name,
            "gender": user.gender,
            "email": user.email,
            "your_phone": user.your_phone,
            "company_name": user.company_name,
            "company_tax": user.company_tax,
            "role": user.role,
            "user_image": (
                f"{user.userImage}" if user.userImage else None
            ),
            "created_at": localtime(user.created_at).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": localtime(user.updated_at).strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
            "deleted_at": localtime(user.deleted_at).strftime("%Y-%m-%d %H:%M:%S") if user.deleted_at else None,
            "restored_at": localtime(user.restored_at).strftime("%Y-%m-%d %H:%M:%S") if user.restored_at else None,
        }
        for user in users
    ]
    return Response(data)

# Get single user
@api_view(['GET'])
def getUser(request):
    user_id = request.GET.get("id")  # Lấy id từ query parameters

    if not user_id:
        return Response({"EC": 1, "EM": "User ID is required"}, status=400)

    try:
        user = User.objects.get(id=user_id)  # Lấy user theo ID
    except User.DoesNotExist:
        return Response({"EC": 1, "EM": "User not found"}, status=404)

    data = {
        "id": user.id,
        "your_name": user.your_name,
        "gender": user.gender,
        "email": user.email,
        "your_phone": user.your_phone,
        "company_name": user.company_name,
        "company_tax": user.company_tax,
        "role": user.role,
        "user_image": (
            f"{user.userImage}" if user.userImage else None
        ),
        "created_at": localtime(user.created_at).strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": localtime(user.updated_at).strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
        "deleted_at": localtime(user.deleted_at).strftime("%Y-%m-%d %H:%M:%S") if user.deleted_at else None,
        "restored_at": localtime(user.restored_at).strftime("%Y-%m-%d %H:%M:%S") if user.restored_at else None,
        "refresh_token": user.refresh_token,
        "refresh_expired": user.refresh_expired
    }
    return Response(data)

# Add user
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def addUser(request):
    try:
        company_name = request.data.get("company_name", "")  # models.py
        your_name = request.data.get("your_name", "")  # name = models.py
        your_phone = request.data.get("your_phone", "")  # models.py
        company_tax = request.data.get("company_tax", "")  # models.py
        email = request.data.get("email", "")  # models.py
        password = request.data.get("password", "")  # models.py
        userImage = request.FILES.get("userImage")  # Lấy file ảnh từ request
        role = request.data.get("role", "")  # models.py
        gender = request.data.get("gender", "")  # models.py

        # Kiểm tra email đã tồn tại chưa
        if User.objects.filter(email=email).exists():
            return Response({
                "DT": "",
                "EC": 1,
                "EM": "Email already registered"
            }, status=400)

        created_at_str = request.data.get("created_at")  # Lấy giá trị từ request
        created_at = parse_datetime(created_at_str) if created_at_str else None

        # Tạo user mới
        user = User.objects.create(
            company_name=company_name,
            your_name=your_name,
            gender=gender,
            your_phone=your_phone,
            company_tax=company_tax,
            email=email,
            password=make_password(password),
            userImage = userImage,  # Lưu file vào model (nếu model có)
            role = role,
            created_at=created_at if created_at else now()
        )

        return Response({
            "DT": {
                "name": user.your_name,
                "gender": user.gender,
                "email": user.email,
                "phone": user.your_phone,
                "company's name": user.company_name,
                "company tax": user.company_tax,
                "user_image": (
                    f"{user.userImage}" if user.userImage else None
                ),
                "role": user.role,
                "created_at": localtime(user.created_at).strftime("%Y-%m-%d %H:%M:%S")
            },
            "EC": 0,
            "EM": "A new user created success"
        }, status=201)

    except Exception as e:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": f"Error: {str(e)}"
        }, status=500)

# Update user
@api_view(['PUT'])
@parser_classes([MultiPartParser, FormParser])
def updateUser(request):
    try:
        # user = get_object_or_404(User, id=pk)  # Lấy user theo ID

        user_id = request.data.get("id")  # Lấy ID từ request body

        if not user_id:
            return Response({
                "DT": "",
                "EC": 1,
                "EM": "User ID is required",
            }, status=400)

        user = get_object_or_404(User, id=user_id)  # Lọc user theo ID

        # Sao chép dữ liệu từ request
        data = request.data.copy()

        # Kiểm tra nếu có ảnh mới được gửi lên
        if 'userImage' in request.FILES:
            data['userImage'] = request.FILES['userImage']

        # Cập nhật user
        serializer = UserSerializer(instance=user, data=data, partial=True)

        if serializer.is_valid():
            user.updated_at = now()  # Cập nhật thời gian thủ công
            serializer.save()
            user.refresh_from_db()  # Lấy lại bản ghi mới từ DB

            return Response({
                "DT": {
                    "id": user.id,
                    "name": user.your_name,
                    "gender": user.gender,
                    "email": user.email,
                    "phone": user.your_phone,
                    "company's name": user.company_name,
                    "company tax": user.company_tax,
                    "user_image": (
                        f"{user.userImage}" if user.userImage else None
                    ),
                    "role": user.role,
                    "updated_at": localtime(user.updated_at).strftime("%Y-%m-%d %H:%M:%S")
                },
                "EC": 0,
                "EM": "User updated successfully"
            }, status=200)

        return Response({
            "DT": "",
            "EC": 1,
            "EM": "Invalid data",
            "errors": serializer.errors
        }, status=400)

    except Exception as e:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": f"Error: {str(e)}"
        }, status=500)

# Delete user
@api_view(['DELETE'])
def deleteUser(request):
    # user = get_object_or_404(User)  # Tìm user, nếu không có sẽ tự động trả 404

    user_id = request.data.get("id")  # Lấy ID từ request body

    if not user_id:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "User ID is required",
        }, status=400)

    user = get_object_or_404(User, id=user_id)  # Lọc user theo ID

    # Xóa ảnh user nếu có
    if user.userImage:
        image_path = os.path.join(settings.MEDIA_ROOT, str(user.userImage))
        if os.path.exists(image_path):
            os.remove(image_path)

    user.soft_delete() # Soft delete thay vì xóa cứng

    return Response({
        "DT": {"deleted_at": localtime(user.deleted_at).strftime("%Y-%m-%d %H:%M:%S")},
        "EC": 0,
        "EM": "User successfully deleted"
    }, status=200)

# Pagination User Active
@api_view(['GET'])
def get_participants(request):
    # users = User.active_users.all()
    users = User.active_users.all().order_by("id") # Sắp xếp theo thứ tự từ nhỏ đến lớn
    paginator = PageNumberPagination()

    # Chuyển đổi limit thành số nguyên, xử lý nếu người dùng nhập sai
    try:
        page_size = int(request.GET.get('limit', 2))  # Chuyển chuỗi thành số nguyên
        if page_size <= 0:  # Kiểm tra nếu giá trị không hợp lệ
            raise ValueError
    except ValueError:
        return Response({"EC": 1, "EM": "Invalid limit value, must be a positive integer."}, status=400)

    paginator.page_size = page_size
    result_page = paginator.paginate_queryset(users, request)

    # Tính tổng số rows và tổng số pages
    total_rows = users.count()
    # total_pages = (total_rows // page_size) + (1 if total_rows % page_size != 0 else 0)
    total_pages = math.ceil(total_rows / page_size)

    data = [
        {
            "id": user.id,
            "your_name": user.your_name,
            "gender": user.gender,
            "email": user.email,
            "your_phone": user.your_phone,
            "company_name": user.company_name,
            "company_tax": user.company_tax,
            "role": user.role,
            "user_image": (
                f"{user.userImage}" if user.userImage else None
            ),
            "created_at": localtime(user.created_at).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": localtime(user.updated_at).strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
            "deleted_at": localtime(user.deleted_at).strftime("%Y-%m-%d %H:%M:%S") if user.deleted_at else None,
            "restored_at": localtime(user.restored_at).strftime("%Y-%m-%d %H:%M:%S") if user.restored_at else None,
        }
        for user in result_page
    ]

    return Response({
        "totalRows": total_rows,
        "totalPages": total_pages,
        "currentPage": paginator.page.number,  # Trang hiện tại
        "pageSize": page_size,
        "participants": data
    })

# ================================== RECYCLE BIN =======================================
# Restore
@api_view(['PUT'])
def restore_user(request):
    user_id = request.data.get("id")

    if not user_id:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "User ID is required",
        }, status=400)

    # user = get_object_or_404(User, id=user_id)  # Lọc user theo ID
    # Kiểm tra xem user có nằm trong danh sách đã xóa mềm không
    try:
        user = User.inactive_users.get(id=user_id)  # Chỉ lấy user đã bị xóa mềm
    except User.DoesNotExist:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "User not found in deleted users list.",
        }, status=404)

    user.restore()  # Khôi phục user

    return Response({
        "DT": {"restore_at": localtime(user.restored_at).strftime("%Y-%m-%d %H:%M:%S")},
        "EC": 0,
        "EM": "User successfully restored"
    }, status=200)

# Obliterate
@api_view(["DELETE"])
def obliterate_user(request):
    user_id = request.data.get("id")  # Lấy ID từ request body

    if not user_id:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "User ID is required",
        }, status=400)

    # user = get_object_or_404(User, id=user_id)  # Lọc user theo ID
    # Kiểm tra xem user có nằm trong danh sách đã xóa mềm không
    try:
        user = User.inactive_users.get(id=user_id)  # Chỉ lấy user đã bị xóa mềm
    except User.DoesNotExist:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "User not found in deleted users list.",
        }, status=404)

    # Xóa ảnh user nếu có
    if user.userImage:
        image_path = os.path.join(settings.MEDIA_ROOT, str(user.userImage))
        if os.path.exists(image_path):
            os.remove(image_path)

    user.hard_delete()  # Xoá user

    return Response({
        "EC": 0,
        "EM": "User successfully obliterated"
    }, status=200)

@api_view(['GET'])
def getDeletedUsers(request):
    users = User.inactive_users.all().order_by("id")  # Sắp xếp theo thứ tự từ nhỏ đến lớn

    data = [
        {
            "id": user.id,
            "your_name": user.your_name,
            "gender": user.gender,
            "email": user.email,
            "your_phone": user.your_phone,
            "company_name": user.company_name,
            "company_tax": user.company_tax,
            "role": user.role,
            "user_image": (
                f"{user.userImage}" if user.userImage else None
            ),
            "created_at": localtime(user.created_at).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": localtime(user.updated_at).strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
            "deleted_at": localtime(user.deleted_at).strftime("%Y-%m-%d %H:%M:%S") if user.deleted_at else None,
            "restored_at": localtime(user.restored_at).strftime("%Y-%m-%d %H:%M:%S") if user.restored_at else None,
        }
        for user in users
    ]
    return Response(data)

# Pagination User Inactive
@api_view(['GET'])
def exclude_participants(request):
    users = User.inactive_users.all().order_by("id")  # Sắp xếp theo thứ tự từ nhỏ đến lớn
    paginator = PageNumberPagination()

    # Chuyển đổi limit thành số nguyên, xử lý nếu người dùng nhập sai
    try:
        page_size = int(request.GET.get('limit', 2))  # Chuyển chuỗi thành số nguyên
        if page_size <= 0:  # Kiểm tra nếu giá trị không hợp lệ
            raise ValueError
    except ValueError:
        return Response({"EC": 1, "EM": "Invalid limit value, must be a positive integer."}, status=400)

    paginator.page_size = page_size
    result_page = paginator.paginate_queryset(users, request)

    # Tính tổng số rows và tổng số pages
    total_rows = users.count()
    total_pages = math.ceil(total_rows / page_size)

    data = [
        {
            "id": user.id,
            "your_name": user.your_name,
            "gender": user.gender,
            "email": user.email,
            "your_phone": user.your_phone,
            "company_name": user.company_name,
            "company_tax": user.company_tax,
            "role": user.role,
            "user_image": (
                f"{user.userImage}" if user.userImage else None
            ),
            "created_at": localtime(user.created_at).strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": localtime(user.updated_at).strftime("%Y-%m-%d %H:%M:%S") if user.updated_at else None,
            "deleted_at": localtime(user.deleted_at).strftime("%Y-%m-%d %H:%M:%S") if user.deleted_at else None,
            "restored_at": localtime(user.restored_at).strftime("%Y-%m-%d %H:%M:%S") if user.restored_at else None,
        }
        for user in result_page
    ]

    return Response({
        "totalRows": total_rows,
        "totalPages": total_pages,
        "currentPage": paginator.page.number,  # Trang hiện tại
        "pageSize": page_size,
        "participants": data
    })

# ===================================== CHAT ==============================================
@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def send_message(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response({"EC": 1, "EM": "Missing Authorization"}, status=401)

    try:
        # payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        token = auth_header.split(" ")[1]
        payload = AccessToken(token)
        # sender = User.objects.get(email=payload['email'])
        sender = User.objects.get(id=payload['user_id'])

        receiver_id = request.data.get("receiver_id")
        message = request.data.get("message", "").strip()

        # file = request.FILES.get("file")  # Hỗ trợ file (PDF, Word, ảnh,...)

        if not receiver_id:
            return Response({"EC": 1, "EM": "receiver_id and message required"}, status=400)

        receiver = User.objects.filter(id=receiver_id).first()
        if not receiver:
            return Response({"EC": 1, "EM": "Receiver not found"}, status=404)

        if not message and not request.FILES:
            return Response({"EC": 1, "EM": "Message or file is required"}, status=400)

        # Tạo bản ghi tin nhắn
        chat = ChatMessage.objects.create(sender=sender, receiver=receiver, message=message) # Delete: file=file

        # Lưu nhiều file
        for file in request.FILES.getlist("files"):
            ChatFile.objects.create(message=chat, file=file)

        return Response({
            "EC": 0,
            "EM": "Message sent",
            "DT": {
                "from": sender.your_name,
                "to": receiver.your_name,
                "message": chat.message,
                # "file_url": request.build_absolute_uri(chat.file.url) if chat.file else None,
                "files": [
                    request.build_absolute_uri(f.file.url) for f in chat.files.all()
                ],
                "sent_at": localtime(chat.sent_at).strftime("%Y-%m-%d %H:%M:%S")
            }
        })

    # except jwt.ExpiredSignatureError:
    #     return Response({"EC": 1, "EM": "Token expired"}, status=401)
    # except jwt.InvalidTokenError:
    #     return Response({"EC": 1, "EM": "Invalid token"}, status=401)

    except TokenError as e:
        return Response({"EC": 1, "EM": f"Token error: {str(e)}"}, status=401)
    except Exception as e:
        return Response({"EC": 1, "EM": f"Unexpected error: {str(e)}"}, status=500)

@csrf_exempt
@api_view(['DELETE'])
def delete_message(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response({"EC": 1, "EM": "Missing or invalid Authorization"}, status=401)

    try:
        token = auth_header.split(" ")[1]

        # Giải mã token để lấy email user đăng nhập
        # payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        # request_user = User.objects.get(email=payload["email"])

        payload = AccessToken(token)
        request_user = User.objects.get(id=payload['user_id'])


        # Lấy message_id từ body
        message_id = request.data.get("message_id")
        if not message_id:
            return Response({"EC": 1, "EM": "Missing message_id"}, status=400)

        try:
            message = ChatMessage.objects.get(id=message_id)
        except ChatMessage.DoesNotExist:
            return Response({"EC": 1, "EM": "Message not found"}, status=404)

        # Kiểm tra quyền sở hữu tin nhắn
        if message.sender.id != request_user.id:
            return Response({"EC": 1, "EM": "Permission denied: You can only delete your own messages"}, status=403)

        # Xoá cứng
        message.delete()

        return Response({"EC": 0, "EM": "Message deleted successfully"})

    # except jwt.ExpiredSignatureError:
    #     return Response({"EC": 1, "EM": "Token expired"}, status=401)
    # except jwt.InvalidTokenError:
    #     return Response({"EC": 1, "EM": "Invalid token"}, status=401)

    except TokenError as e:
        return Response({"EC": 1, "EM": f"Token error: {str(e)}"}, status=401)
    except Exception as e:
        return Response({"EC": 1, "EM": f"Unexpected error: {str(e)}"}, status=500)

@csrf_exempt
@api_view(['PUT'])
def update_message(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return Response({"EC": 1, "EM": "Missing or invalid Authorization"}, status=401)

    try:
        token = auth_header.split(" ")[1]
        # payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        # user = User.objects.get(email=payload["email"])

        payload = AccessToken(token)
        user = User.objects.get(id=payload['user_id'])

        message_id = request.data.get("message_id")
        message_update = request.data.get("message_update", "").strip()

        if not message_id:
            return Response({"EC": 1, "EM": "Missing message_id"}, status=400)

        message = ChatMessage.objects.filter(id=message_id).first()
        if not message:
            return Response({"EC": 1, "EM": "Message not found"}, status=404)

        # Kiểm tra quyền sửa tin nhắn
        if message.sender.id != user.id:
            return Response({"EC": 1, "EM": "Permission denied: You can only update your own messages"}, status=403)

        # Không cho update rỗng
        if not message_update:
            return Response({"EC": 1, "EM": "Message content cannot be empty"}, status=400)

        # Cập nhật nội dung tin nhắn
        message.message = message_update
        message.save()

        return Response({
            "EC": 0,
            "EM": "Message updated successfully",
            "DT": {
                "id": message.id,
                "message": message.message,
                "sent_at": localtime(message.sent_at).strftime("%Y-%m-%d %H:%M:%S"),
            }
        })

    # except jwt.ExpiredSignatureError:
    #     return Response({"EC": 1, "EM": "Token expired"}, status=401)
    # except jwt.InvalidTokenError:
    #     return Response({"EC": 1, "EM": "Invalid token"}, status=401)
    # except Exception as e:
    #     return Response({"EC": 1, "EM": f"Unexpected error: {str(e)}"}, status=500)

    except TokenError as e:
        return Response({"EC": 1, "EM": f"Token error: {str(e)}"}, status=401)
    except Exception as e:
        return Response({"EC": 1, "EM": f"Unexpected error: {str(e)}"}, status=500)


@api_view(['GET'])
def unidirectional_message_history(request): # Tin nhắn 1 chiều
    sender_id = request.GET.get("sender_id")
    receiver_id = request.GET.get("receiver_id")

    if not sender_id or not receiver_id:
        return Response({"EC": 1, "EM": "sender_id and receiver_id required"}, status=400)

    try:
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({"EC": 1, "EM": "User not found"}, status=404)

    messages = ChatMessage.objects.filter(
        sender=sender,
        receiver=receiver
    ).order_by("sent_at")

    result = [
        {
            "id": msg.id,
            "from": msg.sender.your_name,
            "to": msg.receiver.your_name,
            "message": msg.message,
            "sent_at": localtime(msg.sent_at).strftime("%Y-%m-%d %H:%M:%S"),
            "files": [
                request.build_absolute_uri(f.file.url) for f in msg.files.all()
            ],
        } for msg in messages
    ]

    return Response({
        "EC": 0,
        "EM": "Fetched chat history",
        "DT": result
    })

@api_view(['GET'])
def bidirectional_message_history(request): # Tin nhắn 2 chiều
    sender_id = request.GET.get("sender_id")
    receiver_id = request.GET.get("receiver_id")

    if not sender_id or not receiver_id:
        return Response({"EC": 1, "EM": "sender_id and receiver_id required"}, status=400)

    try:
        sender = User.objects.get(id=sender_id)
        receiver = User.objects.get(id=receiver_id)
    except User.DoesNotExist:
        return Response({"EC": 1, "EM": "User not found"}, status=404)

    messages = ChatMessage.objects.filter(
        Q(sender=sender, receiver=receiver) | Q(sender=receiver, receiver=sender)
    ).order_by("sent_at")

    result = [
        {
            "id": msg.id,
            "from": msg.sender.your_name,
            "to": msg.receiver.your_name,
            "message": msg.message,
            "sent_at": localtime(msg.sent_at).strftime("%Y-%m-%d %H:%M:%S"),
            "files": [
                request.build_absolute_uri(f.file.url) for f in msg.files.all()
            ],
        } for msg in messages
    ]

    return Response({
        "EC": 0,
        "EM": "Fetched chat history",
        "DT": result
    })


# ===============================================================================

