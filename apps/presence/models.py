from django.db import models
from django.contrib.auth.models import User
from apps.employees.models import Employee, StatusMaster, TimestampModel

class Presence(models.Model):
    """
    社員の現在状態を保持する。
    社員1名につき1レコードのみ保持する。
    """
    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="presence",
        verbose_name="社員",
    )
    status = models.ForeignKey(
        StatusMaster,
        on_delete=models.PROTECT,
        related_name="presences",
        verbose_name="状態",
    )
    destination = models.CharField(
        max_length=300,
        blank=True,
        default="",
        verbose_name="行先",
    )
    start_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="更新開始日時",
    )
    end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="戻り予定日時",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="更新者",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        db_table = "presence"
        verbose_name = "現在状態"
        verbose_name_plural = "現在状態一覧"
        indexes = [
            models.Index(fields=["updated_at"], name="idx_presence_updated_at"),
        ]

    def __str__(self) -> str:
        return f"{self.employee.name} - {self.status.name}"

class PresenceHistory(models.Model):
    """
    状態変更履歴
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="presence_histories",
        verbose_name="社員",
    )
    status = models.ForeignKey(
        StatusMaster,
        on_delete=models.PROTECT,
        related_name="presence_histories",
        verbose_name="状態",
    )
    destination = models.CharField(
        max_length=300,
        blank=True,
        default="",
        verbose_name="行先",
    )
    start_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="更新開始日時",
    )
    end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="戻り予定日時",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="更新者",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")

    class Meta:
        db_table = "presence_history"
        verbose_name = "状態変更履歴"
        verbose_name_plural = "状態変更履歴一覧"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["employee", "created_at"], name="idx_p_hist_emp_created"),
            models.Index(fields=["employee", "status"], name="idx_p_hist_emp_status"),
        ]

    def __str__(self) -> str:
        return f"{self.employee.name} - {self.status.name} ({self.created_at})"


class FavoriteDestination(models.Model):
    """
    お気に入り行先テンプレート
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="favorite_destinations",
        verbose_name="社員",
    )
    destination = models.CharField(
        max_length=255,
        verbose_name="行先名",
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="表示順",
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="作成日時")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新日時")

    class Meta:
        db_table = "favorite_destination"
        verbose_name = "お気に入り行先"
        verbose_name_plural = "お気に入り行先一覧"
        ordering = ["display_order", "-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["employee", "destination"], name="unique_favorite_destination")
        ]

    def __str__(self) -> str:
        return f"{self.employee.name} - {self.destination}"

class ScheduledStatus(TimestampModel):
    """
    事前登録（Scheduled Status）機能
    """
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="scheduled_statuses",
        verbose_name="社員",
    )
    target_date = models.DateField(verbose_name="対象日")
    status = models.ForeignKey(
        StatusMaster,
        on_delete=models.PROTECT,
        related_name="scheduled_statuses",
        verbose_name="状態",
    )
    destination = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="行先",
    )
    start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="開始時刻",
    )
    end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name="終了時刻",
    )
    memo = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="メモ",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_scheduled_statuses",
        verbose_name="作成者",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_scheduled_statuses",
        verbose_name="更新者",
    )

    class Meta:
        db_table = "scheduled_status"
        verbose_name = "事前登録予定"
        verbose_name_plural = "事前登録予定一覧"
        ordering = ["target_date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "target_date"],
                condition=models.Q(deleted_at__isnull=True),
                name="unique_scheduled_status"
            )
        ]

    def __str__(self) -> str:
        return f"{self.employee.name} - {self.target_date} ({self.status.name})"
