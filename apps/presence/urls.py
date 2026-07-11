from django.urls import path
from .views import SSEEventStreamView

app_name = 'presence'

urlpatterns = [
    path('events/stream/', SSEEventStreamView.as_view(), name='sse-stream'),
]
