"""
apps.employees アプリケーション設定。

TASK-001: Employee Model作成
"""
from django.apps import AppConfig


class EmployeesConfig(AppConfig):
    """employees アプリケーションの設定クラス。"""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.employees"
    verbose_name = "社員管理"
