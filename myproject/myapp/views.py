from rest_framework.response import Response
from rest_framework.decorators import api_view, parser_classes
from django.contrib.auth.models import User
from .models import User
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
import uuid
from .utils import create_access_token
import jwt
from django.views.decorators.csrf import csrf_exempt

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
    email = request.data.get("email")
    password = request.data.get("password")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = None

    if user is None or not check_password(password, user.password):
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "Invalid email or password"
        }, status=status.HTTP_400_BAD_REQUEST)  # hoặc 401 cũng được

    # Nếu đăng nhập thành công
    access_token = create_access_token(user)
    refresh_token = str(uuid.uuid4())
    refresh_expired = now() + timedelta(days=30)

    user.refresh_token = refresh_token
    user.refresh_expired = refresh_expired
    user.save()

    return Response({
        "DT": {
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
    email = request.data.get("email")
    refresh_token = request.data.get("refresh_token")

    if not email or not refresh_token:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "Email and refresh token are required"
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email, refresh_token=refresh_token)

        # Invalidate refresh_token
        user.refresh_token = None
        user.refresh_expired = None
        user.save()

        return Response({
            "DT": "",
            "EC": 0,
            "EM": "User logged out successfully"
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            "DT": "",
            "EC": 1,
            "EM": "Invalid email or refresh token"
        }, status=status.HTTP_401_UNAUTHORIZED)

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
        new_access_token = create_access_token(user)

        # Trong hàm refresh_token, sau khi tạo new_access_token
        decoded_payload = jwt.decode(new_access_token, settings.SECRET_KEY, algorithms=['HS256'])
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

# =====================================================================================

# Refresh Token
# from .utils import create_access_token  # Hàm tạo access token (nếu có)
# @api_view(['POST'])
# def refresh_token(request):
#     email = request.data.get("email")
#     refresh_token = request.data.get("refresh_token")
#
#     # Kiểm tra email có tồn tại trong database không
#     user = User.objects.filter(email=email).first()
#     if not user:
#         return Response({"error": "User not found"}, status=404)
#
#     # Kiểm tra refresh_token hợp lệ không (giả sử có lưu refresh_token trong User model)
#     if user.refresh_token != refresh_token:
#         return Response({"error": "Invalid refresh token"}, status=401)
#
#     # Tạo access token mới
#     new_access_token = create_access_token(user)
#
#     return Response({"access_token": new_access_token}, status=200)
