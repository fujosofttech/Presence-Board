"""
URL configuration for Presence Board project.
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import IndexView

urlpatterns = [
    # 管理画面
    path('admin/', admin.site.urls),

    # OpenAPI スキーマ (AI エージェント向け)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI (開発者向け)
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # API v1
    path('api/v1/', include('apps.presence.urls')),
    path('api/v1/', include('apps.employees.urls')),

    # フロントエンド SPA エントリーポイント (フォールバック)
    re_path(r'^.*$', IndexView.as_view(), name='index'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

