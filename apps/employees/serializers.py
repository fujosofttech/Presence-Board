from rest_framework import serializers
from .models import Department, Group, WorkLocation, StatusMaster, Employee

class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ['id', 'name', 'display_order', 'created_at', 'updated_at', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']

class GroupSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')

    class Meta:
        model = Group
        fields = ['id', 'department', 'department_name', 'name', 'display_order', 'created_at', 'updated_at', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']

class WorkLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkLocation
        fields = ['id', 'company_name', 'office_name', 'address', 'display_order', 'created_at', 'updated_at', 'deleted_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']

class StatusMasterSerializer(serializers.ModelSerializer):
    name_display = serializers.CharField(source='get_name_display', read_only=True)

    class Meta:
        model = StatusMaster
        fields = ['id', 'name', 'name_display', 'display_order', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class EmployeeSerializer(serializers.ModelSerializer):
    department_name = serializers.ReadOnlyField(source='department.name')
    group_name = serializers.ReadOnlyField(source='group.name')
    work_location_company = serializers.ReadOnlyField(source='work_location.company_name')
    work_location_office = serializers.ReadOnlyField(source='work_location.office_name')

    class Meta:
        model = Employee
        fields = [
            'id', 'employee_no', 'name', 'email', 
            'department', 'department_name', 
            'group', 'group_name', 
            'work_location', 'work_location_company', 'work_location_office', 
            'phone_number', 'display_order', 
            'created_at', 'updated_at', 'deleted_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'deleted_at']

    def validate(self, data):
        # 組織の整合性を検証 (Group が指定された Department に属しているか)
        department = data.get('department')
        group = data.get('group')

        # 部分更新 (PATCH) 等で一部のみ送られてくる場合を考慮し、インスタンスの値も考慮
        if not department and self.instance:
            department = self.instance.department
        if not group and self.instance:
            group = self.instance.group

        if department and group and group.department != department:
            raise serializers.ValidationError({
                "group": "選択されたグループは指定された課に属していません。"
            })
        return data
