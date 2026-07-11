"""
社員管理アプリケーションのモデル定義。

TASK-001: Employee Model作成（レビュー修正対応）
対象設計書: docs/design/05_DB設計.md

本モジュールでは以下のモデルを定義する。
- TimestampModel  : 共通基底クラス（タイムスタンプ管理）
- Department      : 課マスタ
- Group           : グループマスタ
- WorkLocation    : 勤務場所マスタ（客先常駐用）
- StatusMaster    : 状態マスタ
- Employee        : 社員
"""

from __future__ import annotations

from django.db import models


# ==============================================================================
# 共通基底クラス
# ==============================================================================


class TimestampModel(models.Model):
    """タイムスタンプ管理の共通基底クラス。

    created_at / updated_at / deleted_at を持つ全モデルが継承する。
    論理削除（deleted_at）は本クラスで一元管理する。

    Attributes:
        created_at: 作成日時（自動設定）。
        updated_at: 更新日時（自動更新）。
        deleted_at: 論理削除日時（NULL の場合は有効）。
    """

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="削除日時")

    class Meta:
        abstract = True


# ==============================================================================
# マスタモデル
# ==============================================================================


class Department(TimestampModel):
    """課マスタ。

    社員が所属する課を管理する。

    Attributes:
        name: 課名（最大100文字、一意）。
        display_order: 表示順（0以上の整数）。
    """

    name = models.CharField(max_length=100, unique=True, verbose_name="課名")
    display_order = models.PositiveIntegerField(default=0, verbose_name="表示順")

    class Meta:
        db_table = "department"
        verbose_name = "課"
        verbose_name_plural = "課一覧"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return str(self.name)


class Group(TimestampModel):
    """グループマスタ。

    課に紐づくグループを管理する。
    同一課内でのグループ名重複は許可しない（複合ユニーク制約）。

    Attributes:
        department: 所属課（FK: Department）。
        name: グループ名（最大100文字）。
        display_order: 表示順（0以上の整数）。
    """

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="groups",
        verbose_name="課",
    )
    name = models.CharField(max_length=100, verbose_name="グループ名")
    display_order = models.PositiveIntegerField(default=0, verbose_name="表示順")

    class Meta:
        db_table = "group"
        verbose_name = "グループ"
        verbose_name_plural = "グループ一覧"
        ordering = ["display_order", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["department", "name"],
                name="uq_group_department_name",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.department.name} - {self.name}"


class WorkLocation(TimestampModel):
    """勤務場所マスタ。

    客先常駐社員の勤務場所を管理する。

    Attributes:
        company_name: 会社名（最大200文字）。
        office_name: 事業所名（最大200文字）。
        address: 住所（最大500文字）。
        display_order: 表示順（0以上の整数）。
    """

    company_name = models.CharField(max_length=200, verbose_name="会社名")
    office_name = models.CharField(max_length=200, verbose_name="事業所名")
    address = models.CharField(max_length=500, verbose_name="住所")
    display_order = models.PositiveIntegerField(default=0, verbose_name="表示順")

    class Meta:
        db_table = "work_location"
        verbose_name = "勤務場所"
        verbose_name_plural = "勤務場所一覧"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return f"{self.company_name} {self.office_name}"


class StatusMaster(models.Model):
    """状態マスタ。

    社員の在籍・行先ステータスを管理する。
    name は言語非依存のコード（例: "PRESENT", "REMOTE"）で管理し、
    表示名のマッピングは UI 側で行う（AI First Design に準拠）。

    StatusCode（TextChoices）を使用することで、コード補完・型安全性・
    可読性を向上させる。

    Attributes:
        name: 状態コード（StatusCode より選択）。
        display_order: 表示順（0以上の整数）。
        created_at: 作成日時（自動設定）。
        updated_at: 更新日時（自動更新）。
    """

    class StatusCode(models.TextChoices):
        """状態コード定義（05_DB設計.md 参照）。"""

        PRESENT = "PRESENT", "在席"
        CUSTOMER = "CUSTOMER", "客先・客先常駐"
        OUT = "OUT", "外出・出張"
        MEETING = "MEETING", "会議"
        REMOTE = "REMOTE", "在宅勤務・リモート"
        HOLIDAY = "HOLIDAY", "休暇"
        LEAVE = "LEAVE", "退社"
        DIRECT_HOME = "DIRECT_HOME", "直帰"

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=StatusCode.choices,
        verbose_name="状態コード",
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        db_table = "status_master"
        verbose_name = "状態マスタ"
        verbose_name_plural = "状態マスタ一覧"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return str(self.name)


# ==============================================================================
# 社員モデル
# ==============================================================================


class Employee(TimestampModel):
    """社員モデル。

    社員情報を管理する中心テーブル。論理削除を採用する。

    Attributes:
        employee_no: 社員番号（最大10文字、一意）。
        name: 氏名（最大100文字）。
        email: メールアドレス（最大255文字、一意）。
        department: 所属課（FK: Department）。
        group: 所属グループ（FK: Group）。
        work_location: 勤務場所（FK: WorkLocation、NULL可）。
        phone_number: 連絡先電話番号（最大50文字、任意）。
        display_order: 表示順（0以上の整数）。
    """

    employee_no = models.CharField(max_length=10, unique=True, verbose_name="社員番号")
    name = models.CharField(max_length=100, verbose_name="氏名")
    email = models.EmailField(max_length=255, unique=True, verbose_name="メールアドレス")
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="課",
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="employees",
        verbose_name="グループ",
    )
    work_location = models.ForeignKey(
        WorkLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employees",
        verbose_name="勤務場所",
    )
    phone_number = models.CharField(
        max_length=50,
        blank=True,
        default="",
        verbose_name="連絡先",
    )
    display_order = models.PositiveIntegerField(default=0, verbose_name="表示順")

    class Meta:
        db_table = "employee"
        verbose_name = "社員"
        verbose_name_plural = "社員一覧"
        ordering = ["display_order", "id"]
        indexes = [
            # employee_no・email は unique=True により自動的にユニークインデックスが生成される
            # そのため idx_employee_no・idx_employee_email は不要（重複インデックス回避）
            models.Index(fields=["group_id"], name="idx_employee_group"),
            models.Index(fields=["department_id"], name="idx_employee_department"),
            models.Index(fields=["display_order"], name="idx_employee_display_order"),
        ]

    def __str__(self) -> str:
        return f"{self.employee_no} {self.name}"
