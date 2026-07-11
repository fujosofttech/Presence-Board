import json
import queue
from django.db import transaction
from django.http import StreamingHttpResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.employees.models import Employee, StatusMaster
from apps.presence.models import Presence, PresenceHistory
from .events import event_bus
from .serializers import PresenceListSerializer, PresenceSerializer, PresenceUpdateSerializer


class SSEEventStreamView(APIView):
    """
    Server-Sent Events (SSE) による状態更新ストリーム配信エンドポイント。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        q = event_bus.register()

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
                event_bus.unregister(q)

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
    ログイン中の自分の現在の所在状態を更新するAPI。
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        try:
            employee = Employee.objects.get(email=request.user.email, deleted_at__isnull=True)
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
                    'updated_by': request.user.id
                }
            )

            if not created:
                presence.status = status_master
                presence.destination = destination
                presence.start_datetime = now
                presence.end_datetime = return_time
                presence.updated_by = request.user.id
                presence.save()

            # 履歴テーブルへの追記
            PresenceHistory.objects.create(
                employee=employee,
                status=status_master,
                destination=destination,
                start_datetime=now,
                end_datetime=return_time,
                updated_by=request.user.id
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
        
        event_bus.broadcast("presence_updated", event_data)

        return Response(PresenceSerializer(presence).data, status=status.HTTP_200_OK)
