from django.utils import timezone
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated

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
    permission_classes = [IsAuthenticated]
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
    permission_classes = [IsAuthenticated]
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
