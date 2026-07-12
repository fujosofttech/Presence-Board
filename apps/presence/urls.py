from django.urls import path
from .views import (
    SSEEventStreamView, 
    PresenceListView, 
    MyPresenceUpdateView, 
    SearchAPIView,
    FavoriteDestinationListView,
    FavoriteDestinationDetailView,
    RecentDestinationListView,
    ScheduledStatusListCreateView,
    ScheduledStatusDetailView
)

app_name = 'presence'

urlpatterns = [
    path('events/stream/', SSEEventStreamView.as_view(), name='sse-stream'),
    path('presence/', PresenceListView.as_view(), name='presence-list'),
    path('presence/me/', MyPresenceUpdateView.as_view(), name='presence-me'),
    path('presence/search/', SearchAPIView.as_view(), name='presence-search'),
    path('destinations/favorites/', FavoriteDestinationListView.as_view(), name='favorite-list'),
    path('destinations/favorites/<int:pk>/', FavoriteDestinationDetailView.as_view(), name='favorite-detail'),
    path('destinations/recent/', RecentDestinationListView.as_view(), name='recent-list'),
    path('scheduled-status/', ScheduledStatusListCreateView.as_view(), name='scheduled-status-list'),
    path('scheduled-status/<int:pk>/', ScheduledStatusDetailView.as_view(), name='scheduled-status-detail'),
]
