from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from apps.presence.models import Presence, PresenceHistory, ScheduledStatus
from apps.presence.events import event_publisher

class Command(BaseCommand):
    help = '今日の予定（ScheduledStatus）を Presence へ適用します'

    def handle(self, *args, **options):
        today = timezone.localdate()
        now = timezone.now()
        
        system_user = User.objects.filter(is_superuser=True).first()

        scheduled_list = ScheduledStatus.objects.filter(
            target_date=today,
            deleted_at__isnull=True
        ).select_related('employee', 'status')

        applied_count = 0
        skipped_count = 0
        error_count = 0

        for scheduled in scheduled_list:
            try:
                with transaction.atomic():
                    employee = scheduled.employee
                    status_master = scheduled.status
                    
                    target_end_datetime = None
                    if scheduled.end_time:
                        target_end_datetime = timezone.make_aware(
                            timezone.datetime.combine(today, scheduled.end_time)
                        )

                    presence = Presence.objects.filter(employee=employee).first()

                    if presence:
                        # 冪等性の担保: すでに適用済み、または手動で同じ状態になっている場合はスキップ
                        if (presence.status == status_master and 
                            presence.destination == scheduled.destination and 
                            presence.end_datetime == target_end_datetime):
                            skipped_count += 1
                            continue
                        
                        presence.status = status_master
                        presence.destination = scheduled.destination
                        presence.start_datetime = now
                        presence.end_datetime = target_end_datetime
                        presence.updated_by = system_user
                        presence.save()
                    else:
                        presence = Presence.objects.create(
                            employee=employee,
                            status=status_master,
                            destination=scheduled.destination,
                            start_datetime=now,
                            end_datetime=target_end_datetime,
                            updated_by=system_user
                        )

                    # PresenceHistory の作成
                    PresenceHistory.objects.create(
                        employee=employee,
                        status=status_master,
                        destination=scheduled.destination,
                        start_datetime=now,
                        end_datetime=target_end_datetime,
                        updated_by=system_user
                    )

                    # SSE イベントを発行 (TASK-011)
                    updated_at_iso = presence.updated_at.isoformat()
                    return_time_iso = presence.end_datetime.isoformat() if presence.end_datetime else ""
                    
                    event_data = {
                        "employee_id": employee.id,
                        "employee_no": employee.employee_no,
                        "status": presence.status.name,
                        "destination": presence.destination,
                        "return_time": return_time_iso,
                        "updated_at": updated_at_iso
                    }
                    event_publisher.broadcast("presence_updated", event_data)

                    applied_count += 1
            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Employee {scheduled.employee.employee_no} の適用に失敗しました: {str(e)}"))
                error_count += 1

        self.stdout.write(self.style.SUCCESS(f'処理完了: {applied_count} 件適用, {skipped_count} 件スキップ, {error_count} 件エラー'))

