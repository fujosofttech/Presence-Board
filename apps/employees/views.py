from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import ensure_csrf_cookie
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

