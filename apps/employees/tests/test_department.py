"""
TASK-001: Department モデル Unit Test

テスト規約（21_AI実装ガイド.md 第10章参照）:
- 正常系
- 異常系
- 境界値
- バリデーション
"""

from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from apps.employees.models import Department, Group


def make_department(name: str = "開発部", display_order: int = 1) -> Department:
    """Department テストデータを生成するヘルパー関数。"""
    return Department.objects.create(name=name, display_order=display_order)


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

    def test_department_name_unique(self) -> None:
        """異常系: 同じ name の Department を2件作成すると IntegrityError が発生すること。"""
        make_department(name="重複部門")
        with self.assertRaises(IntegrityError):
            Department.objects.create(name="重複部門", display_order=2)

    def test_department_display_order_positive_integer(self) -> None:
        """正常系: display_order が 0 以上の整数で保存できること。"""
        dept = make_department(display_order=0)
        self.assertEqual(dept.display_order, 0)

    def test_department_protect_on_group_exists(self) -> None:
        """異常系: Group が存在する Department を削除しようとすると ProtectedError が発生すること。"""
        from django.db.models import ProtectedError

        dept = make_department()
        Group.objects.create(
            department=dept,
            name="グループA",
            display_order=1,
        )
        with self.assertRaises(ProtectedError):
            dept.delete()
