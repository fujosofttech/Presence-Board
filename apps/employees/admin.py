"""
employees アプリの Django Admin 設定。

TASK-001: Employee Model作成
"""
from django.contrib import admin

from apps.employees.models import Department, Employee, Group, StatusMaster, WorkLocation


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Department の Admin 設定。"""

    list_display = ("id", "name", "display_order", "deleted_at", "created_at")
    ordering = ("display_order", "id")
    search_fields = ("name",)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    """Group の Admin 設定。"""

    list_display = ("id", "department", "name", "display_order", "deleted_at", "created_at")
    ordering = ("display_order", "id")
    list_select_related = ("department",)
    search_fields = ("name", "department__name")


@admin.register(WorkLocation)
class WorkLocationAdmin(admin.ModelAdmin):
    """WorkLocation の Admin 設定。"""

    list_display = ("id", "company_name", "office_name", "display_order", "deleted_at")
    ordering = ("display_order", "id")
    search_fields = ("company_name", "office_name")


@admin.register(StatusMaster)
class StatusMasterAdmin(admin.ModelAdmin):
    """StatusMaster の Admin 設定。"""

    list_display = ("id", "name", "display_order", "created_at")
    ordering = ("display_order", "id")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Employee の Admin 設定。"""

    list_display = (
        "id",
        "employee_no",
        "name",
        "email",
        "department",
        "group",
        "display_order",
        "deleted_at",
    )
    ordering = ("display_order", "id")
    list_select_related = ("department", "group", "work_location")
    search_fields = ("employee_no", "name", "email")
    list_filter = ("department", "group")
