from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DepartmentViewSet,
    EmployeeViewSet,
    GroupViewSet,
    StatusMasterViewSet,
    WorkLocationViewSet,
    AuthView,
    LogoutView,
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'work-locations', WorkLocationViewSet, basename='work-location')
router.register(r'status-masters', StatusMasterViewSet, basename='status-master')
router.register(r'employees', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('auth/', AuthView.as_view(), name='auth'),
    path('auth/logout/', LogoutView.as_view(), name='logout'),
    path('', include(router.urls)),
]

