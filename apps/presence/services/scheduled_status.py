from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from apps.presence.models import Presence, PresenceHistory, ScheduledStatus
from apps.presence.events import event_publisher

def apply_scheduled_status_record(scheduled: ScheduledStatus, now=None, performer=None):
    """
    指定された ScheduledStatus レコードを Presence テーブルおよび履歴に適用し、
    SSE イベントを配信して applied_at を更新します。
    """
    if now is None:
        now = timezone.now()
    if performer is None:
        performer = User.objects.filter(is_superuser=True).first()

    today = timezone.localdate(now)
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
            presence.status = status_master
            presence.destination = scheduled.destination
            presence.start_datetime = now
            presence.end_datetime = target_end_datetime
            presence.updated_by = performer
            presence.save()
        else:
            presence = Presence.objects.create(
                employee=employee,
                status=status_master,
                destination=scheduled.destination,
                start_datetime=now,
                end_datetime=target_end_datetime,
                updated_by=performer
            )

        PresenceHistory.objects.create(
            employee=employee,
            status=status_master,
            destination=scheduled.destination,
            start_datetime=now,
            end_datetime=target_end_datetime,
            updated_by=performer
        )

        scheduled.applied_at = now
        scheduled.save(update_fields=['applied_at'])

        # SSE イベントを発行
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

    return presence
