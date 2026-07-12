from rest_framework import serializers
from django.utils import timezone
from apps.employees.models import Employee, StatusMaster
from apps.presence.models import Presence, FavoriteDestination, ScheduledStatus
from apps.presence.validators import validate_presence_data

class PresenceSerializer(serializers.ModelSerializer):
    status = serializers.CharField(source='status.name')

    class Meta:
        model = Presence
        fields = ['status', 'destination', 'start_datetime', 'end_datetime', 'updated_at']

class PresenceListSerializer(serializers.ModelSerializer):
    department_name = serializers.SerializerMethodField()
    group_name = serializers.SerializerMethodField()
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

    def get_department_name(self, obj):
        if obj.department:
            if obj.department.deleted_at:
                return None
            return obj.department.name
        return None

    def get_group_name(self, obj):
        if obj.group:
            if obj.group.deleted_at:
                return None
            return obj.group.name
        return None

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

        validated = validate_presence_data(
            status_name=status_name,
            destination=destination,
            end_time_name='return_time',
            end_time_value=return_time
        )
        
        data['destination'] = validated['destination']
        data['return_time'] = validated['return_time']

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
        if target_date and target_date < timezone.localdate():
            raise serializers.ValidationError({"target_date": "今日以前の日付は登録できません。"})

        status_name = data.get('status')
        destination = data.get('destination', '')
        end_time = data.get('end_time')

        validated = validate_presence_data(
            status_name=status_name,
            destination=destination,
            end_time_name='end_time',
            end_time_value=end_time
        )
        
        data['destination'] = validated['destination']
        data['end_time'] = validated['end_time']

        return data
