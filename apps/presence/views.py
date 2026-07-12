import json
import queue
from django.db import transaction
from django.http import StreamingHttpResponse
from django.utils import timezone
from apps.presence.services.search_parser import SearchParser
from apps.presence.services.search_builder import SearchBuilder
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from datetime import timedelta
from django.db.models import Max
from apps.employees.models import Employee, StatusMaster
from apps.presence.models import Presence, PresenceHistory, FavoriteDestination, ScheduledStatus
from .events import event_publisher, MemoryEventPublisher
from .serializers import (
    PresenceListSerializer, 
    PresenceSerializer, 
    PresenceUpdateSerializer,
    FavoriteDestinationSerializer,
    FavoriteDestinationCreateSerializer,
    ScheduledStatusSerializer
)
from .services.current_employee import get_current_employee


class SSEEventStreamView(APIView):
    """
    Server-Sent Events (SSE) による状態更新ストリーム配信エンドポイント。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        is_memory_bus = isinstance(event_publisher, MemoryEventPublisher)
        q = event_publisher.register() if is_memory_bus else queue.Queue()

        def event_stream():
            yield "event: welcome\ndata: {}\n\n"
            try:
                while True:
                    try:
                        # 30秒間キューからのイベント発生を待つ
                        event_name, data = q.get(timeout=30)
                        yield f"event: {event_name}\ndata: {json.dumps(data)}\n\n"
                    except queue.Empty:
                        # 30秒イベントがない場合はハートビートを送信
                        yield "event: heartbeat\ndata: {}\n\n"
            finally:
                if is_memory_bus:
                    event_publisher.unregister(q)

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class PresenceListView(ListAPIView):
    """
    一覧画面表示用データ取得API。
    """
    serializer_class = PresenceListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # N+1問題を防ぐため select_related / prefetch_related を使用
        queryset = Employee.objects.filter(deleted_at__isnull=True).select_related(
            'department', 'group', 'work_location', 'presence', 'presence__status'
        )
        
        department_id = self.request.query_params.get('department')
        group_id = self.request.query_params.get('group')
        
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if group_id:
            queryset = queryset.filter(group_id=group_id)
            
        return queryset


class MyPresenceUpdateView(APIView):
    """
    ログイン中の自分の現在の所在状態を更新および取得するAPI。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(
                {
                    "error_code": "E0002",
                    "message": "ログインユーザーに対応する社員情報が見つかりません。"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        presence = getattr(employee, 'presence', None)
        presence_data = PresenceSerializer(presence).data if presence else None
        
        data = {
            "id": employee.id,
            "employee_no": employee.employee_no,
            "name": employee.name,
            "email": employee.email,
            "department": employee.department_id,
            "department_name": employee.department.name if employee.department else None,
            "group": employee.group_id,
            "group_name": employee.group.name if employee.group else None,
            "is_staff": request.user.is_staff or request.user.is_superuser,
            "presence": presence_data
        }
        return Response(data, status=status.HTTP_200_OK)

    def patch(self, request, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(
                {
                    "error_code": "E0002",
                    "message": "ログインユーザーに対応する社員情報が見つかりません。"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = PresenceUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "error_code": "E0001",
                    "message": "バリデーションエラーが発生しました。",
                    "details": serializer.errors
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        status_name = validated_data['status']
        destination = validated_data.get('destination', '')
        return_time = validated_data.get('return_time')

        try:
            status_master = StatusMaster.objects.get(name=status_name)
        except StatusMaster.DoesNotExist:
            return Response(
                {
                    "error_code": "E0003",
                    "message": f"状態コード {status_name} は存在しません。"
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        with transaction.atomic():
            now = timezone.now()
            
            presence, created = Presence.objects.get_or_create(
                employee=employee,
                defaults={
                    'status': status_master,
                    'destination': destination,
                    'start_datetime': now,
                    'end_datetime': return_time,
                    'updated_by': request.user
                }
            )

            if not created:
                presence.status = status_master
                presence.destination = destination
                presence.start_datetime = now
                presence.end_datetime = return_time
                presence.updated_by = request.user
                presence.save()

            # 履歴テーブルへの追記
            PresenceHistory.objects.create(
                employee=employee,
                status=status_master,
                destination=destination,
                start_datetime=now,
                end_datetime=return_time,
                updated_by=request.user
            )

        # SSE イベントを発行
        # ISO8601フォーマットで日付と時間をフロントへ渡す
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

        return Response(PresenceSerializer(presence).data, status=status.HTTP_200_OK)


class SearchAPIView(ListAPIView):
    """
    社員および在籍状態の検索API。
    AIエージェントや自然言語クエリに対応する高度な検索機能を提供します。
    """
    serializer_class = PresenceListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Employee.objects.filter(deleted_at__isnull=True).select_related(
            'department', 'group', 'work_location', 'presence', 'presence__status'
        )

        q = self.request.query_params.get('q')
        name = self.request.query_params.get('name')
        employee_no = self.request.query_params.get('employee_no')
        status_name = self.request.query_params.get('status')
        department_id = self.request.query_params.get('department')
        group_id = self.request.query_params.get('group')

        if q:
            query_dto = SearchParser.parse_query(q)
            conditions = SearchBuilder.build_conditions(query_dto)
            if conditions:
                queryset = queryset.filter(*conditions)

        if name:
            queryset = queryset.filter(name__icontains=name)
        if employee_no:
            queryset = queryset.filter(employee_no__iexact=employee_no)
        if status_name:
            queryset = queryset.filter(presence__status__name__iexact=status_name.upper())
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        if group_id:
            queryset = queryset.filter(group_id=group_id)

        return queryset

class FavoriteDestinationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        favorites = FavoriteDestination.objects.filter(employee=employee).order_by('display_order', '-created_at')
        serializer = FavoriteDestinationSerializer(favorites, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        serializer = FavoriteDestinationCreateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                favorite = FavoriteDestination.objects.create(
                    employee=employee,
                    destination=serializer.validated_data['destination'],
                    display_order=serializer.validated_data.get('display_order', 0)
                )
                return Response(FavoriteDestinationSerializer(favorite).data, status=status.HTTP_201_CREATED)
            except Exception:
                return Response(
                    {"error_code": "E0004", "message": "この行先は既にお気に入りに登録されています。"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(
            {"error_code": "E0001", "message": "バリデーションエラーが発生しました。", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

class FavoriteDestinationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk, *args, **kwargs):
        try:
            employee = get_current_employee(request)
            favorite = FavoriteDestination.objects.get(id=pk, employee=employee)
            favorite.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except (Employee.DoesNotExist, FavoriteDestination.DoesNotExist):
            return Response(
                {"error_code": "E0005", "message": "指定されたお気に入り行先が見つかりません。"},
                status=status.HTTP_404_NOT_FOUND
            )

class RecentDestinationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
            
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        recent_histories = (
            PresenceHistory.objects
            .filter(employee=employee, created_at__gte=thirty_days_ago)
            .exclude(destination__exact='')
            .exclude(destination__isnull=True)
            .values('destination')
            .annotate(last_used=Max('created_at'))
            .order_by('-last_used')[:20]
        )
        
        destinations = [{"destination": item["destination"]} for item in recent_histories]
        return Response(destinations, status=status.HTTP_200_OK)

class ScheduledStatusListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        today = timezone.localdate()
        thirty_days_later = today + timedelta(days=30)

        scheduled = ScheduledStatus.objects.filter(
            employee=employee,
            deleted_at__isnull=True,
            target_date__gte=today,
            target_date__lte=thirty_days_later
        ).order_by('target_date', 'start_time')

        serializer = ScheduledStatusSerializer(scheduled, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = ScheduledStatusSerializer(data=request.data)
        if serializer.is_valid():
            try:
                status_master = StatusMaster.objects.get(name=serializer.validated_data['status'])
            except StatusMaster.DoesNotExist:
                return Response({"error_code": "E0003", "message": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                scheduled = ScheduledStatus.objects.create(
                    employee=employee,
                    target_date=serializer.validated_data['target_date'],
                    status=status_master,
                    destination=serializer.validated_data.get('destination', ''),
                    start_time=serializer.validated_data.get('start_time'),
                    end_time=serializer.validated_data.get('end_time'),
                    memo=serializer.validated_data.get('memo', ''),
                    created_by=request.user,
                    updated_by=request.user
                )
                return Response(ScheduledStatusSerializer(scheduled).data, status=status.HTTP_201_CREATED)
            except Exception:
                return Response(
                    {"error_code": "E0004", "message": "指定された日付にはすでに予定が登録されています。"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {"error_code": "E0001", "message": "バリデーションエラー", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

class ScheduledStatusDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, employee):
        try:
            return ScheduledStatus.objects.get(id=pk, employee=employee, deleted_at__isnull=True)
        except ScheduledStatus.DoesNotExist:
            return None

    def patch(self, request, pk, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        scheduled = self.get_object(pk, employee)
        if not scheduled:
            return Response({"error_code": "E0005", "message": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        # 対象日より前のみ変更可能
        if scheduled.target_date <= timezone.localdate():
            return Response(
                {"error_code": "E0006", "message": "当日または過去の予定は変更できません。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # PATCHは一部のフィールドだけ送信される可能性があるので、既存データをマージして検証する方がDRFでは良いが、
        # ここでは Serializer に instance を渡して partial=True で検証する。
        serializer = ScheduledStatusSerializer(scheduled, data=request.data, partial=True)
        if serializer.is_valid():
            if 'status' in serializer.validated_data:
                try:
                    status_master = StatusMaster.objects.get(name=serializer.validated_data['status'])
                    scheduled.status = status_master
                except StatusMaster.DoesNotExist:
                    return Response({"error_code": "E0003", "message": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
            
            if 'target_date' in serializer.validated_data:
                scheduled.target_date = serializer.validated_data['target_date']
            if 'destination' in serializer.validated_data:
                scheduled.destination = serializer.validated_data['destination']
            if 'start_time' in serializer.validated_data:
                scheduled.start_time = serializer.validated_data['start_time']
            # Noneが明示的に渡される場合もあるため、dictにキーが含まれているかで判定する
            if 'end_time' in serializer.validated_data:
                scheduled.end_time = serializer.validated_data['end_time']
            if 'end_time' in request.data and request.data['end_time'] is None:
                scheduled.end_time = None
            if 'memo' in serializer.validated_data:
                scheduled.memo = serializer.validated_data['memo']
            
            scheduled.updated_by = request.user
            try:
                scheduled.save()
                return Response(ScheduledStatusSerializer(scheduled).data, status=status.HTTP_200_OK)
            except Exception:
                return Response(
                    {"error_code": "E0004", "message": "指定された日付にはすでに予定が登録されています。"},
                    status=status.HTTP_400_BAD_REQUEST
                )

        return Response(
            {"error_code": "E0001", "message": "バリデーションエラー", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk, *args, **kwargs):
        try:
            employee = get_current_employee(request)
        except Employee.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        scheduled = self.get_object(pk, employee)
        if not scheduled:
            return Response({"error_code": "E0005", "message": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        if scheduled.target_date <= timezone.localdate():
            return Response(
                {"error_code": "E0006", "message": "当日または過去の予定は取消できません。"},
                status=status.HTTP_400_BAD_REQUEST
            )

        scheduled.deleted_at = timezone.now()
        scheduled.updated_by = request.user
        scheduled.save()

        return Response(status=status.HTTP_204_NO_CONTENT)
