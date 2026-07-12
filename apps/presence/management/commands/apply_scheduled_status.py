from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from apps.employees.models import Employee
from apps.presence.models import Presence, PresenceHistory, ScheduledStatus

class Command(BaseCommand):
    help = '今日の予定（ScheduledStatus）を Presence へ適用します'

    def handle(self, *args, **options):
        today = timezone.localdate()
        now = timezone.now()
        
        # システムユーザー（またはバッチ実行ユーザー）を取得
        # ここでは更新者として扱うためのダミーユーザーを取得するか、Noneを許容するか。
        # 既存の設計では updated_by は User のため、最初のスーパーユーザーを使うか、システムユーザーを作る。
        system_user = User.objects.filter(is_superuser=True).first()

        scheduled_list = ScheduledStatus.objects.filter(
            target_date=today,
            deleted_at__isnull=True
        ).select_related('employee', 'status')

        count = 0
        with transaction.atomic():
            for scheduled in scheduled_list:
                employee = scheduled.employee
                status_master = scheduled.status
                
                # 既に今日の Presence が手動更新されている場合は上書きしない運用にするか、
                # 単純に朝一のバッチとして上書きするか。
                # 要件に「当日になったらScheduledStatus -> Presenceへ反映」とあるため、上書きする。
                presence, created = Presence.objects.get_or_create(
                    employee=employee,
                    defaults={
                        'status': status_master,
                        'destination': scheduled.destination,
                        'start_datetime': now,
                        'end_datetime': None, # scheduled には時間があるが、現在状態としては一旦 end_datetime に帰社予定を入れる場合がある
                        'updated_by': system_user
                    }
                )

                if not created:
                    presence.status = status_master
                    presence.destination = scheduled.destination
                    presence.start_datetime = now
                    # end_time がある場合はそれを当日の datetime に変換して end_datetime に入れる
                    if scheduled.end_time:
                        presence.end_datetime = timezone.make_aware(
                            timezone.datetime.combine(today, scheduled.end_time)
                        )
                    else:
                        presence.end_datetime = None
                    presence.updated_by = system_user
                    presence.save()

                # PresenceHistory の作成
                PresenceHistory.objects.create(
                    employee=employee,
                    status=status_master,
                    destination=scheduled.destination,
                    start_datetime=now,
                    end_datetime=presence.end_datetime,
                    updated_by=system_user
                )

                count += 1

        self.stdout.write(self.style.SUCCESS(f'{count} 件の予定を Presence へ適用しました。'))
