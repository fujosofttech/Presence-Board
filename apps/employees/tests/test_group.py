"""
TASK-001: Group モデル Unit Test

テスト規約（21_AI実装ガイド.md 第10章参照）:
- 正常系
- 異常系
- 境界値
- バリデーション
"""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.employees.models import Department, Employee, Group


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
        dept = make_department(name="開発部2", display_order=2)
        group = make_group(department=dept, name="第2グループ")
        self.assertEqual(str(group), "開発部2 - 第2グループ")

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

    def test_group_unique_constraint_same_department(self) -> None:
        """異常系: 同一課内で同じグループ名を登録すると IntegrityError が発生すること。"""
        make_group(department=self.department, name="重複グループ")
        with self.assertRaises(IntegrityError):
            Group.objects.create(
                department=self.department,
                name="重複グループ",
                display_order=2,
            )

    def test_group_same_name_different_department_allowed(self) -> None:
        """正常系: 異なる課に同じグループ名は登録できること（複合ユニーク制約の確認）。"""
        dept2 = make_department(name="営業部", display_order=2)
        make_group(department=self.department, name="共通グループ")
        group2 = make_group(department=dept2, name="共通グループ")

        self.assertIsNotNone(group2.pk)

    def test_group_display_order_positive_integer(self) -> None:
        """正常系: display_order が 0 以上の整数で保存できること。"""
        group = make_group(department=self.department, display_order=0)
        self.assertEqual(group.display_order, 0)

    def test_group_protect_employee_deletion(self) -> None:
        """異常系: Employee が存在する Group を削除しようとすると ProtectedError が発生すること。"""
        from django.db.models import ProtectedError

        group = make_group(department=self.department)
        Employee.objects.create(
            employee_no="E0001",
            name="テスト社員",
            email="test@example.com",
            department=self.department,
            group=group,
        )
        with self.assertRaises(ProtectedError):
            group.delete()
