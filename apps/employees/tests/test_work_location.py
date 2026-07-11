"""
TASK-001: WorkLocation モデル Unit Test

テスト規約（21_AI実装ガイド.md 第10章参照）:
- 正常系
- 異常系
- 境界値
"""

from django.test import TestCase
from django.utils import timezone

from apps.employees.models import WorkLocation


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
        self.assertIsNotNone(wl.created_at)
        self.assertIsNotNone(wl.updated_at)

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

    def test_work_location_display_order_positive_integer(self) -> None:
        """正常系: display_order が 0 以上の整数で保存できること。"""
        wl = make_work_location(display_order=0)
        self.assertEqual(wl.display_order, 0)
