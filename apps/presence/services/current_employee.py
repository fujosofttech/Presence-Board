from apps.employees.models import Employee

def get_current_employee(request):
    """
    現在のリクエストユーザーに紐づくEmployeeを取得する
    """
    return Employee.objects.get(email=request.user.email, deleted_at__isnull=True)
