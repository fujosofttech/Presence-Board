from django.utils import timezone
from datetime import datetime
from django.contrib.auth.models import User
from apps.employees.models import Employee, StatusMaster
from apps.presence.models import Presence, PresenceHistory
from apps.presence.validators import validate_presence_data
from apps.presence.events import event_publisher

def presence_update(
    employee_no: str,
    status_name: str,
    destination: str = "",
    end_datetime_str: str | None = None,
    performer_username: str | None = None
) -> dict:
    """
    AIエージェント用ツール: 社員の在席状態を更新する。
    """
    employee = Employee.objects.get(employee_no=employee_no, deleted_at__isnull=True)
    status_upper = status_name.upper()
    status_master = StatusMaster.objects.get(name=status_upper)
    
    end_dt = None
    if end_datetime_str:
        end_dt = datetime.fromisoformat(end_datetime_str)
        if timezone.is_naive(end_dt):
            end_dt = timezone.make_aware(end_dt)
        
    validated = validate_presence_data(
        status_name=status_upper,
        destination=destination,
        end_time_name='end_datetime',
        end_time_value=end_dt
    )
    
    performer = None
    if performer_username:
        performer = User.objects.get(username=performer_username)
        
    presence, _ = Presence.objects.get_or_create(employee=employee, defaults={'status': status_master})
    
    presence.status = status_master
    presence.destination = validated['destination']
    presence.start_datetime = timezone.now()
    presence.end_datetime = validated['end_datetime']
    presence.updated_by = performer
    presence.save()
    
    # 履歴登録
    PresenceHistory.objects.create(
        employee=employee,
        status=status_master,
        destination=presence.destination,
        start_datetime=presence.start_datetime,
        end_datetime=presence.end_datetime,
        updated_by=performer
    )
    
    # SSE配信
    payload = {
        "employee_profile_id": employee.id,
        "employee_no": employee.employee_no,
        "status": status_upper,
        "destination": presence.destination,
        "return_time": presence.end_datetime.isoformat() if presence.end_datetime else None,
        "updated_at": presence.updated_at.isoformat()
    }
    event_publisher.broadcast("presence_updated", payload)
    
    return payload

def presence_search(query: str) -> list[dict]:
    """
    AIエージェント用ツール: 条件に基づいて社員の在席状況を検索する。
    """
    from apps.presence.services.search_parser import SearchParser
    from apps.presence.services.search_builder import SearchBuilder
    
    parsed_queries = SearchParser.parse_query(query)
    conditions = SearchBuilder.build_conditions(parsed_queries)
    
    employees = Employee.objects.filter(deleted_at__isnull=True).select_related('presence__status', 'department', 'group')
    if conditions:
        employees = employees.filter(*conditions)
    
    results = []
    for emp in employees:
        presence = getattr(emp, 'presence', None)
        results.append({
            "employee_no": emp.employee_no,
            "name": emp.name,
            "department": emp.department.name if emp.department else "",
            "group": emp.group.name if emp.group else "",
            "status": presence.status.name if presence else "PRESENT",
            "destination": presence.destination if presence else "",
            "return_time": presence.end_datetime.isoformat() if presence and presence.end_datetime else None,
        })
    return results

def presence_list(department_name: str | None = None) -> list[dict]:
    """
    AIエージェント用ツール: 全社員（または特定部署）の現在の在席状況一覧を取得する。
    """
    queryset = Employee.objects.filter(deleted_at__isnull=True).select_related('presence__status', 'department', 'group')
    if department_name:
        queryset = queryset.filter(department__name__icontains=department_name)
        
    results = []
    for emp in queryset:
        presence = getattr(emp, 'presence', None)
        results.append({
            "employee_no": emp.employee_no,
            "name": emp.name,
            "department": emp.department.name if emp.department else "",
            "group": emp.group.name if emp.group else "",
            "status": presence.status.name if presence else "PRESENT",
            "destination": presence.destination if presence else "",
            "return_time": presence.end_datetime.isoformat() if presence and presence.end_datetime else None,
        })
    return results

def employee_find(employee_no: str) -> dict:
    """
    AIエージェント用ツール: 社員番号から特定の社員情報を詳細取得する。
    """
    emp = Employee.objects.get(employee_no=employee_no, deleted_at__isnull=True)
    presence = getattr(emp, 'presence', None)
    return {
        "employee_no": emp.employee_no,
        "name": emp.name,
        "email": emp.email,
        "department": emp.department.name if emp.department else "",
        "group": emp.group.name if emp.group else "",
        "phone_number": emp.phone_number,
        "status": presence.status.name if presence else "PRESENT",
        "destination": presence.destination if presence else "",
        "return_time": presence.end_datetime.isoformat() if presence and presence.end_datetime else None,
    }
