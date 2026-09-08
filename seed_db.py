import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from apps.employees.models import Department, Group, StatusMaster, Employee

def seed():
    # 1. スーパーユーザーの作成
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin1234')
        print("Superuser 'admin' created successfully.")
    else:
        print("Superuser 'admin' already exists.")

    # 2. 状態マスタの作成
    statuses = [
        ("PRESENT", 1),
        ("CUSTOMER", 2),
        ("OUT", 3),
        ("MEETING", 4),
        ("REMOTE", 5),
        ("HOLIDAY", 6),
        ("LEAVE", 7),
        ("DIRECT_HOME", 8),
    ]
    for status_name, order in statuses:
        status_master, created = StatusMaster.objects.get_or_create(
            name=status_name,
            defaults={'display_order': order}
        )
        if created:
            print(f"StatusMaster '{status_name}' created.")

    # 3. 部署・グループの作成
    dept_admin, _ = Department.objects.get_or_create(name="管理部", defaults={'display_order': 1})
    group_admin, _ = Group.objects.get_or_create(department=dept_admin, name="総務グループ", defaults={'display_order': 1})

    dept_dev, _ = Department.objects.get_or_create(name="開発部", defaults={'display_order': 2})
    group_dev1, _ = Group.objects.get_or_create(department=dept_dev, name="第一グループ", defaults={'display_order': 1})
    group_dev2, _ = Group.objects.get_or_create(department=dept_dev, name="第二グループ", defaults={'display_order': 2})

    print("Departments and Groups checked/created.")

    # 4. 管理者用 Employee の紐付け
    # django admin ユーザーと同じ email 'admin@example.com' で Employee を作成する
    if not Employee.objects.filter(email='admin@example.com').exists():
        Employee.objects.create(
            employee_no="E0001",
            name="管理者",
            email="admin@example.com",
            department=dept_admin,
            group=group_admin,
            display_order=1
        )
        print("Employee 'E0001' linked to admin@example.com created.")
    else:
        print("Employee admin already exists.")

if __name__ == '__main__':
    seed()
