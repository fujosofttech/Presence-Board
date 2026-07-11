from django.utils import timezone
from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from .models import Department, Group, WorkLocation, StatusMaster, Employee
from .serializers import (
    DepartmentSerializer, GroupSerializer, WorkLocationSerializer, 
    StatusMasterSerializer, EmployeeSerializer
)

class DepartmentViewSet(viewsets.ModelViewSet):
    """
    課マスタのAPIエンドポイント。
    """
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['display_order', 'id']
    ordering = ['display_order', 'id']

    def get_queryset(self):
        # 論理削除されていないレコードのみ取得
        return Department.objects.filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        # 物理削除の代わりに論理削除
        instance.deleted_at = timezone.now()
        instance.save()

class GroupViewSet(viewsets.ModelViewSet):
    """
    グループマスタのAPIエンドポイント。
    """
    serializer_class = GroupSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['display_order', 'id']
    ordering = ['display_order', 'id']

    def get_queryset(self):
        queryset = Group.objects.filter(deleted_at__isnull=True)
        # クエリパラメータによるフィルタリング
        department_id = self.request.query_params.get('department')
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        return queryset

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

class WorkLocationViewSet(viewsets.ModelViewSet):
    """
    勤務場所マスタのAPIエンドポイント。
    """
    serializer_class = WorkLocationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['display_order', 'id']
    ordering = ['display_order', 'id']

    def get_queryset(self):
        return WorkLocation.objects.filter(deleted_at__isnull=True)

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()

class StatusMasterViewSet(viewsets.ModelViewSet):
    """
    状態マスタのAPIエンドポイント。
    """
    queryset = StatusMaster.objects.all()
    serializer_class = StatusMasterSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['display_order', 'id']
    ordering = ['display_order', 'id']

    # 状態マスタは論理削除フラグを持たず、物理削除とする想定

class EmployeeViewSet(viewsets.ModelViewSet):
    """
    社員のAPIエンドポイント。
    """
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['employee_no', 'name', 'email']
    ordering_fields = ['display_order', 'id']
    ordering = ['display_order', 'id']

    def get_queryset(self):
        queryset = Employee.objects.filter(deleted_at__isnull=True)
        
        # クエリパラメータによるフィルタリング
        department_id = self.request.query_params.get('department')
        group_id = self.request.query_params.get('group')
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if group_id:
            queryset = queryset.filter(group_id=group_id)
            
        return queryset

    def perform_destroy(self, instance):
        instance.deleted_at = timezone.now()
        instance.save()
