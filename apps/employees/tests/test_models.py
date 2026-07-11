"""
TASK-001: Employee Model Unit Test

対象モデル:
- Department
- Group
- WorkLocation
- StatusMaster
- Employee

テスト規約（21_AI実装ガイド.md 第10章参照）:
- 正常系
- 異常系
- 境界値
- バリデーション
"""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.employees.models import Department, Employee, Group, StatusMaster, WorkLocation


# ==============================================================================
# テストデータ生成ヘルパー
# ==============================================================================


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


def make_status_master(
    name: str = StatusMaster.PRESENT, display_order: int = 1
) -> StatusMaster:
    """StatusMaster テストデータを生成するヘルパー関数。"""
    return StatusMaster.objects.create(name=name, display_order=display_order)


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


# ==============================================================================
# Department モデルのテスト
# ==============================================================================


class DepartmentModelTest(TestCase):
    """Department モデルのユニットテスト。"""

    def test_create_department_normal(self) -> None:
        """正常系: Department を作成できること。"""
        dept = make_department(name="システム部", display_order=1)

        self.assertIsNotNone(dept.pk)
        self.assertEqual(dept.name, "システム部")
        self.assertEqual(dept.display_order, 1)
        self.assertIsNone(dept.deleted_at)
        self.assertIsNotNone(dept.created_at)
        self.assertIsNotNone(dept.updated_at)

    def test_department_str(self) -> None:
        """正常系: __str__ が課名を返すこと。"""
        dept = make_department(name="営業部")
        self.assertEqual(str(dept), "営業部")

    def test_department_soft_delete(self) -> None:
        """正常系: 論理削除（deleted_at）を設定できること。"""
        dept = make_department()
        now = timezone.now()
        dept.deleted_at = now
        dept.save()

        refreshed = Department.objects.get(pk=dept.pk)
        self.assertIsNotNone(refreshed.deleted_at)

    def test_department_name_max_length(self) -> None:
        """境界値: 課名が最大100文字で保存できること。"""
        long_name = "あ" * 100
        dept = make_department(name=long_name)
        self.assertEqual(dept.name, long_name)

    def test_department_ordering(self) -> None:
        """正常系: display_order 順で取得できること。"""
        make_department(name="C部門", display_order=3)
        make_department(name="A部門", display_order=1)
        make_department(name="B部門", display_order=2)

        depts = list(Department.objects.all())
        self.assertEqual(depts[0].name, "A部門")
        self.assertEqual(depts[1].name, "B部門")
        self.assertEqual(depts[2].name, "C部門")


# ==============================================================================
# Group モデルのテスト
# ==============================================================================


class GroupModelTest(TestCase):
    """Group モデルのユニットテスト。"""

    def setUp(self) -> None:
        """テスト前処理: 共通の Department を作成。"""
        self.department = make_department()

    def test_create_group_normal(self) -> None:
        """正常系: Group を作成できること。"""
        group = make_group(department=self.department, name="第1グループ", display_order=1)

        self.assertIsNotNone(group.pk)
        self.assertEqual(group.name, "第1グループ")
        self.assertEqual(group.department, self.department)
        self.assertIsNone(group.deleted_at)

    def test_group_str(self) -> None:
        """正常系: __str__ が '課名 - グループ名' を返すこと。"""
        dept = make_department(name="開発部")
        group = make_group(department=dept, name="第2グループ")
        self.assertEqual(str(group), "開発部 - 第2グループ")

    def test_group_soft_delete(self) -> None:
        """正常系: 論理削除（deleted_at）を設定できること。"""
        group = make_group(department=self.department)
        now = timezone.now()
        group.deleted_at = now
        group.save()

        refreshed = Group.objects.get(pk=group.pk)
        self.assertIsNotNone(refreshed.deleted_at)

    def test_group_related_name(self) -> None:
        """正常系: related_name 'groups' で Department から Group を取得できること。"""
        make_group(department=self.department, name="G1")
        make_group(department=self.department, name="G2")

        groups = list(self.department.groups.all())
        self.assertEqual(len(groups), 2)

    def test_group_protect_department_deletion(self) -> None:
        """異常系: Group が存在する Department を削除しようとすると ProtectedError が発生すること。"""
        from django.db.models import ProtectedError

        make_group(department=self.department)
        with self.assertRaises(ProtectedError):
            self.department.delete()


# ==============================================================================
# WorkLocation モデルのテスト
# ==============================================================================


class WorkLocationModelTest(TestCase):
    """WorkLocation モデルのユニットテスト。"""

    def test_create_work_location_normal(self) -> None:
        """正常系: WorkLocation を作成できること。"""
        wl = make_work_location(
            company_name="株式会社テスト",
            office_name="本社",
            address="大阪府大阪市1-1-1",
        )

        self.assertIsNotNone(wl.pk)
        self.assertEqual(wl.company_name, "株式会社テスト")
        self.assertEqual(wl.office_name, "本社")
        self.assertEqual(wl.address, "大阪府大阪市1-1-1")
        self.assertIsNone(wl.deleted_at)

    def test_work_location_str(self) -> None:
        """正常系: __str__ が '会社名 事業所名' を返すこと。"""
        wl = make_work_location(company_name="ABC社", office_name="新宿オフィス")
        self.assertEqual(str(wl), "ABC社 新宿オフィス")

    def test_work_location_soft_delete(self) -> None:
        """正常系: 論理削除（deleted_at）を設定できること。"""
        wl = make_work_location()
        wl.deleted_at = timezone.now()
        wl.save()

        refreshed = WorkLocation.objects.get(pk=wl.pk)
        self.assertIsNotNone(refreshed.deleted_at)

    def test_work_location_address_max_length(self) -> None:
        """境界値: 住所が最大500文字で保存できること。"""
        long_address = "あ" * 500
        wl = make_work_location(address=long_address)
        self.assertEqual(wl.address, long_address)


# ==============================================================================
# StatusMaster モデルのテスト
# ==============================================================================


class StatusMasterModelTest(TestCase):
    """StatusMaster モデルのユニットテスト。"""

    def test_create_status_master_normal(self) -> None:
        """正常系: StatusMaster を作成できること。"""
        status = make_status_master(name=StatusMaster.PRESENT, display_order=1)

        self.assertIsNotNone(status.pk)
        self.assertEqual(status.name, StatusMaster.PRESENT)
        self.assertEqual(status.display_order, 1)

    def test_status_master_str(self) -> None:
        """正常系: __str__ が状態コードを返すこと。"""
        status = make_status_master(name=StatusMaster.REMOTE)
        self.assertEqual(str(status), "REMOTE")

    def test_status_master_all_codes(self) -> None:
        """正常系: 設計書に定義された全8状態を作成できること。"""
        statuses = [
            StatusMaster.PRESENT,
            StatusMaster.CUSTOMER,
            StatusMaster.OUT,
            StatusMaster.MEETING,
            StatusMaster.REMOTE,
            StatusMaster.HOLIDAY,
            StatusMaster.LEAVE,
            StatusMaster.DIRECT_HOME,
        ]
        for i, code in enumerate(statuses):
            StatusMaster.objects.create(name=code, display_order=i + 1)

        self.assertEqual(StatusMaster.objects.count(), 8)

    def test_status_master_unique_name(self) -> None:
        """異常系: 同じ name の StatusMaster を2件作成すると IntegrityError が発生すること。"""
        make_status_master(name=StatusMaster.PRESENT)
        with self.assertRaises(IntegrityError):
            StatusMaster.objects.create(name=StatusMaster.PRESENT, display_order=2)

    def test_status_master_ordering(self) -> None:
        """正常系: display_order 順で取得できること。"""
        StatusMaster.objects.create(name=StatusMaster.LEAVE, display_order=3)
        StatusMaster.objects.create(name=StatusMaster.PRESENT, display_order=1)
        StatusMaster.objects.create(name=StatusMaster.REMOTE, display_order=2)

        statuses = list(StatusMaster.objects.all())
        self.assertEqual(statuses[0].name, StatusMaster.PRESENT)
        self.assertEqual(statuses[1].name, StatusMaster.REMOTE)
        self.assertEqual(statuses[2].name, StatusMaster.LEAVE)


# ==============================================================================
# Employee モデルのテスト
# ==============================================================================


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
            department=self.department, group=self.group, employee_no="E0001", email="a@example.com"
        )
        make_employee(
            department=self.department, group=self.group, employee_no="E0002", email="b@example.com"
        )

        employees = list(self.department.employees.all())
        self.assertEqual(len(employees), 2)

    def test_employee_related_name_from_group(self) -> None:
        """正常系: related_name 'employees' で Group から Employee を取得できること。"""
        make_employee(
            department=self.department, group=self.group, employee_no="E0001", email="a@example.com"
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
