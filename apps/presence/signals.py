import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.contrib.auth.models import User

from apps.employees.models import Employee, Department, Group, WorkLocation, StatusMaster
from apps.presence.models import Presence, AuditLog
from apps.presence.middleware import get_current_user, get_current_request, get_client_ip

logger = logging.getLogger(__name__)


# --- 1. ログイン関連の監査ログ ---

@receiver(user_logged_in)
def log_login_success(sender, request, user, **kwargs):
    employee = getattr(user, 'employee', None)
    ip_address = get_client_ip(request) if request else None
    
    AuditLog.objects.create(
        user=user,
        employee=employee,
        action='LOGIN_SUCCESS',
        description=f"ユーザー {user.username} がログインに成功しました。",
        ip_address=ip_address
    )
    logger.info(f"AuditLog: LOGIN_SUCCESS - user={user.username}")


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user:
        if not user.is_authenticated:
            user = None
        employee = getattr(user, 'employee', None) if user else None
        ip_address = get_client_ip(request) if request else None
        
        AuditLog.objects.create(
            user=user,
            employee=employee,
            action='LOGOUT',
            description=f"ユーザー {user.username if user else 'Unknown'} がログアウトしました。",
            ip_address=ip_address
        )
        logger.info(f"AuditLog: LOGOUT - user={user.username if user else 'Unknown'}")


@receiver(user_login_failed)
def log_login_failed(sender, credentials, request, **kwargs):
    username = credentials.get('username', 'Unknown')
    ip_address = get_client_ip(request) if request else None
    
    user = User.objects.filter(username=username).first()
    employee = getattr(user, 'employee', None) if user else None
    
    AuditLog.objects.create(
        user=user,
        employee=employee,
        action='LOGIN_FAILED',
        description=f"ユーザー {username} のログイン試行に失敗しました。",
        ip_address=ip_address
    )
    logger.info(f"AuditLog: LOGIN_FAILED - username={username}")


# --- 2. 状態変更関連の監査ログ ---

@receiver(post_save, sender=Presence)
def log_presence_save(sender, instance, created, **kwargs):
    current_user = get_current_user()
    current_request = get_current_request()
    ip_address = get_client_ip(current_request) if current_request else None
    
    performer_user = current_user or instance.updated_by
    if performer_user and not performer_user.is_authenticated:
        performer_user = None
    
    status_name = instance.status.name
    destination = instance.destination or "なし"
    start_time = instance.start_datetime.isoformat() if instance.start_datetime else "なし"
    end_time = instance.end_datetime.isoformat() if instance.end_datetime else "なし"
    
    action_type = "PRESENCE_UPDATE"
    desc = f"状態が更新されました。状態: {status_name}, 行先: {destination}, 開始: {start_time}, 戻り予定: {end_time}。"
    
    AuditLog.objects.create(
        user=performer_user,
        employee=instance.employee,
        action=action_type,
        description=desc,
        ip_address=ip_address
    )
    logger.info(f"AuditLog: PRESENCE_UPDATE - employee={instance.employee.name} status={status_name}")


# --- 3. 管理操作関連の監査ログ ---

ADMIN_MODELS = (Employee, Department, Group, WorkLocation, StatusMaster)

def get_model_verbose_name(model_class):
    return getattr(model_class._meta, 'verbose_name', model_class.__name__)

def handle_admin_op(sender, instance, action_verb):
    current_user = get_current_user()
    if current_user and not current_user.is_authenticated:
        current_user = None
    current_request = get_current_request()
    ip_address = get_client_ip(current_request) if current_request else None
    
    model_name = get_model_verbose_name(sender)
    target_employee = instance if isinstance(instance, Employee) else None
    
    desc = f"{model_name} が{action_verb}されました。詳細: {str(instance)}"
    
    AuditLog.objects.create(
        user=current_user,
        employee=target_employee,
        action='ADMIN_OP',
        description=desc,
        ip_address=ip_address
    )
    logger.info(f"AuditLog: ADMIN_OP - model={sender.__name__} action={action_verb}")


@receiver(post_save)
def log_admin_model_save(sender, instance, created, **kwargs):
    if sender in ADMIN_MODELS:
        verb = "新規作成" if created else "更新"
        handle_admin_op(sender, instance, verb)


@receiver(post_delete)
def log_admin_model_delete(sender, instance, **kwargs):
    if sender in ADMIN_MODELS:
        handle_admin_op(sender, instance, "削除")
