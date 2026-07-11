"""
TASK-001: Employee モデル Unit Test

テスト規約（21_AI実装ガイド.md 第10章参照）:
- 正常系
- 異常系
- 境界値
"""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.employees.models import Department, Employee, Group, WorkLocation


def make_department(name: str = "開発部", display_order: int = 1) -> Department:
    """Department テストデータを生成するヘルパー関数。"""
    return Department.objects.create(name=name, display_order=display_order)


def make_group(department: Department, name: str = "第1グループ", display_order: int = 1) -> Group:
    """Group テストデータを生成するヘルパー関数。"""
    return Group.objects.create(
        department=department,
        name=name,
        display_order=display_order,
    )


def make_work_location(
    company_name: str = "テスト株式会社",
    office_name: str = "東京オフィス",
    address: str = "東京都港区1-1-1",
    display_order: int = 1,
) -> WorkLocation:
    """WorkLocation テストデータを生成するヘルパー関数。"""
    return WorkLocation.objects.create(
        company_name=company_name,
        office_name=office_name,
        address=address,
        display_order=display_order,
    )


def make_employee(
    department: Department,
    group: Group,
    employee_no: str = "E0001",
    name: str = "山田 太郎",
    email: str = "yamada.taro@example.com",
    work_location: WorkLocation | None = None,
    phone_number: str = "",
    display_order: int = 1,
) -> Employee:
    """Employee テストデータを生成するヘルパー関数。"""
    return Employee.objects.create(
        employee_no=employee_no,
        name=name,
        email=email,
        department=department,
        group=group,
        work_location=work_location,
        phone_number=phone_number,
        display_order=display_order,
    )


class EmployeeModelTest(TestCase):
    """Employee モデルのユニットテスト。"""

    def setUp(self) -> None:
        """テスト前処理: 共通の Department, Group を作成。"""
        self.department = make_department()
        self.group = make_group(department=self.department)

    def test_create_employee_normal(self) -> None:
        """正常系: Employee を作成できること（勤務場所なし）。"""
        emp = make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0001",
            name="鈴木 一郎",
            email="suzuki.ichiro@example.com",
        )

        self.assertIsNotNone(emp.pk)
        self.assertEqual(emp.employee_no, "E0001")
        self.assertEqual(emp.name, "鈴木 一郎")
        self.assertEqual(emp.email, "suzuki.ichiro@example.com")
        self.assertEqual(emp.department, self.department)
        self.assertEqual(emp.group, self.group)
        self.assertIsNone(emp.work_location)
        self.assertEqual(emp.phone_number, "")
        self.assertIsNone(emp.deleted_at)
        self.assertIsNotNone(emp.created_at)
        self.assertIsNotNone(emp.updated_at)

    def test_create_employee_with_work_location(self) -> None:
        """正常系: work_location を指定して Employee を作成できること。"""
        wl = make_work_location()
        emp = make_employee(
            department=self.department,
            group=self.group,
            work_location=wl,
        )

        self.assertEqual(emp.work_location, wl)

    def test_employee_str(self) -> None:
        """正常系: __str__ が '社員番号 氏名' を返すこと。"""
        emp = make_employee(
            department=self.department,
            group=self.group,
            employee_no="E9999",
            name="田中 花子",
        )
        self.assertEqual(str(emp), "E9999 田中 花子")

    def test_employee_soft_delete(self) -> None:
        """正常系: 論理削除（deleted_at）を設定できること。"""
        emp = make_employee(department=self.department, group=self.group)
        emp.deleted_at = timezone.now()
        emp.save()

        refreshed = Employee.objects.get(pk=emp.pk)
        self.assertIsNotNone(refreshed.deleted_at)

    def test_employee_unique_employee_no(self) -> None:
        """異常系: 同じ employee_no の Employee を2件作成すると IntegrityError が発生すること。"""
        make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0001",
            email="user1@example.com",
        )
        with self.assertRaises(IntegrityError):
            Employee.objects.create(
                employee_no="E0001",  # 重複
                name="別の社員",
                email="user2@example.com",
                department=self.department,
                group=self.group,
            )

    def test_employee_unique_email(self) -> None:
        """異常系: 同じ email の Employee を2件作成すると IntegrityError が発生すること。"""
        make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0001",
            email="duplicate@example.com",
        )
        with self.assertRaises(IntegrityError):
            Employee.objects.create(
                employee_no="E0002",
                name="別の社員",
                email="duplicate@example.com",  # 重複
                department=self.department,
                group=self.group,
            )

    def test_employee_work_location_nullable(self) -> None:
        """正常系: work_location が NULL（None）で保存できること。"""
        emp = make_employee(
            department=self.department,
            group=self.group,
            work_location=None,
        )
        self.assertIsNone(emp.work_location)

    def test_employee_work_location_set_null_on_delete(self) -> None:
        """正常系: WorkLocation を削除しても Employee は残り work_location が NULL になること。"""
        wl = make_work_location()
        emp = make_employee(
            department=self.department,
            group=self.group,
            work_location=wl,
        )

        wl.delete()
        emp.refresh_from_db()
        self.assertIsNone(emp.work_location)

    def test_employee_protect_department_deletion(self) -> None:
        """異常系: Employee が存在する Department を削除しようとすると ProtectedError が発生すること。"""
        from django.db.models import ProtectedError

        make_employee(department=self.department, group=self.group)
        with self.assertRaises(ProtectedError):
            self.department.delete()

    def test_employee_protect_group_deletion(self) -> None:
        """異常系: Employee が存在する Group を削除しようとすると ProtectedError が発生すること。"""
        from django.db.models import ProtectedError

        make_employee(department=self.department, group=self.group)
        with self.assertRaises(ProtectedError):
            self.group.delete()

    def test_employee_phone_number_optional(self) -> None:
        """正常系: phone_number を省略して Employee を作成できること。"""
        emp = make_employee(
            department=self.department,
            group=self.group,
            phone_number="",
        )
        self.assertEqual(emp.phone_number, "")

    def test_employee_phone_number_with_value(self) -> None:
        """正常系: phone_number を設定して Employee を作成できること。"""
        emp = make_employee(
            department=self.department,
            group=self.group,
            phone_number="090-1234-5678",
        )
        self.assertEqual(emp.phone_number, "090-1234-5678")

    def test_employee_employee_no_max_length(self) -> None:
        """境界値: 社員番号が最大10文字で保存できること。"""
        emp = make_employee(
            department=self.department,
            group=self.group,
            employee_no="E123456789",  # 10文字
        )
        self.assertEqual(emp.employee_no, "E123456789")

    def test_employee_related_name_from_department(self) -> None:
        """正常系: related_name 'employees' で Department から Employee を取得できること。"""
        make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0001",
            email="a@example.com",
        )
        make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0002",
            email="b@example.com",
        )

        employees = list(self.department.employees.all())
        self.assertEqual(len(employees), 2)

    def test_employee_related_name_from_group(self) -> None:
        """正常系: related_name 'employees' で Group から Employee を取得できること。"""
        make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0001",
            email="a@example.com",
        )

        employees = list(self.group.employees.all())
        self.assertEqual(len(employees), 1)

    def test_employee_ordering(self) -> None:
        """正常系: display_order 順で Employee を取得できること。"""
        make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0003",
            email="c@example.com",
            display_order=3,
        )
        make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0001",
            email="a@example.com",
            display_order=1,
        )
        make_employee(
            department=self.department,
            group=self.group,
            employee_no="E0002",
            email="b@example.com",
            display_order=2,
        )

        employees = list(Employee.objects.all())
        self.assertEqual(employees[0].employee_no, "E0001")
        self.assertEqual(employees[1].employee_no, "E0002")
        self.assertEqual(employees[2].employee_no, "E0003")

    def test_employee_display_order_positive_integer(self) -> None:
        """正常系: display_order が 0 以上の整数で保存できること。"""
        emp = make_employee(
            department=self.department,
            group=self.group,
            display_order=0,
        )
        self.assertEqual(emp.display_order, 0)
