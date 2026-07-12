from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
from apps.presence.models import PresenceHistory, AuditLog


class Command(BaseCommand):
    help = 'Prunes PresenceHistory and AuditLog records older than their configured retention limits.'

    def handle(self, *args, **options):
        # 1. Prune PresenceHistory
        history_days = getattr(settings, 'PRESENCE_HISTORY_RETENTION_DAYS', 30)
        history_threshold = timezone.now() - timedelta(days=history_days)
        
        history_deleted, _ = PresenceHistory.objects.filter(created_at__lt=history_threshold).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {history_deleted} PresenceHistory records older than {history_days} days."
            )
        )

        # 2. Prune AuditLog
        audit_days = getattr(settings, 'AUDIT_LOG_RETENTION_DAYS', 365)
        audit_threshold = timezone.now() - timedelta(days=audit_days)
        
        audit_deleted, _ = AuditLog.objects.filter(created_at__lt=audit_threshold).delete()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully deleted {audit_deleted} AuditLog records older than {audit_days} days."
            )
        )
