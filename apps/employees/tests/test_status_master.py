"""
TASK-001: StatusMaster モデル Unit Test

テスト規約（21_AI実装ガイド.md 第10章参照）:
- 正常系
- 異常系
- 境界値
"""

from django.db import IntegrityError
from django.test import TestCase

from apps.employees.models import StatusMaster


def make_status_master(
    name: str = StatusMaster.StatusCode.PRESENT, display_order: int = 1
) -> StatusMaster:
    """StatusMaster テストデータを生成するヘルパー関数。"""
    return StatusMaster.objects.create(name=name, display_order=display_order)


class StatusMasterModelTest(TestCase):
    """StatusMaster モデルのユニットテスト。"""

    def test_create_status_master_normal(self) -> None:
        """正常系: StatusMaster を作成できること。"""
        status = make_status_master(
            name=StatusMaster.StatusCode.PRESENT, display_order=1
        )

        self.assertIsNotNone(status.pk)
        self.assertEqual(status.name, StatusMaster.StatusCode.PRESENT)
        self.assertEqual(status.display_order, 1)
        self.assertIsNotNone(status.created_at)
        self.assertIsNotNone(status.updated_at)

    def test_status_master_str(self) -> None:
        """正常系: __str__ が状態コードを返すこと。"""
        status = make_status_master(name=StatusMaster.StatusCode.REMOTE)
        self.assertEqual(str(status), "REMOTE")

    def test_status_master_all_codes(self) -> None:
        """正常系: 設計書に定義された全8状態コードを作成できること（TextChoices 確認）。"""
        statuses = list(StatusMaster.StatusCode)
        for i, code in enumerate(statuses):
            StatusMaster.objects.create(name=code, display_order=i + 1)

        self.assertEqual(StatusMaster.objects.count(), len(statuses))
        self.assertEqual(len(statuses), 8)

    def test_status_master_unique_name(self) -> None:
        """異常系: 同じ name の StatusMaster を2件作成すると IntegrityError が発生すること。"""
        make_status_master(name=StatusMaster.StatusCode.PRESENT)
        with self.assertRaises(IntegrityError):
            StatusMaster.objects.create(
                name=StatusMaster.StatusCode.PRESENT, display_order=2
            )

    def test_status_master_ordering(self) -> None:
        """正常系: display_order 順で取得できること。"""
        StatusMaster.objects.create(
            name=StatusMaster.StatusCode.LEAVE, display_order=3
        )
        StatusMaster.objects.create(
            name=StatusMaster.StatusCode.PRESENT, display_order=1
        )
        StatusMaster.objects.create(
            name=StatusMaster.StatusCode.REMOTE, display_order=2
        )

        statuses = list(StatusMaster.objects.all())
        self.assertEqual(statuses[0].name, StatusMaster.StatusCode.PRESENT)
        self.assertEqual(statuses[1].name, StatusMaster.StatusCode.REMOTE)
        self.assertEqual(statuses[2].name, StatusMaster.StatusCode.LEAVE)

    def test_status_master_text_choices_label(self) -> None:
        """正常系: TextChoices のラベル（日本語名）が取得できること。"""
        self.assertEqual(StatusMaster.StatusCode.PRESENT.label, "在席")
        self.assertEqual(StatusMaster.StatusCode.REMOTE.label, "在宅勤務・リモート")
        self.assertEqual(StatusMaster.StatusCode.DIRECT_HOME.label, "直帰")

    def test_status_master_display_order_positive_integer(self) -> None:
        """正常系: display_order が 0 以上の整数で保存できること。"""
        status = make_status_master(display_order=0)
        self.assertEqual(status.display_order, 0)
