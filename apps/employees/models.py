"""
社員管理アプリケーションのモデル定義。

TASK-001: Employee Model作成
対象設計書: docs/design/05_DB設計.md

本モジュールでは以下のモデルを定義する。
- Department     : 課マスタ
- Group          : グループマスタ
- WorkLocation   : 勤務場所マスタ（客先常駐用）
- StatusMaster   : 状態マスタ
- Employee       : 社員
"""

from __future__ import annotations

from django.db import models


class Department(models.Model):
    """課マスタ。

    社員が所属する課を管理する。

    Attributes:
        name: 課名（最大100文字）。
        display_order: 表示順。
        created_at: 作成日時（自動設定）。
        updated_at: 更新日時（自動更新）。
        deleted_at: 論理削除日時（NULL の場合は有効）。
    """

    name = models.CharField(max_length=100, verbose_name="課名")
    display_order = models.IntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="削除日時")

    class Meta:
        db_table = "department"
        verbose_name = "課"
        verbose_name_plural = "課一覧"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return str(self.name)


class Group(models.Model):
    """グループマスタ。

    課に紐づくグループを管理する。

    Attributes:
        department: 所属課（FK: Department）。
        name: グループ名（最大100文字）。
        display_order: 表示順。
        created_at: 作成日時（自動設定）。
        updated_at: 更新日時（自動更新）。
        deleted_at: 論理削除日時（NULL の場合は有効）。
    """

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="groups",
        verbose_name="課",
    )
    name = models.CharField(max_length=100, verbose_name="グループ名")
    display_order = models.IntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="削除日時")

    class Meta:
        db_table = "group"
        verbose_name = "グループ"
        verbose_name_plural = "グループ一覧"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return f"{self.department.name} - {self.name}"


class WorkLocation(models.Model):
    """勤務場所マスタ。

    客先常駐社員の勤務場所を管理する。

    Attributes:
        company_name: 会社名（最大200文字）。
        office_name: 事業所名（最大200文字）。
        address: 住所（最大500文字）。
        display_order: 表示順。
        created_at: 作成日時（自動設定）。
        updated_at: 更新日時（自動更新）。
        deleted_at: 論理削除日時（NULL の場合は有効）。
    """

    company_name = models.CharField(max_length=200, verbose_name="会社名")
    office_name = models.CharField(max_length=200, verbose_name="事業所名")
    address = models.CharField(max_length=500, verbose_name="住所")
    display_order = models.IntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="削除日時")

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
    nameは言語非依存のコード（例: "PRESENT", "REMOTE"）で管理し、
    表示名のマッピングはUI側で行う（AI First Design に準拠）。

    Attributes:
        name: 状態コード（最大50文字、例: "PRESENT"）。
        display_order: 表示順。
        created_at: 作成日時（自動設定）。
        updated_at: 更新日時（自動更新）。
    """

    # 状態コード定数（05_DB設計.md 参照）
    PRESENT = "PRESENT"
    CUSTOMER = "CUSTOMER"
    OUT = "OUT"
    MEETING = "MEETING"
    REMOTE = "REMOTE"
    HOLIDAY = "HOLIDAY"
    LEAVE = "LEAVE"
    DIRECT_HOME = "DIRECT_HOME"

    STATUS_CHOICES = [
        (PRESENT, "在席"),
        (CUSTOMER, "客先・客先常駐"),
        (OUT, "外出・出張"),
        (MEETING, "会議"),
        (REMOTE, "在宅勤務・リモート"),
        (HOLIDAY, "休暇"),
        (LEAVE, "退社"),
        (DIRECT_HOME, "直帰"),
    ]

    name = models.CharField(
        max_length=50,
        unique=True,
        choices=STATUS_CHOICES,
        verbose_name="状態コード",
    )
    display_order = models.IntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        db_table = "status_master"
        verbose_name = "状態マスタ"
        verbose_name_plural = "状態マスタ一覧"
        ordering = ["display_order", "id"]

    def __str__(self) -> str:
        return str(self.name)


class Employee(models.Model):
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
        display_order: 表示順。
        created_at: 作成日時（自動設定）。
        updated_at: 更新日時（自動更新）。
        deleted_at: 論理削除日時（NULL の場合は有効）。
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
    display_order = models.IntegerField(default=0, verbose_name="表示順")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="削除日時")

    class Meta:
        db_table = "employee"
        verbose_name = "社員"
        verbose_name_plural = "社員一覧"
        ordering = ["display_order", "id"]
        indexes = [
            models.Index(fields=["employee_no"], name="idx_employee_no"),
            models.Index(fields=["email"], name="idx_employee_email"),
            models.Index(fields=["group_id"], name="idx_employee_group"),
            models.Index(fields=["department_id"], name="idx_employee_department"),
            models.Index(fields=["display_order"], name="idx_employee_display_order"),
        ]

    def __str__(self) -> str:
        return f"{self.employee_no} {self.name}"
