from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    DepartmentViewSet,
    EmployeeViewSet,
    GroupViewSet,
    StatusMasterViewSet,
    WorkLocationViewSet,
)

router = DefaultRouter()
router.register(r'departments', DepartmentViewSet, basename='department')
router.register(r'groups', GroupViewSet, basename='group')
router.register(r'work-locations', WorkLocationViewSet, basename='work-location')
router.register(r'status-masters', StatusMasterViewSet, basename='status-master')
router.register(r'employees', EmployeeViewSet, basename='employee')

urlpatterns = [
    path('', include(router.urls)),
]
