from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.shortcuts import render
from django.views import View
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_protect
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .models import Department, Employee, Group, StatusMaster, WorkLocation
from .serializers import (
    DepartmentSerializer,
    EmployeeSerializer,
    GroupSerializer,
    StatusMasterSerializer,
    WorkLocationSerializer,
)

class BaseModelViewSet(viewsets.ModelViewSet):
    """
    論理削除と共通設定をサポートする基底 ViewSet。
    """
    permission_classes = [IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['display_order', 'id']
    ordering = ['display_order', 'id']

    def get_queryset(self):
        return self.queryset.filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()


class DepartmentViewSet(BaseModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        # 一般画面の課絞り込みで GET /departments/ を呼ぶため、listアクションのみ一般ユーザーも許可する。
        # 将来的に新しいアクションが追加された場合でも安全側に倒れるよう、デフォルトはすべて IsAdminUser とする。
        if self.action == 'list':
            return [IsAuthenticated()]
        return [IsAdminUser()]


class GroupViewSet(BaseModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        return queryset


class WorkLocationViewSet(BaseModelViewSet):
    queryset = WorkLocation.objects.all()
    serializer_class = WorkLocationSerializer


class StatusMasterViewSet(viewsets.ModelViewSet):
    queryset = StatusMaster.objects.all()
    serializer_class = StatusMasterSerializer
    permission_classes = [IsAdminUser]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['display_order', 'id']
    ordering = ['display_order', 'id']


class EmployeeViewSet(BaseModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_no', 'name', 'email']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('department', 'group', 'work_location')
        
        department_id = self.request.query_params.get('department')
        group_id = self.request.query_params.get('group')
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if group_id:
            queryset = queryset.filter(group_id=group_id)
            
        return queryset


class AuthView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            user_data = {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
                "is_staff": request.user.is_staff or request.user.is_superuser,
            }
            employee_data = None
            try:
                employee = Employee.objects.get(email=request.user.email, deleted_at__isnull=True)
                employee_data = {
                    "employee_no": employee.employee_no,
                    "name": employee.name,
                }
            except Employee.DoesNotExist:
                pass
            
            return Response({
                "authenticated": True,
                "user": user_data,
                "employee": employee_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "authenticated": False
            }, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                "error_code": "E0001",
                "message": "ユーザー名とパスワードは必須です。"
            }, status=status.HTTP_400_BAD_REQUEST)

        # ユーザー名 または 社員番号 / メールアドレスのいずれでも認証可能にする
        auth_username = username
        if '@' not in username:
            emp = Employee.objects.filter(employee_no=username, deleted_at__isnull=True).first()
            if emp and emp.email:
                user_match = User.objects.filter(email=emp.email).first()
                if user_match:
                    auth_username = user_match.username
                else:
                    auth_username = emp.email
        else:
            user_match = User.objects.filter(email=username).first()
            if user_match:
                auth_username = user_match.username

        user = authenticate(request, username=auth_username, password=password)
        if user is None and auth_username != username:
            user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            user_data = {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff or user.is_superuser,
            }
            employee_data = None
            try:
                employee = Employee.objects.get(email=user.email, deleted_at__isnull=True)
                employee_data = {
                    "employee_no": employee.employee_no,
                    "name": employee.name,
                }
            except Employee.DoesNotExist:
                pass
            
            return Response({
                "authenticated": True,
                "user": user_data,
                "employee": employee_data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "error_code": "E0001",
                "message": "ユーザー名またはパスワードが正しくありません。"
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        logout(request)
        return Response({
            "message": "Logout successful"
        }, status=status.HTTP_200_OK)


class SetPasswordView(View):
    """
    ワンタイムトークンを用いた初回パスワード設定画面のビュー。
    """
    @method_decorator(csrf_protect)
    def get(self, request, uidb64, token, *args, **kwargs):
        user = self._get_user(uidb64)
        if user is None or not default_token_generator.check_token(user, token):
            return render(request, "set_password.html", {"status": "invalid"})

        emp = Employee.objects.filter(email=user.email, deleted_at__isnull=True).first()
        return render(request, "set_password.html", {
            "status": "form",
            "employee_name": emp.name if emp else user.username,
            "employee_no": emp.employee_no if emp else "",
            "email": user.email,
        })

    @method_decorator(csrf_protect)
    def post(self, request, uidb64, token, *args, **kwargs):
        user = self._get_user(uidb64)
        if user is None or not default_token_generator.check_token(user, token):
            return render(request, "set_password.html", {"status": "invalid"})

        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")

        emp = Employee.objects.filter(email=user.email, deleted_at__isnull=True).first()
        context = {
            "status": "form",
            "employee_name": emp.name if emp else user.username,
            "employee_no": emp.employee_no if emp else "",
            "email": user.email,
        }

        if not password or not password_confirm:
            context["error_message"] = "パスワードを入力してください。"
            return render(request, "set_password.html", context)

        if password != password_confirm:
            context["error_message"] = "パスワードと確認用パスワードが一致しません。"
            return render(request, "set_password.html", context)

        if len(password) < 8:
            context["error_message"] = "パスワードは8文字以上で設定してください。"
            return render(request, "set_password.html", context)

        user.set_password(password)
        user.is_active = True
        user.save()

        return render(request, "set_password.html", {"status": "success"})

    def _get_user(self, uidb64):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            return User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return None
