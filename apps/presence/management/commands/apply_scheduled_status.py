from apps.presence.events import event_publisher
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.presence.models import ScheduledStatus
from apps.presence.services.scheduled_status import apply_scheduled_status_record

class Command(BaseCommand):
    help = '今日の予定（ScheduledStatus）を Presence へ適用します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-all',
            action='store_true',
            help='時刻判定を無視して当日の未適用予定をすべて適用する'
        )

    def handle(self, *args, **options):
        now = timezone.now()
        today = timezone.localdate(now)
        current_time = timezone.localtime(now).time()
        force_all = options.get('force_all', False)

        scheduled_list = ScheduledStatus.objects.filter(
            target_date=today,
            deleted_at__isnull=True
        ).select_related('employee', 'status')

        applied_count = 0
        skipped_count = 0
        error_count = 0

        for scheduled in scheduled_list:
            try:
                # 既に適用済みの場合はスキップ
                if scheduled.applied_at is not None:
                    skipped_count += 1
                    continue

                # 開始時刻が指定されている場合、現在時刻が開始時刻に達していなければスキップ
                if not force_all and scheduled.start_time is not None:
                    if current_time < scheduled.start_time:
                        skipped_count += 1
                        continue

                apply_scheduled_status_record(scheduled, now=now)
                applied_count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Employee {scheduled.employee.employee_no} の適用に失敗しました: {str(e)}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f'処理完了: {applied_count} 件適用, {skipped_count} 件スキップ, {error_count} 件エラー'))
