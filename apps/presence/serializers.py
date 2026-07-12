from rest_framework import serializers
from django.utils import timezone
from apps.employees.models import Employee, StatusMaster
from apps.presence.models import Presence, FavoriteDestination, ScheduledStatus

class PresenceSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='status.name')

    class Meta:
        model = Presence
        fields = ['status', 'destination', 'start_datetime', 'end_datetime', 'updated_at']

class PresenceListSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)
    presence = serializers.SerializerMethodField()

    class Meta:
        model = Employee
        fields = [
            'id',
            'employee_no',
            'name',
            'email',
            'department',
            'department_name',
            'group',
            'group_name',
            'work_location',
            'phone_number',
            'display_order',
            'presence',
        ]

    def get_presence(self, obj):
        if hasattr(obj, 'presence'):
            return PresenceSerializer(obj.presence).data
        return {
            'status': 'PRESENT',
            'destination': '',
            'start_datetime': None,
            'end_datetime': None,
            'updated_at': None
        }

class PresenceUpdateSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=50)
    destination = serializers.CharField(max_length=300, required=False, allow_blank=True, default='')
    return_time = serializers.DateTimeField(required=False, allow_null=True)

    def validate_status(self, value):
        upper_val = value.upper()
        if not StatusMaster.objects.filter(name=upper_val).exists():
            raise serializers.ValidationError(f"Invalid status: {value}")
        return upper_val

    def validate(self, data):
        status_name = data.get('status')
        destination = data.get('destination', '')
        return_time = data.get('return_time')

        errors = {}

        # バリデーションルール
        # | present / leave / wfh / left_office (PRESENT, LEAVE, REMOTE, HOLIDAY等) | 空である必要あり | 空である必要あり |
        if status_name in ['PRESENT', 'LEAVE', 'REMOTE', 'HOLIDAY']:
            if destination:
                errors['destination'] = f"Destination must be empty for {status_name}."
            if return_time:
                errors['return_time'] = f"Return time must be empty for {status_name}."
        
        elif status_name == 'OUT':
            if not destination:
                errors['destination'] = "Destination is required for OUT."
            if not return_time:
                errors['return_time'] = "Return time is required for OUT."
        
        elif status_name in ['CUSTOMER', 'MEETING']:
            if not destination:
                errors['destination'] = f"Destination is required for {status_name}."
        
        elif status_name == 'DIRECT_HOME':
            if not destination:
                errors['destination'] = "Destination is required for DIRECT_HOME."
            data['return_time'] = None

        if errors:
            raise serializers.ValidationError(errors)

        return data


class FavoriteDestinationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteDestination
        fields = ['id', 'destination', 'display_order']

class FavoriteDestinationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavoriteDestination
        fields = ['destination', 'display_order']

class ScheduledStatusSerializer(serializers.ModelSerializer):
    status = serializers.CharField(max_length=50)

    class Meta:
        model = ScheduledStatus
        fields = ['id', 'target_date', 'status', 'destination', 'start_time', 'end_time', 'memo']

    def validate_status(self, value):
        upper_val = value.upper()
        if not StatusMaster.objects.filter(name=upper_val).exists():
            raise serializers.ValidationError(f"Invalid status: {value}")
        return upper_val

    def validate(self, data):
        target_date = data.get('target_date')
        if target_date and target_date < timezone.now().date():
            raise serializers.ValidationError({"target_date": "今日以前の日付は登録できません。"})

        status_name = data.get('status')
        destination = data.get('destination', '')
        end_time = data.get('end_time')

        errors = {}

        if status_name in ['PRESENT', 'LEAVE', 'REMOTE', 'HOLIDAY']:
            if destination:
                errors['destination'] = f"Destination must be empty for {status_name}."
            if end_time:
                errors['end_time'] = f"End time must be empty for {status_name}."
        
        elif status_name == 'OUT':
            if not destination:
                errors['destination'] = "Destination is required for OUT."
            if not end_time:
                errors['end_time'] = "End time is required for OUT."
        
        elif status_name in ['CUSTOMER', 'MEETING']:
            if not destination:
                errors['destination'] = f"Destination is required for {status_name}."
        
        elif status_name == 'DIRECT_HOME':
            if not destination:
                errors['destination'] = "Destination is required for DIRECT_HOME."
            data['end_time'] = None

        if errors:
            raise serializers.ValidationError(errors)

        return data
