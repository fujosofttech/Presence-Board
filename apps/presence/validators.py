from rest_framework import serializers
from apps.employees.models import StatusMaster

def validate_presence_data(status_name, destination, end_time_name, end_time_value):
    """
    Presence および ScheduledStatus のバリデーションを共通化
    """
    errors = {}
    return_data = {
        'destination': destination,
        end_time_name: end_time_value
    }
    
    status_code = StatusMaster.StatusCode
    
    if status_name in [status_code.PRESENT, status_code.LEAVE, status_code.REMOTE, status_code.HOLIDAY]:
        if destination:
            errors['destination'] = f"Destination must be empty for {status_name}."
        if end_time_value:
            errors[end_time_name] = f"{end_time_name.replace('_', ' ').capitalize()} must be empty for {status_name}."
            
    elif status_name == status_code.OUT:
        if not destination:
            errors['destination'] = "Destination is required for OUT."
        if not end_time_value:
            errors[end_time_name] = f"{end_time_name.replace('_', ' ').capitalize()} is required for OUT."
            
    elif status_name in [status_code.CUSTOMER, status_code.MEETING]:
        if not destination:
            errors['destination'] = f"Destination is required for {status_name}."
            
    elif status_name == status_code.DIRECT_HOME:
        if not destination:
            errors['destination'] = "Destination is required for DIRECT_HOME."
        return_data[end_time_name] = None

    if errors:
        raise serializers.ValidationError(errors)

    return return_data
