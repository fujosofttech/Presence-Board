from django.urls import path
from .views import (
    SSEEventStreamView, 
    PresenceListView, 
    MyPresenceUpdateView, 
    SearchAPIView,
    FavoriteDestinationListView,
    FavoriteDestinationDetailView,
    RecentDestinationListView
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
]
