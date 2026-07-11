import time
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

class SSEEventStreamView(APIView):
    """
    Server-Sent Events (SSE) による状態更新ストリーム配信エンドポイント。
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        def event_stream():
            yield "event: welcome\ndata: {}\n\n"
            while True:
                time.sleep(30)
                yield "event: heartbeat\ndata: {}\n\n"

        response = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response
